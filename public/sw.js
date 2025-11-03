// Service Worker - 기본 캐싱만 구현
self.addEventListener('install', (event) => {
    console.log('Service Worker 설치됨');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker 활성화됨');
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    // 기본 네트워크 요청만 처리
    event.respondWith(fetch(event.request));
});