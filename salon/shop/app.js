/* 단골 수첩 장보기 — 화면 */
(function () {
  "use strict";
  const P = window.ShopParser, R = window.ShopRank, D = window.ShopData, S = window.SEARCH;
  const $ = s => document.querySelector(s);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const won = R.won;

  /* ---------- 기기 저장 (이 휴대폰에만) ---------- */
  const KEY = "dangol_shop_v1";
  let st = { favs: [], history: [], settings: {}, freeSeen: false };
  try { st = Object.assign(st, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
  const settings = () => Object.assign({}, R.DEFAULTS, st.settings);

  /* ---------- 처음 화면 ---------- */
  if (!st.freeSeen) { $("#free").open = true; st.freeSeen = true; save(); }
  if (S.mode !== "mock") $("#sample").classList.add("hide");

  const EXAMPLES = ["로레알 염색약 6호 10개", "커트 가위 5만원 이하", "샴푸 대용량 리뷰 많은 걸로"];
  $("#ex").innerHTML = EXAMPLES.map(e => `<button type="button" data-q="${esc(e)}">"${esc(e)}"</button>`).join("");

  let tab = "재료";
  function drawTab() {
    document.querySelectorAll(".seg button").forEach(b => b.classList.toggle("on", b.dataset.tab === tab));
    $("#grid").innerHTML = P.CATS.filter(c => c.group === tab)
      .map(c => `<button type="button" data-q="${esc(c.label === "간판·네온" ? "네온사인" : c.label)}"><b>${c.icon}</b>${esc(c.label)}</button>`).join("");
    $("#ideas").innerHTML = tab !== "꾸미기" ? "" : `<h2>매장 꾸미기 아이디어</h2>` + D.IDEAS.map(i => `
      <div class="card idea" style="--c:${i.color}">
        <h3>${esc(i.title)}</h3><p>${esc(i.text)}</p>
        <div class="chips">${i.items.map(id => { const c = P.CATS.find(x => x.id === id); return `<button type="button" class="chip" data-q="${esc(P.MOOD_LABEL[i.mood] + " " + c.label)}">${c.icon} ${esc(c.label)} 찾기</button>`; }).join("")}</div>
      </div>`).join("");
  }
  document.querySelector(".seg").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { tab = b.dataset.tab; drawTab(); } });
  drawTab();

  /* ---------- 검색 ---------- */
  let last = null; // {q, data, result, counts}
  async function run(text) {
    text = String(text || "").trim();
    if (!text) { $("#q").focus(); return; }
    $("#q").value = text;
    const q = P.parse(text);
    if (q.item && q.item.group !== tab) { tab = q.item.group; drawTab(); }
    const box = $("#results");
    box.innerHTML = `<div class="loading">찾는 중이에요…</div>`;
    let data;
    try { data = await S.find(q); }
    catch (err) { box.innerHTML = `<div class="card empty">검색이 잠시 안 돼요. ${esc(err.message)}<br>조금 뒤 다시 눌러 주세요.</div>`; return; }
    const result = R.rank(data.items, q, settings());
    last = { q, data, result, counts: {} };
    draw();
    box.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function chipsOf(q) {
    const c = [];
    if (q.item) c.push(["item", q.item.label]);
    if (q.brand) c.push(["brand", q.brand]);
    if (q.shade) c.push(["shade", q.shade + "호"]);
    if (q.percent != null) c.push(["percent", q.percent + "%"]);
    if (q.volume) c.push(["volume", q.volume.v >= 1000 && q.volume.u === "ml" ? q.volume.v / 1000 + "L" : q.volume.v + q.volume.u]);
    if (q.big) c.push(["big", "대용량"]);
    if (q.pieces) c.push(["pieces", q.pieces + "매"]);
    if (q.count) c.push(["count", q.count + "개"]);
    if (q.minPrice != null && q.maxPrice != null) c.push(["price", won(q.minPrice) + "~" + won(q.maxPrice)]);
    else if (q.maxPrice != null) c.push(["maxPrice", won(q.maxPrice) + " 이하"]);
    else if (q.minPrice != null) c.push(["minPrice", won(q.minPrice) + " 이상"]);
    if (q.rocket) c.push(["rocket", "로켓배송"]);
    if (q.freeShip) c.push(["freeShip", "무료배송"]);
    if (q.mood) c.push(["mood", P.MOOD_LABEL[q.mood]]);
    q.keywords.forEach(k => c.push(["kw:" + k, "'" + k + "'"]));
    const sortLabel = { cheap: "제일 싼 순", reviews: "리뷰 많은 순", rating: "평점 높은 순", quality: "평점·리뷰 좋은 순", balanced: "추천순" }[q.sort];
    return { c, sortLabel };
  }

  function draw() {
    const { q, data, result } = last;
    const box = $("#results");
    const { c, sortLabel } = chipsOf(q);
    const isFav = st.favs.some(f => f.q === q.raw);
    const rows = result.rows.slice(0, 8);
    const sources = [...new Set(rows.map(r => r.p.source))];
    const notices = sources.map(s => S.SOURCES[s] && S.SOURCES[s].notice).filter(Boolean);

    let h = `<h2>찾은 결과 <span class="note">${esc(data.from)} · ${esc(sortLabel)}</span></h2>
      <div class="understood"><span class="lab">알아들은 조건</span>
        ${c.map(([k, l]) => `<button type="button" class="chip c" data-drop="${esc(k)}" aria-label="${esc(l)} 조건 빼기">${esc(l)}<i>✕</i></button>`).join("") || `<span class="note">'${esc(q.raw)}'로 찾았어요</span>`}
        <button type="button" class="favbtn ${isFav ? "on" : ""}" id="favBtn">${isFav ? "★ 자주 사는 것" : "☆ 자주 사는 것에 넣기"}</button>
      </div>
      <div class="disc" id="disc">
        ${notices.map(n => `<p>${esc(n)}</p>`).join("")}
        <p>가격·평점은 검색 시점 기준이며, 실제와 다를 수 있습니다.${data.sample ? " <b>(지금 보이는 상품은 예시 데이터)</b>" : ""}</p>
      </div>`;
    (data.warnings || []).filter(Boolean).forEach(w => { h += `<div class="relax">${esc(w)}</div>`; });
    if (result.relaxed.length) h += `<div class="relax">딱 맞는 상품이 없어서 <b>${esc(result.relaxed.join(", "))}</b> 조건은 빼고 찾았어요.</div>`;
    if (!rows.length) {
      h += `<div class="card empty">조건에 맞는 상품을 못 찾았어요.<br>위의 조건 단추(✕)를 눌러 하나씩 빼 보세요.</div>`;
    }
    h += rows.map((r, i) => card(r, i)).join("");
    if (result.rows.length > rows.length) h += `<p class="note">비슷한 상품 ${result.rows.length - rows.length}개는 점수가 낮아 숨겼어요.</p>`;
    const out = result.few.concat(result.lowRate);
    if (out.length) h += `<details class="few"><summary>리뷰가 ${result.settings.minReviews}개보다 적어 뺀 상품 ${out.length}개</summary><ul>${out.map(p => `<li>${esc(p.name)} — ${won(p.price)} · 리뷰 ${p.reviews ?? "?"}개</li>`).join("")}</ul></details>`;
    box.innerHTML = h;
  }

  function card(r, i) {
    const p = r.p, src = S.SOURCES[p.source] || S.SOURCES.coupang;
    const n = last.counts[p.id] || last.q.count || 1;
    const packs = Math.ceil(n / r.pack), buyQty = packs * r.pack, total = packs * p.price;
    const ship = [p.rocket ? "🚀 로켓배송" : "", p.freeShip ? "무료배송" : (p.rocket ? "" : "배송비 따로")].filter(Boolean).join(" · ");
    const rate = p.rating != null ? `⭐ <b>${p.rating.toFixed(1)}</b>` : `평점 정보 없음`;
    const rev = p.reviews != null ? ` · 리뷰 <b>${p.reviews.toLocaleString("ko-KR")}</b>개` : (p.rating != null ? "" : "");
    const badges = r.badges.map(b => b === "cheap" ? `<span class="bdg cheap">💰 가장 싼 것</span>` : `<span class="bdg best">⭐ 평점·리뷰 최고</span>`).join("");
    return `<article class="card res" data-id="${esc(p.id)}">
      <div class="top"><span class="src" style="background:${src.color}">${esc(src.label)}</span>${badges}</div>
      <h3>${esc(p.name)}</h3>
      <div><span class="price">${won(p.price)}</span>${r.pack > 1 ? `<span class="unit">${r.pack}개 · 개당 ${won(r.unit)}</span>` : `<span class="unit">개당 ${won(r.unit)}</span>`}</div>
      <div class="meta">${rate}${rev}${ship ? " · " + ship : ""}</div>
      <div class="why">${esc(r.reason)}</div>
      <div class="qty">
        <div class="st"><button type="button" data-step="-1" aria-label="하나 빼기">−</button><output aria-label="필요한 개수">${n}</output><button type="button" data-step="1" aria-label="하나 더">＋</button></div>
        <div class="sum">필요 ${n}개 → 합계 <b>${won(total)}</b>${r.pack > 1 ? `<br><span class="note">${packs}묶음 = ${buyQty}개</span>` : ""}</div>
      </div>
      <a class="buy" style="background:${src.color}" href="${esc(S.linkFor(p))}" target="_blank" rel="sponsored nofollow noopener" data-buy="${esc(p.id)}">${esc(src.btn)}<small>${src.notice ? "광고 · 추천 링크" : "가격 참고용 링크"}</small></a>
      ${packs > 1 ? `<div class="hint">${esc(src.label)} 화면에서 수량을 <b>${packs}</b>(으)로 바꿔 담아 주세요</div>` : ""}
    </article>`;
  }

  /* ---------- 클릭 처리 ---------- */
  document.addEventListener("click", e => {
    const t = e.target.closest("[data-q],[data-drop],[data-step],[data-buy],#favBtn,[data-again],[data-unfav]");
    if (!t) return;
    if (t.dataset.q) { run(t.dataset.q); return; }
    if (t.dataset.again) { run(t.dataset.again); return; }
    if (t.dataset.unfav) { st.favs = st.favs.filter(f => f.q !== t.dataset.unfav); save(); drawMine(); return; }
    if (t.id === "favBtn" && last) {
      const i = st.favs.findIndex(f => f.q === last.q.raw);
      if (i >= 0) st.favs.splice(i, 1); else st.favs.unshift({ q: last.q.raw, at: Date.now() });
      st.favs = st.favs.slice(0, 20); save(); draw(); drawMine();
      toast(i >= 0 ? "자주 사는 것에서 뺐어요" : "자주 사는 것에 넣었어요 ★");
      return;
    }
    if (t.dataset.drop && last) { dropCond(t.dataset.drop); return; }
    if (t.dataset.step && last) {
      const id = t.closest(".res").dataset.id;
      const cur = last.counts[id] || last.q.count || 1;
      last.counts[id] = Math.max(1, Math.min(999, cur + +t.dataset.step));
      const row = last.result.rows.find(r => r.p.id === id);
      const i = last.result.rows.indexOf(row);
      t.closest(".res").outerHTML = card(row, i);
      return;
    }
    if (t.dataset.buy && last) {
      const row = last.result.rows.find(r => r.p.id === t.dataset.buy);
      if (row) {
        const n = last.counts[row.p.id] || last.q.count || 1;
        st.history = [{ q: last.q.raw, name: row.p.name, source: row.p.source, count: n, total: Math.ceil(n / row.pack) * row.p.price, at: Date.now() }]
          .concat(st.history.filter(h => !(h.q === last.q.raw && h.name === row.p.name))).slice(0, 15);
        save(); drawMine();
      }
    }
  });

  /* 알아들은 조건 하나 빼고 다시 고르기 (다시 검색하지 않음 → 호출 아낌) */
  function dropCond(k) {
    const q = last.q;
    if (k === "price") { q.minPrice = q.maxPrice = null; }
    else if (k.startsWith("kw:")) q.keywords = q.keywords.filter(x => x !== k.slice(3));
    else if (k in q) q[k] = (typeof q[k] === "boolean") ? false : null;
    last.result = R.rank(last.data.items, q, settings());
    draw();
  }

  /* ---------- 즐겨찾기·지난번 ---------- */
  function ago(t) {
    const d = Math.floor((Date.now() - t) / 86400000);
    return d <= 0 ? "오늘" : d === 1 ? "어제" : d + "일 전";
  }
  function drawMine() {
    let h = "";
    if (st.favs.length) h += `<h2>★ 자주 사는 것</h2><div class="chips">${st.favs.map(f => `<button type="button" class="chip" data-q="${esc(f.q)}">${esc(f.q)}</button>`).join("")}</div>`;
    if (st.history.length) h += `<h2>🕘 지난번 담으러 간 것</h2><div class="card">${st.history.slice(0, 8).map(x => `
      <div class="hist"><div>${esc(x.name.replace(/^\[예시\]\s*/, ""))}<small>${ago(x.at)} · ${esc((S.SOURCES[x.source] || {}).label || "")} · ${x.count}개 · ${won(x.total)}</small></div>
      <button type="button" data-again="${esc(x.q)}">다시 찾기</button></div>`).join("")}</div>
      <p class="note">실제 주문 여부는 알 수 없어요. 링크를 누른 기록만 이 휴대폰에 남겨요.</p>`;
    $("#mine").innerHTML = h;
  }
  drawMine();

  /* ---------- 글로 찾기 ---------- */
  $("#form").addEventListener("submit", e => { e.preventDefault(); stopVoice(); run($("#q").value); });

  /* ---------- 말로 찾기 (Web Speech API, ko-KR) ---------- */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null, listening = false;
  function showGuide(html) { const g = $("#guide"); g.innerHTML = html; g.classList.remove("hide"); }
  function keyboardGuide(why) {
    showGuide(`${why ? esc(why) + "<br>" : ""}아래 칸을 누른 뒤 <b>키보드의 🎤(마이크) 단추</b>를 눌러 말씀하세요. 다 말씀하시면 「찾기」를 누르면 돼요.`);
    $("#q").focus();
  }
  function stopVoice() { if (rec && listening) { try { rec.stop(); } catch (e) {} } }
  $("#mic").addEventListener("click", () => {
    if (!SR) { keyboardGuide("이 휴대폰 브라우저는 바로 듣기를 지원하지 않아요."); return; }
    if (listening) { stopVoice(); return; }
    rec = new SR();
    rec.lang = "ko-KR"; rec.interimResults = true; rec.maxAlternatives = 1; rec.continuous = false;
    let finalText = "";
    rec.onstart = () => { listening = true; $("#mic").classList.add("on"); $("#mic").textContent = "■ 그만 듣기"; const l = $("#listen"); l.textContent = "듣고 있어요… 물건과 조건을 말씀하세요"; l.classList.remove("hide"); $("#guide").classList.add("hide"); };
    rec.onresult = ev => {
      let txt = "";
      for (let i = 0; i < ev.results.length; i++) { txt += ev.results[i][0].transcript; if (ev.results[i].isFinal) finalText = txt; }
      $("#q").value = txt; $("#listen").textContent = "“" + txt + "”";
    };
    rec.onerror = ev => {
      if (ev.error === "not-allowed" || ev.error === "service-not-allowed") keyboardGuide("마이크 사용이 허용되지 않았어요. (주소창 옆 🔒 → 마이크 허용)");
      else if (ev.error === "no-speech") showGuide("말씀이 들리지 않았어요. 🎤를 다시 누르고 또박또박 말씀해 주세요.");
      else if (ev.error !== "aborted") keyboardGuide("듣기가 잠시 안 돼요.");
    };
    rec.onend = () => {
      listening = false; $("#mic").classList.remove("on"); $("#mic").textContent = "🎤 말로 찾기"; $("#listen").classList.add("hide");
      const t = (finalText || $("#q").value).trim();
      if (finalText && t) run(t);
    };
    try { rec.start(); } catch (e) { keyboardGuide("듣기를 시작하지 못했어요."); }
  });

  /* ---------- 기준 설정 ---------- */
  const dlg = $("#setDlg");
  const fields = [["wPrice", "vPrice", v => v + ""], ["wRating", "vRating", v => v + ""], ["wReviews", "vReviews", v => v + ""], ["minReviews", "vMin", v => v + "개"]];
  function fillSet() { const s = settings(); fields.forEach(([k, vid, f]) => { $("#" + k).value = s[k]; $("#" + vid).textContent = f(s[k]); }); }
  fields.forEach(([k, vid, f]) => $("#" + k).addEventListener("input", e => {
    st.settings[k] = +e.target.value; $("#" + vid).textContent = f(+e.target.value); save();
    if (last) { last.result = R.rank(last.data.items, last.q, settings()); draw(); }
  }));
  $("#setReset").addEventListener("click", () => { st.settings = {}; save(); fillSet(); if (last) { last.result = R.rank(last.data.items, last.q, settings()); draw(); } });
  $("#setBtn").addEventListener("click", () => { fillSet(); if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", ""); });

  let tt;
  function toast(m) { let el = $(".toast"); if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); } el.textContent = m; el.classList.remove("hide"); clearTimeout(tt); tt = setTimeout(() => el.classList.add("hide"), 1800); }

  /* 주소로 바로 찾기: shop.html?q=염색약 (수첩 다른 화면에서 연결할 때) */
  try { const q0 = new URLSearchParams(location.search).get("q"); if (q0) run(q0); } catch (e) {}
})();
