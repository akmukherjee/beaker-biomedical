import json
import ipaddress
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.parse import urlsplit

def live_execution_available() -> bool:
    return True

ALLOWED_HOST = 'federation.ccdi.cancer.gov'

_PATH_ALLOWLIST = (
    (re.compile(r'^/subject$'), {
        'age_at_vital_status', 'depositions', 'ethnicity', 'identifiers',
        'page', 'per_page', 'race', 'sex', 'vital_status',
    }),
    (re.compile(r'^/subject/summary$'), set()),
    (re.compile(r'^/subject-mapping$'), {
        'age_at_vital_status', 'depositions', 'ethnicity', 'identifiers',
        'page', 'per_page', 'race', 'search', 'sex', 'vital_status',
    }),
    (re.compile(r'^/sample$'), {
        'age_at_collection', 'age_at_diagnosis', 'anatomical_sites', 'depositions',
        'diagnosis', 'diagnosis_category', 'disease_phase', 'library_selection_method',
        'library_source_material', 'library_strategy', 'page', 'per_page',
        'preservation_method', 'specimen_molecular_analyte_type', 'tissue_type',
        'tumor_classification', 'tumor_grade', 'tumor_tissue_morphology',
    }),
    (re.compile(r'^/sample/summary$'), set()),
    (re.compile(r'^/file$'), {
        'checksums', 'depositions', 'description', 'page', 'per_page', 'size', 'type',
    }),
    (re.compile(r'^/file/summary$'), set()),
    (re.compile(r'^/metadata/fields/(subject|sample|file)$'), set()),
    (re.compile(r'^/namespace$'), set()),
    (re.compile(r'^/organization$'), set()),
    (re.compile(r'^/info$'), set()),
    (re.compile(r'^/sample-diagnosis$'), {
        'age_at_collection', 'age_at_diagnosis', 'anatomical_sites', 'depositions',
        'diagnosis', 'disease_phase', 'library_selection_method',
        'library_source_material', 'library_strategy', 'page', 'per_page',
        'preservation_method', 'search', 'specimen_molecular_analyte_type',
        'tissue_type', 'tumor_classification', 'tumor_tissue_morphology',
    }),
    (re.compile(r'^/subject-diagnosis$'), {
        'age_at_vital_status', 'depositions', 'ethnicity', 'identifiers',
        'page', 'per_page', 'race', 'search', 'sex', 'vital_status',
    }),
    (re.compile(r'^/subject/[^/]+/[^/]+/[^/]+$'), set()),
    (re.compile(r'^/subject/by/[^/]+/count$'), set()),
    (re.compile(r'^/sample/[^/]+/[^/]+/[^/]+$'), set()),
    (re.compile(r'^/sample/by/[^/]+/count$'), set()),
    (re.compile(r'^/file/[^/]+/[^/]+/[^/]+$'), set()),
    (re.compile(r'^/file/by/[^/]+/count$'), set()),
    (re.compile(r'^/namespace/[^/]+/[^/]+$'), set()),
    (re.compile(r'^/organization/[^/]+$'), set()),
)

# Hostnames that are always blocked regardless of IP resolution.
# These include loopback aliases and cloud instance metadata endpoints
# that should never be reachable from this client.
_BLOCKED_HOSTNAMES = {
    'localhost',
    'metadata.google.internal',
    'metadata',
}

# Explicit IP addresses to block in addition to the broader checks in
# _is_blocked_host (private, loopback, link-local, reserved, multicast, and
# unspecified ranges).  Add any specific addresses here that are not already
# covered by those categories.
_BLOCKED_IPS: set[str] = set()
_UNHARMONIZED_PREFIX = 'metadata.unharmonized.'


def _error(url: str, error_code: str, status: int | None = None) -> dict:
    return {
        'ok': False,
        'url': url,
        'status': status,
        'payload': None,
        'errors': [error_code],
    }


