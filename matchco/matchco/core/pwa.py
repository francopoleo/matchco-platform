from django.http import HttpResponse
from django.views.decorators.cache import never_cache


SERVICE_WORKER = """
const CACHE_NAME = 'matchco-static-v2';
self.addEventListener('install', event => {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
  )).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) return;
  // Never cache navigation responses: authenticated HTML contains masked CSRF
  // tokens tied to the current browser cookie/session.
  const isNavigation = event.request.mode === 'navigate' || event.request.headers.get('accept')?.includes('text/html');
  if (isNavigation) {
    event.respondWith(fetch(event.request, {cache: 'no-store'}));
    return;
  }
  // Keep the worker limited to static assets. API and other dynamic GETs must
  // always reflect the current organization and permission scope.
  const cacheable = ['script', 'style', 'image', 'font'].includes(event.request.destination);
  if (!cacheable) return;
  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone();
    if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request)));
});
self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {title: 'MatchCo', message: 'Você tem uma nova atualização.'};
    event.waitUntil(self.registration.showNotification(data.title || 'MatchCo', {body: data.message || data.body || '', data: {url: data.url || '/'}}));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data && event.notification.data.url || '/'));
});
"""


@never_cache
def service_worker(request):
    return HttpResponse(SERVICE_WORKER, content_type='application/javascript')
