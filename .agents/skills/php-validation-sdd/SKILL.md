---
name: php-validation-sdd
description: Mantener especificación, plan y tareas de php_cgi_validation junto con cambios funcionales y sus pruebas.
---

# Desarrollo desde la especificación

Localiza la raíz de `php_cgi_validation` y lee `AGENTS.md`, `docs/spec.md`,
`docs/plan.md` y `docs/tasks.md`. Para cambios funcionales, identifica o añade
primero el requisito y su criterio de aceptación. Actualiza el plan si afecta
arquitectura, límites, dependencias o publicación; implementa y verifica el comportamiento.

Registra evidencia real en las tareas: distingue pruebas locales, compilación y
validación remota. Mantén trazabilidad requisito/prueba y documenta límites sin
convertir una inferencia por versión en una afirmación de explotación.

Sincroniza ES/EN, comentarios en español, changelog y versión cuando corresponda.
Lee la skill de release del repositorio para versionar o publicar; una modificación
funcional por sí sola no autoriza operaciones externas.
