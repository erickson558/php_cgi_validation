# Revisión de seguridad

Fecha: 24 de octubre de 2026. Alcance: motor HTTP, diagnóstico local heredado, entrada de URLs, interpretación de versiones y exportación de informes. Es una revisión de código y pruebas locales; no constituye una certificación de ausencia de vulnerabilidades ni una prueba de penetración de los destinos consultados.

## Resumen

Se corrigieron problemas de ampliación de alcance en el diagnóstico local, exposición accidental de configuración, manejo de evidencia remota y tolerancia a errores al guardar informes. No se identificaron hallazgos críticos en los componentes revisados. Continúan existiendo límites operativos ante servidores que responden lentamente y ante evidencia de versión manipulada; se explican abajo.

El proyecto utiliza Python con Tkinter y urllib, además de un archivo PHP de diagnóstico. No emplea Django, Flask o FastAPI. La revisión se centra en los límites reales de una aplicación de escritorio, los datos no confiables de los servidores HTTP y la confidencialidad de los informes.

## Hallazgos moderados corregidos

### SEC-001 · El diagnóstico local seguía redirecciones

Antes: la URL inicial de `check_cgi.py` se validaba como local, pero `urlopen()` podía seguir un destino indicado por una respuesta 3xx. También podía utilizar un proxy configurado en el entorno.

Impacto: un servicio local podía provocar peticiones fuera del alcance declarado y el diagnóstico local podía circular por un intermediario.

