# Manual de preparación, versionado y publicación

Los comandos usan PowerShell desde la raíz del proyecto. Sustituye las versiones de ejemplo por la versión real; no ejecutes de nuevo la creación del repositorio ni el commit inicial si ya existen. Los comandos de publicación modifican GitHub y requieren la cuenta y autorización adecuadas.

## 1. Análisis inicial

La base funcional es una GUI Tkinter que consulta URLs por HTTP, compara las versiones anunciadas con las correcciones de dos CVE PHP y exporta evidencia local. Para distribuirla se añaden licencia, metadatos, dependencias de build, icono, versión centralizada, pruebas, documentación, automatización y procedimientos de mantenimiento.

La distribución pública prevista es `erickson558/php_cgi_validation`, rama `main`, licencia Apache-2.0. El repositorio publica código y documentación; los ejecutables se adjuntan a releases. No se incluyen informes de clientes, listas privadas de URLs, secretos ni el entorno virtual.

Supuestos y límites:

- Python 3.10+ con Tkinter ejecuta el código; la compilación `.exe` se hace en Windows.
- La cuenta GitHub requerida es `erickson558`; la autenticación se verifica antes de publicar. No se guardan tokens en archivos del proyecto.
- Si no existe un icono local, se incorpora `app.ico` al proyecto antes de compilar.
- Se usan dependencias de build fijadas. El procedimiento repetible no implica compilación idéntica a nivel binario.
- Las comprobaciones de seguridad y pruebas no garantizan ausencia de vulnerabilidades. La comparación por cabeceras sigue siendo preliminar.
- Un GET normal puede activar lógica del servidor; solo se introducen rutas autorizadas para esta operación.
- El lote admite 1 MiB UTF-8, 1.000 URLs únicas y 8.192 caracteres por URL. El núcleo limita evidencia y versiones para tratar datos de servidores no confiables.

## 2. Estrategia de versionado

`app_version.py` contiene `VERSION = "1.0.0"` y deriva `APP_VERSION = "V1.0.0"`. La GUI importa esta fuente. Build, metadatos, README, changelog, tag, release y nombre del ejecutable deben concordar.

| Cambio | Incremento | Ejemplo |
| --- | --- | --- |
| Incompatibilidad pública, por ejemplo un cambio incompatible del formato de informe. | `major` | V1.2.3 → V2.0.0 |
| Función nueva compatible. | `minor` | V1.2.3 → V1.3.0 |
| Corrección, mantenimiento o documentación que llegue en un commit nuevo a main. | `patch` | V1.2.3 → V1.2.4 |

Cada commit nuevo que se suba a `main` necesita una versión nueva. El workflow rechaza un tag existente que apunte a otro commit. Esto evita que dos estados de código distintos compartan una distribución. Una reejecución del mismo commit no exige incremento y puede completar una publicación pendiente, sin reemplazar un release publicado.

Se recomienda Conventional Commits: `feat: ...`, `fix: ...`, `docs: ...`, `build: ...`, `chore: ...`; usa `!` para señalar incompatibilidad. El tipo del mensaje explica el cambio; el incremento se realiza explícitamente antes del commit.

## 3. Archivos creados o actualizados

| Grupo | Archivos |
| --- | --- |
| Aplicación | `php_audit.py`, `php_audit_gui.py`, `i18n.py`, `app_version.py`, `app.ico` |
| Instalación y build | `pyproject.toml`, `requirements.txt`, `requirements-build.txt`, `requirements-dev.txt`, `build.py` |
| Automatización | `.github/workflows/`, `scripts/bump_version.py`, `.gitignore` |
| Documentación | `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, este manual |
| SDD | `docs/spec.md`, `docs/plan.md`, `docs/tasks.md`, `docs/SECURITY_REVIEW.md` |
| Mantenimiento | `AGENTS.md` y skills de proyecto |
| Comprobaciones | `tests/` |

## 4. Contenido completo de los archivos

Los archivos completos forman parte del repositorio. La entrega consolidada se encuentra en [ENTREGABLES.md](ENTREGABLES.md). El contenido operativo autoritativo está en cada archivo: evita copiar un workflow antiguo sobre uno que ya se haya actualizado. Consulta también [README](../README.md), [licencia](../LICENSE), [dependencias](../requirements.txt) y [versión](../app_version.py).

## 5. Comandos paso a paso

### Preparar Python y comprobar el proyecto

```powershell
# Identificar las herramientas instaladas.
python --version
git --version
gh --version

