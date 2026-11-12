// 3D 덕심 갤러리 — Cloudflare Pages 고급 모드 워커(11/12).
// /img?u=<쿠팡 상품 이미지 주소> : 쿠팡 파트너스가 제공한 상품 이미지를 3D 진열장에 그릴 수 있게 CORS만 붙여 전달(저장하지 않음).
// 그 밖의 요청은 그대로 정적 파일.
const SEC = {"X-Content-Type-Options":"nosniff","Referrer-Policy":"strict-origin-when-cross-origin","X-Frame-Options":"SAMEORIGIN","Permissions-Policy":"camera=(), microphone=(), geolocation=()"};
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/img") {
      let t; try { t = new URL(url.searchParams.get("u") || ""); } catch { return new Response("bad", {status: 400}); }
      if (t.protocol !== "https:" || !/(^|\.)coupangcdn\.com$/i.test(t.hostname)) return new Response("forbidden", {status: 403});
      const r = await fetch(t.toString(), {cf: {cacheTtl: 86400, cacheEverything: true}});
      const ct = r.headers.get("Content-Type") || "";
      if (!r.ok || !ct.startsWith("image/")) return new Response("not found", {status: 404});
      return new Response(r.body, {headers: {"Content-Type": ct, "Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=86400", ...SEC}});
    }
    const res = await env.ASSETS.fetch(req);
    const out = new Response(res.body, res);
    for (const [k, v] of Object.entries(SEC)) if (!out.headers.has(k)) out.headers.set(k, v);
    return out;
  }
};
