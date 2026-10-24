"""Genera la entrega solicitada con el contenido íntegro de los archivos operativos."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "README.md", "requirements.txt", "requirements-build.txt", "requirements-dev.txt",
    "LICENSE", "NOTICE", "app_version.py", "pyproject.toml", ".github/workflows/release.yml",
    ".gitignore", ".gitattributes", "build.py", "scripts/bump_version.py", "scripts/publish_release.py",
)


def render(root=ROOT):
    """El contenido se toma de los originales para evitar mantener copias a mano."""
    sections = ["# Contenido completo de la entrega\n\n"
                "Documento generado con `python scripts/export_delivery.py`. "
                "Los archivos originales son la fuente operativa. "
                "Para análisis, estrategia, listado, comandos y compilación, consulta [MANUAL.md](MANUAL.md).\n"]
    for name in FILES:
        content = (root / name).read_text(encoding="utf-8")
        language = "python" if name.endswith(".py") else "yaml" if name.endswith(".yml") else "text"
        sections.append(f"\n## {name}\n\n~~~~{language}\n{content.rstrip()}\n~~~~\n")
    return "".join(sections)


def generate(root=ROOT):
    target = root / "docs" / "ENTREGABLES.md"
    target.write_text(render(root), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if (ROOT / "docs" / "ENTREGABLES.md").read_text(encoding="utf-8") != render():
            parser.exit(1, "Regenera docs/ENTREGABLES.md antes de continuar.\n")
        print("Entrega consolidada sincronizada.")
    else:
        generate()


if __name__ == "__main__":
    main()