def _is_blocked_host(hostname: str) -> bool:
    host = hostname.lower()
    if host in _BLOCKED_HOSTNAMES or host.endswith('.local'):
        return True
    if host in _BLOCKED_IPS:
        return True

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False

    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_base_url(base_url: str) -> str | None:
    parsed = urlsplit(base_url)

    if parsed.scheme.lower() != 'https':
        return 'https_required'
    if parsed.username or parsed.password:
        return 'credentials_not_allowed'

    host = parsed.hostname or ''
    if not host:
        return 'invalid_host'
    if _is_blocked_host(host):
        return 'blocked_host'
    if host.lower() != ALLOWED_HOST:
        return 'external_host_not_allowed'

    try:
        port = parsed.port
    except ValueError:
        return 'port_not_allowed'
    if port is not None:
        return 'port_not_allowed'
    if parsed.query or parsed.fragment:
        return 'base_url_must_not_include_query_or_fragment'
    if parsed.path.rstrip('/') != '/api/v1':
        return 'base_path_not_allowed'
    return None


def _allowed_params_for_path(path: str) -> set[str] | None:
    for pattern, params in _PATH_ALLOWLIST:
        if pattern.fullmatch(path):
            return params
    return None


def _validate_path_and_params(path: str, params: dict) -> str | None:
    if not path.startswith('/') or '//' in path or '..' in path:
        return 'unsupported_path'

    allowed_params = _allowed_params_for_path(path)
    if allowed_params is None:
        return 'unsupported_path'

    for key in params:
        if key in allowed_params:
            continue
        if key.startswith(_UNHARMONIZED_PREFIX) and len(key) > len(_UNHARMONIZED_PREFIX):
            continue
        return 'unsupported_query_parameter'

    return None


def build_request_url(base_url: str, path: str, params: dict | None = None) -> str:
    base = base_url.rstrip('/')
    route = path if path.startswith('/') else f'/{path}'
    if not params:
        return f'{base}{route}'

    return f'{base}{route}?{urlencode(params, doseq=True)}'


def read_only_get(
    base_url: str,
    path: str,
    params: dict | None = None,
    timeout_seconds: int = 90,
    max_retries: int = 0,
    urlopen=None,
) -> dict:
    """Execute a read-only GET request against the CCDI Federation API.

    Args:
        base_url: The base URL of the API (e.g. ``https://federation.ccdi.cancer.gov/api/v1/``).
        path: The API path relative to *base_url*.
        params: Optional query parameters to include in the request, such as
            endpoint-specific filters or pagination values.
        timeout_seconds: Request timeout in seconds.
        max_retries: Number of additional retry attempts on failure.
        urlopen: Injectable URL opener for testing; defaults to :func:`urllib.request.urlopen`.
    """
    if urlopen is None:
        from urllib.request import HTTPRedirectHandler
        from urllib.request import build_opener

        class _NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = build_opener(_NoRedirect)

        def _urlopen(url, timeout=30):
            return opener.open(url, timeout=timeout)

        urlopen = _urlopen

    merged_params: dict = dict(params) if params else {}
    route = path if path.startswith('/') else f'/{path}'

    base_error = _validate_base_url(base_url)
    if base_error:
        url = build_request_url(base_url, route, merged_params)
        return _error(url, base_error)

    path_error = _validate_path_and_params(route, merged_params)
    if path_error:
        url = build_request_url(base_url, route, merged_params)
        return _error(url, path_error)

    url = build_request_url(base_url, route, merged_params)
    attempts = max_retries + 1
    last_error = ''

    for _ in range(attempts):
        try:
            with urlopen(url, timeout=timeout_seconds) as response:
                if hasattr(response, 'geturl') and response.geturl() != url:
                    return _error(url, 'redirect_not_allowed')

                payload = response.read().decode('utf-8')
                status = getattr(response, 'status', None)
                try:
                    parsed_payload = json.loads(payload)
                except json.JSONDecodeError:
                    return _error(url, 'invalid_json_response', status=status)

                return {
                    'ok': True,
                    'url': url,
                    'status': status,
                    'payload': parsed_payload,
                    'errors': [],
                }
        except HTTPError as exc:
            if 300 <= exc.code < 400:
                return _error(url, 'redirect_not_allowed', status=exc.code)
            last_error = str(exc)
        except OSError as exc:
            last_error = str(exc)

    return _error(url, last_error if last_error else 'unknown_error')
