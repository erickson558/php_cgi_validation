"""Publica una versión verificada sin sobrescribir releases ya publicados."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Al ejecutar un archivo de scripts/, Python no incluye automáticamente la raíz.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bump_version import check  # noqa: E402

REPOSITORY = "erickson558/php_cgi_validation"


def run(*args, required=True):
    """Ejecuta sin shell y conserva errores visibles, nunca imprime credenciales."""
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if required and result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Falló {args[0]}")
    return result


def validate_tag(tag, commit):
    """Un tag existente solo se admite si apunta exactamente al commit evaluado."""
    result = run("git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}", required=False)
    if result.returncode == 0 and result.stdout.strip() != commit:
        raise ValueError(f"{tag} pertenece a otro commit. Incrementa la versión antes del push.")
    return result.returncode == 0


def verify_checksum(tag, root=ROOT):
    """Impide publicar un archivo modificado con un checksum anterior."""
    name = f"php_cgi_validation-{tag}.exe"
    checksum = (root / "SHA256SUMS.txt").read_text(encoding="ascii").strip()
    match = re.fullmatch(r"([0-9a-fA-F]{64})  " + re.escape(name), checksum)
    if not match:
        raise ValueError("SHA256SUMS.txt no identifica exactamente el ejecutable de esta versión.")
    digest = hashlib.sha256()
    with (root / name).open("rb") as binary:
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != match.group(1).lower():
        raise ValueError("El ejecutable no coincide con SHA256SUMS.txt. Recompila antes de publicar.")


def should_be_latest(tag, previous_tag):
    """Recuperar un draft antiguo no debe desplazar una versión pública posterior."""
    if previous_tag is None:
        return True
    pattern = r"V([0-9]+)\.([0-9]+)\.([0-9]+)"
    current, previous = re.fullmatch(pattern, tag), re.fullmatch(pattern, previous_tag)
    return bool(current and previous and tuple(map(int, current.groups())) >= tuple(map(int, previous.groups())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validar tag sin modificar GitHub")
    args = parser.parse_args()
    version = check(ROOT)
    tag = f"V{version}"
    commit = run("git", "rev-parse", "HEAD").stdout.strip()
    exists = validate_tag(tag, commit)
    previous = run("git", "show", "HEAD^:app_version.py", required=False)
    if previous.returncode == 0:
        match = re.search(r'^VERSION = "([0-9]+\.[0-9]+\.[0-9]+)"$', previous.stdout, re.M)
        if match and tuple(map(int, version.split("."))) <= tuple(map(int, match.group(1).split("."))):
            raise ValueError("Cada commit de main debe incrementar VERSION respecto a su primer padre.")
    if args.check:
        print(f"Versión publicable: {tag} ({commit[:7]})")
        return
    # Previene publicaciones desde ramas auxiliares o contra un remoto inesperado.
    remote = run("git", "remote", "get-url", "origin").stdout.strip()
    if not re.fullmatch(r"(?:https://github\.com/|git@github\.com:)erickson558/php_cgi_validation(?:\.git)?", remote):
        raise ValueError("origin no corresponde al repositorio esperado.")
    branch = run("git", "branch", "--show-current").stdout.strip()
    if branch != "main" and os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("Las publicaciones se realizan desde main.")
    if run("git", "status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise ValueError("Hay cambios rastreados sin commit.")
    # Los archivos se pasan individualmente: no hay expansión arbitraria de globs.
    names = [f"php_cgi_validation-{tag}.exe", "SHA256SUMS.txt", "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.txt"]
    artifacts = [str(ROOT / name) for name in names]
    if not all(Path(path).is_file() for path in artifacts):
        raise ValueError("Faltan artefactos: ejecuta python build.py primero.")
    verify_checksum(tag)
    view = run("gh", "release", "view", tag, "--repo", REPOSITORY, "--json", "isDraft", required=False)
    if view.returncode == 0 and not json.loads(view.stdout)["isDraft"]:
        print(f"{tag} ya está publicado; se conserva sin modificar.")
        return
    if not exists:
        run("git", "tag", "-a", tag, commit, "-m", f"Release {tag}")
    run("git", "push", "origin", f"refs/tags/{tag}")
    if view.returncode:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        entry = re.split(r"^## \[V", changelog, flags=re.M)[1]
        notes = ROOT / "build" / "release_notes.md"
        notes.parent.mkdir(exist_ok=True)
        notes.write_text("## [V" + entry + "\n\nEjecutable Windows x64; verifique SHA256SUMS.txt.\n", encoding="utf-8")
        run("gh", "release", "create", tag, "--repo", REPOSITORY, "--verify-tag", "--draft",
            "--title", tag, "--notes-file", str(notes))
    # Un draft puede completarse tras un fallo; un release público es inmutable aquí.
    run("gh", "release", "upload", tag, "--repo", REPOSITORY, "--clobber", *artifacts)
    latest = run("gh", "release", "view", "--repo", REPOSITORY, "--json", "tagName", required=False)
    previous_tag = json.loads(latest.stdout)["tagName"] if latest.returncode == 0 else None
    latest_flag = "--latest" if should_be_latest(tag, previous_tag) else "--latest=false"
    run("gh", "release", "edit", tag, "--repo", REPOSITORY, "--draft=false", latest_flag)
    print(f"Publicado: https://github.com/{REPOSITORY}/releases/tag/{tag}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
