---
name: php-validation-security
description: Revisar o endurecer explícitamente la seguridad de php_cgi_validation, sus entradas HTTP, exportación y cadena de publicación.
---

# Revisión de seguridad del proyecto

Aplica esta revisión al solicitarse una auditoría o endurecimiento, o cuando un
cambio afecte directamente límites de confianza. Lee `SECURITY.md`, `docs/spec.md`
y `docs/SECURITY_REVIEW.md`. Trata cabeceras, URLs y archivos TXT como datos no confiables.

Verifica límites de lote, longitud y evidencia; TLS; ausencia de redirecciones;
neutralización de fórmulas CSV; escritura atómica; aislamiento de errores por URL;
y diagnóstico PHP limitado a loopback. Revisa por separado los permisos de Actions,
el origen y el commit de tags, secretos y dependencias de compilación.

Reproduce hallazgos con servidores loopback y fixtures. No pruebes terceros ni
agregues exploits para validar seguridad. Corrige dentro de la autorización vigente,
añade regresiones relevantes y documenta gravedad, evidencia y riesgo residual.

Ejecuta `python -m pip_audit -r requirements-build.txt --strict` con el entorno de
desarrollo; distingue vulnerabilidades conocidas de paquetes, fallos propios y
limitaciones del protocolo. Un resultado sin hallazgos no demuestra ausencia de
vulnerabilidades. Actualiza el informe y la trazabilidad SDD tras las correcciones.
