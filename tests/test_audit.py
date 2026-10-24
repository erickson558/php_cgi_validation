import csv
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from check_cgi import fetch, local_url
from php_audit import (MAX_INPUT_BYTES, MAX_TARGETS, MAX_URL_LENGTH, assess_version,
                       audit_url, csv_cell, export_results, normalize_url, parse_targets)


class TestHandler(BaseHTTPRequestHandler):
    hits = []

    def do_GET(self):
        type(self).hits.append(self.path)
        routes = {
            "/old": (200, "PHP/8.2.34"),
            "/fixed": (200, "PHP/8.2.35"),
            "/hidden": (200, None),
            "/denied": (403, None),
            "/error": (500, "PHP/8.4.26"),
            "/redirect": (302, None),
            "/conflict": (200, "PHP/8.2.34; PHP/8.2.35"),
            "/huge": (200, "PHP/8.2.35; " + "a" * 17000),
            "/huge-version": (200, "PHP/" + "9" * 5000 + ".2.35"),
            "/folded": (200, "PHP/8.2.35\r\n X-Fake: evidence"),
        }
        code, banner = routes.get(self.path, (404, None))
        self.send_response(code)
        if banner:
            self.send_header("x-powered-by", banner)
        if self.path == "/redirect":
            self.send_header("Location", "/old")
        self.end_headers()

    def log_message(self, *args):
        pass


