# Contenido completo de la entrega

Documento generado con `python scripts/export_delivery.py`. Los archivos originales son la fuente operativa. Para análisis, estrategia, listado, comandos y compilación, consulta [MANUAL.md](MANUAL.md).

## README.md

~~~~text
# php_cgi_validation

**Versión: V1.0.1** · Python 3.10+ · Windows · Licencia Apache-2.0

Evaluación preliminar de exposición PHP desde una interfaz de escritorio en **español e inglés**. Compara las versiones anunciadas por URLs autorizadas con las correcciones de CVE-2026-109618 y CVE-2026-109619. Permite documentar indicios y preparar una revisión con el administrador del servidor.

[Descargar releases](https://github.com/erickson558/php_cgi_validation/releases) · [Manual paso a paso](docs/MANUAL.md) · [Especificación](docs/spec.md) · [Cambios](CHANGELOG.md) · [Seguridad](SECURITY.md)

## Qué hace

Realiza un GET normal por URL, analiza `Server` y `X-Powered-By` y conserva la evidencia con fecha UTC. Admite listas TXT, elimina duplicados, ejecuta las consultas en serie, permite detener el lote y exporta JSON o CSV. La interfaz permanece disponible durante las consultas. El botón **Cómprame una cerveza / Buy me a beer** abre la página de donación solo al pulsarlo.

La comparación de versiones **no confirma explotación ni certifica seguridad**. Una cabecera puede estar oculta, modificada o proceder de un proxy. Un proveedor puede aplicar correcciones sin cambiar la versión base. El programa no envía exploits ni provoca fallos de memoria. Úsalo sobre sistemas propios o con autorización del responsable.

## Instalación y ejecución

La aplicación utiliza la biblioteca estándar; no necesita dependencias externas de ejecución. Para ejecutar el código necesitas Python 3.10 o posterior con Tkinter, normalmente incluido en el instalador de Python para Windows. El ejecutable Windows de un release no requiere instalar Python.

```powershell
git clone https://github.com/erickson558/php_cgi_validation.git
cd php_cgi_validation
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe php_audit_gui.py
```

Desde una carpeta del proyecto ya preparada:

```powershell
python php_audit_gui.py
```

## Uso

1. Introduce una URL completa por línea o carga un archivo TXT UTF-8. Se admiten líneas vacías y comentarios que empiecen con `#`; las URLs duplicadas se evalúan una sola vez.
2. Selecciona el idioma de la interfaz y el timeout.
3. Pulsa **Evaluar URLs**. Selecciona una fila para consultar cabeceras, interpretación y recomendación.
4. Exporta el informe a JSON o CSV. Incluye evidencia, fecha UTC, CVE evaluadas, fecha de las reglas, fuente y limitaciones.

Ejemplo de lista, sustituyendo el dominio por un sistema autorizado:

```text
# Entorno local
http://127.0.0.1:888/
https://servidor-autorizado.example/aplicacion/
```

**Detener** evita nuevas consultas y conserva los resultados completados. La petición en curso debe terminar antes de finalizar el lote. El timeout de socket no equivale a un plazo absoluto de toda la operación, especialmente ante respuestas lentas o resolución DNS. Cerrar la ventana termina la aplicación.

Solo se solicita la ruta introducida: no hay rastreo ni búsqueda de endpoints. No se siguen redirecciones. Si recibes un 3xx, introduce el destino por separado cuando esté autorizado. Se valida TLS. La GUI no descarga cuerpos de respuesta ni guarda cookies. Los informes contienen las URLs introducidas, incluidos sus parámetros: revísalos antes de compartirlos.

El lote admite hasta **1 MiB de texto UTF-8**, **1.000 URLs únicas** y **8.192 caracteres por URL**. La evidencia combinada de `Server` y `X-Powered-By` se limita a 16.384 caracteres; una respuesta que exceda ese tamaño se registra como error. Las versiones de más de 128 caracteres se consideran inconclusas. Los archivos de informe se sustituyen de forma atómica para reducir el riesgo de dejar un informe incompleto si falla la escritura.

## Vulnerabilidades y reglas

El [aviso oficial de PHP del 21 de octubre](https://www.php.net/archive/2026.php) identifica:

| CVE | Problema | Primera versión corregida por rama |
| --- | --- | --- |
| CVE-2026-109618 | Corrupción de memoria durante el manejo de falta de memoria | 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12 |
| CVE-2026-109619 | Estado global obsoleto entre peticiones | 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12 |

Afectan a instalaciones que sirven peticiones web, incluyendo PHP-FPM, mod_php y PHP-CGI. Comprobar únicamente que el handler no sea CGI no descarta estas CVE.

**Reglas verificadas el 24/10/2026.** La aplicación evalúa las dos CVE del día 21. El 23 de octubre se anunció también **CVE-2026-115560**, asociada a una combinación particular de configuración y código de sesiones. La GUI recuerda este aviso, pero no la evalúa: no puede inferirse por una versión o una cabecera. PHP recomienda `session.upload_progress.enabled=0` hasta la siguiente corrección regular; el administrador debe aplicar la indicación en la configuración que corresponda y reiniciar los workers. Consulta el aviso vigente antes de remediar.

## Interpretar el informe

| Resultado | Significado |
| --- | --- |
| POSIBLE AFECTACIÓN | La versión anunciada es anterior al umbral de su rama, o pertenece a una rama antigua sin soporte del proyecto PHP. Puede haber parches del proveedor que no cambien la versión base. |
| VERSIÓN CON CORRECCIÓN | La cabecera anuncia una versión estable que alcanza el umbral para las dos CVE del día 21. Debe comprobarse en el servidor; no certifica seguridad general ni cubre CVE-2026-115560. |
| INCONCLUSO | Versión oculta, incompleta, contradictoria, preliminar o rama fuera de las reglas. No significa ausencia de PHP ni de vulnerabilidades. |
| ERROR | Fallo de conexión, TLS o protocolo; no permite concluir nada sobre las CVE. |

Se examinan `X-Powered-By` y `Server`. Una respuesta 403/500 se registra como tal; por sí sola no demuestra vulnerabilidad. Una CDN, un proxy, un WAF o una cabecera modificada pueden impedir atribuir la versión al backend real. Las mitigaciones parciales tampoco se deducen mediante estas peticiones.

Para una evaluación de cliente, usa el informe como indicio y solicita inventario del paquete exacto, revisión del proveedor y configuración del backend que atiende la URL. Verifica las correcciones en todos los workers después de actualizar. `php -v` puede consultar un PHP de consola distinto al que usa el servidor web. Solo afirma afectación o remediación verificada cuando exista evidencia del servidor correspondiente.

Las reglas están en `php_audit.py` (`FIXED`, `assess_version`); no se actualizan automáticamente. Contrasta con los avisos de PHP y del proveedor antes de usar la herramienta en otra fecha. Cambiar el idioma afecta a la presentación; los estados de los informes conservan su formato estable.

## Dependencias y compilación

| Archivo | Uso |
| --- | --- |
| `requirements.txt` | Ejecución: biblioteca estándar, sin paquetes externos. |
| `requirements-build.txt` | Herramientas y versiones fijadas para compilar. |
| `requirements-dev.txt` | Herramientas para desarrollo y comprobaciones. |
| `pyproject.toml` | Metadatos y configuración del proyecto. |

En Windows, desde la raíz y con el entorno virtual activo:

```powershell
python -m pip install -r requirements-build.txt
python build.py --check
python build.py
```

El script usa el icono local `app.ico` y genera un ejecutable sin consola, en la misma carpeta que `php_audit_gui.py`: `php_cgi_validation-V1.0.1.exe`. La versión se obtiene de `app_version.py`. El entorno y las dependencias fijadas hacen repetible el procedimiento; no garantizan que dos compilaciones produzcan bytes idénticos. Los binarios no tienen firma de código salvo que se añada un certificado propio.

## Versionado y releases

La fuente de versión es `app_version.py`: `VERSION` tiene formato `x.y.z`; la interfaz, tags, releases y binarios usan el prefijo `V`, actualmente `V1.0.1`.

| Incremento | Cuándo | Ejemplo |
| --- | --- | --- |
| `major` | Cambios incompatibles en uso o formato público. | V1.2.3 → V2.0.0 |
| `minor` | Funcionalidad compatible. | V1.2.3 → V1.3.0 |
| `patch` | Correcciones compatibles. | V1.2.3 → V1.2.4 |

Antes de cada commit que llegue a `main`, incrementa la versión con `python scripts/bump_version.py patch` (o `minor` / `major`) y completa el changelog. Usa `patch` para ajustes de documentación que se publiquen en un commit nuevo. No basta cambiar el tag. La app, README y changelog deben coincidir antes de publicar.

Cada push a `main` ejecuta el workflow de validación y release. Una versión nueva crea su tag y release y adjunta el `.exe` y `SHA256SUMS.txt`. Si el tag ya apunta a otro commit, el workflow falla y exige incrementar la versión; una reejecución del mismo commit puede completar una publicación pendiente sin sustituir un release publicado. Consulta el [manual](docs/MANUAL.md) para los comandos y la recuperación de errores.

## Estructura

```text
php_audit_gui.py         Interfaz, hilo de consultas y eventos
php_audit.py             HTTP, reglas de versión e informes
i18n.py                  Textos y traducciones de la interfaz
app_version.py           Versión única de la aplicación
app.ico                  Icono de la ventana y el ejecutable
build.py                 Validación y compilación Windows
check_cgi.py             Diagnóstico local anterior
diagnostic.php           Endpoint auxiliar solo para laboratorio local
tests/                   Pruebas locales
scripts/                 Herramientas de mantenimiento y versionado
docs/                    Especificación, plan, tareas y manual
.github/workflows/       Validación y publicación automática
AGENTS.md                Responsabilidades y convenciones de mantenimiento
```

El trabajo sigue [especificación](docs/spec.md), [plan](docs/plan.md) y [tareas](docs/tasks.md). Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para proponer cambios.

## Diagnóstico local anterior

Se conservan `check_cgi.py` y `diagnostic.php`, del diagnóstico original orientado a CVE-2024-4577. Son independientes de la GUI nueva.

1. Copia `diagnostic.php` únicamente al DocumentRoot de una copia local aislada de Apache.
2. Abre `http://localhost:888/diagnostic.php` para ver `PHP_VERSION`, `PHP_SAPI` y `SERVER_SOFTWARE`.
3. Ejecuta `python check_cgi.py http://localhost:888/diagnostic.php` para obtener el diagnóstico original.
4. Retira el archivo al terminar: revela configuración. La GUI no consulta este diagnóstico automáticamente ni interpreta su cuerpo.

El endpoint auxiliar rechaza clientes cuya dirección no sea loopback. El script heredado bloquea redirecciones, no utiliza proxies y normaliza `localhost` a `127.0.0.1`; si usas HTTPS local, el certificado debe ser válido para esa dirección, o puedes utilizar `::1` con un certificado adecuado. El diagnóstico local no sustituye la revisión del backend de una URL remota.

## Verificación

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan un servidor HTTP de loopback; comprueban reglas de versiones, evidencia ausente o contradictoria, errores HTTP, fallos de conexión, bloqueo de redirecciones y exportación. No se prueban URLs de terceros.

## Licencia y apoyo

Copyright 2026 erickson558. Distribuido bajo [Apache License 2.0](LICENSE). Conserva la licencia y los avisos aplicables al redistribuir.

[Cómprame una cerveza](https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN). La donación es opcional y no habilita funciones adicionales.
~~~~

## requirements.txt

~~~~text
# Ejecución: únicamente biblioteca estándar de Python 3.10+ y Tkinter.
# Tkinter se instala con Python o con el gestor del sistema, nunca mediante pip.
~~~~

## requirements-build.txt

~~~~text
# Resolución fijada para Windows x64 / Python 3.12; marcadores permiten pruebas Linux.
altgraph==0.17.5
packaging==26.3
pip==26.2.2
pefile==2024.8.26; sys_platform == "win32"
pyinstaller==6.22.3
pyinstaller-hooks-contrib==2026.9
pywin32-ctypes==0.2.3; sys_platform == "win32"
setuptools==84.2.1
~~~~

## requirements-dev.txt

~~~~text
-r requirements-build.txt
pip-audit==2.10.1
ruff==0.17.2
PyYAML==6.0.3
~~~~

## LICENSE

~~~~text

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
~~~~

## NOTICE

~~~~text
php_cgi_validation
Copyright 2026 erickson558

Licensed under the Apache License, Version 2.0.
This distribution includes the project's original geometric shield icon.
Windows executables bundle Python/Tcl/Tk and PyInstaller runtime components;
their applicable license notices are distributed with each release.
~~~~

## app_version.py

~~~~python
"""Fuente única de versión para la interfaz, el paquete y las publicaciones."""

# SemVer usa dígitos en el paquete; el prefijo V identifica tags y releases.
VERSION = "1.0.1"
APP_VERSION = f"V{VERSION}"
~~~~

## pyproject.toml

~~~~text
[build-system]
requires = ["setuptools==84.2.1"]
build-backend = "setuptools.build_meta"

[project]
name = "php-cgi-validation"
dynamic = ["version"]
description = "Evaluación preliminar de versiones PHP mediante HTTP normal con GUI ES/EN"
readme = "README.md"
requires-python = ">=3.10"
license = "Apache-2.0"
license-files = ["LICENSE", "NOTICE"]
authors = [{name = "erickson558"}]
dependencies = []

[project.urls]
Repository = "https://github.com/erickson558/php_cgi_validation"
Issues = "https://github.com/erickson558/php_cgi_validation/issues"

[project.gui-scripts]
php-cgi-validation = "php_audit_gui:main"

[tool.setuptools]
py-modules = ["app_version", "php_audit", "php_audit_gui", "i18n"]

[tool.setuptools.dynamic]
version = {attr = "app_version.VERSION"}

[tool.ruff]
target-version = "py310"
line-length = 120
exclude = [".venv", "build"]

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]
~~~~

## .github/workflows/release.yml

~~~~yaml
name: Validate and release

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

# Los jobs de validaciÃ³n no pueden escribir en el repositorio.
permissions:
  contents: read

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  validate:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            python: '3.10'
          - os: windows-latest
            python: '3.12'
          - os: ubuntu-latest
            python: '3.12'
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: ${{ matrix.python }}
          cache: pip
      - run: python -m pip install -r requirements-dev.txt
      - run: python scripts/bump_version.py --check
      - run: python build.py --check
      - run: python scripts/export_delivery.py --check
      - run: python scripts/publish_release.py --check
      - run: python -m ruff check .
      - name: Unit and GUI tests (Windows)
        if: runner.os == 'Windows'
        run: python -m unittest discover -s tests -v
      - name: Unit and GUI tests (Linux virtual display)
        if: runner.os == 'Linux'
        run: xvfb-run -a python -m unittest discover -s tests -v
      - name: PHP syntax
        if: runner.os == 'Linux'
        run: php -l diagnostic.php
      - name: Dependency audit
        run: python -m pip_audit -r requirements-build.txt --strict

  windows-build:
    needs: validate
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: '3.12'
          cache: pip
      - run: python -m pip install -r requirements-build.txt
      - run: python build.py
      - name: Packaged startup test
        shell: pwsh
        run: |
          $version = python -c "from app_version import APP_VERSION; print(APP_VERSION)"
          $binary = Join-Path $PWD "php_cgi_validation-$version.exe"
          $process = Start-Process -FilePath $binary -ArgumentList '--smoke-test' -PassThru -WindowStyle Hidden
          if (-not $process.WaitForExit(60000)) {
            Stop-Process -Id $process.Id -Force
            throw 'El ejecutable no terminÃ³ la prueba de arranque.'
          }
          if ($process.ExitCode -ne 0) { throw "Fallo de arranque: $($process.ExitCode)" }
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: windows-release
          if-no-files-found: error
          path: |
            php_cgi_validation-V*.exe
            SHA256SUMS.txt
            THIRD_PARTY_NOTICES.txt

  publish:
    needs: windows-build
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: '3.12'
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: windows-release
      - name: Publish immutable version
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
          python scripts/publish_release.py
~~~~

## .gitignore

~~~~text
# Entornos, cachés y resultados locales.
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
*.egg-info/
build/
dist/
*.spec
*.exe
SHA256SUMS.txt
THIRD_PARTY_NOTICES.txt
.coverage
htmlcov/

# Informes de clientes y credenciales nunca se versionan.
reports/
release-download/
evaluacion_php*.json
evaluacion_php*.csv
php_audit_*.json
php_audit_*.csv
.env
.env.*
!.env.example
*.pem
*.key
*.pfx
*.p12
.DS_Store
Thumbs.db
~~~~

## .gitattributes

~~~~text
* text=auto
*.py text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.toml text eol=lf
*.txt text eol=lf
*.ico binary
~~~~

## build.py

~~~~python
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
~~~~

## scripts/bump_version.py

~~~~python
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
~~~~

## scripts/publish_release.py

~~~~python
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
~~~~
