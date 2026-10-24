# Tareas y evidencia

Esta lista registra evidencia de ejecución; no debe confundir archivos preparados con publicación completada.

## Base observada

- [x] Diagnóstico original de PHP-CGI identificado y separado de la evaluación nueva.
- [x] Evaluación inicial de cabeceras y reglas de las dos CVE del 21/10 implementada.
- [x] Suite inicial de 12 pruebas locales superada antes de preparar la distribución.
- [x] Especificación y plan escritos para la preparación de V1.0.0.

## Preparación de V1.0.0

- [x] Completar y verificar endurecimiento de entradas, respuestas e informes. Evidencia: `docs/SECURITY_REVIEW.md` y pruebas.
- [x] Completar y verificar GUI ES/EN, versión e interacción del botón de donación.
- [x] Comentar los bloques significativos del código en español.
- [x] Crear y validar roles de mantenimiento y skills del proyecto.
- [x] Validar versión, metadatos, README y changelog.
- [x] Ejecutar la suite completa y registrar resultado real.
- [x] Revisar dependencias y comprobar hallazgos de las herramientas configuradas.
- [x] Compilar el ejecutable Windows y comprobar inicio, nombre e icono.
- [x] Revisar licencia, archivos incluidos y exclusiones antes del commit.

## Publicación

- [ ] Inicializar Git con `main` y crear el primer commit.
- [ ] Crear o verificar `erickson558/php_cgi_validation` como repositorio público.
- [ ] Configurar `origin` y subir `main`.
- [ ] Comprobar ejecución satisfactoria del workflow.
- [ ] Verificar tag de la versión y release con ejecutable y checksums.
- [ ] Registrar URL del repositorio, URL del release y evidencia final de validación.

## Mantenimiento

- [ ] Antes de cada cambio funcional: revisar `spec.md` y `plan.md`.
- [ ] Antes de cada commit relevante: incrementar versión y completar `CHANGELOG.md`.
- [ ] Antes de cada publicación: ejecutar pruebas, comprobaciones y build; revisar contenido preparado para Git.
- [ ] Después de cada publicación: confirmar el resultado remoto y cerrar las tareas con evidencia.

## Evidencia final de la preparación

Preparación local verificada el 2026-10-24: 26 pruebas aprobadas, Ruff correcto, dependencias de compilación sin vulnerabilidades conocidas según pip-audit, cuatro skills validadas y ejecutable Windows con arranque, subsistema GUI, icono y versión comprobados. La instalación editable y el entry point también se verificaron. La publicación se registrará después de comprobar GitHub Actions.
