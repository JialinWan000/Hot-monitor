// Service Worker for Push Notifications
self.addEventListener('push', function(event) {
  if (!event.data) return;

  const data = event.data.json();
  
  const options = {
    body: data.body || '有新的热点资讯',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/',
      id: data.id
    },
    actions: [
      { action: 'open', title: '查看详情' },
      { action: 'dismiss', title: '忽略' }
    ],
    tag: data.id || 'hot-monitor',
    renotify: true,
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Hot Monitor', options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'dismiss') return;

  const url = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(function(clientList) {
        // 如果有窗口打开，聚焦到它
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(url);
            return client.focus();
          }
        }
        // 否则打开新窗口
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// 安装事件
self.addEventListener('install', function(event) {
  self.skipWaiting();
});

// 激活事件
self.addEventListener('activate', function(event) {
  event.waitUntil(clients.claim());
});
