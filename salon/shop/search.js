/* 단골 수첩 장보기 — SEARCH 어댑터
   mode "mock"   : data.js 예시 데이터 (지금)
   mode "netlify": /.netlify/functions/shop-search 를 부름 (쿠팡 키를 받은 뒤). 키는 서버 환경변수에만 있음.
   매장 꾸미기(오늘의집)는 검색 API가 없어 두 모드 모두 우리가 고른 목록(DECOR)을 씀. */
(function (root) {
  "use strict";
  const P = root.ShopParser, D = root.ShopData;

  const SOURCES = {
    coupang:    { label: "쿠팡",    btn: "쿠팡에서 보기",    color: "#e3342f",
                  notice: "이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
                  searchUrl: q => "https://www.coupang.com/np/search?q=" + encodeURIComponent(q),
                  hosts: ["coupang.com", "coupa.ng"] },
    oliveyoung: { label: "올리브영", btn: "올리브영에서 보기", color: "#8bb83d",
                  notice: "올리브영 쇼핑 큐레이터 활동의 일환으로, 구매 시 일정액의 수수료를 받을 수 있습니다.",
                  searchUrl: q => "https://www.oliveyoung.co.kr/store/search/getSearchMain.do?query=" + encodeURIComponent(q),
                  hosts: ["oliveyoung.co.kr"] },
    ohou:       { label: "오늘의집", btn: "오늘의집에서 보기", color: "#35c5f0",
                  notice: "오늘의집 큐레이터 활동의 일환으로, 구매 시 일정액의 수수료를 받을 수 있습니다.",
                  searchUrl: q => "https://ohou.se/search/index?query=" + encodeURIComponent(q),
                  hosts: ["ohou.se"] },
    naver:      { label: "네이버 쇼핑", btn: "네이버에서 보기", color: "#03c75a",
                  notice: "", // 네이버 쇼핑 링크는 제휴 수수료가 없음(가격 참고용)
                  searchUrl: q => "https://search.shopping.naver.com/search/all?query=" + encodeURIComponent(q),
                  hosts: ["naver.com", "naver.me"] }
  };

  const cfg = Object.assign({ mode: "mock", endpoint: "/.netlify/functions/shop-search", sources: ["coupang"], subId: "dangol" }, root.SHOP_CONFIG || {});
  try { const m = new URLSearchParams(location.search).get("mode"); if (m === "mock" || m === "netlify") cfg.mode = m; } catch (e) {}

  /* 링크: 서버가 준 제휴 링크(p.url)가 있으면 그것, 없으면(예시) 판매처 검색 주소 */
  function linkFor(p) {
    const src = SOURCES[p.source] || SOURCES.coupang;
    if (p.url && /^https:\/\//.test(p.url) && src.hosts.some(h => new URL(p.url).hostname.endsWith(h))) return p.url;
    return src.searchUrl(String(p.name || "").replace(/^\[예시\]\s*/, "").replace(/\(.*?\)/g, "").trim());
  }

  /* API 결과에 호수·용량·묶음 칸이 없으면 상품명에서 짐작 */
  function enrich(p, q) {
    const g = P.fromName(p.name || "");
    return Object.assign({
      cat: q.item ? q.item.id : (g.item && g.item.id), brand: g.brand, shade: g.shade, volume: g.volume ? g.volume.v : null,
      percent: g.percent, pieces: g.pieces, pack: g.pack, rating: null, reviews: null
    }, Object.fromEntries(Object.entries(p).filter(([, v]) => v != null)));
  }

  async function findMock(q) {
    await new Promise(r => setTimeout(r, 250));
    const all = D.MOCK.concat(D.DECOR);
    return { items: all.map(p => Object.assign({}, p)), sample: true, from: "예시 데이터" };
  }

  async function findNetlify(q) {
    if (q.item && q.item.group === "꾸미기") return { items: D.DECOR.map(p => Object.assign({}, p)), sample: true, from: "우리가 고른 목록" };
    const url = cfg.endpoint + "?q=" + encodeURIComponent(q.query) + "&source=" + encodeURIComponent(cfg.sources.join(",")) + "&subId=" + encodeURIComponent(cfg.subId);
    const res = await fetch(url, { headers: { accept: "application/json" } });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) throw new Error(j.message || "검색 서버가 답하지 않아요 (" + res.status + ")");
    return { items: j.items.map(p => enrich(p, q)), sample: false, from: j.cachedAt ? "검색 시각 " + new Date(j.cachedAt).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }) : "방금 검색", warnings: j.warnings || [] };
  }

  const SEARCH = {
    get mode() { return cfg.mode; },
    config: cfg,
    SOURCES,
    linkFor,
    find: q => (cfg.mode === "netlify" ? findNetlify(q) : findMock(q))
  };
  root.SEARCH = SEARCH;
})(window);
