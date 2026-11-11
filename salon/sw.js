/* 단골 수첩 서비스워커
   - 앱 껍데기(화면 파일·아이콘)는 설치 때 미리 저장 → 인터넷이 없어도 열림
   - 염색 미리보기의 MediaPipe 프로그램·모델은 color.html을 처음 쓸 때 받아서 저장
   - 손님 기록(localStorage)은 여기서 다루지 않음 */
const VER = "dangol-shell-v2";
const MODEL_CACHE = "dangol-models-v1";
const SHELL = [
  "./", "index.html", "color.html", "manifest.webmanifest",
  "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"
];
const isModel = u =>
  (u.hostname === "cdn.jsdelivr.net" && u.pathname.startsWith("/npm/@mediapipe/")) ||
  (u.hostname === "storage.googleapis.com" && u.pathname.startsWith("/mediapipe-models/"));

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VER && k !== MODEL_CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  /* MediaPipe: 한 번 받으면 저장해 두고 계속 씀 (cache-first) */
  if (isModel(url)) {
    e.respondWith(caches.open(MODEL_CACHE).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok || res.type === "opaque") c.put(req, res.clone()).catch(() => {});
      return res;
    }));
    return;
  }

  if (url.origin !== self.location.origin) return;

  /* 앱 화면: 저장본을 바로 보여 주고, 뒤에서 새 버전을 받아 둠 (다음에 열 때 반영) */
  e.respondWith(caches.open(VER).then(async c => {
    const hit = await c.match(req, { ignoreSearch: true }) ||
      (req.mode === "navigate" ? await c.match("index.html") : null);
    const fresh = fetch(req).then(res => {
      if (res.ok && res.type === "basic") c.put(req, res.clone()).catch(() => {});
      return res;
    }).catch(() => null);
    if (hit) { e.waitUntil(fresh); return hit; }
    return (await fresh) || new Response("인터넷 연결이 없어요", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }));
});
