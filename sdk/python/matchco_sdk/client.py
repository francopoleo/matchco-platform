import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class MatchCoAPIError(RuntimeError):
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload
        super().__init__(f'MatchCo API error {status}: {payload}')


class MatchCoClient:
    """Small dependency-free client for MatchCo REST v1."""

    def __init__(self, base_url, api_key=None, timeout=20):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method, path, payload=None):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-MatchCo-API-Key'] = self.api_key
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(f'{self.base_url}{path}', data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else {}
        except HTTPError as error:
            raw = error.read().decode()
            try:
                data = json.loads(raw)
            except ValueError:
                data = {'detail': raw}
            raise MatchCoAPIError(error.code, data) from error

    def documents(self, query=''):
        path = '/api/v1/documents/' + (f'?q={query}' if query else '')
        return self._request('GET', path)

    def document(self, document_id):
        return self._request('GET', f'/api/v1/documents/{document_id}/')

    def update_document(self, document_id, payload):
        return self._request('PATCH', f'/api/v1/documents/{document_id}/', payload)

    def archive_document(self, document_id):
        return self._request('DELETE', f'/api/v1/documents/{document_id}/')

    def engagement(self, days=30):
        return self._request('GET', f'/api/v1/analytics/engagement/?days={int(days)}')

    def partner(self):
        return self._request('GET', '/api/v1/partner/me/')

    def mobile_sync(self, last_sync=None):
        suffix = f'?last_sync={last_sync}' if last_sync else ''
        return self._request('GET', f'/api/mobile/sync/{suffix}')

    def mobile_events(self, events):
        return self._request('POST', '/api/mobile/events/', {'events': events})
