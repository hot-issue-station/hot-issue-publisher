/* 단골 수첩 장보기 — 문장 해석기
   "로레알 염색약 6호 10개" → {item:염색약, brand:로레알, shade:"6", count:10}
   브라우저(window.ShopParser)와 Node(require) 양쪽에서 씀. 외부 라이브러리 없음. */
(function (root) {
  "use strict";

  /* 업종 프리셋: 품목 id, 이름, 알아듣는 말(길이 긴 말이 먼저 이김), 묶음 단위 */
  const CATS = [
    // 재료
    { id: "dye", group: "재료", label: "염색약", icon: "🎨", words: ["염색약", "염색제", "염모제", "새치염색", "헤어컬러", "컬러크림", "칼라크림", "염색"] },
    { id: "oxid", group: "재료", label: "산화제", icon: "🧪", words: ["산화제", "현상제", "디벨로퍼", "옥시던트", "과산화수소"] },
    { id: "shampoo", group: "재료", label: "샴푸", icon: "🧴", words: ["샴푸"] },
    { id: "treat", group: "재료", label: "트리트먼트", icon: "💧", words: ["트리트먼트", "컨디셔너", "헤어팩", "헤어 팩", "클리닉", "린스", "앰플", "헤어에센스", "헤어 에센스"] },
    { id: "perm", group: "재료", label: "펌제", icon: "🌀", words: ["펌제", "파마약", "펌약", "매직약", "셋팅펌", "디지털펌", "중화제", "파마"] },
    { id: "scissors", group: "재료", label: "가위", icon: "✂️", words: ["커트가위", "커트 가위", "숱가위", "틴닝가위", "틴닝", "시저", "가위"], kw: { "숱가위": "틴닝", "틴닝가위": "틴닝", "틴닝": "틴닝" } },
    { id: "comb", group: "재료", label: "빗", icon: "🪮", words: ["꼬리빗", "커트빗", "커트 빗", "롤빗", "브러시", "브러쉬", "빗"], kw: { "꼬리빗": "꼬리빗", "롤빗": "롤빗" } },
    { id: "cape", group: "재료", label: "케이프", icon: "🧥", words: ["케이프", "커트보", "미용보", "미용가운", "가운"] },
    { id: "glove", group: "재료", label: "장갑", icon: "🧤", words: ["니트릴장갑", "니트릴 장갑", "라텍스장갑", "위생장갑", "장갑"], kw: { "니트릴장갑": "니트릴", "니트릴 장갑": "니트릴", "라텍스장갑": "라텍스" } },
    { id: "foil", group: "재료", label: "호일", icon: "🪙", words: ["하이라이트호일", "하이라이트 호일", "염색호일", "호일", "포일"] },
    { id: "dryer", group: "재료", label: "드라이기", icon: "💨", words: ["드라이기", "헤어드라이어", "드라이어"] },
    { id: "towel", group: "재료", label: "수건", icon: "🧺", words: ["미용수건", "수건", "타올", "타월"] },
    // 매장 꾸미기
    { id: "light", group: "꾸미기", label: "조명", icon: "💡", words: ["펜던트조명", "펜던트 조명", "스탠드조명", "조명", "전등", "스탠드"] },
    { id: "mirror", group: "꾸미기", label: "거울", icon: "🪞", words: ["전신거울", "벽거울", "거울"] },
    { id: "chair", group: "꾸미기", label: "미용 의자", icon: "💺", words: ["미용의자", "미용 의자", "바버체어", "바버 체어", "커트의자", "의자", "체어"] },
    { id: "sofa", group: "꾸미기", label: "대기 소파", icon: "🛋️", words: ["대기소파", "대기 소파", "대기의자", "대기 의자", "소파", "쇼파", "벤치"] },
    { id: "cabinet", group: "꾸미기", label: "수납장", icon: "🗄️", words: ["수납장", "선반", "왜건", "트롤리", "카트", "장식장"] },
    { id: "plant", group: "꾸미기", label: "화분", icon: "🪴", words: ["화분", "식물", "몬스테라", "조화"] },
    { id: "sign", group: "꾸미기", label: "간판·네온", icon: "✨", words: ["네온사인", "네온 사인", "네온", "간판", "사인"] },
    { id: "rug", group: "꾸미기", label: "카펫", icon: "🟫", words: ["카펫", "카페트", "러그", "매트"] }
  ];

  /* 브랜드: 표준 이름 ← 들릴 수 있는 말 */
  const BRANDS = {
    "로레알": ["로레알프로페셔널", "로레알 프로페셔널", "로레알", "로래알", "loreal", "l'oreal"],
    "웰라": ["웰라", "wella"],
    "밀본": ["밀본", "milbon"],
    "아모스": ["아모스프로페셔널", "아모스", "amos"],
    "미쟝센": ["미쟝센", "미장센"],
    "려": ["려"],
    "다슈": ["다슈"],
    "케라스타즈": ["케라스타즈", "케라스타스"],
    "엘라스틴": ["엘라스틴"],
    "모로칸오일": ["모로칸오일", "모로칸 오일"],
    "시세이도": ["시세이도"],
    "유닉스": ["유닉스"],
    "다이슨": ["다이슨"],
    "조아스": ["조아스"]
  };

  const MOODS = {
    wood: ["따뜻한 우드", "우드", "원목", "따뜻한", "나무"],
    white: ["화이트 미니멀", "미니멀", "화이트", "하얀", "깔끔한"],
    vintage: ["빈티지", "레트로", "앤틱", "엔틱"]
  };
  const MOOD_LABEL = { wood: "따뜻한 우드", white: "화이트 미니멀", vintage: "빈티지" };

  const COUNT_UNITS = "개|통|박스|상자|세트|병|팩|봉지|봉|묶음|롤|자루|벌|켤레|쌍|장|ea|EA";
  const NUM_ONES = { "한": 1, "하나": 1, "두": 2, "둘": 2, "세": 3, "셋": 3, "석": 3, "네": 4, "넷": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9 };
  const NUM_TENS = { "열": 10, "스물": 20, "스무": 20, "서른": 30 };

  const STOP = new Set(["찾아줘", "찾아", "줘", "주세요", "좀", "요", "사고", "싶어", "싶어요", "사야", "돼", "해줘", "보여줘", "담아줘", "주문", "주문해줘", "구매", "사줘",
    "걸로", "거", "걸", "것", "거로", "제일", "가장", "젤", "하고", "그리고", "랑", "이랑", "으로", "로", "있는", "같은", "용", "제품", "상품", "추천", "추천해줘", "이거", "그거", "괜찮은", "좋은", "많은", "많고", "높은", "높고"]);

  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const norm = s => String(s || "").replace(/\s+/g, " ").trim();

  /* 1) 한글 수사 → 숫자 ("열두 개" → "12개", "다섯 박스" → "5박스") */
  function koreanCounts(s) {
    const tens = Object.keys(NUM_TENS).join("|"), ones = Object.keys(NUM_ONES).sort((a, b) => b.length - a.length).join("|");
    const re = new RegExp("(^|[^가-힣])(?:(" + tens + ")\\s*)?(" + ones + ")?\\s*(" + COUNT_UNITS + ")(?![가-힣])", "g");
    return s.replace(re, (m, pre, t, o, u) => {
      if (!t && !o) return m;
      const n = (t ? NUM_TENS[t] : 0) + (o ? NUM_ONES[o] : 0);
      return pre + n + u;
    });
  }

  /* 돈 표현 하나를 숫자로: "5만", "2만5천", "15,000", "만", "3천" */
  function money(txt) {
    let m;
    const t = txt.replace(/\s+/g, "").replace(/,/g, "");
    if ((m = t.match(/^(\d+(?:\.\d+)?)?만(?:(\d)천)?(\d+)?원?$/))) {
      return Math.round((m[1] ? parseFloat(m[1]) : 1) * 10000 + (m[2] ? +m[2] * 1000 : 0) + (m[3] ? +m[3] : 0));
    }
    if ((m = t.match(/^(\d)천원?$/))) return +m[1] * 1000;
    if ((m = t.match(/^(\d+)원$/))) return +m[1];
    return null;
  }

  function parse(input) {
    const raw = norm(input);
    let s = " " + koreanCounts(raw.replace(/만\s+원/g, "만원").replace(/천\s+원/g, "천원")) + " ";
    const out = { raw, item: null, brand: null, shade: null, volume: null, percent: null, pieces: null, big: false, count: null,
      maxPrice: null, minPrice: null, sort: "balanced", rocket: false, freeShip: false, mood: null, keywords: [], query: "" };
    const cut = re => { s = s.replace(re, " "); };

    /* 2) 가격 */
    const PRICE = "(\\d+(?:\\.\\d+)?\\s*만(?:\\s*\\d\\s*천)?(?:\\d{1,4}(?=\\s*원))?\\s*원?|만\\s*원|\\d\\s*천\\s*원|\\d{1,3}(?:,\\d{3})+\\s*원|\\d{3,}\\s*원)";
    let m;
    const range = new RegExp(PRICE + "\\s*(?:에서|부터|~|-)\\s*" + PRICE + "\\s*(?:사이|까지)?");
    if ((m = s.match(range))) {
      const a = money(m[1]), b = money(m[2]);
      if (a != null && b != null) { out.minPrice = Math.min(a, b); out.maxPrice = Math.max(a, b); cut(m[0]); }
    }
    const pre = new RegExp(PRICE + "\\s*(대|이하|미만|까지|안쪽|안으로|안에서|안|아래|밑으로|밑|이내|넘지\\s*않는|이상|넘는|부터|초과)?", "g");
    s = s.replace(pre, (all, amt, q) => {
      const v = money(amt);
      if (v == null || v < 100) return all;
      q = (q || "").replace(/\s+/g, "");
      if (q === "대") { const step = v >= 100000 ? 100000 : v >= 10000 ? 10000 : 1000; out.minPrice = v; out.maxPrice = v + step - 1; }
      else if (q === "미만") out.maxPrice = v - 1;
      else if (q === "이상" || q === "넘는" || q === "부터") out.minPrice = v;
      else if (q === "초과") out.minPrice = v + 1;
      else out.maxPrice = v;           // "이하·까지·안" 또는 금액만 말한 경우 = 예산 상한
      return " ";
    });

    /* 3) 용량·농도·매수 */
    s = s.replace(/(\d+(?:\.\d+)?)\s*(ml|mL|ML|밀리리터|밀리|리터|l|L|kg|킬로그램|킬로|g|그램)(?![a-zA-Z가-힣])/g, (all, n, u) => {
      n = parseFloat(n);
      const ul = u.toLowerCase();
      if (ul === "l" || u === "리터") out.volume = { v: Math.round(n * 1000), u: "ml" };
      else if (ul === "ml" || u.startsWith("밀리")) out.volume = { v: Math.round(n), u: "ml" };
      else if (ul === "kg" || u.startsWith("킬로")) out.volume = { v: Math.round(n * 1000), u: "g" };
      else out.volume = { v: Math.round(n), u: "g" };
      return " ";
    });
    s = s.replace(/(\d+(?:\.\d+)?)\s*(%|프로|퍼센트)/g, (a, n) => { out.percent = parseFloat(n); return " "; });
    s = s.replace(/(\d+)\s*매(?![가-힣])/g, (a, n) => { out.pieces = +n; return " "; });
    if (/대용량|큰\s*통|업소용|살롱용/.test(s)) { out.big = true; cut(/대용량|큰\s*통|업소용|살롱용/g); }

    /* 4) 호수: 6호, 7-1호, 7.1호, 6/0호 → "6", "7.1" */
    s = s.replace(/(\d{1,2})\s*(?:[.\-\/]\s*(\d{1,2}))?\s*호(?![가-힣])/g, (a, x, y) => { out.shade = shadeKey(x + (y != null ? "." + y : "")); return " "; });

    /* 5) 개수 */
    s = s.replace(new RegExp("(\\d+)\\s*(" + COUNT_UNITS + ")(?!갑)(?![가-힣])", "g"), (a, n) => { out.count = +n; return " "; });

    /* 6) 정렬 조건 */
    const wantCheap = /제일\s*싼|가장\s*싼|젤\s*싼|최저가|제일\s*저렴|가장\s*저렴|저렴한|싼\s*(?:거|걸|것)|싸게|싼\s*걸로/.test(s);
    const wantReviews = /리뷰\s*(?:가|도)?\s*많|후기\s*(?:가|도)?\s*많|많이\s*(?:팔|산|사는|쓰는)|잘\s*팔리|인기\s*(?:많|있|좋)|인기/.test(s);
    const wantRating = /평점\s*(?:이|도)?\s*(?:높|좋)|별점\s*(?:이|도)?\s*(?:높|좋)|후기\s*(?:가|도)?\s*좋|평\s*좋|만족도\s*높/.test(s);
    out.sort = wantCheap ? "cheap" : wantReviews && wantRating ? "quality" : wantReviews ? "reviews" : wantRating ? "rating" : "balanced";
    cut(/제일|가장|젤|최저가|저렴한|저렴|싼|싸게|리뷰\S*|후기\S*|평점\S*|별점\S*|만족도|인기\S*|많이|잘\s*팔리는|팔리는|높은|높고|좋은|많은|많고/g);

    /* 7) 배송 */
    if (/로켓|내일\s*도착|빨리\s*오는|빠른\s*배송/.test(s)) { out.rocket = true; cut(/로켓\s*배송\S*|로켓\S*|내일\s*도착\S*|빨리\s*오는|빠른\s*배송/g); }
    if (/무료\s*배송|무배|배송비\s*없/.test(s)) { out.freeShip = true; cut(/무료\s*배송\S*|무배|배송비\s*없\S*/g); }

    /* 8) 분위기(매장 꾸미기) */
    outer: for (const k of Object.keys(MOODS)) for (const w of MOODS[k]) {
      if (s.includes(w)) { out.mood = k; break outer; }
    }
    if (out.mood) for (const w of MOODS[out.mood]) s = s.split(w).join(" ");

    /* 9) 브랜드 */
    let bestB = null;
    for (const [std, alts] of Object.entries(BRANDS)) for (const a of alts) {
      const re = new RegExp("(^|[^가-힣a-z])" + esc(a) + "(?=$|[^가-힣a-z]|의|꺼|거|제품|에서)", "i");
      if (re.test(s) && (!bestB || a.length > bestB.a.length)) bestB = { std, a };
    }
    if (bestB) { out.brand = bestB.std; s = s.replace(new RegExp(esc(bestB.a), "ig"), " "); }

    /* 10) 품목: 가장 먼저 나온 말, 같은 자리면 긴 말 */
    let hit = null;
    for (const c of CATS) for (const w of c.words) {
      const i = s.indexOf(w);
      if (i < 0) continue;
      if (!hit || i < hit.i || (i === hit.i && w.length > hit.w.length)) hit = { c, w, i };
    }
    if (hit) {
      out.item = { id: hit.c.id, label: hit.c.label, group: hit.c.group };
      if (hit.c.kw && hit.c.kw[hit.w]) out.keywords.push(hit.c.kw[hit.w]);
      for (const w of hit.c.words.slice().sort((a, b) => b.length - a.length)) s = s.split(w).join(" ");
    }

    /* 11) 남은 말 = 추가 키워드 (니트릴, 블랙, LED …) */
    s.replace(/[,.!?~·]/g, " ").split(/\s+/).forEach(t => {
      t = t.replace(/(으로|로|을|를|이|가|은|는|도|만|요)$/, "");
      if (t.length >= 2 && !STOP.has(t) && !/^\d+$/.test(t) && !out.keywords.includes(t)) out.keywords.push(t);
    });

    out.query = buildQuery(out);
    return out;
  }

  function shadeKey(x) {
    x = String(x).replace(/\s+/g, "").replace(/[-\/]/g, ".");
    return x.replace(/\.0+$/, "");
  }

  /* 판매처 검색창에 보낼 검색어 (가격·개수·정렬은 빼고) */
  function buildQuery(p) {
    const parts = [];
    if (p.brand) parts.push(p.brand);
    if (p.item) parts.push(p.item.label === "간판·네온" ? "네온사인" : p.item.label);
    if (p.shade) parts.push(p.shade + "호");
    if (p.percent != null) parts.push(p.percent + "%");
    if (p.volume) parts.push(p.volume.u === "ml" ? (p.volume.v >= 1000 ? (p.volume.v / 1000) + "L" : p.volume.v + "ml") : p.volume.v + "g");
    if (p.pieces) parts.push(p.pieces + "매");
    if (p.big) parts.push("대용량");
    if (p.mood) parts.push(MOOD_LABEL[p.mood].split(" ").pop());
    p.keywords.forEach(k => { if (!parts.includes(k)) parts.push(k); });
    if (p.item && p.item.group === "재료" && !p.brand && /가위|빗|케이프/.test(p.item.label)) parts.push("미용");
    return parts.join(" ").trim() || p.raw;
  }

  /* 상품명에서 호수·용량·묶음 수 짐작 (API 결과에 칸이 없을 때) */
  function fromName(name) {
    const p = parse(name);
    let pack = 1, m;
    const n = String(name);
    if ((m = n.match(/(\d+)\s*개입/)) || (m = n.match(/[x×X\*]\s*(\d+)\s*(?:개|통|병|팩|롤|세트|박스)?/)) || (m = n.match(/(\d+)\s*(?:개|통|병|팩|롤|벌|자루)\s*(?:세트|묶음|set)?/))) pack = Math.max(1, +m[1]);
    return { shade: p.shade, volume: p.volume, percent: p.percent, pieces: p.pieces, pack, brand: p.brand, item: p.item };
  }

  const api = { parse, fromName, buildQuery, shadeKey, CATS, BRANDS, MOODS, MOOD_LABEL };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ShopParser = api;
})(typeof window !== "undefined" ? window : globalThis);
