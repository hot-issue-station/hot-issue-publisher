"""움직이는 자막 쇼츠(9:16, 1080x1920, 약 18초)를 round JSON 하나로 만든다. 목소리·음악 없음(무음 트랙).

python3 scripts/make_shorts.py rounds/<회차>.json /home/claude/reels/<이름>.mp4

장면: ① 표지(그림이 있으면 천천히 확대 + 분야 칸 + 훅 자막이 한 줄씩 튀어나옴)
      ② 큰 숫자(정수면 0부터 올라감) + 옆 글 3줄
      ③~⑤ 사실 3개(제목이 아래에서 올라오고 설명이 이어서 나타남)
      ⑥ 해석 한 줄(가장 크게)  ⑦ 저장 유도 + 계정 이름
화면 위 진행 막대. 인스타 글자·버튼에 가리지 않게 위 240px·아래 440px·오른쪽 160px을 비운다.
색은 make_post.py 의 회차별 색 묶음(AM·PM·NT·RS)을 그대로 쓴다.
"""
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_post  # noqa: E402

W, H, FPS = 1080, 1920, 30
E = html.escape


def rich(t):
    """*강조* → 강조색, \\n → 줄바꿈."""
    t = E(str(t))
    t = re.sub(r"\*(.+?)\*", r'<span class="hi">\1</span>', t)
    return t.replace("\n", "<br>")


