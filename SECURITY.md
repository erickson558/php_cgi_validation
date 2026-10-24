# Seguridad

## Alcance y versiones

Se aceptan reportes de seguridad sobre la última versión publicada de este proyecto. Las versiones anteriores deben actualizarse para recibir las correcciones. No existe una garantía de ausencia de vulnerabilidades ni un compromiso de atención en un plazo fijo.

El programa es un cliente de escritorio para evaluación preliminar de versiones PHP. No demuestra que una CVE sea explotable, no certifica la seguridad del objetivo y no sustituye la revisión de paquetes y configuración. Úsalo únicamente sobre sistemas propios o autorizados.

## Reportar una vulnerabilidad

Usa [Report a vulnerability](https://github.com/erickson558/php_cgi_validation/security/advisories/new) en GitHub si la función está habilitada para el repositorio. Describe la versión, sistema operativo, pasos mínimos con datos sintéticos, impacto y mitigación conocida. No incluyas tokens, datos de clientes ni objetivos de terceros.

Si el canal privado no está disponible, crea un issue solicitando un canal privado de contacto **sin publicar detalles de explotación ni información sensible**. Los errores ordinarios de uso o solicitudes de funciones pueden tratarse en issues públicos.

Los problemas del runtime PHP deben reportarse al proyecto PHP o al proveedor correspondiente. El [aviso PHP de octubre de 2026](https://www.php.net/archive/2026.php) es la referencia para las reglas incluidas.

## Medidas y límites

- HTTP/HTTPS con validación TLS; sin seguir redirecciones ni descubrir rutas adicionales.
- Entradas y respuestas consideradas no confiables: límite de 1 MiB por lote, 1.000 URLs únicas, 8.192 caracteres por URL, 16.384 caracteres de evidencia y 128 por versión. Los errores de red se presentan como errores, no como confirmación de vulnerabilidad.
- Exportación atómica y CSV con neutralización de fórmulas. Los informes contienen las URLs y la evidencia: el operador debe revisar su sensibilidad antes de compartirlos.
- Dependencias de ejecución limitadas a la biblioteca estándar. Las herramientas de build y desarrollo tienen su propio ciclo de revisión y actualización.
- El diagnóstico `diagnostic.php` pertenece a un laboratorio local y debe retirarse después de usarse.
- Los checksums de release permiten comparar integridad. Los ejecutables no tienen firma de código por defecto.

La revisión realizada y los riesgos residuales se documentan en [docs/SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md). Los resultados de una herramienta de análisis o de una suite de pruebas se limitan a lo que cada comprobación cubre.
