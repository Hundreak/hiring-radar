// No-op service worker placeholder.
// This prevents stale browser registrations from turning /sw.js into a noisy 404 during local development.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