class VersionTests(unittest.TestCase):
    def test_fixed_boundaries_for_both_cves(self):
        for branch, fixed_patch in (("8.2", 35), ("8.3", 36), ("8.4", 27), ("8.5", 12)):
            with self.subTest(branch=branch):
                self.assertEqual(assess_version(f"{branch}.{fixed_patch - 1}").state, "POSIBLE AFECTACIÓN")
                self.assertEqual(assess_version(f"{branch}.{fixed_patch}").state, "VERSIÓN CON CORRECCIÓN")
                self.assertEqual(assess_version(f"{branch}.{fixed_patch + 1}").state, "VERSIÓN CON CORRECCIÓN")

    def test_prerelease_and_unknown_never_claim_correction(self):
        for version in ("", "8.2", "8.2.35RC1", "8.5.12-dev", "8.6.0", "9.0.0"):
            with self.subTest(version=version):
                self.assertEqual(assess_version(version).state, "INCONCLUSO")

    def test_vendor_backport_caveat(self):
        for version in ("8.2.34-1ubuntu1", "8.1.33-1", "7.4.33"):
            with self.subTest(version=version):
                self.assertEqual(assess_version(version).state, "POSIBLE AFECTACIÓN")

    def test_target_validation_before_network(self):
        for url in ("file:///etc/passwd", "example.com", "https://user:pass@example.com/",
                    "https://example.com:invalid", "https://example.com/\nheader", "https://example.com/a b"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_url(url)
        self.assertEqual(normalize_url("http://[::1]:888/#fragment"), "http://[::1]:888/")
        self.assertEqual(normalize_url("https://ejemplo.mx/ruta?q=1#parte"), "https://ejemplo.mx/ruta?q=1")

    def test_batch_comments_and_deduplication(self):
        self.assertEqual(parse_targets("# cliente\nhttps://example.com\n\nhttps://example.com/\n"),
                         ["https://example.com/"])
        with self.assertRaisesRegex(ValueError, "Línea 2"):
            parse_targets("https://example.com\ninvalid")

    def test_resource_limits_reject_oversized_inputs(self):
        # Los límites se comprueban antes de crear peticiones o convertir enteros.
        with self.assertRaises(ValueError):
            normalize_url("https://example.com/" + "a" * MAX_URL_LENGTH)
        with self.assertRaises(ValueError):
            parse_targets("#" + "a" * MAX_INPUT_BYTES)
        with self.assertRaises(ValueError):
            parse_targets("\n".join(f"https://example.com/{i}" for i in range(MAX_TARGETS + 1)))
        self.assertEqual(assess_version("9" * 5000 + ".2.35").state, "INCONCLUSO")

    def test_malformed_version_does_not_claim_a_fix(self):
        for version in ("8.2.35.9", "8.2.35evil", "8.2.35/extra"):
            with self.subTest(version=version):
                self.assertEqual(assess_version(version).state, "INCONCLUSO")

    def test_local_helper_rejects_remote_destinations(self):
        self.assertEqual(local_url("http://localhost:8080/a#b"), "http://127.0.0.1:8080/a")
        with self.assertRaises(ValueError):
            local_url("https://example.com/")

    def test_csv_formula_prefixes(self):
        for value in ("=1+1", "+1", "-1", "@SUM(1)", "\t=1", "\ufeff=1"):
            self.assertEqual(csv_cell(value), "'" + value)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_normal_get_and_version_evidence(self):
        TestHandler.hits.clear()
        result = audit_url(self.base + "/old")
        self.assertEqual(TestHandler.hits, ["/old"])
        self.assertEqual(result.php_version, "8.2.34")
        self.assertEqual(result.state, "POSIBLE AFECTACIÓN")
        self.assertEqual(len(result.cves), 2)

    def test_fixed_banner(self):
        self.assertEqual(audit_url(self.base + "/fixed").state, "VERSIÓN CON CORRECCIÓN")

    def test_missing_and_conflicting_banners(self):
        for route in ("/hidden", "/conflict"):
            self.assertEqual(audit_url(self.base + route).state, "INCONCLUSO")

    def test_http_errors_do_not_prove_vulnerability(self):
        denied = audit_url(self.base + "/denied")
        self.assertEqual(denied.http_status, 403)
        self.assertEqual(denied.state, "INCONCLUSO")
        error = audit_url(self.base + "/error")
        self.assertEqual(error.http_status, 500)
        self.assertEqual(error.state, "POSIBLE AFECTACIÓN")
        self.assertEqual(error.php_version, "8.4.26")

    def test_redirect_does_not_contact_destination(self):
        TestHandler.hits.clear()
        result = audit_url(self.base + "/redirect")
        self.assertEqual(TestHandler.hits, ["/redirect"])
        self.assertEqual(result.http_status, 302)
        self.assertEqual(result.state, "INCONCLUSO")
        self.assertIn("sin seguir", result.detail)

    def test_legacy_helper_also_blocks_redirects(self):
        TestHandler.hits.clear()
        result = fetch(self.base + "/redirect")
        self.assertEqual(TestHandler.hits, ["/redirect"])
        self.assertEqual(result["status"], 302)

    def test_malicious_header_input_stays_bounded(self):
        self.assertEqual(audit_url(self.base + "/huge").state, "ERROR")
        self.assertEqual(audit_url(self.base + "/huge-version").state, "INCONCLUSO")
        folded = audit_url(self.base + "/folded")
        self.assertNotIn("\n", folded.x_powered_by)
        self.assertIn("\\x0a", folded.x_powered_by)

    def test_closed_port_is_error(self):
        unused = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        port = unused.server_port
        unused.server_close()
        result = audit_url(f"http://127.0.0.1:{port}/", timeout=1)
        self.assertEqual(result.state, "ERROR")
        self.assertTrue(result.error)

    def test_reports_preserve_evidence_and_neutralize_csv_formulas(self):
        result = audit_url(self.base + "/old")
        result.server = "=HYPERLINK(\"example\")"
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "report.json"
            csv_path = Path(directory) / "report.csv"
            export_results([result], json_path)
            export_results([result], csv_path)
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["results"][0]["php_version"], "8.2.34")
            self.assertTrue(report["limitation"])
            self.assertIn("115560", report["additional_notice"])
            with csv_path.open(encoding="utf-8-sig", newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(rows[0]["server"], "'" + result.server)
            self.assertIn("CVE-2026-109618", rows[0]["cves"])

    def test_failed_export_keeps_existing_report(self):
        result = audit_url(self.base + "/old")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            target.write_text("previous report", encoding="utf-8")
            with patch("php_audit.os.replace", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    export_results([result], target)
            self.assertEqual(target.read_text(encoding="utf-8"), "previous report")
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
