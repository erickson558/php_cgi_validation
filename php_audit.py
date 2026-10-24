"""Evaluación de versiones PHP con HTTP normal, sin pruebas de explotación."""

from __future__ import annotations

import csv
import http.client
import json
import os
import re
import ssl
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from app_version import VERSION


# Reglas del aviso verificado y límites que también puede usar la interfaz.
# El motor solo conserva evidencia pequeña: una respuesta remota no controla
# el tamaño de los informes ni permite convertir números arbitrariamente largos.
MAX_URL_LENGTH = 8192
MAX_TARGETS = 1000
MAX_INPUT_BYTES = 1024 * 1024
MAX_HEADER_CHARS = 16384
MAX_VERSION_LENGTH = 128
ADVISORY_URL = "https://www.php.net/archive/2026.php"
RULES_DATE = "2026-10-24"
CVES = ("CVE-2026-109618", "CVE-2026-109619")
FIXED = {(8, 2): 35, (8, 3): 36, (8, 4): 27, (8, 5): 12}
LIMITATION = (
    "Evaluación por versión anunciada; no confirma explotación. Las cabeceras pueden "
    "estar ocultas, alteradas o pertenecer a un intermediario. Verificar el paquete "
    "instalado y los parches del proveedor en el servidor que atiende la URL."
)
EXTRA_NOTICE = (
    "El aviso del 23/10/2026 sobre CVE-2026-115560 requiere revisar configuración "
    "y código. Esta herramienta no la evalúa. PHP recomienda "
    "session.upload_progress.enabled=0 hasta la siguiente corrección regular."
)


@dataclass
class Assessment:
    """Interpretación orientativa; no representa una explotación confirmada."""

    state: str
    detail: str
    recommendation: str


@dataclass
class AuditResult:
    """Evidencia y límites de una petición, independientes de la GUI."""

    url: str
    checked_at_utc: str
    http_status: int | None
    server: str
    x_powered_by: str
    php_version: str
    state: str
    detail: str
    recommendation: str
    error: str = ""
    cves: tuple[str, ...] = CVES
    rules_date: str = RULES_DATE
    source: str = ADVISORY_URL
    limitation: str = LIMITATION
    additional_notice: str = EXTRA_NOTICE
    app_version: str = VERSION


