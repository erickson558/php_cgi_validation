"""Incrementa SemVer y mantiene sincronizados código, README y changelog."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read_version(root: Path = ROOT) -> str:
    """Lee un literal sin ejecutar código del archivo de versión."""
    tree = ast.parse((root / "app_version.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "VERSION" for t in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", value):
                return value
    raise ValueError("VERSION debe ser un literal SemVer x.y.z válido.")


def check(root: Path = ROOT) -> str:
    """Impide publicar una versión con documentación fuera de sincronía."""
    version = read_version(root)
    readme = (root / "README.md").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if re.findall(r"\*\*Versión: V([^*]+)\*\*", readme) != [version]:
        raise ValueError("README no coincide con VERSION o tiene marcadores duplicados.")
    headings = re.findall(r"^## \[V([^\]]+)\] - \d{4}-\d{2}-\d{2}$", changelog, re.M)
    if not headings or headings[0] != version:
        raise ValueError("La primera versión del CHANGELOG debe coincidir con VERSION.")
    return version


def bump(part: str, root: Path = ROOT) -> str:
    """Prepara un incremento explícito; el commit y la publicación son pasos separados."""
    old = check(root)
    values = list(map(int, old.split(".")))
    index = {"major": 0, "minor": 1, "patch": 2}[part]
    values[index] += 1
    for following in range(index + 1, 3):
        values[following] = 0
    new = ".".join(map(str, values))
    version_path = root / "app_version.py"
    source = version_path.read_text(encoding="utf-8")
    source, count = re.subn(r'^VERSION = "[^"]+"$', f'VERSION = "{new}"', source, count=1, flags=re.M)
    if count != 1:
        raise ValueError("No se encontró la asignación VERSION esperada.")
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8").replace(f"V{old}", f"V{new}")
    changelog_path = root / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    # America/Mexico_City es la zona del proyecto; Windows puede carecer de tzdata.
    try:
        date = datetime.now(ZoneInfo("America/Mexico_City")).date().isoformat()
    except KeyError:
        date = datetime.now(timezone(timedelta(hours=-6))).date().isoformat()
    first = re.search(r"^## \[V", changelog, re.M)
    if first is None:
        raise ValueError("Falta una entrada anterior en CHANGELOG.")
    entry = f"## [V{new}] - {date}\n\n- Describe aquí los cambios antes del commit.\n\n"
    changelog = changelog[:first.start()] + entry + changelog[first.start():]
    # Todo el contenido se valida antes de modificar los tres archivos.
    version_path.write_text(source, encoding="utf-8")
    readme_path.write_text(readme, encoding="utf-8")
    changelog_path.write_text(changelog, encoding="utf-8")
    checked = check(root)
    if (root / "docs" / "ENTREGABLES.md").exists():
        # La entrega consolidada es generada; no debe conservar una versión anterior.
        from scripts.export_delivery import generate
        generate(root)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", nargs="?", choices=("major", "minor", "patch"))
    parser.add_argument("--check", action="store_true", help="Solo comprobar coherencia")
    args = parser.parse_args()
    if args.check and args.part:
        parser.error("--check no incrementa una versión; omite major/minor/patch.")
    if not args.check and not args.part:
        parser.error("Elige major/minor/patch o --check.")
    try:
        version = check() if args.check else bump(args.part)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"V{version}")


if __name__ == "__main__":
    main()
