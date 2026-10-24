"""Interfaz bilingüe de evaluación PHP. Ejecutar: python php_audit_gui.py."""

import argparse
import gc
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app_version import APP_VERSION, VERSION
from i18n import result_explanation, translate
from php_audit import (ADVISORY_URL, CVES, MAX_INPUT_BYTES, RULES_DATE, AuditResult,
                       audit_url, export_results, parse_targets)


# El enlace es fijo; ninguna respuesta remota puede cambiar el destino del botón.
DONATION_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


def run_batch(targets, timeout, events, stop):
    """Consulta sin retener la ventana ni ningún objeto Tk en el hilo de red."""
    try:
        for url in targets:
            if stop.is_set():
                break
            try:
                result = audit_url(url, timeout)
            except Exception as exc:
                result = AuditResult(url, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                     None, "", "", "", "ERROR",
                                     translate("es", "unexpected_detail"),
                                     translate("es", "unexpected_action"), str(exc)[:1000])
            events.put(("result", result))
            # La pausa se interrumpe al detener; no se ejecutan peticiones en paralelo.
            if stop.wait(0.3):
                break
    finally:
        events.put(("done", len(targets)))


class AuditApp(tk.Tk):
    """Coordina los controles Tk y recibe resultados mediante una cola segura."""

    def __init__(self):
        super().__init__()
        self.geometry("1160x840")
        self.minsize(920, 700)
        self.results = []
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.running = False
        self.worker = None
        self.language = "es"
        self.status_key, self.status_values = "ready", {}
        self.translated_widgets = []
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_ui()
        self.set_language("es")
        self.load_icon()
        self.poll_id = self.after(100, self.poll)

    def tr(self, key, **values):
        """Abrevia el acceso al catálogo del idioma activo."""
        return translate(self.language, key, **values)

    def label(self, parent, key, **options):
        """Registra etiquetas para traducirlas sin reconstruir la ventana."""
        widget = ttk.Label(parent, **options)
        self.translated_widgets.append((widget, key))
        return widget

    def build_ui(self):
        """Crea entradas, acciones, tabla y panel de evidencia una sola vez."""
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        heading = ttk.Frame(root)
        heading.pack(fill="x")
        self.label(heading, "heading", font=("Segoe UI", 19, "bold")).pack(side="left")
        self.language_choice = tk.StringVar(value="Español")
        self.language_select = ttk.Combobox(heading, values=("Español", "English"),
                                            textvariable=self.language_choice, state="readonly", width=10)
        self.language_select.pack(side="right")
        self.language_select.bind("<<ComboboxSelected>>", self.change_language)
        self.label(heading, "language").pack(side="right", padx=6)
        self.rules_label = ttk.Label(root)
        self.rules_label.pack(anchor="w", pady=(2, 8))
        self.label(root, "scope").pack(anchor="w")
        self.label(root, "method").pack(anchor="w")
        self.targets = tk.Text(root, height=5, wrap="none", font=("Consolas", 10))
        self.targets.pack(fill="x", pady=8)
        self.targets.insert("1.0", "http://localhost:888/diagnostic.php\n")

        # El idioma y la donación siguen disponibles durante una evaluación.
        controls = ttk.Frame(root)
        controls.pack(fill="x")
        self.load_button = ttk.Button(controls, command=self.load_targets)
        self.load_button.pack(side="left")
        self.label(controls, "timeout").pack(side="left")
        self.timeout = tk.StringVar(value="8")
        self.timeout_input = ttk.Spinbox(controls, from_=1, to=30, textvariable=self.timeout, width=4)
        self.timeout_input.pack(side="left")
        self.start_button = ttk.Button(controls, command=self.start)
        self.start_button.pack(side="left", padx=12)
        self.cancel_button = ttk.Button(controls, command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left")
        self.export_button = ttk.Button(controls, command=self.export, state="disabled")
        self.export_button.pack(side="right")
        for widget, key in ((self.load_button, "load"), (self.start_button, "start"),
                            (self.cancel_button, "cancel"), (self.export_button, "export")):
            self.translated_widgets.append((widget, key))

        self.status = tk.StringVar()
        ttk.Label(root, textvariable=self.status).pack(anchor="w", pady=(10, 4))
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 8))
        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_frame, columns=("url", "http", "version", "state"),
                                 show="headings", height=8)
        for key, width in (("url", 430), ("http", 55), ("version", 140), ("state", 235)):
            self.table.column(key, width=width, minwidth=50)
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        for state, color in (("POSIBLE AFECTACIÓN", "#a4262c"),
                             ("VERSIÓN CON CORRECCIÓN", "#18643a"), ("ERROR", "#9b4d00")):
            self.table.tag_configure(state, foreground=color)
        self.table.bind("<<TreeviewSelect>>", self.show_details)

        self.label(root, "evidence", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 2))
        details_frame = ttk.Frame(root)
        details_frame.pack(fill="x")
        self.details = tk.Text(details_frame, height=9, wrap="word", font=("Segoe UI", 10), state="disabled")
        details_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.details.yview)
        self.details.configure(yscrollcommand=details_scroll.set)
        self.details.pack(side="left", fill="x", expand=True)
        details_scroll.pack(side="right", fill="y")
        self.donate_button = ttk.Button(root, command=self.donate)
        self.donate_button.pack(anchor="e", pady=(10, 0))
        self.translated_widgets.append((self.donate_button, "donate"))

    def load_icon(self):
        """Resuelve el recurso tanto desde fuentes como desde un ejecutable onefile."""
        resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        icon = resource_root / "app.ico"
        if icon.is_file():
            try:
                self.iconbitmap(str(icon))
            except tk.TclError:
                # En plataformas sin soporte ICO se conserva el icono del sistema.
                pass

    def change_language(self, _event=None):
        self.set_language("en" if self.language_choice.get() == "English" else "es")

    def set_language(self, language):
        """Actualiza textos y filas conservando URLs, selección y resultados."""
        self.language = language if language in ("es", "en") else "es"
        self.language_choice.set("English" if self.language == "en" else "Español")
        self.title(self.tr("title", version=APP_VERSION))
        for widget, key in self.translated_widgets:
            widget.configure(text=self.tr(key))
        self.rules_label.configure(text=self.tr("rules", cves=" / ".join(CVES), date=RULES_DATE))
        for key in ("url", "http", "version", "state"):
            self.table.heading(key, text=self.tr(key))
        self.status.set(self.tr(self.status_key, **self.status_values))
        for index, result in enumerate(self.results):
            self.table.item(str(index), values=self.row_values(result))
        if self.table.selection():
            self.show_details()
        else:
            self.set_details(self.general_notice())

    def general_notice(self):
        return f"{self.tr('limitation')}\n\n{self.tr('notice')}\n\n{self.tr('source')}: {ADVISORY_URL}"

    def set_status(self, key, **values):
        self.status_key, self.status_values = key, values
        self.status.set(self.tr(key, **values))

    def row_values(self, result):
        return (result.url, result.http_status or "—", result.php_version or self.tr("not_visible"), self.tr(result.state))

    def set_details(self, text):
        """El panel es de solo lectura para no modificar la evidencia accidentalmente."""
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")

    def load_targets(self):
        """Limita el tamaño del archivo antes de cargarlo en la interfaz."""
        path = filedialog.askopenfilename(filetypes=[(self.tr("urls_file"), "*.txt"), (self.tr("all_files"), "*.*")])
        if path:
            try:
                with open(path, "rb") as source:
                    raw = source.read(MAX_INPUT_BYTES + 1)
                if len(raw) > MAX_INPUT_BYTES:
                    raise ValueError("El archivo supera 1 MiB." if self.language == "es" else "The file exceeds 1 MiB.")
                content = raw.decode("utf-8-sig")
                self.targets.delete("1.0", "end")
                self.targets.insert("1.0", content)
            except (OSError, UnicodeError, ValueError) as exc:
                messagebox.showerror(self.tr("load_error"), str(exc))

    def start(self):
        """Valida el lote completo antes de lanzar el único hilo de red."""
        if self.running:
            return
        try:
            targets = parse_targets(self.targets.get("1.0", "end"))
            timeout = float(self.timeout.get())
            if not 1 <= timeout <= 30:
                raise ValueError(self.tr("timeout_error"))
        except ValueError as exc:
            detail = str(exc) if self.language == "es" else self.tr("input_help")
            messagebox.showerror(self.tr("input_error"), detail)
            return
        self.results.clear()
        self.table.delete(*self.table.get_children())
        self.set_details(self.general_notice())
        self.stop.clear()
        self.running = True
        self.targets.configure(state="disabled")
        for widget in (self.load_button, self.start_button, self.export_button, self.timeout_input):
            widget.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress.configure(maximum=len(targets), value=0)
        self.set_status("progress", count=0, total=len(targets))
        # Pasar únicamente datos evita que el último dueño de Tk sea el trabajador.
        self.worker = threading.Thread(target=run_batch,
                                       args=(targets, timeout, self.events, self.stop), daemon=True)
        self.worker.start()

    def poll(self):
        """Solo el hilo principal modifica controles Tk; el trabajador escribe la cola."""
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "result":
                    index = len(self.results)
                    self.results.append(data)
                    self.table.insert("", "end", iid=str(index), values=self.row_values(data), tags=(data.state,))
                    self.progress.configure(value=len(self.results))
                    if not self.stop.is_set():
                        self.set_status("progress", count=len(self.results), total=int(float(self.progress["maximum"])))
                    if index == 0:
                        self.table.selection_set("0")
                elif kind == "done":
                    # La señal se emite después de terminar HTTP; unir aquí no espera red.
                    self.worker.join()
                    self.worker = None
                    self.running = False
                    self.targets.configure(state="normal")
                    for widget in (self.load_button, self.start_button, self.timeout_input):
                        widget.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.export_button.configure(state="normal" if self.results else "disabled")
                    self.set_status("stopped" if self.stop.is_set() else "done", count=len(self.results), total=data)
        except queue.Empty:
            pass
        self.poll_id = self.after(100, self.poll)

    def cancel(self):
        """Detiene nuevas URLs; la conexión activa termina o agota su timeout."""
        self.stop.set()
        self.cancel_button.configure(state="disabled")
        self.set_status("stopping")

    def show_details(self, _event=None):
        selection = self.table.selection()
        if not selection:
            return
        result = self.results[int(selection[0])]
        detail, action = result_explanation(result, self.language)
        self.set_details(
            f"{result.url}\n{self.tr('state')}: {self.tr(result.state)} · HTTP: {result.http_status} · UTC: {result.checked_at_utc}\n"
            f"Server: {result.server or self.tr('not_visible')}\nX-Powered-By: {result.x_powered_by or self.tr('not_visible')}\n"
            f"{detail}\n{self.tr('action')}: {action}\n"
            + (f"Error: {result.error}\n" if result.error else "")
            + f"\n{self.general_notice()}"
        )

    def export(self):
        """Exporta las evidencias canónicas independientemente del idioma visible."""
        if not self.results:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=f"php_audit_{VERSION}.json",
                                          filetypes=[("JSON", "*.json"), ("CSV", "*.csv")])
        if path:
            try:
                export_results(self.results, path)
                self.set_status("saved", path=path)
            except (OSError, ValueError) as exc:
                messagebox.showerror(self.tr("save_error"), str(exc))

    def donate(self):
        """Abre PayPal únicamente por una acción explícita del usuario."""
        try:
            opened = webbrowser.open_new_tab(DONATION_URL)
        except (webbrowser.Error, OSError):
            opened = False
        if not opened:
            messagebox.showinfo(self.tr("donation_error"), self.tr("donation_manual", url=DONATION_URL))

    def close(self):
        """Cancela tareas pendientes y cierra sin dejar callbacks Tk registrados."""
        self.stop.set()
        if hasattr(self, "poll_id"):
            self.after_cancel(self.poll_id)
        self.destroy()


def main():
    """Ofrece versión de consola y prueba de arranque sin enviar tráfico de red."""
    parser = argparse.ArgumentParser(description="PHP version assessment GUI")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = AuditApp()
    if args.smoke_test:
        app.withdraw()
        app.after(100, app.close)
    app.mainloop()
    # Tk crea ciclos entre widgets y variables. Se liberan en el hilo que creó
    # el intérprete antes de que un GC posterior en otro hilo pueda encontrarlos.
    del app
    gc.collect()


if __name__ == "__main__":
    main()
