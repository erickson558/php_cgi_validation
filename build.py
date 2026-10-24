"""Compila la GUI Windows junto a sus fuentes y genera sumas SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

from app_version import APP_VERSION, VERSION
from scripts.bump_version import check

ROOT = Path(__file__).resolve().parent


def third_party_notices():
    """Conserva licencias del intérprete, toolkit y cargador incluidos en el binario."""
    candidates = [Path(sys.base_prefix) / "LICENSE.txt"]
    candidates.extend((Path(sys.base_prefix) / "tcl").glob("*/license.terms"))
    distribution = importlib.metadata.distribution("pyinstaller")
    candidates.extend(distribution.locate_file(file) for file in distribution.files or []
                      if str(file).endswith(("COPYING.txt", "LICENSE.txt", "COPYING", "LICENSE")))
    sections = []
    for path in candidates:
        if path.is_file():
            sections.append(f"--- {path.parent.name}/{path.name} ---\n" + path.read_text(encoding="utf-8", errors="replace"))
    if not sections:
        raise RuntimeError("No se localizaron avisos de licencia de terceros.")
    target = ROOT / "THIRD_PARTY_NOTICES.txt"
    target.write_text("Licencias de componentes redistribuidos\n\n" + "\n\n".join(sections), encoding="utf-8")
    return target


def version_resource(path: Path):
    """Añade metadatos de versión visibles en las propiedades del .exe."""
    numbers = tuple(map(int, VERSION.split("."))) + (0,)
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers!r}, prodvers={numbers!r}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'erickson558'),
    StringStruct('FileDescription', 'PHP version exposure assessment'),
    StringStruct('FileVersion', '{VERSION}'),
    StringStruct('ProductName', 'php_cgi_validation'),
    StringStruct('ProductVersion', '{APP_VERSION}'),
    StringStruct('LegalCopyright', 'Copyright 2026 erickson558')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
"""
    path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validar sin compilar")
    args = parser.parse_args()
    check(ROOT)
    for name in ("app.ico", "LICENSE", "NOTICE", "php_audit_gui.py"):
        if not (ROOT / name).is_file():
            parser.error(f"Falta {name}")
    if args.check:
        print(f"Configuración válida: {APP_VERSION}")
        return
    if os.name != "nt":
        parser.error("El ejecutable Windows debe compilarse en Windows.")
    work = ROOT / "build"
    work.mkdir(exist_ok=True)
    resource = work / "version_info.txt"
    version_resource(resource)
    notices = third_party_notices()
    name = f"php_cgi_validation-{APP_VERSION}"
    # Argumentos separados y sin shell: las rutas nunca se ejecutan como comandos.
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
               "--onefile", "--windowed", "--noupx", "--name", name,
               "--distpath", str(ROOT), "--workpath", str(work / "pyinstaller"),
               "--specpath", str(work), "--icon", str(ROOT / "app.ico"),
               "--version-file", str(resource), "--add-data", f"{ROOT / 'app.ico'}{os.pathsep}.",
               "--add-data", f"{ROOT / 'LICENSE'}{os.pathsep}.",
               "--add-data", f"{ROOT / 'NOTICE'}{os.pathsep}.",
               "--add-data", f"{notices}{os.pathsep}.",
               str(ROOT / "php_audit_gui.py")]
    print(subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    executable = ROOT / f"{name}.exe"
    with executable.open("rb") as binary:
        digest = hashlib.sha256(binary.read()).hexdigest()
    (ROOT / "SHA256SUMS.txt").write_text(f"{digest}  {executable.name}\n", encoding="ascii")
    print(f"Generado: {executable.name}")


if __name__ == "__main__":
    main()