# Crear un entorno aislado sin cambiar la política de ejecución de PowerShell.
python -m venv .venv

# Instalar las dependencias con el intérprete del entorno.
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# Validar las reglas, HTTP local, informes y GUI según el entorno disponible.
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Validar que la versión y los archivos requeridos estén sincronizados.
.\.venv\Scripts\python.exe scripts/bump_version.py --check
.\.venv\Scripts\python.exe build.py --check
.\.venv\Scripts\python.exe scripts/export_delivery.py --check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip_audit -r requirements-build.txt --strict

# Ejecutar la aplicación desde código.
.\.venv\Scripts\python.exe php_audit_gui.py
```

### Verificar la cuenta GitHub

```powershell
# Muestra la cuenta activa; no copies tokens a documentación o commits.
gh auth status

# Selecciona la cuenta solicitada si ya está autenticada.
gh auth switch --hostname github.com --user erickson558

# Comprueba el usuario usado por las siguientes operaciones.
gh api user --jq .login
```

Si la cuenta no está autenticada, usa `gh auth login --hostname github.com --git-protocol https --web` y completa el inicio de sesión. Después repite la comprobación. No generes un token dentro del repositorio.

### Inicializar Git y hacer el primer commit

```powershell
# Solo cuando esta carpeta todavía no es un repositorio.
git init -b main

# Examina la identidad ya configurada.
git config user.name
git config user.email

# Revisa qué se incluirá; .gitignore excluye secretos y artefactos locales.
git status --short
git add .
git diff --cached --check
git diff --cached --stat

# Primer commit con el producto y su preparación de distribución.
git commit -m "feat: prepare PHP assessment GUI and automated Windows releases"
```

Si no hay identidad configurada, configura una identidad que te pertenezca antes del commit. Para usar la dirección privada de GitHub, consulta la dirección de correo de commits en la configuración de tu cuenta y aplica `git config user.email` con ese valor. No inventes una identidad ni publiques una dirección personal sin revisarla.

### Crear el repositorio público y subir main

```powershell
# Comprueba si el nombre ya existe antes de crearlo.
gh repo view erickson558/php_cgi_validation --json nameWithOwner,url,visibility
```

Si el repositorio no existe:

```powershell
# Crea el remoto público y asocia origin con este directorio.
gh repo create erickson558/php_cgi_validation --public --source . --remote origin --description "Evaluación preliminar PHP con GUI ES/EN e informes locales"

# Publica el commit inicial y deja configurado el seguimiento de main.
git push -u origin main
```

Si el repositorio ya existe, revisa su contenido e historial antes de asociarlo. No fuerces el push para sustituir historia existente. Para un remoto verificado y compatible:

```powershell
git remote -v
# Solo si origin aún no existe:
git remote add origin https://github.com/erickson558/php_cgi_validation.git
git fetch origin
# Revisa diferencias e integra la historia si el remoto ya contiene commits.
git log --oneline --all --decorate -10
git push -u origin main
```

Si `origin` apunta a otra URL, comprueba que corresponde cambiarlo y usa `git remote set-url origin https://github.com/erickson558/php_cgi_validation.git`. No es necesario crear a mano el tag o release para el flujo automático.

### Verificar Actions, tags y release

```powershell
# Localiza la ejecución del push a main y anota su ID.
gh run list --repo erickson558/php_cgi_validation --branch main --limit 5

# Sustituye 123456789 por el ID real y espera al resultado.
gh run watch 123456789 --repo erickson558/php_cgi_validation --exit-status

# Comprueba el tag y la publicación de la versión esperada.
git ls-remote --tags origin V1.0.0
gh release view V1.0.0 --repo erickson558/php_cgi_validation

# Descarga artefactos para revisar el ejecutable y su checksum.
gh release download V1.0.0 --repo erickson558/php_cgi_validation --dir release-download
Get-FileHash -Algorithm SHA256 .\release-download\php_cgi_validation-V1.0.0.exe
Get-Content .\release-download\SHA256SUMS.txt
```

