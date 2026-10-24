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
