"""Regresiones de coherencia SemVer y metadatos de compilación."""

import tempfile
import hashlib
import unittest
from pathlib import Path

from scripts.bump_version import bump, check
from scripts.publish_release import should_be_latest, verify_checksum


class VersionToolTests(unittest.TestCase):
    def project(self, root):
        (root / "app_version.py").write_text('VERSION = "1.2.3"\n', encoding="utf-8")
        (root / "README.md").write_text("**Versión: V1.2.3**\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text("# Cambios\n\n## [V1.2.3] - 2026-10-24\n\n- anterior\n", encoding="utf-8")

    def test_major_minor_patch_preserve_previous_history(self):
        for part, expected in (("major", "2.0.0"), ("minor", "1.3.0"), ("patch", "1.2.4")):
            with self.subTest(part=part), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.project(root)
                self.assertEqual(bump(part, root), expected)
                self.assertEqual(check(root), expected)
                self.assertIn("[V1.2.3]", (root / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_mismatch_aborts_without_changing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.project(root)
            (root / "README.md").write_text("**Versión: V0.0.0**\n", encoding="utf-8")
            previous = (root / "app_version.py").read_bytes()
            with self.assertRaises(ValueError):
                bump("patch", root)
            self.assertEqual((root / "app_version.py").read_bytes(), previous)

    def test_release_rejects_stale_or_wrong_filename_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "php_cgi_validation-V1.0.0.exe"
            binary.write_bytes(b"release fixture")
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            checksum = root / "SHA256SUMS.txt"
            checksum.write_text(f"{digest}  {binary.name}\n", encoding="ascii")
            verify_checksum("V1.0.0", root)
            binary.write_bytes(b"changed fixture")
            with self.assertRaisesRegex(ValueError, "no coincide"):
                verify_checksum("V1.0.0", root)
            checksum.write_text(f"{digest}  another.exe\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "exactamente"):
                verify_checksum("V1.0.0", root)

    def test_older_release_recovery_does_not_replace_latest(self):
        self.assertFalse(should_be_latest("V1.2.3", "V2.0.0"))
        self.assertTrue(should_be_latest("V1.10.0", "V1.9.0"))
        self.assertTrue(should_be_latest("V1.0.0", None))
        self.assertFalse(should_be_latest("V1.0.0", "custom-tag"))


if __name__ == "__main__":
    unittest.main()
