"""Tests for ccdi_client.py."""

import json
import unittest
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from ccdi_client import build_request_url, read_only_get

BASE_URL = 'https://federation.ccdi.cancer.gov/api/v1/'
SUBJECT_PATH = '/subject'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeResponse:
    """Minimal file-like object that mimics :class:`http.client.HTTPResponse`."""

    def __init__(self, body: dict, status: int = 200, final_url: str | None = None):
        self._data = BytesIO(json.dumps(body).encode())
        self.status = status
        self.headers = {}
        self._final_url = final_url

    def read(self) -> bytes:
        return self._data.read()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def geturl(self) -> str | None:
        return self._final_url


def _make_urlopen(body: dict, status: int = 200, final_url: str | None = None):
    """Return a fake *urlopen* that captures the requested URL and returns *body*."""
    captured = {}

    def _urlopen(url, **kwargs):
        captured['url'] = url
        return _FakeResponse(body, status, final_url=final_url or url)

    return _urlopen, captured


def _query_params(url: str) -> dict:
    """Parse query string from *url* into a ``{key: [value, …]}`` dict."""
    return parse_qs(urlparse(url).query)


# ---------------------------------------------------------------------------
# build_request_url
# ---------------------------------------------------------------------------

class TestBuildRequestUrl(unittest.TestCase):
    def test_no_params(self):
        url = build_request_url(BASE_URL, SUBJECT_PATH)
        self.assertEqual(url, 'https://federation.ccdi.cancer.gov/api/v1/subject')

    def test_with_params(self):
        url = build_request_url(BASE_URL, SUBJECT_PATH, {'sex': 'F'})
        self.assertIn('sex=F', url)

    def test_trailing_slash_stripped(self):
        url = build_request_url('https://example.com/api/v1/', '/subject')
        self.assertTrue(url.startswith('https://example.com/api/v1/subject'))


# ---------------------------------------------------------------------------
# Read-only GET request params
# ---------------------------------------------------------------------------

class TestReadOnlyGetRequestParams(unittest.TestCase):
    def test_none_params_produces_no_query_string(self):
        urlopen, captured = _make_urlopen({'data': []})
        read_only_get(BASE_URL, SUBJECT_PATH, params=None, urlopen=urlopen)
        self.assertEqual(captured['url'], 'https://federation.ccdi.cancer.gov/api/v1/subject')

    def test_original_params_not_mutated(self):
        original = {'sex': 'F'}
        urlopen, _ = _make_urlopen({'data': []})
        read_only_get(BASE_URL, SUBJECT_PATH, params=original, urlopen=urlopen)
        self.assertEqual(original, {'sex': 'F'})

    def test_supplied_params_are_sent(self):
        urlopen, captured = _make_urlopen({'data': []})
        read_only_get(BASE_URL, SUBJECT_PATH, params={'sex': 'F', 'page': '1'}, urlopen=urlopen)
        qs = _query_params(captured['url'])
        self.assertEqual(qs['sex'], ['F'])
        self.assertEqual(qs['page'], ['1'])


# ---------------------------------------------------------------------------
# Return-value sanity checks
# ---------------------------------------------------------------------------

class TestReadOnlyGetReturnValue(unittest.TestCase):
    def test_successful_response_includes_request_url(self):
        urlopen, _ = _make_urlopen({'data': [{'id': '1'}]})
        result = read_only_get(BASE_URL, SUBJECT_PATH, urlopen=urlopen)
        self.assertTrue(result['ok'])
        self.assertEqual(result['url'], 'https://federation.ccdi.cancer.gov/api/v1/subject')

    def test_network_error_includes_request_url(self):
        def _failing_urlopen(url, timeout=30):
            raise OSError('connection refused')

        result = read_only_get(BASE_URL, SUBJECT_PATH, urlopen=_failing_urlopen)
        self.assertFalse(result['ok'])
        self.assertEqual(result['url'], 'https://federation.ccdi.cancer.gov/api/v1/subject')
        self.assertNotIn('headers', result)

    def test_success_response_returns_minimal_fields(self):
        urlopen, _ = _make_urlopen({'data': [{'id': '1'}]})
        result = read_only_get(BASE_URL, SUBJECT_PATH, urlopen=urlopen)
        self.assertEqual(set(result.keys()), {'ok', 'url', 'status', 'payload', 'errors'})


class TestReadOnlyGetSecurityValidation(unittest.TestCase):
    def test_rejects_http_scheme(self):
        result = read_only_get('http://federation.ccdi.cancer.gov/api/v1/', SUBJECT_PATH)
        self.assertEqual(result['errors'], ['https_required'])

    def test_rejects_external_host(self):
        result = read_only_get('https://example.com/api/v1/', SUBJECT_PATH)
        self.assertEqual(result['errors'], ['external_host_not_allowed'])

    def test_rejects_embedded_credentials(self):
        credentialed_url = f"https://{'user'}:{'pass'}@federation.ccdi.cancer.gov/api/v1/"
        result = read_only_get(credentialed_url, SUBJECT_PATH)
        self.assertEqual(result['errors'], ['credentials_not_allowed'])

    def test_rejects_any_port(self):
        result = read_only_get('https://federation.ccdi.cancer.gov:444/api/v1/', SUBJECT_PATH)
        self.assertEqual(result['errors'], ['port_not_allowed'])

    def test_rejects_standard_https_port(self):
        result = read_only_get('https://federation.ccdi.cancer.gov:443/api/v1/', SUBJECT_PATH)
        self.assertEqual(result['errors'], ['port_not_allowed'])

    def test_rejects_malformed_port(self):
        result = read_only_get('https://federation.ccdi.cancer.gov:notaport/api/v1/', SUBJECT_PATH)
        self.assertEqual(result['errors'], ['port_not_allowed'])

    def test_rejects_private_ip_host(self):
        result = read_only_get('https://169.254.169.254/api/v1/', SUBJECT_PATH)
        self.assertEqual(result['errors'], ['blocked_host'])

    def test_rejects_unsupported_path(self):
        result = read_only_get(BASE_URL, '/admin')
        self.assertEqual(result['errors'], ['unsupported_path'])

    def test_rejects_unsupported_query_parameter(self):
        result = read_only_get(BASE_URL, SUBJECT_PATH, params={'not_allowed': 'x'})
        self.assertEqual(result['errors'], ['unsupported_query_parameter'])

    def test_allows_documented_unharmonized_parameter(self):
        urlopen, _ = _make_urlopen({'data': []})
        result = read_only_get(BASE_URL, SUBJECT_PATH, params={'metadata.unharmonized.study': 'X'}, urlopen=urlopen)
        self.assertTrue(result['ok'])

    def test_rejects_redirect(self):
        redirected_to = 'https://federation.ccdi.cancer.gov/api/v1/sample'
        urlopen, _ = _make_urlopen({'data': []}, final_url=redirected_to)
        result = read_only_get(BASE_URL, SUBJECT_PATH, urlopen=urlopen)
        self.assertEqual(result['errors'], ['redirect_not_allowed'])


if __name__ == '__main__':
    unittest.main()
