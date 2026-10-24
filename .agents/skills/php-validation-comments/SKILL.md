---
name: php-validation-comments
description: Explicar en español el código de php_cgi_validation cuando se añadan o cambien bloques de lógica para facilitar su aprendizaje.
---

# Comentarios para aprender el proyecto

En `php_cgi_validation`, añade docstrings para módulos, clases y funciones públicas
y comentarios antes de cada bloque significativo: validación, petición HTTP,
interpretación de evidencia, concurrencia, traducción, exportación y publicación.

Explica propósito, datos de entrada/salida y decisiones que no sean obvias.
En límites de seguridad explica qué fallo evitan. No narres cada asignación ni
dupliques el código en prosa. Corrige comentarios que dejen de describir la lógica.

Mantén nombres y comportamiento de las API al hacer una edición de comentarios.
Los comentarios son en español; las etiquetas visibles se mantienen en ES/EN
mediante `i18n.py`. Después de cambiar lógica aplica también SDD y las pruebas pertinentes.
