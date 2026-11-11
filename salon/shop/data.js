/* 단골 수첩 장보기 — 예시 데이터(mock) + 매장 꾸미기 아이디어
   ※ 아래 상품·가격·평점·리뷰 수는 화면 시험용으로 지어낸 '예시 데이터'입니다. 실제 상품이 아닙니다.
   ※ 링크는 판매처 '검색 결과' 주소로만 연결(제휴 링크 아님). 실제 운영 땐 netlify 어댑터가 제휴 링크를 받아 옴.
   공통 형식: {source, id, cat, name, brand, price, pack, shade, volume(ml|g), percent, pieces, rating, reviews, rocket, freeShip, mood, tags} */
(function (root) {
  "use strict";
  const C = "coupang", O = "oliveyoung", H = "ohou";
  const MOCK = [
    // 염색약 (8)
    { source: C, id: "m01", cat: "dye", name: "[예시] 로레알 프로페셔널 마지렐 6호 50ml", brand: "로레알", price: 9800, pack: 1, shade: "6", rating: 4.7, reviews: 1240, rocket: true, freeShip: true },
    { source: C, id: "m02", cat: "dye", name: "[예시] 로레알 마지렐 6호 50ml x 10개 묶음", brand: "로레알", price: 89000, pack: 10, shade: "6", rating: 4.6, reviews: 312, rocket: true, freeShip: true },
    { source: C, id: "m03", cat: "dye", name: "[예시] 로레알 이노아 6호 60g x 3개", brand: "로레알", price: 31500, pack: 3, shade: "6", rating: 4.8, reviews: 96, rocket: false, freeShip: true },
    { source: C, id: "m04", cat: "dye", name: "[예시] 로레알 마지렐 7호 50ml", brand: "로레알", price: 9800, pack: 1, shade: "7", rating: 4.7, reviews: 860, rocket: true, freeShip: true },
    { source: C, id: "m05", cat: "dye", name: "[예시] 웰라 콜레스톤 퍼펙트 6/0호 60ml", brand: "웰라", price: 8500, pack: 1, shade: "6", rating: 4.5, reviews: 540, rocket: false, freeShip: false },
    { source: C, id: "m06", cat: "dye", name: "[예시] 밀본 올디브 7-1호 80g x 5개", brand: "밀본", price: 47000, pack: 5, shade: "7.1", rating: 4.8, reviews: 205, rocket: false, freeShip: true },
    { source: C, id: "m07", cat: "dye", name: "[예시] 아모스 컬러젠 6호 80g", brand: "아모스", price: 6900, pack: 1, shade: "6", rating: 4.4, reviews: 24, rocket: false, freeShip: false },
    { source: C, id: "m08", cat: "dye", name: "[예시] 무명 살롱 염색약 6호 100g", brand: null, price: 3900, pack: 1, shade: "6", rating: 3.9, reviews: 7, rocket: false, freeShip: false },
    // 산화제 (3)
    { source: C, id: "m09", cat: "oxid", name: "[예시] 웰라 웰록손 산화제 6% 1000ml", brand: "웰라", price: 7900, pack: 1, volume: 1000, percent: 6, rating: 4.7, reviews: 1830, rocket: true, freeShip: true },
    { source: C, id: "m10", cat: "oxid", name: "[예시] 로레알 옥시던트 크림 6% 1000ml", brand: "로레알", price: 8900, pack: 1, volume: 1000, percent: 6, rating: 4.8, reviews: 950, rocket: true, freeShip: true },
    { source: C, id: "m11", cat: "oxid", name: "[예시] 아모스 산화제 6% 1000ml x 3통", brand: "아모스", price: 18900, pack: 3, volume: 1000, percent: 6, rating: 4.5, reviews: 520, rocket: false, freeShip: true },
    // 샴푸 (4 + 올리브영 1)
    { source: C, id: "m12", cat: "shampoo", name: "[예시] 아모스 그린티 샴푸 1500ml", brand: "아모스", price: 19800, pack: 1, volume: 1500, rating: 4.6, reviews: 8920, rocket: true, freeShip: true },
    { source: C, id: "m13", cat: "shampoo", name: "[예시] 려 함빛 대용량 샴푸 1000ml x 2개", brand: "려", price: 21900, pack: 2, volume: 1000, rating: 4.7, reviews: 15400, rocket: true, freeShip: true },
    { source: C, id: "m14", cat: "shampoo", name: "[예시] 미쟝센 퍼펙트 샴푸 1500ml", brand: "미쟝센", price: 14900, pack: 1, volume: 1500, rating: 4.5, reviews: 2100, rocket: true, freeShip: true },
    { source: C, id: "m15", cat: "shampoo", name: "[예시] 살롱 전용 약산성 샴푸 5L", brand: null, price: 32000, pack: 1, volume: 5000, rating: 4.3, reviews: 140, rocket: false, freeShip: true },
    { source: O, id: "m16", cat: "shampoo", name: "[예시] 다슈 데일리 두피 샴푸 500ml (손님 홈케어)", brand: "다슈", price: 15900, pack: 1, volume: 500, rating: 4.8, reviews: 6200, rocket: false, freeShip: false, tags: ["홈케어"] },
    // 트리트먼트 (3)
    { source: C, id: "m17", cat: "treat", name: "[예시] 아모스 리페어 트리트먼트 1000ml", brand: "아모스", price: 22000, pack: 1, volume: 1000, rating: 4.7, reviews: 3400, rocket: true, freeShip: true },
    { source: C, id: "m18", cat: "treat", name: "[예시] 로레알 앱솔루트 리페어 마스크 500ml", brand: "로레알", price: 34000, pack: 1, volume: 500, rating: 4.8, reviews: 980, rocket: true, freeShip: true },
    { source: O, id: "m19", cat: "treat", name: "[예시] 엘라스틴 손상 케어 헤어팩 200ml (손님 홈케어)", brand: "엘라스틴", price: 9900, pack: 1, volume: 200, rating: 4.6, reviews: 4100, rocket: false, freeShip: false, tags: ["홈케어"] },
    // 펌제 (2)
    { source: C, id: "m20", cat: "perm", name: "[예시] 아모스 펌제 1제+2제 1000ml 세트", brand: "아모스", price: 13500, pack: 1, volume: 1000, rating: 4.6, reviews: 710, rocket: true, freeShip: true },
    { source: C, id: "m21", cat: "perm", name: "[예시] 살롱 셋팅펌 약 1000ml", brand: null, price: 11000, pack: 1, volume: 1000, rating: 4.3, reviews: 88, rocket: false, freeShip: true },
    // 가위 (4)
    { source: C, id: "m22", cat: "scissors", name: "[예시] 미용 커트가위 6인치 일본강", brand: null, price: 45000, pack: 1, rating: 4.6, reviews: 410, rocket: true, freeShip: true, tags: ["커트"] },
    { source: C, id: "m23", cat: "scissors", name: "[예시] 프로 커트가위 6인치 코발트", brand: null, price: 129000, pack: 1, rating: 4.9, reviews: 88, rocket: false, freeShip: true, tags: ["커트"] },
    { source: C, id: "m24", cat: "scissors", name: "[예시] 틴닝 숱가위 30발 6인치", brand: null, price: 39000, pack: 1, rating: 4.4, reviews: 260, rocket: true, freeShip: true, tags: ["틴닝", "숱"] },
    { source: C, id: "m25", cat: "scissors", name: "[예시] 초저가 커트가위", brand: null, price: 12900, pack: 1, rating: 3.6, reviews: 15, rocket: false, freeShip: false, tags: ["커트"] },
    // 빗 (2)
    { source: C, id: "m26", cat: "comb", name: "[예시] 카본 꼬리빗 x 10개", brand: null, price: 5900, pack: 10, rating: 4.5, reviews: 1320, rocket: true, freeShip: true, tags: ["꼬리빗"] },
    { source: C, id: "m27", cat: "comb", name: "[예시] 커트 콤 5종 세트", brand: null, price: 8900, pack: 1, rating: 4.4, reviews: 640, rocket: true, freeShip: true },
    // 케이프 (2)
    { source: C, id: "m28", cat: "cape", name: "[예시] 방수 커트보 케이프 블랙", brand: null, price: 12900, pack: 1, rating: 4.5, reviews: 890, rocket: true, freeShip: true },
    { source: C, id: "m29", cat: "cape", name: "[예시] 염색 케이프 x 5벌", brand: null, price: 19800, pack: 5, rating: 4.3, reviews: 230, rocket: false, freeShip: true },
    // 장갑 (2)
    { source: C, id: "m30", cat: "glove", name: "[예시] 니트릴 장갑 블랙 100매", brand: null, price: 8900, pack: 1, pieces: 100, rating: 4.7, reviews: 15200, rocket: true, freeShip: true, tags: ["니트릴"] },
    { source: C, id: "m31", cat: "glove", name: "[예시] 니트릴 장갑 화이트 100매", brand: null, price: 7500, pack: 1, pieces: 100, rating: 4.6, reviews: 4210, rocket: true, freeShip: false, tags: ["니트릴"] },
    // 호일 (2)
    { source: C, id: "m32", cat: "foil", name: "[예시] 하이라이트 염색 호일 롤 100m", brand: null, price: 9800, pack: 1, rating: 4.6, reviews: 770, rocket: true, freeShip: true },
    { source: C, id: "m33", cat: "foil", name: "[예시] 엠보 염색 호일 시트 500매", brand: null, price: 14000, pack: 1, pieces: 500, rating: 4.5, reviews: 310, rocket: false, freeShip: true }
  ];

  /* 매장 꾸미기 — 오늘의집(검색 API 없음 → 우리가 고른 목록). 지금은 예시. */
  const DECOR = [
    { source: H, id: "d01", cat: "light", mood: "wood", name: "[예시] 라탄 우드 펜던트 조명", price: 59000, pack: 1, rating: 4.7, reviews: 1820, freeShip: true },
    { source: H, id: "d02", cat: "light", mood: "white", name: "[예시] 화이트 미니멀 플로어 스탠드", price: 45000, pack: 1, rating: 4.6, reviews: 960, freeShip: true },
    { source: H, id: "d03", cat: "mirror", mood: "white", name: "[예시] 원형 LED 벽거울 70cm", price: 89000, pack: 1, rating: 4.8, reviews: 2400, freeShip: true, tags: ["LED"] },
    { source: H, id: "d04", cat: "mirror", mood: "vintage", name: "[예시] 앤틱 골드 프레임 벽거울", price: 129000, pack: 1, rating: 4.7, reviews: 410, freeShip: false },
    { source: H, id: "d05", cat: "chair", mood: "vintage", name: "[예시] 빈티지 바버 체어 유압식", price: 690000, pack: 1, rating: 4.6, reviews: 75, freeShip: false },
    { source: H, id: "d06", cat: "sofa", mood: "white", name: "[예시] 화이트 부클 2인 대기 소파", price: 239000, pack: 1, rating: 4.7, reviews: 530, freeShip: true },
    { source: H, id: "d07", cat: "sofa", mood: "wood", name: "[예시] 원목 프레임 대기 벤치", price: 149000, pack: 1, rating: 4.6, reviews: 220, freeShip: true },
    { source: H, id: "d08", cat: "cabinet", mood: "wood", name: "[예시] 원목 3단 수납장", price: 119000, pack: 1, rating: 4.7, reviews: 1340, freeShip: true },
    { source: H, id: "d09", cat: "cabinet", mood: "white", name: "[예시] 화이트 미용 왜건 트롤리 3단", price: 49000, pack: 1, rating: 4.5, reviews: 3100, freeShip: true },
    { source: H, id: "d10", cat: "plant", mood: "wood", name: "[예시] 몬스테라 화분 (토분 포함)", price: 39000, pack: 1, rating: 4.6, reviews: 5200, freeShip: false },
    { source: H, id: "d11", cat: "sign", mood: "vintage", name: "[예시] 문구 맞춤 LED 네온사인", price: 99000, pack: 1, rating: 4.8, reviews: 860, freeShip: true, tags: ["LED"] },
    { source: H, id: "d12", cat: "rug", mood: "vintage", name: "[예시] 빈티지 페르시안 러그 160x230", price: 79000, pack: 1, rating: 4.5, reviews: 1150, freeShip: true }
  ];

  /* 분위기별 아이디어 (우리 글, 이미지 없음) */
  const IDEAS = [
    { mood: "wood", title: "따뜻한 우드", color: "#b7794b",
      text: "원목 수납장과 라탄 조명 하나만 바꿔도 손님이 '집처럼 편하다'고 느껴요. 노란빛(전구색) 조명에 초록 화분 하나를 더하면 사진도 따뜻하게 나옵니다.",
      items: ["light", "cabinet", "plant", "sofa"] },
    { mood: "white", title: "화이트 미니멀", color: "#94a3b8",
      text: "벽·선반을 흰색으로 통일하고 물건은 왜건 하나에 모으세요. 둥근 LED 거울이 얼굴을 밝게 비춰서 시술 전후 사진이 깔끔해집니다.",
      items: ["mirror", "cabinet", "sofa", "light"] },
    { mood: "vintage", title: "빈티지", color: "#7c4a3a",
      text: "바버 체어나 금테 거울처럼 '포인트 하나'만 오래된 느낌으로 두세요. 러그와 네온 문구 한 줄이면 손님이 사진 찍고 싶어지는 자리가 생깁니다.",
      items: ["chair", "mirror", "rug", "sign"] }
  ];

  const api = { MOCK, DECOR, IDEAS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ShopData = api;
})(typeof window !== "undefined" ? window : globalThis);
