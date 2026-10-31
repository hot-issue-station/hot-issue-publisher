"""정치·경제·사회 '이슈 브리핑' 카드 1장 (대표 결정 2026-10-31 20:07~20:14).

릴스(어두운 배경·움직임·임팩트)와 정반대 분위기: 밝은 종이색 바탕, 명조 제목, 사진 1장을 크게, 양쪽 입장을 같은 크기로.
카드는 1장(1080x1350)이고, 자세한 내용은 기사형 소개글(1,000~1,800자)이 맡는다.

python scripts/make_brief.py rounds/<ID>.json --out posts/<ID> [--style A|B|C|D|auto]
디자인 패턴 4가지를 돌려 쓴다(대표 결정 10/31 20:27, 같은 모양 반복 방지). auto(기본) = 파일 이름 기준 순환. round JSON 의 "style" 이 있으면 그것.
  A 신문: 종이색 바탕·명조 제목·빨간 띠            B 야간판: 짙은 남색 바탕·흰 글·노란 강조
  C 빨간 머리띠: 위쪽 빨간 띠 머리·흰 바탕·굵은 검정 테 사진   D TV 뉴스: 사진을 위 절반에 꽉 채우고 제목을 사진 위에
round JSON:
{ "date":"2026-10-31", "category":"정치 · 사법", "flash":"여야 정면충돌"(사진 위 빨간 띠, 기사 표현 범위에서), "headline":"…(*강조할 말*)", "deck":"한 줄 설명",
  "photo":"assets/thumbs/x.jpg", "photoCrop":[x0,y0,x1,y1](선택, 원본 픽셀), "photoLabel":"영상 화면 · ○○ 공식 유튜브",
  "points":["쟁점 1","쟁점 2","쟁점 3"],
  "sides":[{"name":"더불어민주당","say":"…"},{"name":"국민의힘","say":"…"}],   # 같은 분량
  "question":"올바른 관점은?", "sources":[{"outlet","date"}] }
"""
import argparse, base64, html, io, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_post import LOGO  # 우리 로고(와이파이 무지개)

E = html.escape
PAPER, INK, SUB, LINE, ACC, NAVY = "#F6F2EA", "#1B1A17", "#5C5850", "#D9D2C3", "#B23A2E", "#1F3A5F"


HL = {"A": ACC, "B": "#FFC845", "C": "#D7263D", "D": "#FFD84D"}
STYLE_CSS = {
 "A": "",
 "B": """.c{background:#0E1B2C;color:#F3F5F9}.top,.bot{border-color:#F3F5F9}.date,.src,.deck{color:#A9B6CF}
 .tag{background:#FFC845;color:#0E1B2C}.flash{background:#FFC845;color:#0E1B2C}.cat{color:#FFC845}
 .side{background:#15263D;border-color:#2A3D5C}.vs{background:#FFC845;color:#0E1B2C}.lg{background:#16243A}""",
 "C": """.c{background:#FFFFFF}.top{margin:-48px -68px 0;padding:22px 68px;background:#D7263D;color:#fff;border:none}.top .date{color:#fff}
 .tag{background:#fff;color:#D7263D}.ph{border:6px solid #111;box-sizing:border-box}.flash{background:#111}
 h1{font-family:'Noto Sans CJK KR',sans-serif;font-size:64px;letter-spacing:-2px}.cat{color:#111;border-left:10px solid #D7263D;padding-left:14px}
 .side{background:#F4F4F4;border-color:#E2E2E2}.q{font-family:'Noto Sans CJK KR';color:#D7263D}""",
 "D": """.c{background:#0B0F17;color:#F4F7FF;padding-top:0}.top{position:absolute;z-index:3;left:68px;right:68px;top:40px;border:none;color:#fff}
 .top .date{color:#fff}.ph{margin:0 -68px;height:700px}.ph .shade{background:linear-gradient(180deg,rgba(0,0,0,.45) 0%,rgba(0,0,0,0) 30%,rgba(0,0,0,.2) 55%,rgba(0,0,0,.92) 100%)}
 .ph h1{position:absolute;left:68px;right:68px;bottom:70px;color:#fff;font-size:62px;z-index:2}.ph .cat{position:absolute;left:68px;bottom:250px;z-index:2;color:#FFD84D}
 .flash{top:120px;bottom:auto;background:#D7263D}.ph .lb{bottom:16px}.side{background:#151C2B;border-color:#26324A}.vs{background:#FFD84D;color:#0B0F17}
 .bot{border-color:#F4F7FF}.src{color:#A9B6CF}.c{position:relative}""",
}


def hl(t, style="A"):
    """제목의 *단어*는 강조색으로 (대표 요청 10/31)."""
    import re
    return re.sub(r"\*(.+?)\*", lambda m: f'<span style="color:{HL.get(style, ACC)}">{m.group(1)}</span>', E(t))


def photo_uri(path, crop):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(tuple(crop))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def page(r, style="A"):
    m, d = r["date"][5:7], r["date"][8:10]
    pts = "".join(f'<li>{E(p)}</li>' for p in r["points"])
    cols = ["#1E5BD8", "#D7263D"]
    sv = [f'''<div class="side"><div class="nm" style="background:{cols[k % 2]}">{E(s["name"])}</div><div class="say">{E(s["say"])}</div></div>''' for k, s in enumerate(r["sides"])]
    sides = sv[0] + '<div class="vs">VS</div>' + sv[1] if len(sv) == 2 else "".join(sv)
    src = " · ".join(f'{E(s["outlet"])}({E(s["date"])})' for s in r["sources"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;word-break:keep-all}}