Corrección: [local_url](../check_cgi.py#L14) valida las URLs y convierte `localhost` en `127.0.0.1`; [fetch](../check_cgi.py#L26) desactiva proxies y usa el mismo bloqueo de redirecciones que el motor principal. Las conexiones HTTPS siguen validando certificados; un certificado usado con `127.0.0.1` debe incluir esa dirección. No se desactiva TLS para evitar un error de certificado.

Verificación: las pruebas de redirección comprueban que únicamente se recibe la petición inicial y que el destino redirigido no se consulta.

### SEC-002 · El diagnóstico PHP no imponía acceso local

Antes: la recomendación de utilizar `diagnostic.php` solo localmente dependía de que el operador no lo publicara por error.

Impacto: al copiarlo a un servidor accesible desde Internet, podía revelar la versión de PHP, el SAPI y el software del servidor.

Corrección: [diagnostic.php](../diagnostic.php#L4) exige que la conexión directa proceda de `127.0.0.1` o `::1`, devuelve 403 en otro caso y envía `Cache-Control: no-store`. No confía en `X-Forwarded-For`. Debe retirarse al terminar incluso con esta protección: un proxy local puede hacer que peticiones externas aparezcan como locales.

Validación: PHP CLI no estaba disponible localmente. La integración del primer release ejecutó `php -l diagnostic.php` correctamente en Linux. Sigue pendiente una prueba de despliegue real del diagnóstico; el lint no comprueba su configuración de red ni el comportamiento de un proxy.

### SEC-003 · Versiones remotas podían interrumpir el lote

Antes: se convertían componentes numéricos arbitrariamente largos y se aceptaban sufijos no estructurados. Una cadena remota podía provocar un error de conversión o sugerir una versión corregida pese a ser una cadena malformada.

Corrección: [assess_version](../php_audit.py#L127) limita el token a 128 caracteres, limita cada componente numérico a tres dígitos y admite solo formatos completos y sufijos delimitados. Las compilaciones preliminares o desconocidas continúan como inconclusas. Un sufijo de proveedor no demuestra que el paquete tenga un backport.

Verificación: pruebas de versiones con miles de dígitos, sufijos malformados, prereleases y límites de corrección de las cuatro ramas.

## Hallazgos bajos corregidos

### SEC-004 · Faltaban límites explícitos de entrada y evidencia

Corrección: [constantes de límites](../php_audit.py#L25), [normalización](../php_audit.py#L77) y [parse_targets](../php_audit.py#L104) permiten hasta 8192 caracteres por URL, 1 MiB de texto UTF-8 y 1000 URLs únicas por lote. La deduplicación usa un conjunto para evitar coste cuadrático.

[audit_url](../php_audit.py#L167) conserva hasta 16 KiB combinados de `Server` y `X-Powered-By`; una respuesta con mayor evidencia devuelve ERROR. Los controles se escapan mediante [visible_text](../php_audit.py#L220) para evitar líneas engañosas en el panel. El cliente HTTP de la biblioteca estándar tiene además sus propios límites de análisis de cabeceras; los límites de la aplicación se aplican después de ese análisis, no a todo el tráfico recibido.

### SEC-005 · Prefijos especiales de hojas de cálculo

Corrección: [csv_cell](../php_audit.py#L214) neutraliza fórmulas que empiecen con `=`, `+`, `-` o `@`, incluso tras espacios, tabulaciones o BOM. El JSON conserva el dato como cadena sin ejecutarlo.

### SEC-006 · Una exportación fallida podía dañar el informe anterior

Corrección: [export_results](../php_audit.py#L225) escribe y sincroniza un archivo temporal en el mismo directorio; reemplaza el destino solo al finalizar. Si hay un error, conserva el informe anterior y retira el temporal. No garantiza persistencia frente a todos los fallos físicos del almacenamiento o de una carpeta sincronizada.

Verificación: una prueba provoca un error de reemplazo y comprueba que el informe anterior permanece y no quedan temporales.

## Riesgos residuales y uso operativo

- Una cabecera puede estar falsificada, ocultada o proceder de un proxy. El programa compara evidencia anunciada; no confirma explotación ni ausencia de vulnerabilidad. Los parches del proveedor deben comprobarse en el servidor correspondiente.
- El timeout de urllib limita operaciones de socket; no es un plazo total frente a un servidor que entregue bytes muy lentamente. La resolución DNS también puede depender del sistema. La interfaz puede detener nuevas peticiones o cerrarse, pero la petición en curso no se cancela de inmediato. Para un límite total estricto haría falta aislar cada petición en un proceso terminable y diseñar su ciclo de vida.
- La aplicación admite direcciones privadas y loopback porque son destinos útiles de auditoría. No debe exponerse como un servicio web que reciba URLs de usuarios no confiables sin un diseño adicional de control de alcance y red.
- El motor principal respeta los proxies del entorno. El operador debe conocer su configuración; el diagnóstico heredado desactiva proxies para conservar su alcance local.
- Los informes contienen URLs y sus parámetros; pueden incluir identificadores o tokens que el operador haya introducido. Deben guardarse y compartirse de acuerdo con la sensibilidad de esos datos.
- El uso de GET normal puede activar comportamiento de la aplicación de destino. Deben emplearse rutas de lectura dentro del alcance autorizado.
- Las reglas del 24/10/2026 cubren las dos CVE del 21/10. CVE-2026-115560 requiere revisar configuración y código; no se evalúa automáticamente.
- No se invocan shells con datos de los destinos ni se ejecuta contenido de respuesta. El análisis no reemplaza actualizar Python, las dependencias de compilación y los componentes del servidor auditado.

## Cadena de compilación y publicación

La revisión de integración detectó avisos conocidos para el pip 25.0.1 que traía
el entorno virtual. Se fija y actualiza a pip 26.2.2 antes de distribuir. La
auditoría de `requirements-build.txt` incluye esta herramienta y las dependencias
transitivas de PyInstaller. El entorno de desarrollo se revisa por separado;
el propio paquete editable no está publicado en PyPI y no puede auditarse allí.

Las acciones externas están fijadas por commit y solo el job de publicación
recibe `contents: write`. Los pull requests validan y compilan sin publicar.
El script de publicación verifica la coherencia de versión, el remoto previsto
y que un tag existente corresponda al mismo commit. Nunca reemplaza artefactos
de un release público. El binario incluye avisos de sus componentes y checksum;
no incorpora una firma Authenticode. Estas medidas no auditan el sistema operativo,
el intérprete completo ni todas sus bibliotecas nativas: deben mantenerse actualizados.

## Evidencia de pruebas y fuentes

Comando del motor: `python -m unittest discover -s tests -p test_audit.py -v`. Resultado: 19 pruebas correctas usando únicamente loopback y archivos temporales. La suite integrada incluye 28 pruebas, superadas localmente y en la matriz Windows/Python 3.10, Windows/Python 3.12 y Linux/Python 3.12 del [primer workflow completo](https://github.com/erickson558/php_cgi_validation/actions/runs/40099362835). PHP pasó lint en Linux; la prueba de su despliegue real permanece fuera de esa comprobación.

Referencias de comportamiento: [urllib.request y sus timeouts/proxies](https://docs.python.org/3/library/urllib.request.html), [http.client](https://docs.python.org/3/library/http.client.html), [os.replace](https://docs.python.org/3/library/os.html#os.replace) y [avisos de PHP de octubre de 2026](https://www.php.net/archive/2026.php).
