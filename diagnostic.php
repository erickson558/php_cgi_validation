<?php
/* Diagnóstico temporal: copiar solo al servidor local y retirar al terminar.
 * Se comprueba la conexión directa; no se confía en X-Forwarded-For. */
if (!isset($_SERVER['REMOTE_ADDR']) || !in_array($_SERVER['REMOTE_ADDR'], array('127.0.0.1', '::1'), true)) {
    http_response_code(403);
    exit;
}

/* Evita que el navegador o un intermediario almacenen esta configuración. */
header('Content-Type: text/plain; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

/* Solo se muestran tres datos; no se expone phpinfo() ni el entorno completo. */
echo 'PHP_VERSION=' . PHP_VERSION . "\n";
echo 'PHP_SAPI=' . PHP_SAPI . "\n";
echo 'SERVER_SOFTWARE=' . (isset($_SERVER['SERVER_SOFTWARE']) ? $_SERVER['SERVER_SOFTWARE'] : 'unknown') . "\n";
?>
