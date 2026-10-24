# Contribuir

Revisa el [alcance del producto](docs/spec.md) antes de proponer una función. Usa issues para describir el problema y su resultado esperado; para vulnerabilidades del propio programa consulta [SECURITY.md](SECURITY.md).

## Preparación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

No pruebes objetivos de terceros para contribuir. Los casos HTTP deben utilizar un servidor de loopback y datos sintéticos. Las pruebas de interfaz pueden omitirse cuando el entorno no disponga de pantalla; registra esa limitación.

## Preparar un cambio

1. Explica el comportamiento esperado y actualiza los requisitos afectados en `docs/spec.md`.
2. Ajusta el plan y las tareas si cambia el alcance o la validación.
3. Implementa la solución con comentarios en español que expliquen bloques significativos y decisiones.
4. Añade o ajusta pruebas que comprueben comportamientos y riesgos reales; conserva TLS, ausencia de redirecciones y estados inconclusos.
5. Actualiza traducciones ES/EN y documentación cuando cambie una interacción.
6. Incrementa la versión para el commit que se integrará en main, completa el changelog y ejecuta las comprobaciones.

Usa mensajes como `feat: add compatible functionality`, `fix: handle malformed response` o `docs: clarify report interpretation`. Antes de hacer commit, revisa `git diff --cached` para evitar incluir credenciales, informes, URLs privadas o binarios.

Cada commit nuevo de `main` necesita una versión sin publicar. Si se combinan cambios de varias ramas, prepara una versión coherente para el commit final que publique el mantenedor. El [manual](docs/MANUAL.md) describe el incremento, build y release.

## Revisión

Incluye en la propuesta el problema concreto, el nuevo comportamiento, la validación realizada y los límites pendientes. Para cambios de reglas PHP, aporta la fuente oficial, fecha y casos de prueba de sus fronteras; no afirmes vulnerabilidad confirmada basándote solo en cabeceras.

Las contribuciones se distribuyen bajo Apache License 2.0. No incluyas código, recursos o datos que no tengas derecho a compartir.