def build_html(r):
    th = make_post.THEMES.get(r.get("theme", r["slot"]), make_post.THEMES["NT"])
    big = r.get("big") or {}
    num = str(big.get("number", ""))
    facts = r["facts"][:3]
    photo = make_post.photo_uri(r["photo"]) if r.get("photo") else ""
    # 장면 시간표(초): 시작, 길이
    S = {"cover": (0.0, 3.4), "num": (3.4, 3.0)}
    t = 6.4
    for i in range(len(facts)):
        S[f"f{i}"] = (t, 2.8)
        t += 2.8
    S["interp"] = (t, 3.0)
    t += 3.0
    S["cta"] = (t, 2.4)
    total = t + 2.4

    def scene(key, inner, extra=""):
        s, d = S[key]
        return (f'<section class="sc" style="animation:show {d}s linear {s}s both;{extra}">{inner}</section>')

    hook_lines = str(r.get("hookCover", r["hook"])).split("\n")
    hook = "".join(f'<div class="pop" style="animation-delay:{0.35 + 0.35 * i:.2f}s">{rich(l)}</div>' for i, l in enumerate(hook_lines))
    cover_img = (f'<div class="ph"><div class="phi" style="background-image:url({photo});background-position:{r.get("photoPos", "50% 50%")};animation:kb {S["cover"][1] + 0.5}s ease-out 0s both"></div>'
                 + (f'<div class="tag">{E(r.get("photoLabel", ""))}</div>' if r.get("photoLabel") else "") + '</div>') if photo else ""
    cover = scene("cover", f'''{cover_img}
<div class="low"><div class="chip pop" style="animation-delay:.15s">{E(r["category"])}</div>
<div class="hook">{hook}</div></div>''')

    lines = "".join(f'<div class="pop" style="animation-delay:{S["num"][0] + 0.5 + 0.25 * i:.2f}s">{rich(l)}</div>' for i, l in enumerate(big.get("lines", [])))
    numsc = scene("num", f'''<div class="mid"><div class="num" id="num">{E(num)}</div>
<div class="nl">{lines}</div>{f'<div class="cap pop" style="animation-delay:{S["num"][0] + 1.3:.2f}s">{E(big.get("caption", ""))}</div>' if big.get("caption") else ""}</div>''') if num else ""

    fsc = ""
    for i, f in enumerate(facts):
        s = S[f"f{i}"][0]
        fsc += scene(f"f{i}", f'''<div class="mid"><div class="idx pop" style="animation-delay:{s + .05:.2f}s">{i + 1} / {len(facts)}</div>
<div class="ft rise" style="animation-delay:{s + .15:.2f}s">{rich(f["title"])}</div>
<div class="fd fade" style="animation-delay:{s + .7:.2f}s">{rich(f["desc"])}</div></div>''')

    s = S["interp"][0]
    interp = scene("interp", f'''<div class="mid"><div class="it rise" style="animation-delay:{s + .1:.2f}s">{rich(r["interp"])}</div>
<div class="is fade" style="animation-delay:{s + .8:.2f}s">{rich(r.get("interpSub", ""))}</div></div>''', f"background:{th['CYAN']};color:{th['ONACC']}")
    s = S["cta"][0]
    cta = scene("cta", f'''<div class="mid" style="align-items:center;text-align:center">{make_post.LOGO.replace('width="68" height="68"', 'width="150" height="150"')}
<div class="ct rise" style="animation-delay:{s + .1:.2f}s">{rich(r.get("cta", "저장해 두세요"))}</div>
<div class="acc fade" style="animation-delay:{s + .5:.2f}s">@hot.issue.station</div></div>''')

    css = f"""
*{{box-sizing:border-box}} body{{margin:0;background:{th['BG']};font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;word-break:keep-all}}
#stage{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{th['BG']};color:{th['INK']}}}
.sc{{position:absolute;inset:0;padding:240px 160px 440px 90px;display:flex;flex-direction:column}}
.hi{{color:{th['PINK']}}}
.ph{{position:absolute;left:0;top:0;width:{W}px;height:1060px;overflow:hidden}}
.phi{{position:absolute;inset:0;background-size:cover}}
.ph:after{{content:"";position:absolute;inset:0;background:linear-gradient(rgba({th['BGRGB']},.0) 55%,rgba({th['BGRGB']},1) 100%)}}
.tag{{position:absolute;right:180px;top:880px;padding:8px 20px;border-radius:999px;background:rgba({th['BGRGB']},.75);color:{th['SOFT']};font-size:26px;z-index:2}}
.low{{margin-top:auto;display:flex;flex-direction:column;gap:26px;position:relative}}
.chip{{align-self:flex-start;padding:10px 28px;border:4px solid {th['CYAN']};border-radius:999px;color:{th['CYAN']};font-size:36px;font-weight:700}}
.hook{{font-size:104px;font-weight:900;line-height:1.18}}
.mid{{margin:auto 0;display:flex;flex-direction:column;gap:30px}}
.num{{font-size:330px;font-weight:900;line-height:.9;color:{th['CYAN']};letter-spacing:-8px}}
.nl{{font-size:76px;font-weight:900;line-height:1.25}}
.cap{{font-size:40px;color:{th['SOFT']}}}
.idx{{font-size:36px;font-weight:700;color:{th['CYAN']}}}
.ft{{font-size:88px;font-weight:900;line-height:1.2}}
.fd{{font-size:46px;line-height:1.55;color:{th['BODY']}}}
.it{{font-size:96px;font-weight:900;line-height:1.25}}
.is{{font-size:46px;line-height:1.55;opacity:.92}}
.ct{{font-size:64px;font-weight:900;line-height:1.3}}
.acc{{font-size:44px;color:{th['MUTED']}}}
#bar{{position:absolute;left:0;top:0;height:12px;width:{W}px;background:rgba(255,255,255,.18)}}
#barf{{height:100%;width:100%;transform-origin:0 0;background:{th['CYAN']};animation:bar {total}s linear 0s both}}
.pop{{animation:pop .5s cubic-bezier(.2,1.4,.4,1) both}}
.rise{{animation:rise .55s cubic-bezier(.2,.9,.3,1) both}}
.fade{{animation:fade .6s ease-out both}}
@keyframes show{{0%{{opacity:0}}4%{{opacity:1}}96%{{opacity:1}}100%{{opacity:0}}}}
@keyframes pop{{0%{{opacity:0;transform:scale(.6) translateY(30px)}}100%{{opacity:1;transform:none}}}}
@keyframes rise{{0%{{opacity:0;transform:translateY(120px)}}100%{{opacity:1;transform:none}}}}
@keyframes fade{{0%{{opacity:0;transform:translateY(20px)}}100%{{opacity:1;transform:none}}}}
@keyframes kb{{0%{{transform:scale(1.0)}}100%{{transform:scale(1.14)}}}}
@keyframes bar{{0%{{transform:scaleX(0)}}100%{{transform:scaleX(1)}}}}
"""
    count = ""
    if re.fullmatch(r"\d{1,6}", num):
        s0 = S["num"][0]
        count = f"""const el=document.getElementById('num');const N={int(num)};
const t0={s0 + 0.1},d=1.1;const k=Math.min(1,Math.max(0,(t-t0)/d));const e=1-Math.pow(1-k,3);el.textContent=Math.round(N*e).toLocaleString('ko-KR');"""
    js = f"""<script>window.seek=function(t){{document.getAnimations().forEach(a=>{{a.pause();a.currentTime=t*1000;}});{count}}};</script>"""
    page = f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div id="stage">{cover}{numsc}{fsc}{interp}{cta}<div id="bar"><div id="barf"></div></div></div>{js}</body></html>'
    return page, total


def main():
    r = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    page, total = build_html(r)
    n = int(total * FPS)
    from playwright.sync_api import sync_playwright
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{n / FPS:.3f}",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(page)
        pg.wait_for_timeout(400)
        stage = pg.locator("#stage")
        for i in range(n):
            pg.evaluate(f"seek({i / FPS:.4f})")
            ff.stdin.write(stage.screenshot(type="jpeg", quality=90))
        b.close()
    ff.stdin.close()
    ff.wait()
    print(f"done {total:.1f}s -> {out}")


if __name__ == "__main__":
    main()
