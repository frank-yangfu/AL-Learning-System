// AL 自学系统 Service Worker
// ⚠ 不要改回 cache-first：以前的 cache-first + 固定版本号会让浏览器永远加载旧 app.js，
//   新功能全部看不见（改完代码「没生效」的头号原因）。
//   现在的策略是 network-first：联网时永远取最新代码，断网时才回退到缓存（离线可用照旧）。
const CACHE_NAME = 'al-v4';  // v4: 学习机模式（宫格主页 + AI 学伴）
const ASSETS = ['/', '/index.html', '/app.js', '/styles.css', '/manifest.json', '/icon-192.png', '/icon-512.png'];

self.addEventListener('install', e => {
  self.skipWaiting();   // 新版本立即待命，不等到所有页面关闭
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS).catch(() => {})));
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const ks = await caches.keys();
    await Promise.all(ks.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));
    await self.clients.claim();   // 立刻接管已有页面
  })());
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  let u;
  try { u = new URL(req.url); } catch (err) { return; }
  if (u.origin !== self.location.origin) return;
  if (u.pathname.startsWith('/api/')) return;   // 接口一律不缓存，避免拿到旧数据
  e.respondWith((async () => {
    try {
      const fresh = await fetch(req);
      if (fresh && fresh.ok) {
        const c = await caches.open(CACHE_NAME);
        c.put(req, fresh.clone()).catch(() => {});
      }
      return fresh;
    } catch (err) {
      const cached = await caches.match(req);
      if (cached) return cached;
      throw err;
    }
  })());
});
