self.addEventListener('push', function (event) {
  const data = event.data ? event.data.json() : {title: 'Talk', body: 'Você tem uma nova atualização.'};
  event.waitUntil(self.registration.showNotification(data.title || 'Talk', {body: data.body || '', data: {url: data.url || '/'}}));
});
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data && event.notification.data.url || '/'));
});
