"""정치·경제·사회 '이슈 브리핑' 카드 1장 (대표 결정 2026-10-31 20:07~20:14).

릴스(어두운 배경·움직임·임팩트)와 정반대 분위기: 밝은 종이색 바탕, 명조 제목, 사진 1장을 크게, 양쪽 입장을 같은 크기로.
카드는 1장(1080x1350)이고, 자세한 내용은 기사형 소개글(1,000~1,800자)이 맡는다.

python scripts/make_brief.py rounds/<ID>.json --out posts/<ID>
round JSON:
{ "date":"2026-10-31", "category":"정치 · 사법", "headline":"…", "deck":"한 줄 설명",
  "photo":"assets/thumbs/x.jpg", "photoCrop":[x0,y0,x1,y1](선택, 원본 픽셀), "photoLabel":"영상 화면 · ○○ 공식 유튜브",
  "points":["쟁점 1","쟁점 2","쟁점 3"],
  "sides":[{"name":"더불어민주당","say":"…"},{"name":"국민의힘","say":"…"}],   # 같은 분량
  "question":"올바른 관점은?", "sources":[{"outlet","date"}] }
"""
import argparse, base64, html, io, json, pathlib, sys

E = html.escape
PAPER, INK, SUB, LINE, ACC, NAVY = "#F6F2EA", "#1B1A17", "#5C5850", "#D9D2C3", "#B23A2E", "#1F3A5F"


def photo_uri(path, crop):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(tuple(crop))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def page(r):
    m, d = r["date"][5:7], r["date"][8:10]
    pts = "".join(f'<li>{E(p)}</li>' for p in r["points"])
    sides = "".join(f'''<div class="side"><div class="nm">{E(s["name"])}</div><div class="say">{E(s["say"])}</div></div>''' for s in r["sides"])
    src = " · ".join(f'{E(s["outlet"])}({E(s["date"])})' for s in r["sources"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;word-break:keep-all}}
.c{{width:1080px;height:1350px;background:{PAPER};color:{INK};font-family:'Noto Sans CJK KR',sans-serif;box-sizing:border-box;padding:48px 68px;display:flex;flex-direction:column;gap:18px}}
.top{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid {INK};padding-bottom:16px;font-size:28px}}
.brand{{font-weight:900;letter-spacing:.5px}} .date{{color:{SUB}}}
.ph{{position:relative;flex-shrink:0;height:470px;background:#000 url({photo_uri(r["photo"], r.get("photoCrop"))}) {r.get("photoPos","50% 35%")}/cover no-repeat}}
.ph .lb{{position:absolute;right:12px;bottom:12px;background:rgba(0,0,0,.55);color:#fff;font-size:20px;padding:6px 12px;border-radius:6px}}
.cat{{color:{ACC};font-weight:700;font-size:30px}}
h1{{margin:0;font-family:'Noto Serif CJK KR','Noto Serif CJK JP',serif;font-weight:900;font-size:54px;line-height:1.25}}
.deck{{font-size:31px;line-height:1.5;color:{SUB}}}
ul{{margin:0;padding-left:30px;font-size:27px;line-height:1.5}} li{{margin:2px 0}}
.sides{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.side{{border:2px solid {LINE};background:#FFFDF8;padding:18px 20px;border-radius:10px}}
.nm{{font-weight:900;font-size:27px;color:{NAVY};margin-bottom:6px}} .say{{font-size:26px;line-height:1.45}}
.bot{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid {INK};padding-top:14px}}
.q{{font-family:'Noto Serif CJK KR','Noto Serif CJK JP',serif;font-weight:900;font-size:36px}}
.src{{font-size:20px;color:{SUB};text-align:right;max-width:560px}}
</style></head><body><div class="c">
<div class="top"><div class="brand">hot.issue.station · 이슈 브리핑</div><div class="date">{m}.{d}</div></div>
<div class="ph"><div class="lb">{E(r["photoLabel"])}</div></div>
<div class="cat">{E(r["category"])}</div>
<h1>{E(r["headline"])}</h1>
{f'<div class="deck">{E(r["deck"])}</div>' if r.get("deck") else ""}
<ul>{pts}</ul>
<div class="sides">{sides}</div>
<div class="bot"><div class="q">{E(r.get("question","올바른 관점은?"))}<div style="font-family:'Noto Sans CJK KR';font-weight:400;font-size:22px;color:{SUB};margin-top:6px">자세한 내용은 본문에</div></div><div class="src">출처 {src}</div></div>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("round"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = json.loads(pathlib.Path(a.round).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.set_content(page(r)); pg.wait_for_timeout(300)
        over = pg.evaluate("(() => { const c=document.querySelector('.c'); return c.scrollHeight > c.clientHeight + 2 })()")
        pg.screenshot(path=str(out / "brief.jpg"), type="jpeg", quality=92); b.close()
    if r.get("caption"):
        (out / "caption.txt").write_text(r["caption"], encoding="utf-8")
    print("완료", out / "brief.jpg", "(글 넘침!)" if over else "")
    return 2 if over else 0


if __name__ == "__main__":
    sys.exit(main())
