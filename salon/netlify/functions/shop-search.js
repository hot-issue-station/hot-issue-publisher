/* 단골 수첩 장보기 — 상품 검색 서버 함수 (Netlify Functions, 무료 요금제) 초안
   - 키는 코드에 없음. Netlify 사이트 설정 → Environment variables 에만 넣음:
       COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY     (쿠팡 파트너스 최종 승인 뒤 발급)
       NAVER_CLIENT_ID, NAVER_CLIENT_SECRET       (선택: 가격 참고용, 제휴 수익 없음)
       SHOP_CACHE_SECONDS  (기본 1800 = 30분. 약관 확인 결과 캐시 금지면 0)
       COUPANG_PER_MINUTE  (기본 45 — 보조자료상 검색 1분 50회 한도보다 낮게)
       COUPANG_PER_HOUR    (기본 25 — 보조자료상 '1시간 30회 넘으면 24시간 정지' 대비. 공식 확인 뒤 조정)
   - 부르는 법: GET /.netlify/functions/shop-search?q=로레알 염색약 6호&source=coupang,naver&subId=dangol
   - 답: {ok, items:[공통 형식], cachedAt, warnings}
     공통 형식 = {source, id, name, brand, price, rating, reviews, rocket, freeShip, url, image, store}
   - HMAC 서명 방식은 보조자료(블로그 코드) 기준. 공식 문서로 다시 확인할 것: salon/docs/장보기_API조사.md */
"use strict";
const crypto = require("crypto");

const CACHE = new Map();               // 함수 인스턴스가 살아 있는 동안만 (짧은 캐시)
const CALLS = [];                      // 쿠팡 호출 시각 기록 (인스턴스 단위 — 정확한 전역 제한은 아님)
const TTL = () => Math.max(0, parseInt(process.env.SHOP_CACHE_SECONDS || "1800", 10)) * 1000;

const COUPANG_HOST = "https://api-gateway.coupang.com";
const COUPANG_SEARCH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search";

/* 쿠팡 Open API 서명: signed-date = UTC yyMMdd'T'HHmmss'Z', message = date + METHOD + path + query */
function coupangAuth(method, path, query, accessKey, secretKey, now = new Date()) {
  const iso = now.toISOString();
  const date = iso.slice(2, 4) + iso.slice(5, 7) + iso.slice(8, 10) + "T" + iso.slice(11, 13) + iso.slice(14, 16) + iso.slice(17, 19) + "Z";
  const message = date + method + path + query;
  const signature = crypto.createHmac("sha256", secretKey).update(message).digest("hex");
  return `CEA algorithm=HmacSHA256, access-key=${accessKey}, signed-date=${date}, signature=${signature}`;
}

function rateOk() {
  const now = Date.now(), perMin = +(process.env.COUPANG_PER_MINUTE || 45), perHour = +(process.env.COUPANG_PER_HOUR || 25);
  while (CALLS.length && now - CALLS[0] > 3600e3) CALLS.shift();
  const lastMin = CALLS.filter(t => now - t < 60e3).length;
  if (lastMin >= perMin || CALLS.length >= perHour) return false;
  CALLS.push(now);
  return true;
}

const num = v => (v == null || v === "" ? null : Number(String(v).replace(/[^\d.]/g, "")) || null);

