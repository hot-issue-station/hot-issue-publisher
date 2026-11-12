/* 덕심저장소 갤러리 — 안내 페이지 공용 스크립트 (외부 라이브러리 없음)
   - 언어: ?lang= → localStorage "hall-lang"(갤러리와 같은 키) → 브라우저 언어 → ko
   - 머리말·공통 푸터를 그리고, site-config.js 값을 [data-c] 자리에 채움, [data-form] 버튼에 FORM_URL 연결 */
(function(){
  "use strict";
  var LANGS = ["ko","ja","en","zh"];
  var NAMES = {ko:"한국어", ja:"日本語", en:"English", zh:"繁體中文"};
  var T = {
    ko:{brand:"3D 덕심 갤러리", sub:"공식 공개 영상을 모아 보는 팬 갤러리", back:"갤러리로", guide:"모험 안내서", notes:"쇼핑 노트", about:"소개", privacy:"개인정보 처리방침", terms:"이용 약관", ads:"광고 문의", takedown:"권리 침해 신고",
        fine:"3D 덕심 갤러리는 팬이 운영하는 비공식 갤러리이며, 아티스트·소속사와 관계가 없습니다. 영상의 권리는 각 권리자에게 있습니다.", soon:"문의 양식 준비 중", pending:"양식 주소가 아직 연결되지 않았어요"},
    ja:{brand:"推し心アーカイブ・ギャラリー", sub:"公式公開映像を集めたファンギャラリー", back:"ギャラリーへ", guide:"冒険ガイド", notes:"ショッピングノート", about:"紹介", privacy:"プライバシーポリシー", terms:"利用規約", ads:"広告のお問い合わせ", takedown:"権利侵害の申告",
        fine:"推し心アーカイブ・ギャラリーはファンが運営する非公式ギャラリーで、アーティスト・所属事務所とは関係ありません。映像の権利は各権利者に帰属します。", soon:"お問い合わせフォーム準備中", pending:"フォームのURLはまだ設定されていません"},
    en:{brand:"Deoksim Archive Gallery", sub:"A fan gallery of officially published videos", back:"To gallery", guide:"Adventure Guide", notes:"Shopping notes", about:"About", privacy:"Privacy Policy", terms:"Terms of Use", ads:"Advertising", takedown:"Rights Takedown",
        fine:"Deoksim Archive Gallery is an unofficial, fan-run gallery and is not affiliated with any artist or agency. All video rights belong to their respective owners.", soon:"Contact form coming soon", pending:"The form link has not been set yet"},
    zh:{brand:"追星心意典藏館", sub:"收集官方公開影片的粉絲畫廊", back:"回到畫廊", guide:"冒險指南", notes:"購物筆記", about:"簡介", privacy:"隱私權政策", terms:"使用條款", ads:"廣告洽詢", takedown:"權利侵害檢舉",
        fine:"追星心意典藏館為粉絲經營的非官方畫廊，與藝人及經紀公司無關。影片權利屬於各權利人。", soon:"洽詢表單準備中", pending:"表單網址尚未設定"}
  };
  var PAGES = [["guide","guide.html"],["notes","notes.html"],["about","about.html"],["privacy","privacy.html"],["terms","terms.html"],["ads","ads.html"],["takedown","takedown.html"]];
  var CFG = window.SITE_CONFIG || {};

  function get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } }
  function set(k,v){ try{ localStorage.setItem(k,v); }catch(e){} }
  function pick(){
    var q = null; try{ q = new URLSearchParams(location.search).get("lang"); }catch(e){}
    if(LANGS.indexOf(q) >= 0) return q;
    var s = get("hall-lang"); if(LANGS.indexOf(s) >= 0) return s;
    var n = (navigator.language || "ko").slice(0,2).toLowerCase();
    return LANGS.indexOf(n) >= 0 ? n : "ko";
  }
  function el(tag, attrs, text){
    var e = document.createElement(tag);
    for(var k in attrs) if(attrs[k] != null) e.setAttribute(k, attrs[k]);
    if(text != null) e.textContent = text;
    return e;
  }
  var page = document.body.getAttribute("data-page");
  var formReady = typeof CFG.FORM_URL === "string" && /^https:\/\//.test(CFG.FORM_URL);

  function render(lang){
    if(!document.querySelector('article[lang="' + (lang === "zh" ? "zh-Hant" : lang) + '"]')) lang = "ko";   // 한국어로만 쓴 글(쇼핑 노트 등)
    var t = T[lang] || T.ko;
    document.documentElement.setAttribute("data-lang", lang);
    document.documentElement.lang = lang === "zh" ? "zh-Hant" : lang;
    var art = document.querySelector('article[lang="' + (lang === "zh" ? "zh-Hant" : lang) + '"]');
    var h = art && art.querySelector("h1");
    document.title = (h ? h.textContent + " · " : "") + t.brand;

    var top = document.getElementById("top");
    top.textContent = "";
    var bar = el("div", {"class":"bar"});
    var home = el("a", {"class":"home", href:"./", "aria-label":t.back});
    home.appendChild(el("b", {}, t.brand));
    home.appendChild(el("small", {}, "← " + t.back + " · " + t.sub));
    var sel = el("select", {"class":"langSel", id:"langSel", "aria-label":"Language"});
    LANGS.forEach(function(l){ var o = el("option", {value:l}, NAMES[l]); if(l === lang) o.selected = true; sel.appendChild(o); });
    sel.onchange = function(){ set("hall-lang", sel.value); render(sel.value); };
    bar.appendChild(home); bar.appendChild(sel); top.appendChild(bar);

    var foot = document.getElementById("foot");
    foot.textContent = "";
    var nav = el("nav", {"aria-label":"Footer"});
    PAGES.forEach(function(p){ nav.appendChild(el("a", {href:p[1], "aria-current": p[0] === page ? "page" : null}, t[p[0]])); });
    foot.appendChild(nav);
    foot.appendChild(el("p", {}, t.fine));

    document.querySelectorAll("[data-form]").forEach(function(b){
      if(formReady){ b.href = CFG.FORM_URL; b.target = "_blank"; b.rel = "noopener"; b.removeAttribute("aria-disabled"); }
      else { b.removeAttribute("href"); b.setAttribute("aria-disabled","true"); b.title = t.pending;
        if(!b.dataset.label) b.dataset.label = b.textContent; }
    });
    document.querySelectorAll("[data-form-note]").forEach(function(n){ n.hidden = formReady; n.textContent = t.pending; });
  }

  document.querySelectorAll("[data-c]").forEach(function(s){
    var v = CFG[s.getAttribute("data-c")]; if(typeof v === "string" && v) s.textContent = v;
  });
  render(pick());
})();
