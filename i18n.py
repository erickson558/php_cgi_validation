"""Textos de la interfaz; los informes conservan su esquema y estados originales."""

from php_audit import EXTRA_NOTICE, LIMITATION


# Los identificadores permanecen estables aunque cambie el texto de un idioma.
TEXTS = {
    "es": {
        "title": "Evaluación PHP · {version}",
        "heading": "Evaluación de exposición PHP",
        "rules": "{cves} · Reglas: {date}",
        "language": "Idioma:",
        "scope": "Introduce URLs de sistemas propios o con autorización. Una URL completa por línea.",
        "method": "Un GET normal por URL, sin seguir redirecciones. Evaluación basada en cabeceras.",
        "load": "Cargar TXT…", "timeout": "  Timeout (s): ",
        "start": "Evaluar URLs", "cancel": "Detener", "export": "Exportar JSON / CSV…",
        "donate": "Cómprame una cerveza", "url": "URL", "http": "HTTP",
        "version": "PHP anunciado", "state": "Evaluación", "evidence": "Evidencia y recomendación",
        "ready": "Listo. No se han enviado peticiones.",
        "progress": "Evaluadas {count} / {total}…",
        "done": "Finalizado: {count} / {total} URLs evaluadas.",
        "stopped": "Detenido: {count} / {total} URLs evaluadas.",
        "stopping": "Deteniendo; se espera a que termine la petición en curso…",
        "saved": "Informe guardado: {path}", "source": "Fuente", "action": "Acción",
        "not_visible": "No visible", "load_error": "No se pudo cargar",
        "input_error": "Revisar datos", "save_error": "No se pudo guardar",
        "donation_error": "No se pudo abrir el navegador",
        "donation_manual": "Abre este enlace en tu navegador:\n{url}",
        "urls_file": "Lista de URLs", "all_files": "Todos", "timeout_error": "El timeout debe estar entre 1 y 30 segundos.",
        "input_help": "Revisa las URLs, el formato del archivo y el timeout.",
        "unexpected_detail": "No se pudo completar la evaluación de esta URL.",
        "unexpected_action": "Revisar el error y repetir únicamente esta URL cuando se haya resuelto.",
        "limitation": LIMITATION, "notice": EXTRA_NOTICE,
        "POSIBLE AFECTACIÓN": "POSIBLE AFECTACIÓN", "VERSIÓN CON CORRECCIÓN": "VERSIÓN CON CORRECCIÓN",
        "INCONCLUSO": "INCONCLUSO", "ERROR": "ERROR",
    },
    "en": {
        "title": "PHP assessment · {version}",
        "heading": "PHP exposure assessment",
        "rules": "{cves} · Rules: {date}",
        "language": "Language:",
        "scope": "Enter URLs of systems you own or are authorized to assess. One complete URL per line.",
        "method": "One normal GET per URL, without following redirects. Assessment based on headers.",
        "load": "Load TXT…", "timeout": "  Timeout (s): ",
        "start": "Assess URLs", "cancel": "Stop", "export": "Export JSON / CSV…",
        "donate": "Buy me a beer", "url": "URL", "http": "HTTP",
        "version": "Advertised PHP", "state": "Assessment", "evidence": "Evidence and recommendation",
        "ready": "Ready. No requests have been sent.",
        "progress": "Assessed {count} / {total}…",
        "done": "Finished: {count} / {total} URLs assessed.",
        "stopped": "Stopped: {count} / {total} URLs assessed.",
        "stopping": "Stopping; waiting for the current request to finish…",
        "saved": "Report saved: {path}", "source": "Source", "action": "Action",
        "not_visible": "Not visible", "load_error": "Could not load file",
        "input_error": "Check input", "save_error": "Could not save report",
        "donation_error": "Could not open browser",
        "donation_manual": "Open this link in your browser:\n{url}",
        "urls_file": "URL list", "all_files": "All files", "timeout_error": "Timeout must be between 1 and 30 seconds.",
        "input_help": "Check that every URL is complete, uses HTTP(S), has a valid host and port, and contains no credentials, whitespace or control characters. Check the file size and timeout too.",
        "unexpected_detail": "Could not complete the assessment of this URL.",
        "unexpected_action": "Review the error and retry this URL after resolving it.",
        "limitation": "Assessment based on the advertised version; it does not confirm exploitation. Headers may be hidden, modified or supplied by an intermediary. Verify the installed package and vendor patches on the server handling the URL.",
        "notice": "The 23 October 2026 advisory for CVE-2026-115560 requires configuration and application-code review. This tool does not assess it. PHP recommends session.upload_progress.enabled=0 until the next regular fix release.",
        "POSIBLE AFECTACIÓN": "POSSIBLY AFFECTED", "VERSIÓN CON CORRECCIÓN": "VERSION WITH FIX",
        "INCONCLUSO": "INCONCLUSIVE", "ERROR": "ERROR",
    },
}


def translate(language, key, **values):
    """Resuelve una clave con retorno a español si falta una traducción."""
    return TEXTS.get(language, TEXTS["es"]).get(key, TEXTS["es"].get(key, key)).format(**values)


def result_explanation(result, language):
    """Traduce la interpretación visible sin alterar la evidencia exportada."""
    if language == "es":
        return result.detail, result.recommendation
    # En inglés explicamos los mismos estados usando la evidencia del resultado.
    # No se recalcula la clasificación ni se confunde con confirmación de explotación.
    if result.state == "POSIBLE AFECTACIÓN":
        detail = "The advertised PHP version is below the fixed release for its branch, or belongs to an older unsupported branch. Vendor backports may exist."
        action = "Update to PHP 8.2.35, 8.3.36, 8.4.27 or 8.5.12 (or a later supported release in the corresponding branch), or verify the exact vendor package and its backported fixes."
    elif result.state == "VERSIÓN CON CORRECCIÓN":
        detail = "The advertised version reaches the fixed-release threshold for both CVEs published on 21 October 2026. This is header evidence only."
        action = "Verify the actual installed package, every worker and the additional 23 October advisory. This result does not certify general security."
    elif result.state == "ERROR":
        detail = "The request or assessment failed. No vulnerability conclusion can be drawn."
        action = "Check the URL, network connectivity, TLS certificate and the reported error before retrying."
    else:
        detail = "No single supported stable PHP version could be established. Headers may be missing, incomplete or conflicting, or the advertised branch/build is outside the tool's rules."
        action = "Ask the administrator for an inventory of the actual backend package, its exact build and vendor patch status."
    if result.http_status is not None and 300 <= result.http_status < 400:
        detail += " Redirect not followed: assess its destination separately only if authorized."
    return detail, action
