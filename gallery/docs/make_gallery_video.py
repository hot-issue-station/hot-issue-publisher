"""덕심저장소 갤러리 「3분 둘러보기」 영상 만들기 — 최소판(뼈대)

지금 되는 것: 갤러리(hall.html)를 Playwright로 자동 조작해 3장면(입장 → 건물·로비 → 방 이동)을 녹화하고,
가로 16:9(1920×1080) 자막을 얹어 mp4 로 만든다. 내레이션(g01.wav…)이 있으면 장면 길이를 맞추고 소리를 넣는다.
나머지 장면(액자 보기·좋아요·퀴즈·굿즈 샵·4개 언어 등)은 영상계획.md 의 장면표대로 SCENES 에 하나씩 더하면 된다.

사용법:
  python3 make_gallery_video.py                                  # 자막만(무음)
  python3 make_gallery_video.py --narration-dir 폴더             # g01.wav… 를 문장별로 잘라 넣기
  python3 make_gallery_video.py --three-dir <three build 폴더>   # three.js 를 인터넷(jsdelivr)에서 못 받는 환경일 때
  python3 make_gallery_video.py --style museum                   # 건물 외관 바꿔 보기(classic=신전풍, museum=박물관풍)
  python3 make_gallery_video.py --narration-md                   # 대본 문서(narration_tour.md)만 다시 쓰기

- 갤러리 파일(hall.html)은 고치지 않는다. 화면만 누른다.
- 이 환경(클라우드)에서는 유튜브 썸네일·영상 임베드가 막혀 액자가 비어 보인다 → 액자·영상 장면은 집 PC 크롬에서 OBS로 녹화(영상계획.md 참고).
- 영상 속 유튜브 화면·멤버 얼굴은 공식 임베드 화면 그대로, 짧게, 출처 표시. 갤러리 공개 전에는 이 영상도 공개하지 않는다.
- 내레이션 자르기·소리 맞추기는 미용실 make_video.py 의 함수를 그대로 쓴다(한 곳에서만 고치도록).
필요한 것: python3, playwright(chromium), Pillow, ffmpeg
"""
import argparse, datetime as dt, functools, http.server, json, os, shutil, socketserver, sys, threading, time
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
GAL = os.path.dirname(HERE)                                             # gallery/
SALON_DOCS = os.path.join(os.path.dirname(GAL), "salon", "docs")
sys.path.insert(0, SALON_DOCS)
import make_video as mv     # font, ff, dur_of, load_narration, scene_need, build_track, join, loudness, silences …

SCRATCH = "/tmp/claude-0/-home-claude/5b86d6bf-3b46-51b5-bd15-5d22f7dac018/scratchpad"
KST = ZoneInfo("Asia/Seoul")
W, H, FPS = 1920, 1080, 30
VW, VH = 1280, 720                                                       # 녹화 창(가로)
BG = (14, 12, 40); Y = (255, 214, 64); TX = (255, 255, 255); SUB = (185, 190, 215); BAND = (14, 12, 40, 200)