async function searchCoupang(q, subId) {
  const ak = process.env.COUPANG_ACCESS_KEY, sk = process.env.COUPANG_SECRET_KEY;
  if (!ak || !sk) return { items: [], warning: "쿠팡 키가 아직 없어요(환경변수 미설정)." };
  if (!rateOk()) return { items: [], warning: "쿠팡 호출 한도에 가까워 잠시 쉬어요. 조금 뒤 다시 찾아 주세요." };
  const query = "keyword=" + encodeURIComponent(q) + "&limit=10" + (subId ? "&subId=" + encodeURIComponent(subId) : "");
  const res = await fetch(COUPANG_HOST + COUPANG_SEARCH + "?" + query, {
    headers: { Authorization: coupangAuth("GET", COUPANG_SEARCH, query, ak, sk), "Content-Type": "application/json;charset=UTF-8" }
  });
  const j = await res.json().catch(() => ({}));
  // 쿠팡은 권한 오류도 200으로 줄 수 있음 → rCode 확인
  if (!res.ok || (j.rCode && j.rCode !== "0")) throw new Error("쿠팡 응답 오류 " + res.status + " " + (j.rMessage || ""));
  const list = (j.data && (j.data.productData || j.data)) || [];
  return {
    items: list.map(p => ({
      source: "coupang",
      id: "cp" + p.productId,
      name: p.productName,
      brand: null,
      price: num(p.productPrice),
      // 평점·리뷰 칸은 공식 응답에 있는지 미확인 → 있으면 쓰고 없으면 null
      rating: num(p.rating ?? p.productRating ?? p.score),
      reviews: num(p.reviewCount ?? p.ratingCount ?? p.review_count),
      rocket: !!p.isRocket,
      freeShip: !!p.isFreeShipping,
      url: p.productUrl,              // 이미 파트너스 추적 링크
      image: p.productImage,          // 쿠팡 주소 그대로 표시, 우리 쪽 저장 안 함
      store: "쿠팡"
    })).filter(p => p.price)
  };
}

async function searchNaver(q) {
  const id = process.env.NAVER_CLIENT_ID, sec = process.env.NAVER_CLIENT_SECRET;
  if (!id || !sec) return { items: [], warning: "" };
  const res = await fetch("https://openapi.naver.com/v1/search/shop.json?display=20&sort=sim&query=" + encodeURIComponent(q), {
    headers: { "X-Naver-Client-Id": id, "X-Naver-Client-Secret": sec }
  });
  if (!res.ok) throw new Error("네이버 응답 오류 " + res.status);
  const j = await res.json();
  return {
    items: (j.items || []).map(p => ({
      source: "naver",
      id: "nv" + p.productId,
      name: String(p.title || "").replace(/<[^>]+>/g, ""),
      brand: p.brand || p.maker || null,
      price: num(p.lprice),
      rating: null, reviews: null,     // 네이버 쇼핑 검색 API는 평점·리뷰 수를 주지 않음
      rocket: false, freeShip: false,
      url: p.link, image: p.image, store: p.mallName || "네이버 쇼핑"
    })).filter(p => p.price)
  };
}

const SOURCES = { coupang: searchCoupang, naver: searchNaver };

exports.handler = async event => {
  const headers = { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" };
  if (event.httpMethod !== "GET") return { statusCode: 405, headers, body: JSON.stringify({ ok: false, message: "GET만 받아요" }) };
  const p = event.queryStringParameters || {};
  const q = String(p.q || "").trim().slice(0, 100);
  if (q.length < 2) return { statusCode: 400, headers, body: JSON.stringify({ ok: false, message: "검색어를 두 글자 이상 넣어 주세요" }) };
  const subId = String(p.subId || "dangol").replace(/[^a-zA-Z0-9_]/g, "").slice(0, 30);
  const want = String(p.source || "coupang").split(",").filter(s => SOURCES[s]);

  const key = want.join(",") + "|" + q;
  const hit = CACHE.get(key);
  if (hit && Date.now() - hit.at < TTL()) return { statusCode: 200, headers, body: JSON.stringify({ ok: true, items: hit.items, cachedAt: hit.at, warnings: hit.warnings, cached: true }) };

  const items = [], warnings = [];
  let failed = 0;
  await Promise.all(want.map(async s => {
    try { const r = await SOURCES[s](q, subId); items.push(...r.items); if (r.warning) warnings.push(r.warning); }
    catch (e) { failed++; warnings.push(e.message); }
  }));
  if (!items.length && failed) return { statusCode: 502, headers, body: JSON.stringify({ ok: false, message: warnings.join(" / ") }) };
  const at = Date.now();
  if (items.length && TTL() > 0) {           // 실패·빈 결과는 캐시하지 않음
    CACHE.set(key, { at, items, warnings });
    if (CACHE.size > 300) CACHE.delete(CACHE.keys().next().value);
  }
  return { statusCode: 200, headers, body: JSON.stringify({ ok: true, items, cachedAt: at, warnings }) };
};

exports._test = { coupangAuth };