.c{{width:1080px;height:1350px;background:{PAPER};color:{INK};font-family:'Noto Sans CJK KR',sans-serif;box-sizing:border-box;padding:48px 68px;display:flex;flex-direction:column;gap:18px}}
.top{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid {INK};padding-bottom:16px;font-size:28px}}
.brand{{font-weight:900;letter-spacing:.5px;display:flex;align-items:center;gap:12px;font-size:30px}} .lg{{background:#0B1220;border-radius:14px;padding:4px}} .lg svg{{width:48px;height:48px}}
.tag{{margin-left:6px;background:{ACC};color:#fff;font-size:22px;font-weight:700;padding:4px 12px;border-radius:6px}} .date{{color:{SUB};font-weight:700}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 55%,rgba(0,0,0,.55))}}
.flash{{position:absolute;left:0;bottom:22px;background:{ACC};color:#fff;font-weight:900;font-size:44px;padding:10px 26px 12px 22px;letter-spacing:1px;box-shadow:0 6px 18px rgba(0,0,0,.3)}}
.ph{{position:relative;flex-shrink:0;height:470px;background:#000 url({photo_uri(r["photo"], r.get("photoCrop"))}) {r.get("photoPos","50% 35%")}/cover no-repeat}}
.ph .lb{{position:absolute;right:12px;bottom:12px;background:rgba(0,0,0,.55);color:#fff;font-size:20px;padding:6px 12px;border-radius:6px}}
.cat{{color:{ACC};font-weight:700;font-size:30px}}
h1{{margin:0;font-family:'Noto Serif CJK KR','Noto Serif CJK JP',serif;font-weight:900;font-size:60px;line-height:1.22;letter-spacing:-1px}}
.deck{{font-size:31px;line-height:1.5;color:{SUB}}}
ul{{margin:0;padding-left:30px;font-size:27px;line-height:1.5}} li{{margin:2px 0}}
.sides{{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:stretch}}
.vs{{align-self:center;font-family:'Noto Sans CJK KR';font-weight:900;font-size:34px;color:#fff;background:{INK};border-radius:50%;width:70px;height:70px;display:flex;align-items:center;justify-content:center}}
.side{{border:2px solid {LINE};background:#FFFDF8;border-radius:10px;overflow:hidden}}
.nm{{font-weight:900;font-size:27px;color:#fff;padding:8px 18px}} .say{{font-size:26px;line-height:1.45;padding:12px 18px 16px}}
.bot{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid {INK};padding-top:14px}}
.q{{font-family:'Noto Serif CJK KR','Noto Serif CJK JP',serif;font-weight:900;font-size:36px}}
.src{{font-size:20px;color:{SUB};text-align:right;max-width:560px}}
{STYLE_CSS.get(style, "")}
</style></head><body><div class="c">
<div class="top"><div class="brand"><div class="lg">{LOGO}</div>hot.issue.station<span class="tag">이슈 브리핑</span></div><div class="date">{m}.{d}</div></div>
<div class="ph"><div class="shade"></div>{f'<div class="flash">{E(r["flash"])}</div>' if r.get("flash") else ""}<div class="lb">{E(r["photoLabel"])}</div>{f'<div class="cat">{E(r["category"])}</div><h1>{hl(r["headline"], style)}</h1>' if style == "D" else ""}</div>
{"" if style == "D" else f'<div class="cat">{E(r["category"])}</div><h1>{hl(r["headline"], style)}</h1>'}
{f'<div class="deck">{E(r["deck"])}</div>' if r.get("deck") else ""}
<ul>{pts}</ul>
<div class="sides">{sides}</div>
<div class="bot"><div class="q">{E(r.get("question","올바른 관점은?"))}<div style="font-family:'Noto Sans CJK KR';font-weight:400;font-size:22px;color:{SUB};margin-top:6px">자세한 내용은 본문에</div></div><div class="src">출처 {src}</div></div>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("round"); ap.add_argument("--out", required=True); ap.add_argument("--style", default="auto")
    a = ap.parse_args()
    r = json.loads(pathlib.Path(a.round).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    style = a.style if a.style in STYLE_CSS else r.get("style") if r.get("style") in STYLE_CSS else None
    if not style:
        import zlib
        style = "ABCD"[zlib.crc32(pathlib.Path(a.round).stem.encode()) % 4]
    name = "brief.jpg" if a.style == "auto" else f"brief_{style}.jpg"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.set_content(page(r, style)); pg.wait_for_timeout(300)
        over = pg.evaluate("(() => { const c=document.querySelector('.c'); return c.scrollHeight > c.clientHeight + 2 })()")
        pg.screenshot(path=str(out / name), type="jpeg", quality=92); b.close()
    if r.get("caption"):
        (out / "caption.txt").write_text(r["caption"], encoding="utf-8")
    print("완료", style, out / name, "(글 넘침!)" if over else "")
    return 2 if over else 0


if __name__ == "__main__":
    sys.exit(main())
