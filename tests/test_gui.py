"""Verifica comportamientos visibles sin abrir navegadores ni contactar terceros."""

import gc
import threading
import time
import tkinter as tk
import unittest
import weakref
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from app_version import APP_VERSION
from php_audit import AuditResult
from php_audit_gui import AuditApp, DONATION_URL


class GuiTests(unittest.TestCase):
    def setUp(self):
        # Los entornos CI sin servidor gráfico omiten estas pruebas explícitamente.
        try:
            self.app = AuditApp()
            self.app.withdraw()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.close()
            # Destruir widgets no elimina por sí solo los ciclos Python de Tk.
            # Soltamos la referencia y ejecutamos GC en el hilo principal antes
            # de que otro test cree un trabajador que pueda iniciar el GC allí.
            del self.app
            gc.collect()

    def pump_until(self, predicate, timeout=8):
        """Procesa eventos reales de Tk mientras termina una operación corta."""
        deadline = time.monotonic() + timeout
        while not predicate():
            self.app.update()
            if time.monotonic() > deadline:
                self.fail("GUI operation timed out")
            time.sleep(0.01)
        self.app.update()

    def test_language_switch_preserves_input_evidence_and_selection(self):
        app = self.app
        url = "http://127.0.0.1/"
        app.targets.delete("1.0", "end")
        app.targets.insert("1.0", url)
        result = AuditResult(url, "2026-10-24T00:00:00+00:00", 200, "test", "PHP/8.2.34",
                             "8.2.34", "POSIBLE AFECTACIÓN", "Evidencia original", "Revisar paquete")
        app.results.append(result)
        app.table.insert("", "end", iid="0", values=app.row_values(result))
        app.table.selection_set("0")
        app.set_language("en")
        self.assertIn(APP_VERSION, app.title())
        self.assertEqual(app.start_button["text"], "Assess URLs")
        self.assertEqual(app.table.item("0", "values")[-1], "POSSIBLY AFFECTED")
        self.assertIn("advertised PHP version", app.details.get("1.0", "end"))
        self.assertEqual(app.targets.get("1.0", "end").strip(), url)
        self.assertEqual(result.detail, "Evidencia original")
        app.set_language("es")
        self.assertEqual(app.table.selection(), ("0",))
        self.assertEqual(app.start_button["text"], "Evaluar URLs")
        self.assertIn("Evidencia original", app.details.get("1.0", "end"))

    def test_donation_only_opens_fixed_link_on_click(self):
        with patch("php_audit_gui.webbrowser.open_new_tab", return_value=True) as browser:
            self.app.set_language("en")
            browser.assert_not_called()
            self.app.donate_button.invoke()
            browser.assert_called_once_with(DONATION_URL)

    def test_unexpected_url_failure_does_not_abort_remaining_urls(self):
        app = self.app
        app.targets.delete("1.0", "end")
        app.targets.insert("1.0", "http://127.0.0.1/first\nhttp://127.0.0.1/second")
        good = AuditResult("http://127.0.0.1/second", "2026-10-24T00:00:00+00:00", 200,
                           "", "", "", "INCONCLUSO", "Sin versión", "Revisar paquete")
        with patch("php_audit_gui.audit_url", side_effect=[RuntimeError("unexpected"), good]) as audit:
            app.start_button.invoke()
            self.pump_until(lambda: not app.running)
        self.assertEqual(audit.call_count, 2)
        self.assertEqual([r.state for r in app.results], ["ERROR", "INCONCLUSO"])
        self.assertEqual(str(app.export_button["state"]), "normal")

    def test_local_request_cancel_keeps_completed_result(self):
        # La primera respuesta se bloquea controladamente para cancelar con red activa.
        app = self.app
        started, release = threading.Event(), threading.Event()
        hits = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                started.set()
                release.wait(5)
                self.send_response(200)
                self.send_header("X-Powered-By", "PHP/8.5.12")
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            app.targets.delete("1.0", "end")
            app.targets.insert("1.0", base + "/first\n" + base + "/second")
            app.start_button.invoke()
            self.pump_until(started.is_set)
            app.set_language("en")
            app.cancel_button.invoke()
            release.set()
            self.pump_until(lambda: not app.running)
            self.assertEqual(hits, ["/first"])
            self.assertEqual(len(app.results), 1)
            self.assertIn("Stopped: 1 / 2", app.status.get())
            self.assertEqual(str(app.start_button["state"]), "normal")
        finally:
            release.set()
            server.shutdown()
            server.server_close()
            thread.join()

    def test_closing_during_request_releases_tk_on_main_thread(self):
        """Un trabajador activo no debe retener la ventana ni su intérprete Tcl."""
        started, release = threading.Event(), threading.Event()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                started.set()
                release.wait(5)
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            self.app.targets.delete("1.0", "end")
            self.app.targets.insert("1.0", f"http://127.0.0.1:{server.server_port}/")
            self.app.start_button.invoke()
            self.pump_until(started.is_set)
            worker = self.app.worker
            reference = weakref.ref(self.app)
            self.app.close()
            del self.app
            gc.collect()
            self.assertIsNone(reference(), "El trabajador está reteniendo objetos Tk")
            release.set()
            worker.join(5)
            self.assertFalse(worker.is_alive())
        finally:
            release.set()
            server.shutdown()
            server.server_close()
            server_thread.join()


if __name__ == "__main__":
    unittest.main()
