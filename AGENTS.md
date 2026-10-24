# Guía de mantenimiento

Este proyecto evalúa indicios de exposición PHP mediante peticiones HTTP normales.
La especificación vigente está en [docs/spec.md](docs/spec.md); mantén alineados
[plan](docs/plan.md), [tareas](docs/tasks.md) y pruebas cuando cambie el comportamiento.

## Roles y skills

- **Coordinación y especificación:** define alcance y criterios de aceptación;
  aplica [.agents/skills/php-validation-sdd/SKILL.md](.agents/skills/php-validation-sdd/SKILL.md).
- **Interfaz y aprendizaje:** conserva ES/EN, datos al cambiar idioma y donación solo
  por clic; aplica [.agents/skills/php-validation-comments/SKILL.md](.agents/skills/php-validation-comments/SKILL.md).
- **Seguridad y verificación:** revisa límites, entradas remotas, exportación y
  tolerancia a fallos; aplica [.agents/skills/php-validation-security/SKILL.md](.agents/skills/php-validation-security/SKILL.md).
- **Versionado y publicación:** mantiene versión única, ejecutable y releases;
  aplica [.agents/skills/php-validation-release/SKILL.md](.agents/skills/php-validation-release/SKILL.md).

Los roles pueden delegarse cuando el usuario solicite trabajo con varios agentes.
Asigna archivos distintos y coordina cualquier cambio de API antes de integrarlo.

## Invariantes

- Una URL explícita es el alcance. No agregar rastreo, payloads de explotación ni
  seguimiento automático de redirecciones. No afirmar vulnerabilidad confirmada
  basándose en cabeceras ni prometer ausencia de vulnerabilidades.
- Mantener `VERSION` en `app_version.py` como fuente única. Usar `Vx.x.x` en GUI,
  tags, releases y nombres de ejecutable; SemVer numérico en metadatos Python.
- Comentar en español cada bloque significativo y explicar decisiones y límites.
  Las cadenas de interfaz deben existir en español e inglés.
- No registrar credenciales, informes reales de clientes ni secretos. Conservar
  los informes locales en `reports/`, excluido de Git.
- No añadir atribuciones de asistencia automatizada ni trailers de coautoría.
- Publicar en `erickson558/php_cgi_validation` solo cuando la petición lo autorice.
  No guardar tokens en código, skills, logs ni documentación.

## Validación habitual

```powershell
python scripts/bump_version.py --check
python build.py --check
python -m unittest discover -s tests -v
python -m ruff check .
python -m pip_audit -r requirements-build.txt --strict
```

Compilar en Windows con `python build.py`; verificar el binario con `--smoke-test`.
Los detalles de reproducción y publicación están en [docs/MANUAL.md](docs/MANUAL.md).
