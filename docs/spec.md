# Especificación del producto

Estado: base funcional distribuible; la versión vigente se consulta en `app_version.py`. Fecha de reglas PHP: 2026-10-24.

## Problema y alcance

Un operador necesita revisar URLs de sistemas propios o autorizados y registrar si la versión PHP anunciada coincide con ramas anteriores a las correcciones publicadas el 21/10/2026. El resultado sirve como indicio para una revisión con el administrador. No demuestra ejecución remota ni sustituye inventario, revisión de paquetes o evaluación de configuración.

La aplicación es de escritorio, funciona desde Python o un ejecutable Windows y mantiene informes locales. No ofrece un servicio web, descubrimiento de objetivos, explotación, ejecución de comandos remotos ni comprobación activa de CVE-2026-115560.

## Requisitos funcionales

| ID | Requisito | Criterio de aceptación | Componente |
| --- | --- | --- | --- |
| RF-01 | Recibir varias URLs y cargar TXT UTF-8. | Validar antes de iniciar, ignorar comentarios y vacíos, eliminar duplicados. | GUI / `parse_targets` |
| RF-02 | Obtener evidencia HTTP con una petición normal por URL. | Registrar HTTP, Server y X-Powered-By; no seguir 3xx ni descargar cuerpos. | `audit_url` |
| RF-03 | Comparar versiones con las dos correcciones del 21/10. | Evaluar límites de cada rama y devolver inconcluso cuando falte evidencia fiable. | `assess_version` |
| RF-04 | Mostrar evidencia y recomendación por resultado. | Seleccionar una fila muestra fecha UTC, cabeceras, interpretación y límites. | GUI |
| RF-05 | Exportar JSON y CSV. | Preservar evidencia, CVE, fecha de reglas, fuente y limitaciones. | `export_results` |
| RF-06 | Mantener interfaz disponible y permitir detener. | El operador puede detener entre consultas sin perder resultados completados. | GUI / worker |
| RF-07 | Ofrecer español e inglés. | Selector cambia los textos de presentación sin perder entradas ni resultados. | GUI / traducciones |
| RF-08 | Mostrar versión del producto. | La app usa la misma versión que los metadatos y la distribución. | `app_version.py` |
| RF-09 | Ofrecer donación opcional. | El botón abre únicamente el enlace PayPal previsto y solo al pulsarse. | GUI |

## Requisitos de seguridad y operación

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RNF-01 | Limitar el alcance introducido. | Solo HTTP/HTTPS; sin credenciales embebidas, redirecciones ni rastreo. |
| RNF-02 | Tratar respuestas y listas como datos no confiables. | Validar entradas, controlar tamaños y aislar errores de consulta sin ejecutar contenido recibido. |
| RNF-03 | Verificar TLS. | No desactivar comprobación de certificados para obtener un resultado. |
| RNF-04 | Reducir efectos al compartir informes. | Neutralizar fórmulas CSV y documentar que las URLs pueden contener datos sensibles. |
| RNF-05 | Mantener incertidumbre explícita. | No traducir una cabecera oculta, un 403/500 o un error de red a «seguro» o «vulnerable confirmado». |
| RNF-06 | Mantener entorno de ejecución sencillo. | Python 3.10+ y biblioteca estándar con Tkinter; herramientas de build separadas. |
| RNF-07 | Distribuir de forma trazable. | Tag, versión de app y nombre de artefacto coherentes; SHA-256 del ejecutable. |
| RNF-08 | Mantener instrucciones comprensibles. | Comentarios en español explican decisiones y bloques significativos, junto a un manual repetible. |
| RNF-09 | Publicar bajo Apache-2.0. | Incluir texto de licencia y excluir secretos, informes privados y artefactos locales del historial. |

Los límites de entrada iniciales son 1 MiB UTF-8 por lote, 1.000 URLs únicas y 8.192 caracteres por URL. La evidencia combinada de `Server` y `X-Powered-By` se limita a 16.384 caracteres, y las versiones a 128 caracteres. Los límites deben aplicarse antes de que el dato llegue a una operación costosa; un exceso debe producir un error o resultado inconcluso explícito, sin ejecutar contenido. Los informes se escriben de forma atómica.

## Reglas de decisión

Para ambas CVE, los umbrales estables son PHP 8.2.35, 8.3.36, 8.4.27 y 8.5.12. Versiones menores dentro de esas ramas originan **posible afectación**, siempre con advertencia de backports. Las ramas antiguas se remiten al proveedor. Las compilaciones preliminares, ramas desconocidas y cabeceras contradictorias son **inconclusas**.

Una versión anunciada que alcanza el umbral se describe como **versión con corrección**, con verificación pendiente del backend real. Los estados exportados conservan una representación estable aunque cambie el idioma de la interfaz.

El [aviso oficial de PHP](https://www.php.net/archive/2026.php) contiene las fuentes y el aviso adicional del 23/10 sobre sesiones. La revisión de reglas es manual; una nueva fecha o CVE exige revisar requisitos, implementación, pruebas y documentación.

## Límites aceptados

- Las cabeceras no prueban el código ejecutado por el servidor. Los parches de proveedor pueden no ser visibles.
- La aplicación no descubre todos los backends detrás de un balanceador.
- DNS y operaciones de socket lentas pueden retrasar la cancelación; detener evita iniciar nuevas consultas.
- El ejecutable no está firmado por defecto. El checksum verifica integridad respecto al artefacto publicado, no establece por sí solo confianza en el publicador.
- Una revisión de seguridad reduce riesgos conocidos y no garantiza ausencia de vulnerabilidades.

## Gestión de cambios

Antes de modificar comportamiento, actualizar los requisitos afectados y el plan; después, registrar tareas, pruebas y limitaciones reales. Un cambio relevante incrementa la versión mediante `scripts/bump_version.py`, actualiza el changelog y se publica como un nuevo tag. No se sustituye un binario de una versión ya publicada.
