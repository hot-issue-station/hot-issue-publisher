/* 단골 수첩 장보기 — 거르기 + 점수 매기기
   점수 = 가격 순위(개당 가격) · 평점 · 리뷰 수 가중합. 평점·리뷰가 없는 상품(쿠팡 API 미확인, 네이버)은
   그 항목을 빼고 남은 무게로 계산. 리뷰가 너무 적은 상품은 따로 빼서 보여 줌. */
(function (root) {
  "use strict";
  const DEFAULTS = { wPrice: 40, wRating: 30, wReviews: 30, minReviews: 30, minRating: 0 };
  const won = n => (n == null ? "-" : Math.round(n).toLocaleString("ko-KR") + "원");

  function volOk(want, have) { return have == null ? null : have >= want * 0.8 && have <= want * 1.25; }

  /* 조건 하나하나를 함수로 → 결과가 0개면 덜 중요한 조건부터 하나씩 풀어 봄 */
  function conditions(q) {
    const c = [];
    if (q.item) c.push({ key: "item", label: q.item.label, f: p => p.cat === q.item.id, hard: true });
    if (q.brand) c.push({ key: "brand", label: q.brand, f: p => p.brand === q.brand || (p.name || "").includes(q.brand) });
    if (q.shade) c.push({ key: "shade", label: q.shade + "호", f: p => p.shade === q.shade });
    if (q.percent != null) c.push({ key: "percent", label: q.percent + "%", f: p => p.percent == null || p.percent === q.percent });
    if (q.volume) c.push({ key: "volume", label: q.volume.v + q.volume.u, f: p => volOk(q.volume.v, p.volume) !== false });
    if (q.big) c.push({ key: "big", label: "대용량", f: p => (p.volume || 0) >= 1000 });
    if (q.pieces) c.push({ key: "pieces", label: q.pieces + "매", f: p => p.pieces == null || p.pieces === q.pieces });
    if (q.maxPrice != null) c.push({ key: "maxPrice", label: won(q.maxPrice) + " 이하", f: p => p.price <= q.maxPrice });
    if (q.minPrice != null) c.push({ key: "minPrice", label: won(q.minPrice) + " 이상", f: p => p.price >= q.minPrice });
    if (q.rocket) c.push({ key: "rocket", label: "로켓배송", f: p => !!p.rocket });
    if (q.freeShip) c.push({ key: "freeShip", label: "무료배송", f: p => !!p.freeShip || !!p.rocket });
    if (q.mood) c.push({ key: "mood", label: "분위기", f: p => !p.mood || p.mood === q.mood });
    return c;
  }
  const RELAX_ORDER = ["mood", "pieces", "percent", "volume", "big", "rocket", "freeShip", "brand", "minPrice", "shade", "maxPrice"];

  function rank(products, q, opt) {
    const s = Object.assign({}, DEFAULTS, opt || {});
    const conds = conditions(q);
    let active = conds.slice(), relaxed = [];
    const pass = p => active.every(c => c.f(p));
    let cand = products.filter(pass);
    for (const key of RELAX_ORDER) {
      if (cand.length) break;
      const i = active.findIndex(c => c.key === key);
      if (i < 0) continue;
      relaxed.push(active[i].label);
      active.splice(i, 1);
      cand = products.filter(pass);
    }

    /* 리뷰 너무 적은 상품 빼기 (리뷰 수를 모르는 상품은 빼지 않음) */
    const few = cand.filter(p => p.reviews != null && p.reviews < s.minReviews);
    const lowRate = cand.filter(p => s.minRating && p.rating != null && p.rating < s.minRating && !few.includes(p));
    cand = cand.filter(p => !few.includes(p) && !lowRate.includes(p));

    const need = Math.max(1, q.count || 1);
    const rows = cand.map(p => {
      const pack = Math.max(1, p.pack || 1);
      const unit = p.price / pack;
      return { p, unit, pack };
    });
    const byUnit = rows.slice().sort((a, b) => a.unit - b.unit);
    const n = rows.length, maxR = Math.max(1, ...rows.map(r => r.p.reviews || 0));
    const kws = (q.keywords || []).map(k => k.toLowerCase());
    rows.forEach(r => {
      const idx = byUnit.indexOf(r);
      r.sPrice = n <= 1 ? 1 : 1 - idx / (n - 1);
      r.sRating = r.p.rating == null ? null : Math.max(0, Math.min(1, (r.p.rating - 3.5) / 1.5));
      r.sReviews = r.p.reviews == null ? null : Math.log10(1 + r.p.reviews) / Math.log10(1 + maxR);
      let w = 0, t = 0;
      [[s.wPrice, r.sPrice], [s.wRating, r.sRating], [s.wReviews, r.sReviews]].forEach(([wt, v]) => { if (v != null && wt > 0) { w += wt; t += wt * v; } });
      r.kwHit = kws.filter(k => ((r.p.name || "") + " " + (r.p.tags || []).join(" ")).toLowerCase().includes(k)).length;
      r.score = (w ? t / w : 0) + 0.08 * r.kwHit;
      r.sQuality = (r.sRating == null ? 0.5 : r.sRating) * 0.5 + (r.sReviews == null ? 0 : r.sReviews) * 0.5;
      r.packs = Math.ceil(need / r.pack);
      r.buyQty = r.packs * r.pack;
      r.total = r.packs * r.p.price;
    });

    const cmp = {
      cheap: (a, b) => a.unit - b.unit || b.score - a.score,
      reviews: (a, b) => (b.p.reviews || 0) - (a.p.reviews || 0) || a.unit - b.unit,
      rating: (a, b) => (b.p.rating || 0) - (a.p.rating || 0) || (b.p.reviews || 0) - (a.p.reviews || 0),
      quality: (a, b) => b.sQuality - a.sQuality || a.unit - b.unit,
      balanced: (a, b) => b.score - a.score || a.unit - b.unit
    }[q.sort] || ((a, b) => b.score - a.score);
    rows.sort(cmp);

    const cheapest = byUnit[0] || null;
    const best = rows.slice().sort((a, b) => b.sQuality - a.sQuality || a.unit - b.unit)[0] || null;
    rows.forEach(r => {
      r.badges = [];
      if (r === cheapest) r.badges.push("cheap");
      if (r === best && (r.p.rating != null || r.p.reviews != null)) r.badges.push("best");
      r.reason = reason(r, { q, cheapest, best, rows, byUnit });
    });
    return { rows, few, lowRate, relaxed, used: active.map(c => c.label), settings: s };
  }

  function reason(r, ctx) {
    const out = [], p = r.p;
    const second = ctx.byUnit[1];
    if (r === ctx.cheapest && r === ctx.best) out.push("가장 싸면서 평점·리뷰도 가장 좋아요");
    else if (r === ctx.cheapest) out.push(second ? `같은 조건 중 개당 가격이 가장 낮아요 (다음보다 ${won(second.unit - r.unit)} 쌈)` : "같은 조건 중 개당 가격이 가장 낮아요");
    else if (r === ctx.best) out.push(p.reviews != null ? `리뷰 ${p.reviews.toLocaleString("ko-KR")}개${p.rating != null ? "·평점 " + p.rating : ""}로 가장 믿을 만해요` : `평점 ${p.rating}로 가장 높아요`);
    else if (ctx.q.sort === "reviews" && p.reviews != null) out.push(`리뷰 ${p.reviews.toLocaleString("ko-KR")}개`);
    else if (ctx.q.sort === "rating" && p.rating != null) out.push(`평점 ${p.rating}`);
    else if (r.sPrice >= 0.6 && (r.sRating || 0) >= 0.6) out.push("가격과 평점이 둘 다 괜찮아요");
    else if (r.sPrice >= 0.6) out.push("싼 편이에요");
    else if ((r.sReviews || 0) >= 0.8) out.push("많이 사는 상품이에요");
    else out.push("조건에 맞아요");
    if (r.pack > 1) out.push(`${r.pack}개 묶음이라 개당 ${won(r.unit)}`);
    if (p.rocket) out.push("로켓배송");
    if (r.kwHit) out.push("말씀하신 '" + ctx.q.keywords.filter(k => ((p.name || "") + (p.tags || []).join(" ")).includes(k)).join("·") + "' 포함");
    return out.slice(0, 2).join(" · ");
  }

  const api = { rank, DEFAULTS, won };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ShopRank = api;
})(typeof window !== "undefined" ? window : globalThis);
