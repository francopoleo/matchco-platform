class MatchCoAPIError extends Error {
  constructor(status, payload) {
    super(`MatchCo API error ${status}`);
    this.status = status;
    this.payload = payload;
  }
}

class MatchCoClient {
  constructor({ baseUrl, apiKey, fetchImpl = globalThis.fetch }) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.fetch = fetchImpl;
  }

  async request(path, options = {}) {
    const headers = { Accept: 'application/json', ...(options.headers || {}) };
    if (this.apiKey) headers['X-MatchCo-API-Key'] = this.apiKey;
    if (options.body) headers['Content-Type'] = 'application/json';
    const response = await this.fetch(`${this.baseUrl}${path}`, { ...options, headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new MatchCoAPIError(response.status, payload);
    return payload;
  }

  documents(query = '') { return this.request(`/api/v1/documents/${query ? `?q=${encodeURIComponent(query)}` : ''}`); }
  document(id) { return this.request(`/api/v1/documents/${id}/`); }
  updateDocument(id, payload) { return this.request(`/api/v1/documents/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }); }
  archiveDocument(id) { return this.request(`/api/v1/documents/${id}/`, { method: 'DELETE' }); }
  engagement(days = 30) { return this.request(`/api/v1/analytics/engagement/?days=${Number(days)}`); }
  partner() { return this.request('/api/v1/partner/me/'); }
  mobileSync(lastSync) { return this.request(`/api/mobile/sync/${lastSync ? `?last_sync=${encodeURIComponent(lastSync)}` : ''}`); }
  mobileEvents(events) { return this.request('/api/mobile/events/', { method: 'POST', body: JSON.stringify({ events }) }); }
}

module.exports = { MatchCoClient, MatchCoAPIError };
