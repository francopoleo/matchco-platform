from django.http import HttpResponse
from django.views.decorators.cache import never_cache


SERVICE_WORKER = """
const CACHE_NAME = 'talk-shell-v1';
const APP_SHELL = ['/', '/course-list/', '/notifications/'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) return;
  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request).then(cached => cached || caches.match('/'))));
});
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {title: 'Talk', message: 'Você tem uma nova atualização.'};
  event.waitUntil(self.registration.showNotification(data.title || 'Talk', {body: data.message || data.body || '', data: {url: data.url || '/'}}));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data && event.notification.data.url || '/'));
});
"""


@never_cache
def service_worker(request):
    return HttpResponse(SERVICE_WORKER, content_type='application/javascript')