def normalize_url(value: str) -> str:
    """Valida el destino antes de permitir que urllib construya una petición."""
    value = value.strip()
    if len(value) > MAX_URL_LENGTH:
        raise ValueError(f"La URL supera el límite de {MAX_URL_LENGTH} caracteres.")
    if not value or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError("La URL está vacía o contiene espacios/caracteres de control.")
    parts = urlsplit(value)
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        raise ValueError("Usa una URL completa: https://servidor/ruta")
    if parts.username is not None or parts.password is not None:
        raise ValueError("No se aceptan credenciales dentro de la URL.")
    if "\\" in parts.netloc:
        raise ValueError("El servidor contiene una barra no válida.")
    try:
        parts.port
        host = parts.hostname.encode("idna").decode("ascii")
        parts.path.encode("ascii")
        parts.query.encode("ascii")
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Puerto o URL inválidos; codifica rutas Unicode con %XX.") from exc
    if ":" in host:
        host = f"[{host}]"
    netloc = host + (f":{parts.port}" if parts.port is not None else "")
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def parse_targets(text: str) -> list[str]:
    """Una URL por línea. Valida todo antes de iniciar peticiones."""
    if len(text.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("La lista supera el límite de 1 MiB.")
    targets = []
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            url = normalize_url(line)
        except ValueError as exc:
            raise ValueError(f"Línea {number}: {exc}") from exc
        if url not in seen:
            if len(targets) >= MAX_TARGETS:
                raise ValueError(f"Se permiten como máximo {MAX_TARGETS} URLs por lote.")
            seen.add(url)
            targets.append(url)
    if not targets:
        raise ValueError("Introduce al menos una URL.")
    return targets


def assess_version(version: str) -> Assessment:
    """Compara solo versiones completas y acotadas, conservando incertidumbre."""
    # No convertir dígitos remotos sin límites: int() puede rechazar entradas
    # enormes y una cabecera maliciosa no debe interrumpir el lote completo.
    match = None
    if len(version) <= MAX_VERSION_LENGTH:
        match = re.fullmatch(r"([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})([+-][0-9A-Za-z][0-9A-Za-z.+~:_-]*|(?:dev|alpha|beta|RC)[0-9]*)?", version, re.I)
    if not match:
        return Assessment("INCONCLUSO", "No hay una versión PHP completa verificable.",
                          "Solicitar inventario del servidor y estado de parches al administrador.")
    major, minor, patch = map(int, match.group(1, 2, 3))
    suffix = match.group(4) or ""
    if re.search(r"dev|alpha|beta|rc", suffix, re.I) or (major, minor) not in FIXED:
        if (5, 0) <= (major, minor) <= (8, 1) and not suffix:
            return Assessment("POSIBLE AFECTACIÓN", "Rama antigua sin soporte del proyecto PHP.",
                              "Migrar a una rama soportada o verificar un parche del proveedor.")
        if (5, 0) <= (major, minor) <= (8, 1) and not re.search(r"dev|alpha|beta|rc", suffix, re.I):
            return Assessment("POSIBLE AFECTACIÓN", "Rama antigua; puede tener un backport del proveedor.",
                              "Verificar el aviso y la revisión exacta del paquete del proveedor.")
        return Assessment("INCONCLUSO", "Rama o compilación preliminar fuera de las reglas de esta herramienta.",
                          "Consultar el aviso de PHP y el proveedor para esta compilación exacta.")
    minimum = FIXED[(major, minor)]
    fixed_version = f"{major}.{minor}.{minimum}"
    if patch < minimum:
        return Assessment("POSIBLE AFECTACIÓN",
                          f"La versión anunciada es anterior a {fixed_version}; puede haber backports.",
                          f"Actualizar a {fixed_version} o posterior de esta rama, o acreditar el parche del proveedor.")
    return Assessment("VERSIÓN CON CORRECCIÓN",
                      f"La versión anunciada alcanza {fixed_version}, umbral para las dos CVE del 21/10.",
                      "Verificar el paquete real, todos los workers y el aviso adicional del 23/10. No acredita seguridad general.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Mantiene las peticiones dentro de las URLs introducidas explícitamente."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Cada URL introducida es el alcance: no se siguen destinos adicionales.
        return None


def audit_url(url: str, timeout: float = 8) -> AuditResult:
    """Hace un GET sin cuerpo ni redirecciones y conserva evidencia acotada."""
    url = normalize_url(url)
    if not 1 <= timeout <= 30:
        raise ValueError("El timeout debe estar entre 1 y 30 segundos.")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    opener = urllib.request.build_opener(
        NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context())
    )
    request = urllib.request.Request(url, headers={"User-Agent": f"PHP-Version-Audit/{VERSION}"})
    status = None
    server = powered = ""
    try:
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            # Un 403/500 también puede aportar cabeceras; no indica una CVE.
            response = exc
        with response:
            status = response.code
            values = response.headers.get_all("Server", []) + response.headers.get_all("X-Powered-By", [])
            if sum(map(len, values)) > MAX_HEADER_CHARS:
                raise ValueError("Las cabeceras de evidencia superan el límite de 16 KiB.")
            # Los controles se representan como texto para que una cabecera no
            # pueda introducir líneas falsas en el panel de evidencia.
            server = visible_text("; ".join(response.headers.get_all("Server", [])))
            powered = visible_text("; ".join(response.headers.get_all("X-Powered-By", [])))
            # No descargamos cuerpos, ni pedimos phpinfo/diagnostic.php.
    except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException) as exc:
        return AuditResult(url, timestamp, status, server, powered, "", "ERROR",
                           "No se pudo obtener una respuesta HTTP válida.",
                           "Revisar conectividad, URL y certificado TLS; no se infiere vulnerabilidad.", visible_text(str(exc))[:2048])
    versions = sorted(set(re.findall(r"\bPHP/([0-9]+\.[0-9]+\.[0-9]+[^\s;,)\"<>]*)",
                                    f"{powered}; {server}", re.I)))
    if len(versions) == 1:
        assessment = assess_version(versions[0])
    elif versions:
        assessment = Assessment("INCONCLUSO", "Se anunciaron versiones PHP contradictorias.",
                                "Identificar las versiones reales de cada backend con el administrador.")
    else:
        assessment = assess_version("")
    if status is not None and 300 <= status < 400:
        assessment.detail += " Redirección sin seguir: evaluar la URL de destino solo si está autorizada."
    return AuditResult(url, timestamp, status, server, powered, ", ".join(versions),
                       assessment.state, assessment.detail, assessment.recommendation)


def csv_cell(value):
    # Evita que una cabecera o URL se interprete como fórmula al abrir el CSV.
    text = str(value) if value is not None else ""
    return "'" + text if text.lstrip("\ufeff \t\r\n").startswith(("=", "+", "-", "@")) else text


def visible_text(value: str) -> str:
    """Escapa controles remotos sin interpretar ni ejecutar su contenido."""
    return "".join(f"\\x{ord(char):02x}" if ord(char) < 32 or ord(char) == 127 else char for char in value)


def export_results(results: list[AuditResult], path: str | Path) -> None:
    """Escribe primero un temporal vecino para conservar el informe si falla."""
    path = Path(path)
    records = [asdict(result) for result in results]
    temporary = None
    try:
        encoding = "utf-8-sig" if path.suffix.lower() == ".csv" else "utf-8"
        with tempfile.NamedTemporaryFile(mode="w", encoding=encoding, newline="", dir=path.parent,
                                         prefix=".php-audit-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            if path.suffix.lower() == ".csv":
                writer = csv.DictWriter(output, fieldnames=list(AuditResult.__dataclass_fields__))
                writer.writeheader()
                for record in records:
                    record["cves"] = ", ".join(record["cves"])
                    writer.writerow({key: csv_cell(value) for key, value in record.items()})
            else:
                json.dump({"results": records, "app_version": VERSION, "rules_date": RULES_DATE,
                           "source": ADVISORY_URL, "limitation": LIMITATION,
                           "additional_notice": EXTRA_NOTICE}, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        # El temporal está en el mismo directorio: no hay copia parcial entre discos.
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