# ── 내레이션 대본 (Veda) — 영상계획.md 장면표와 같은 글. 고치면 둘 다 고친다 ─────────────
# 한 파일 = AI Studio 에 한 번에 붙여 넣는 덩어리(500자 안팎), 한 줄 = 한 문장(문장 사이 1초 쉼으로 자름)
NARR_TOUR = [
    ("g01.wav", [
        ("intro",    "안녕하세요, 덕심저장소 갤러리에 오신 걸 환영해요."),
        ("intro",    "좋아하는 아이돌의 영상을, 미술관을 걷듯 천천히 둘러보는 곳이에요."),
        ("enter",    "처음 들어오면 언어와 함께 걸을 동물 친구, 그리고 둘러보는 방법을 고를 수 있어요."),
        ("enter",    "다 고르셨으면 시작 버튼을 눌러 주세요."),
        ("building", "눈앞에 보이는 신전 모양 건물이 리센느관이에요."),
        ("building", "문으로 들어가면 로비를 지나 전시관으로 이어져요."),
        ("statue",   "건물 앞 조각상을 누르면 멤버 소개를 볼 수 있어요."),
        ("move",     "걷기 모드에서는 왼쪽 아래 여덟 방향 버튼으로 움직여요."),
        ("move",     "가운데 칸이나 양옆 화살표를 누르면, 고개를 돌리듯 주위를 둘러볼 수 있어요."),
    ]),
    ("g02.wav", [
        ("room",     "전시관에는 무대 영상, 이번 앨범 PULSE, 안원잘부, TV 예능, 유튜브 출연, 멤버들의 일상, 생일 이벤트 방이 있어요."),
        ("room",     "방은 하나씩 차례로 열려요. 앞 방에서 영상을 몇 편 보면 다음 방 문이 열린답니다."),
        ("frame",    "벽에 걸린 액자를 누르면, 유튜브 공식 영상이 그 자리에서 열려요."),
        ("frame",    "영상은 유튜브 원본 그대로 보여 드려요."),
        ("react",    "마음에 드는 영상에는 좋아요를 누르고, 짧은 댓글도 남길 수 있어요."),
        ("quiz",     "방마다 공식 정보로 만든 퀴즈가 기다리고 있어요."),
        ("quiz",     "생일카페 풍선 아래 어딘가에는 편지 한 통도 숨어 있답니다."),
        ("secret",   "방들을 다 둘러보면 비밀의 방이 열리고, 공식 채널에 공개된 보상 영상을 만날 수 있어요."),
    ]),
    ("g03.wav", [
        ("shop",     "굿즈 샵에서는 앨범과 포토카드처럼, 함께 보면 좋은 물건을 모아 볼 수 있어요."),
        ("pets",     "함께 걷는 친구는 진돗개, 삽살개, 코리안숏헤어 고양이, 시바, 웰시코기처럼 여러 나라 친구들 가운데 고를 수 있어요."),
        ("lang",     "갤러리는 한국어, 일본어, 영어, 중국어, 네 가지 말로 볼 수 있어요."),
        ("lang",     "멀리 있는 팬 친구에게도 편하게 소개해 주세요."),
        ("outro",    "오늘 본 무대가 마음에 남았다면, 언제든 다시 놀러 오세요."),
        ("outro",    "덕심저장소 갤러리에서 기다릴게요."),
    ]),
]
# 30초 홍보 쇼츠(세로) — 대본만. 촬영 장면은 영상계획.md ②
NARR_PROMO = [
    ("p01.wav", [
        ("p_hook",  "좋아하는 아이돌 영상, 아직 하나씩 찾아보세요?"),
        ("p_walk",  "이제 미술관을 걷듯 둘러보세요."),
        ("p_rooms", "무대, 예능, 일상까지 방마다 모아 두었어요."),
        ("p_frame", "액자를 누르면 공식 영상이 바로 열려요."),
        ("p_quiz",  "퀴즈를 풀고 숨은 편지를 찾으면 비밀의 방이 열려요."),
        ("p_pets",  "동물 친구와 함께 걸어요."),
        ("p_end",   "덕심저장소 갤러리, 무료로 열려 있어요."),
    ]),
]
NARR_STYLE = "밝고 따뜻하게, 친구에게 좋아하는 곳을 소개하듯 또박또박. 문장이 끝날 때마다 1초쯤 쉬어 주세요."

# ── 그림 ─────────────────────────────────────────
def center(d, y, text, fo, fill, w=W):
    tw = d.textlength(text, font=fo); d.text(((w - tw) / 2, y), text, font=fo, fill=fill)

