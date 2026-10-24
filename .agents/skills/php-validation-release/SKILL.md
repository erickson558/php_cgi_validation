---
name: php-validation-release
description: Versionar, compilar y publicar php_cgi_validation en erickson558/php_cgi_validation con GitHub CLI y releases Windows.
---

# Publicación del proyecto

Esta skill se limita a `erickson558/php_cgi_validation`. La cuenta es `erickson558`;
las credenciales permanecen en el keyring de GitHub CLI. Comprueba `gh auth status`
y `gh api user --jq .login`; si se pide publicar con esta cuenta y hay otra activa,
usa `gh auth switch --hostname github.com --user erickson558`. Nunca vuelques tokens.

Lee `AGENTS.md`, `docs/MANUAL.md`, `CHANGELOG.md` y `.github/workflows/release.yml`.
Revisa estado, diff y archivos excluidos antes de preparar el commit. Publicar
requiere autorización en la petición vigente; si ya está concedida, completa la
preparación, validación, commit y push sin pedirla otra vez.

`app_version.py` es la única fuente. Antes de un commit nuevo en `main`, ejecuta
`python scripts/bump_version.py patch`, `minor` o `major` según el impacto;
completa la nueva entrada de changelog y mantén SDD. La versión inicial es la
excepción natural al incremento. Valida con `--check`, pruebas, Ruff y auditoría.

Compila en Windows con `python build.py`, que usa `app.ico` y produce un .exe
sin consola junto al .py, más `SHA256SUMS.txt` y avisos de terceros. Comprueba
`--smoke-test`; la compilación no implica firma de código ni reproducibilidad bit a bit.

Un push a `main` ejecuta pruebas, compilación y publicación automática. No crees
una publicación manual paralela. Si falla, inspecciona el run: reejecuta cuando
sea un problema transitorio; si cambia código, crea una nueva versión. Nunca muevas
tags publicados ni reemplaces binarios de un release público. Usa Conventional Commits
sin trailers de coautoría y verifica run, tag, assets y SHA-256 antes de dar por terminada
la publicación. Consulta `docs/MANUAL.md` para recuperación manual autorizada.
