const CACHE = "carnes-luevanos-v57-ortografia";
const APP_SHELL = [
  "/manifest.webmanifest",
  "/logo-luevanos.png",
  "/apple-touch-icon.png",
  "/icon-192.png",
  "/icon-512.png",
  "/icon-maskable-512.png",
  "/jelox.png",
  "/jelox-x.png",
  "/jelox-welcome-hd.png",
  "/google-authenticator.png",
  "/splash-bg.png",
  "/icons/refresh-cw.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: "window", includeUncontrolled: true }))
      .then((clients) => clients.forEach((client) => client.postMessage({ type: "PWA_UPDATED", cache: CACHE }))),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  if (event.request.mode === "navigate") {
    event.respondWith(fetch(event.request, { cache: "no-store" }));
    return;
  }
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const sameOrigin = new URL(event.request.url).origin === self.location.origin;
        const isAppDocument = event.request.destination === "document";
        if (sameOrigin && response.ok && !isAppDocument) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        }
        return response;
      })
      .catch(async () => {
        const cached = await caches.match(event.request);
        if (cached) return cached;
        return Response.error();
      }),
  );
});

self.addEventListener("push", (event) => {
  const data = event.data?.json?.() || {};
  event.waitUntil(
    self.registration.showNotification(data.title || "JELOX · Carnes Luévanos", {
      body: data.body || "Tienes una nueva notificación del sistema.",
      icon: "/jelox.png",
      badge: "/jelox.png",
      tag: data.tag || "jelox-system",
      data: { url: data.url || "/" },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(self.clients.openWindow(event.notification.data?.url || "/"));
});