def band_png(path, title, sub, foot=None):
    """녹화 화면 위에 얹는 자막(아래 띠) — 투명 PNG. 갤러리 아래쪽 안내·버튼을 덜 가리게 낮고 얇게.
    foot = 오른쪽 아래 작은 글(예: 「영상 출처: RESCENE 공식 YouTube」 — 임베드 장면에서만)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([300, H - 178, W - 300, H - 28], radius=24, fill=BAND)
    center(d, H - 168, title, mv.font(56), Y)
    center(d, H - 94, sub, mv.font(38, "Medium"), TX)
    if foot:
        fo = mv.font(26, "Regular"); d.text((W - 40 - d.textlength(foot, font=fo), H - 70), foot, font=fo, fill=(255, 255, 255, 220))
    im.save(path)

def card_png(path, lines):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    total = sum(int(s * 1.5) for _, s, _ in lines); y = (H - total) // 2
    for t, s, c in lines: center(d, y, t, mv.font(s, "Bold" if s >= 70 else "Medium"), c); y += int(s * 1.5)
    im.save(path)

# ── 녹화 ─────────────────────────────────────────
PAN_JS = """([a,b,ms])=>new Promise(res=>{const d=window.Gallery&&Gallery._debug; if(!d) return res(false);
  const t0=performance.now(); (function f(){const k=Math.min(1,(performance.now()-t0)/ms);
  d.yaw=a+(b-a)*(0.5-0.5*Math.cos(Math.PI*k)); k<1?requestAnimationFrame(f):res(true)})()})"""

def pan(page, a, b, sec):
    if not page.evaluate(PAN_JS, [a, b, int(sec * 1000)]): time.sleep(sec)   # 3D가 안 켜졌으면(평면 모드) 그냥 기다림

def go(page, view, h=None, r=None, wait=1.4):
    page.evaluate("([v,h,r])=>Gallery.go(v,h,r)", [view, h, r])
    page.wait_for_function("([v,r])=>Gallery.view===v && (Gallery.roomId||null)===r", arg=[view, r], timeout=8000)
    time.sleep(wait)

def sc_enter(page):          # 입장 화면(언어·동물 친구·방법) → 시작
    page.wait_for_selector("#introGo", state="visible", timeout=15000); time.sleep(2.5)
    page.click("#introGo"); time.sleep(1.0)
    pan(page, 0.0, 0.0, 0.1)

def sc_building(page):       # 건물 밖에서 천천히 둘러보기 → 로비
    page.evaluate("Gallery._debug && (Gallery._debug.pitch=0.18)")
    pan(page, -0.5, 0.5, 4.0)
    go(page, "lobby"); pan(page, 0.4, -0.4, 3.0)

def sc_room(page):           # 리센느관 → 무대 영상 방
    go(page, "hub", "rescene"); pan(page, -0.3, 0.3, 2.5)
    go(page, "room", "rescene", "stage"); pan(page, 0.6, -0.6, 4.0)

SCENES = [  # key, 자막 큰 줄, 자막 작은 줄, 동작   ← 영상계획.md 장면표 순서대로 더해 가면 된다
    ("enter",    "입장",            "언어 · 동물 친구 · 둘러보는 방법 고르기", sc_enter),
    ("building", "리센느관",        "신전 모양 건물 → 로비로",              sc_building),
    ("room",     "방 고르기",       "무대 영상 · 앨범 · 예능 · 일상 · 생일",  sc_room),
]

def serve(root):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv

def record(tmp, three_dir, style, lang, need):
    from playwright.sync_api import sync_playwright
    srv = serve(GAL); q = f"lang={lang}" + (f"&style={style}" if style else "")
    url = f"http://127.0.0.1:{srv.server_address[1]}/hall.html?{q}"
    steps, skipped = [], []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        ctx = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=1, locale="ko-KR", timezone_id="Asia/Seoul",
                            record_video_dir=tmp, record_video_size={"width": VW, "height": VH})
        page = ctx.new_page()
        if three_dir:   # three.js 를 jsdelivr 에서 못 받는 환경: 같은 판(r186)을 로컬 폴더에서 넣어 준다
            def h(route):
                f = os.path.join(three_dir, route.request.url.rsplit("/", 1)[1])
                if os.path.exists(f): route.fulfill(path=f, content_type="text/javascript", headers={"access-control-allow-origin": "*"})
                else: route.abort()
            page.route("https://cdn.jsdelivr.net/npm/three@*/build/*", h)
        page.goto(url)
        page.wait_for_function("window.Gallery && Gallery.mode!=='loading'", timeout=30000); time.sleep(1.2)
        mode = page.evaluate("Gallery.mode")
        if mode != "3d": print(f"  ⚠️ 3D가 켜지지 않았어요(mode={mode}) — three.js 를 못 받았을 수 있어요. --three-dir 를 확인해 주세요")
        t0 = time.monotonic()
        for key, title, sub, fn in SCENES:
            s = time.monotonic() - t0
            try: fn(page)
            except Exception as e:
                skipped.append(f"{key}: {str(e)[:100]}"); print("  ⚠️ 건너뜀:", key, str(e)[:120]); continue
            stay = need.get(key, 0.0) - (time.monotonic() - t0 - s + 0.4)
            if stay > 0: time.sleep(stay)          # 내레이션이 더 길면 그 화면에 머문다
            e = time.monotonic() - t0
            steps.append({"key": key, "title": title, "sub": sub, "start": round(s, 2), "end": round(e, 2)}); print(f"  ✓ {key} ({e - s:.1f}초)")
        raw = page.video.path(); ctx.close(); b.close()
    srv.shutdown()
    return raw, steps, skipped, mode

# ── 편집 ─────────────────────────────────────────
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]

def seg_clip(raw, band, start, dur, out):
    mv.ff(["-ss", f"{start:.2f}", "-i", raw, "-i", band, "-filter_complex",
           f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=60[v];[v][1:v]overlay=0:0,format=yuv420p[o]",
           "-map", "[o]", "-t", f"{dur:.2f}", *ENC, out])

def seg_still(png, dur, out):
    mv.ff(["-loop", "1", "-framerate", str(FPS), "-i", png, "-t", f"{dur:.2f}", "-vf", "fade=in:st=0:d=0.4", *ENC, out])

def make_tour(raw, steps, tmp, out, narr):
    narr = narr or {}; parts, track, chapters, t = [], [], [], 0.0
    def add(v, key):
        nonlocal t; parts.append(v); track.append((v, narr.get(key))); d = mv.dur_of(v); chapters.append({"key": key, "start": round(t, 2), "dur": round(d, 2)}); t += d
    p = os.path.join(tmp, "g_intro.png")
    card_png(p, [("덕심저장소 갤러리", 110, Y), ("3분 둘러보기", 80, TX), ("", 30, TX), ("좋아하는 무대를 미술관처럼", 46, SUB)])
    v = os.path.join(tmp, "g00.mp4"); seg_still(p, max(3.0, mv.scene_need(narr.get("intro"))), v); add(v, "intro")
    for i, s in enumerate(steps):
        d = max(s["end"] - s["start"] + 0.4, mv.scene_need(narr.get(s["key"])))
        bg = os.path.join(tmp, f"g_{s['key']}.png"); band_png(bg, s["title"], s["sub"])
        v = os.path.join(tmp, f"g{i + 1:02}.mp4"); seg_clip(raw, bg, max(0, s["start"] - 0.2), d, v); add(v, s["key"])
    missing = [k for k in narr if k not in {"intro", "outro"} | {s["key"] for s in steps}]
    if missing: print("  · 아직 녹화 장면이 없어 빠진 내레이션:", ", ".join(dict.fromkeys(missing)))
    p = os.path.join(tmp, "g_outro.png")
    card_png(p, [("덕심저장소 갤러리", 100, Y), ("한국어 · 日本語 · English · 中文", 50, TX), ("", 30, TX), ("(주소 자리 — 공개 뒤 넣기)", 40, SUB)])
    v = os.path.join(tmp, "g99.mp4"); seg_still(p, max(3.5, mv.scene_need(narr.get("outro"))), v); add(v, "outro")
    mv.join(parts, out, tmp, mv.build_track(track, os.path.join(tmp, "tour_voice.wav")) if narr else None)
    return chapters

def narration_md(path):
    L = ["# 덕심저장소 갤러리 영상 — 내레이션 대본 (Veda)", "",
         "> `make_gallery_video.py --narration-md` 로 만든 문서예요. 대본 원본은 make_gallery_video.py 의 `NARR_TOUR`·`NARR_PROMO` 예요.", "",
         f"- 목소리: **Veda** · 스타일 지시: `{NARR_STYLE}`", "- 덩어리 하나씩 붙여 넣고, 받은 파일을 아래 이름으로 바꿔 한 폴더에.", ""]
    for title, script in (("① 3분 둘러보기 (가로 16:9)", NARR_TOUR), ("② 30초 홍보 쇼츠 (세로)", NARR_PROMO)):
        L.extend([f"## {title}", ""])
        for fname, sents in script:
            text = " ".join(t for _, t in sents)
            L.extend([f"### 파일 이름: `{fname}` — {len(text)}자 · 문장 {len(sents)}개", "", "```", text, "```", "", "| # | 장면 | 문장 |", "|---|---|---|"])
            L.extend(f"| {i + 1} | {k} | {t} |" for i, (k, t) in enumerate(sents)); L.append("")
    open(path, "w", encoding="utf-8").write("\n".join(L)); return path

def main():
    ap = argparse.ArgumentParser(description="덕심저장소 갤러리 3분 둘러보기 영상(최소판)")
    ap.add_argument("--out-dir", default=SCRATCH)
    ap.add_argument("--narration-dir", metavar="폴더", help="g01.wav~g03.wav 가 있는 폴더(없으면 자막만)")
    ap.add_argument("--three-dir", metavar="폴더", help="three.js r186 build 폴더(three.module.js·three.core.js). 인터넷 되는 PC에선 필요 없음")
    ap.add_argument("--style", choices=["classic", "museum"], help="건물 외관(기본: hall.html 설정)")
    ap.add_argument("--lang", default="ko", choices=["ko", "ja", "en", "zh"])
    ap.add_argument("--narration-md", action="store_true", help="대본 문서 narration_tour.md 만 쓰고 끝")
    ap.add_argument("--keep-raw", action="store_true")
    a = ap.parse_args()
    if a.narration_md: print("대본:", narration_md(os.path.join(HERE, "narration_tour.md"))); return
    os.makedirs(a.out_dir, exist_ok=True)
    tmp = os.path.join(a.out_dir, "_gallery_video_tmp"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    narr = None
    if a.narration_dir:
        print("⓪ 내레이션 문장별로 자르는 중…"); narr = mv.load_narration(a.narration_dir, NARR_TOUR, os.path.join(tmp, "narr"), "둘러보기")
    need = {k: mv.scene_need(v) for k, v in (narr or {}).items()}
    print("① 갤러리를 눌러 가며 녹화 중…")
    raw, steps, skipped, mode = record(tmp, a.three_dir, a.style, a.lang, need)
    if not steps: sys.exit("❌ 녹화된 장면이 없어요:\n  " + "\n  ".join(skipped))
    print("② 편집 중…")
    out = os.path.join(a.out_dir, "gallery_tour_min.mp4"); chapters = make_tour(raw, steps, tmp, out, narr)
    if narr: print(f"  · 소리 크기: {mv.loudness(out)} LUFS (목표 -14 안팎)")
    json.dump({"made": f"{dt.datetime.now(KST):%Y-%m-%d %H:%M}", "mode": mode, "chapters": chapters, "skipped": skipped},
              open(os.path.join(a.out_dir, "gallery_tour_chapters.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if a.keep_raw: shutil.copy(raw, os.path.join(a.out_dir, "gallery_raw.webm"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n둘러보기(최소판): {out} ({mv.dur_of(out):.1f}초)")
    for c in chapters: print(f"  {c['start']:5.1f}초  {c['key']}")

if __name__ == "__main__":
    main()