Compara el hash con `SHA256SUMS.txt`. Descarga en una carpeta vacía; no uses `--clobber` para reemplazar archivos sin revisarlos. Los tags y releases se crean después de las comprobaciones del workflow. Un push correcto por sí solo no demuestra que el release haya terminado.

### Publicar el siguiente cambio

```powershell
# Parte de un main actualizado e identifica cambios locales antes de integrar.
git status --short
git switch main
git pull --ff-only

# Realiza el cambio y actualiza especificación, plan y tareas si afecta al producto.
# Incrementa patch; elige minor o major cuando corresponda.
.\.venv\Scripts\python.exe scripts/bump_version.py patch

# Completa la nueva sección de CHANGELOG.md con los cambios reales.
.\.venv\Scripts\python.exe scripts/bump_version.py --check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe build.py
$version = .\.venv\Scripts\python.exe -c "from app_version import APP_VERSION; print(APP_VERSION)"
& ".\php_cgi_validation-$version.exe" --smoke-test

# Revisa el conjunto y publica un commit con una versión nueva.
git add .
git diff --cached --check
git diff --cached --stat
git commit -m "fix: describe the correction being released"
git push origin main
```

Consulta de nuevo Actions y el release con la nueva versión. No ejecutes además `git tag` o `gh release create`: el workflow se encarga de ambas operaciones. Si corriges un fallo del workflow en un commit nuevo, incrementa también la versión; si solo reejecutas el mismo commit, puedes usar `gh run rerun ID --repo erickson558/php_cgi_validation` tras revisar la causa.

### Tags y publicación manual: recuperación excepcional

El procedimiento normal es automático. Si necesitas diagnosticar un tag sin modificarlo:

```powershell
git fetch origin --tags
git show V1.0.0 --no-patch
gh release view V1.0.0 --repo erickson558/php_cgi_validation
```

No borres ni muevas un tag publicado para reparar un binario. Corrige el proyecto y publica una versión nueva. Si falta un release por un fallo temporal, revisa los logs y reejecuta el workflow del mismo commit para que aplique su recuperación prevista.

## 6. Instrucciones de compilación

El comando de compilación que debe repetirse es:

```powershell
.\.venv\Scripts\python.exe build.py
```

El script valida la versión y los recursos y utiliza PyInstaller para generar una aplicación Windows de un solo archivo, con `app.ico` y sin consola. La versión forma parte del nombre; para V1.0.0 el resultado esperado es `php_cgi_validation-V1.0.0.exe` en la raíz, junto a `php_audit_gui.py`.

Para revisar la configuración sin compilar:

```powershell
.\.venv\Scripts\python.exe build.py --check
```

Para calcular manualmente la integridad del resultado:

```powershell
Get-FileHash -Algorithm SHA256 .\php_cgi_validation-V1.0.0.exe
```

La compilación local es independiente del push: el workflow instala sus propias dependencias fijadas, compila en Windows y publica sus propios artefactos. No hagas commit del `.exe`, `.venv` ni carpetas de trabajo de PyInstaller. Conserva `app.ico`, los scripts y las dependencias en el repositorio.

El nombre mostrado en los ejemplos corresponde al primer release. Obtén el nombre actual sin copiar una versión anterior:

```powershell
$version = .\.venv\Scripts\python.exe -c "from app_version import APP_VERSION; print(APP_VERSION)"
& ".\php_cgi_validation-$version.exe" --smoke-test
```

Si editas los archivos incluidos en la entrega consolidada, ejecuta `python scripts/export_delivery.py` antes del commit. El incremento de versión también la regenera. Para instalar las cuatro skills en un entorno de mantenimiento diferente, copia las carpetas de `.agents/skills/` a la carpeta personal de skills sin sobrescribir versiones existentes; `AGENTS.md` documenta los roles y las rutas del proyecto.
