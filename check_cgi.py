#!/usr/bin/env python3
"""Diagnóstico local de PHP-CGI con peticiones normales y sin explotación."""

import argparse
import http.client
import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

from php_audit import NoRedirect, normalize_url


def local_url(url):
    """Comprueba el alcance y evita que 'localhost' dependa de resolución DNS."""
    url = normalize_url(url)
    parts = urlsplit(url)
    if parts.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Solo se permiten destinos localhost/127.0.0.1/::1.")
    if parts.hostname == "localhost":
        netloc = "127.0.0.1" + (f":{parts.port}" if parts.port is not None else "")
        url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, ""))
    return url


def fetch(url):
    """Devuelve solo cabeceras y una muestra de cuerpo de hasta 2048 bytes."""
    # Una redirección local no puede ampliar el alcance ni pasar por un proxy.
    url = local_url(url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    req = urllib.request.Request(url, headers={'User-Agent': 'Local-PHP-CGI-Audit/1.0'})
    try:
        response = opener.open(req, timeout=8)
    except urllib.error.HTTPError as exc:
        # Un estado 3xx/4xx/5xx también es una respuesta que se puede comparar.
        response = exc
    with response:
        return {
            'status': response.code,
            'headers': {key.lower(): value for key, value in response.headers.items()},
            'sample': response.read(2048).decode('utf-8', 'replace'),
        }


def main():
    # Este modo heredado solo compara respuestas; no decide si PHP es explotable.
    p = argparse.ArgumentParser(description='Diagnóstico local de configuración PHP-CGI')
    p.add_argument('url', help='Endpoint local, por ejemplo http://localhost:888/diagnostic.php')
    args = p.parse_args()
    try:
        url = local_url(args.url)
        parts = urlsplit(url)
        base = fetch(url)
        query = fetch(url + ('&' if parts.query else '?') + 'php_cgi_audit=1')
    except (OSError, ValueError, http.client.HTTPException) as exc:
        p.exit(1, f'No se pudo realizar el diagnóstico: {exc}\n')
    # Las cabeceras HTTP no distinguen mayúsculas; se normalizan en fetch().
    report = {
        'url': url,
        'baseline': {
            'status': base['status'],
            'server': base['headers'].get('server'),
            'x_powered_by': base['headers'].get('x-powered-by'),
        },
        'benign_query': {'status': query['status']},
        'interpretation': (
            'Estas peticiones no explotan CVE-2024-4577 ni demuestran el modo CGI. '
            'Revisar el diagnóstico PHP y la configuración Apache para identificar el handler.'
        ),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
