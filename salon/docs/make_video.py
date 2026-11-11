"""단골 수첩 사용 영상 만들기 (앱을 실제로 눌러 가며 화면 녹화 → 자막 붙여 세로 영상)

사용법:
  python3 make_video.py                         # 사용법 영상 + 15초 소개 쇼츠 + 설명서 그림(screenshots/)
  python3 make_video.py --out-dir 폴더          # 결과 폴더 바꾸기
  python3 make_video.py --factory-clips 폴더    # 쇼츠 공장 「기능 30초 소개」용 클립 8개 + 채우기 파일도 만들기
  python3 make_video.py --keep-raw              # 원본 녹화(webm)를 지우지 않고 남기기

- 앱(index.html·color.html)은 고치지 않는다. 읽어서 누르기만 한다.
- 화면 속 손님은 모두 시험용 가짜 이름·가짜 번호(010-0000-xxxx)다. 실존 인물 아님.
- 앱이 바뀌어도 다시 돌리면 새로 나온다. 버튼은 글자로 찾고, 못 찾는 단계는 건너뛰고 알려 준다.
- v3 기능(말로 기록·예약·단체 문자 등)은 화면에 그 버튼이 있을 때만 자동으로 들어간다.
- 배경음악 없음(무음 트랙만). 폰트: 시스템 Noto Sans CJK KR.
필요한 것: python3, playwright(chromium), Pillow, ffmpeg
"""
import argparse, datetime as dt, functools, http.server, json, os, shutil, socketserver, subprocess, sys, threading, time
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)                       # salon/
SCRATCH = "/tmp/claude-0/-home-claude/5b86d6bf-3b46-51b5-bd15-5d22f7dac018/scratchpad"
SHOTS = os.path.join(HERE, "screenshots")
KST = ZoneInfo("Asia/Seoul")

# ── 화면·글자 ─────────────────────────────────────
W, H, FPS = 1080, 1920, 30
VW, VH = 390, 844                                  # 휴대폰 화면(세로)
SW, SH = 684, 1480                                 # 영상 속 휴대폰 화면 크기
SX, SY = (W - SW) // 2, 372
BG = (255, 248, 243); MAIN = (194, 65, 12); TX = (43, 34, 32); SUB = (122, 106, 100); LINE = (234, 217, 207)
FD = "/usr/share/fonts/opentype/noto/"
def font(size, w="Bold"):
    for name in (f"NotoSansCJK-{w}.ttc", "NotoSansCJK-Bold.ttc", "NotoSansCJK-Regular.ttc"):
        p = FD + name
        if os.path.exists(p): return ImageFont.truetype(p, size, index=1)   # index 1 = KR
    sys.exit("한글 폰트(Noto Sans CJK)를 찾을 수 없어요. fc-list :lang=ko 로 확인해 주세요.")

def center(d, y, text, fo, fill):
    w = d.textlength(text, font=fo); d.text(((W - w) / 2, y), text, font=fo, fill=fill)

def fit(d, text, size, maxw=1000, w="Bold"):
    while d.textlength(text, font=font(size, w)) > maxw and size > 30: size -= 2
    return font(size, w)

def frame_png(path, title, sub, foot="화면 속 손님은 모두 시험용 가짜 이름이에요"):
    """자막 판(위 큰 글씨 2줄) + 휴대폰 화면 자리(테두리) + 아래 작은 안내."""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=MAIN)
    center(d, 70, title, fit(d, title, 86), MAIN)
    center(d, 200, sub, fit(d, sub, 56, w="Medium"), TX)
    d.rounded_rectangle([SX - 8, SY - 8, SX + SW + 8, SY + SH + 8], radius=34, fill=LINE)
    if foot: center(d, H - 52, foot, font(28, "Regular"), SUB)
    im.save(path)

def card_png(path, lines, foot=""):
    """제목 화면·끝 화면. lines = [(글, 크기, 색), ...]"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=MAIN); d.rectangle([0, H - 14, W, H], fill=MAIN)
    total = sum(int(s * 1.45) for _, s, _ in lines); y = (H - total) // 2 - 40
    for t, s, c in lines:
        center(d, y, t, fit(d, t, s, w="Bold" if s >= 70 else "Medium"), c); y += int(s * 1.45)
    if foot: center(d, H - 120, foot, font(32, "Regular"), SUB)
    im.save(path)

# ── 시험용 가짜 손님 (실존 인물 아님) ─────────────────
def seed_customers(now):
    day = lambda n: (now - dt.timedelta(days=n)).strftime("%Y-%m-%d")
    base = int((now - dt.timedelta(days=30)).timestamp() * 1000)
    def b36(n):
        s, a = "", "0123456789abcdefghijklmnopqrstuvwxyz"
        while n: n, r = divmod(n, 36); s = a[r] + s
        return s
    people = [
        ("김미소", "010-0000-1201", "모발 얇음. 뿌리 볼륨 좋아하심", [(80, "일반 펌", 70000, "C컬 굵게"), (34, "여성 커트", 20000, ""), (0, "뿌리 염색", 50000, "6호 + 산화제 6%, 30분")]),
        ("박다온", "010-0000-3402", "", [(45, "남성 커트", 15000, ""), (14, "남성 커트", 15000, ""), (0, "남성 커트 + 다운 펌", 45000, "옆머리 다운")]),
        ("최예린", "010-0000-5603", "두피 예민 — 저자극 약 사용", [(62, "전체 염색", 80000, "7호 애쉬브라운"), (3, "클리닉", 50000, "")]),
        ("정하람", "010-0000-7804", "", [(150, "매직", 120000, ""), (75, "여성 커트", 20000, "단발 유지")]),
        ("윤가을", "010-0000-9005", "", [(120, "디지털 펌", 120000, "굵은 웨이브"), (92, "드라이", 15000, "")]),
        ("한솔비", "010-0000-2206", "앞머리만 자주 오심", [(20, "앞머리", 5000, ""), (6, "앞머리", 5000, ""), (1, "여성 커트", 20000, "")]),
        ("오세린", "010-0000-4107", "", [(40, "셋팅 펌", 100000, ""), (33, "뿌리 염색", 50000, "5호 + 6%, 25분")]),
    ]
    out = []
    for i, (n, p, m, recs) in enumerate(people):
        r = [{"d": day(a), "t": t, "m": mm, "price": str(pr), "img": None} for a, t, pr, mm in recs]
        r.sort(key=lambda x: x["d"])
        out.append({"id": b36(base + i * 997), "n": n, "p": p, "m": m, "r": r})
    return out

SEED_JS = """(seed)=>{
  const ks=Object.keys(localStorage);
  const k=ks.find(k=>{try{const o=JSON.parse(localStorage.getItem(k));return o&&Array.isArray(o.c)&&o.menu}catch(e){return false}});
  if(!k) return null;
  const db=JSON.parse(localStorage.getItem(k)); db.c=(db.c||[]).concat(seed); localStorage.setItem(k,JSON.stringify(db)); return k; }"""

RIPPLE_JS = """([x,y])=>{const d=document.createElement('div');
  d.style.cssText=`position:fixed;left:${x-30}px;top:${y-30}px;width:60px;height:60px;border-radius:50%;`+
  'border:5px solid rgba(194,65,12,.95);background:rgba(194,65,12,.25);z-index:2147483647;pointer-events:none;transition:all .6s ease-out';
  document.body.appendChild(d); requestAnimationFrame(()=>{d.style.transform='scale(1.5)';d.style.opacity='0'}); setTimeout(()=>d.remove(),900);}"""

# ── 녹화 ─────────────────────────────────────────
class Recorder:
    def __init__(self, page):
        self.page, self.t0, self.steps, self.skipped = page, time.monotonic(), [], []
    def now(self): return time.monotonic() - self.t0
    def find(self, *cands, timeout=1500):
        """후보(CSS 또는 text=글자) 중 화면에 보이는 첫 번째."""
        for c in cands:
            loc = self.page.locator(c).locator("visible=true").first
            try:
                loc.wait_for(state="visible", timeout=timeout); return loc
            except Exception:
                continue
        return None
    def show_tap(self, loc, pause=0.45):
        loc.scroll_into_view_if_needed(timeout=3000); time.sleep(0.25)
        b = loc.bounding_box()
        if b: self.page.evaluate(RIPPLE_JS, [b["x"] + b["width"] / 2, b["y"] + b["height"] / 2])
        time.sleep(pause)
    def tap(self, *cands, pause=0.45, after=0.9, click=True):
        loc = self.find(*cands)
        if not loc: raise LookupError(" / ".join(cands))
        self.show_tap(loc, pause)
        if click: loc.click()
        time.sleep(after); return loc
    def type(self, text, *cands, delay=85):
        loc = self.find(*cands)
        if not loc: raise LookupError(" / ".join(cands))
        self.show_tap(loc, 0.3); loc.click(); loc.press_sequentially(text, delay=delay); time.sleep(0.5)
    def step(self, key, title, sub, fn, shot=None, optional=False):
        s = self.now()
        try:
            fn(self)
        except Exception as e:
            self.skipped.append(f"{key}: {e.__class__.__name__} {str(e)[:90]}")
            print(("  · 건너뜀(없음): " if optional else "  ⚠️ 건너뜀: ") + key, "-", str(e)[:120])
            return
        e = self.now()
        if shot:
            os.makedirs(SHOTS, exist_ok=True); self.page.screenshot(path=os.path.join(SHOTS, shot))
        self.steps.append({"key": key, "title": title, "sub": sub, "start": round(s, 2), "end": round(e, 2), "shot": shot})
        print(f"  ✓ {key} ({e - s:.1f}초)")

def scroll_to(r, *cands):
    loc = r.find(*cands)
    if not loc: raise LookupError(" / ".join(cands))
    loc.scroll_into_view_if_needed(); r.page.evaluate("window.scrollBy(0,-90)"); time.sleep(1.2)

def tab(r, name): r.tap(f"nav >> text={name}", f"text={name}", after=1.0)

# 단계별 동작 ─ 글자로 버튼을 찾는다(앱이 바뀌어도 되도록 후보 여러 개)
def s_setup(r):
    r.find("text=어떤 가게세요?", "text=업종", timeout=4000)
    time.sleep(1.0)
    r.tap("button.chip:has-text('헤어')", "text=헤어", after=0.6)
    r.type("봄날 헤어", "#shopName", "input[placeholder*='헤어']")
    r.tap("text=시작하기", after=1.2)

def s_today(r):
    time.sleep(1.6); r.page.evaluate("window.scrollBy({top:260,behavior:'smooth'})"); time.sleep(2.0)
    r.page.evaluate("window.scrollTo({top:0,behavior:'smooth'})"); time.sleep(0.8)

def s_newcust(r):
    tab(r, "손님")
    r.tap("text=+ 새 손님", "text=새 손님", after=1.0)
    r.type("오다정", "#cn", "section:not(.hide) input >> nth=0")
    r.type("010-0000-5678", "#cp", "input[type=tel]")
    r.type("곱슬머리, 뿌리 볼륨 원하심", "#cm", "section:not(.hide) textarea")
    r.tap("#agree", "input[type=checkbox]", after=0.6)
    r.tap("button:has-text('저장')", after=1.6)

def s_record(r):
    r.tap("text=+ 오늘 시술 기록", "text=시술 기록", after=1.0)
    r.tap("#menuChips >> text=여성 커트", "button.chip:has-text('여성 커트')", after=0.6)
    r.tap("#menuChips >> text=뿌리 염색", "button.chip:has-text('뿌리 염색')", after=1.0)
    r.type("7호 + 산화제 6%, 25분", "#rm", "section:not(.hide) textarea", delay=70)
    r.tap("text=기록 저장", after=2.0)

def s_voice(r):   # v3: 「🎤 말로 기록」 버튼이 있을 때만 (마이크는 켜지 않고 버튼 위치만 보여 줌)
    loc = r.find("button:has-text('말로 기록')", "text=말로 기록", timeout=800)
    if not loc: raise LookupError("말로 기록 버튼 없음")
    r.show_tap(loc, 1.2); time.sleep(1.4)

def s_search(r):
    tab(r, "손님")
    r.type("5678", "#q", "input[placeholder*='번호']", delay=180)
    time.sleep(1.6)
    r.page.locator("#q").fill("") if r.page.locator("#q").count() else None

def s_sms(r):
    tab(r, "오늘")
    scroll_to(r, "text=오래 안 오신 손님")
    loc = r.find("#longList >> text=문자", "a.chip:has-text('문자')")
    if loc: r.show_tap(loc, 1.0)
    time.sleep(1.2)

def s_booking(r):   # v3: 예약
    r.tap("nav >> text=예약", "button:has-text('예약')", "text=예약", after=2.4)

def s_group(r):     # v3: 단체 문자 도우미
    r.tap("button:has-text('단체 문자')", "text=단체 문자", after=2.4)

def s_sales(r):
    tab(r, "매출")
    for p in ("오늘", "이번 주", "이번 달"):
        r.tap(f"#periodChips >> text={p}", f"button.chip:has-text('{p}')", after=1.0)
    time.sleep(0.6)

def s_backup(r):
    tab(r, "설정")
    scroll_to(r, "text=기록 지키기", "text=백업")
    r.tap("text=백업 파일로 저장", "button:has-text('백업')", after=1.6)

def s_color(r):
    tab(r, "손님")
    r.tap("text=오다정", after=1.2)
    r.tap("text=염색 미리보기", "a[href*='color']", after=0.2)
    r.page.wait_for_load_state("domcontentloaded"); time.sleep(2.2)
    loc = r.find("#agree", "input[type=checkbox]")
    if loc: r.show_tap(loc, 0.4); loc.click(); time.sleep(1.6)

STEPS = [  # key, 자막 큰 줄, 자막 작은 줄, 동작, 설명서 그림 파일, v3 전용(없으면 조용히 건너뜀)
    ("setup",   "1. 처음 한 번만",        "업종 고르고 가게 이름 적기",        s_setup,   "01_업종고르기.png", False),
    ("today",   "2. '오늘' 화면",         "오늘 손님 수와 매출이 한눈에",      s_today,   "02_오늘화면.png", False),
    ("newcust", "3. 새 손님 등록",        "이름·번호·메모 적고 동의 체크",     s_newcust, "03_새손님.png", False),
    ("record",  "4. 시술 기록",           "메뉴를 누르면 금액이 저절로",       s_record,  "04_시술기록.png", False),
    ("voice",   "말로 기록",              "버튼 누르고 말하면 글자로 적혀요",  s_voice,   "04b_말로기록.png", True),
    ("search",  "5. 손님 찾기",           "이름이나 번호 뒷자리로",            s_search,  "05_손님찾기.png", False),
    ("sms",     "6. 오래 안 오신 손님",   "'문자' 한 번이면 안부 인사",        s_sms,     "06_오래안오신손님.png", False),
    ("booking", "예약",                   "예약 날짜·시간을 적어 두세요",      s_booking, "06b_예약.png", True),
    ("group",   "단체 문자 도우미",       "여러 손님께 차례로 보내기",         s_group,   "06c_단체문자.png", True),
    ("sales",   "7. 매출 보기",           "오늘·이번 주·이번 달",              s_sales,   "07_매출.png", False),
    ("backup",  "8. 일주일에 한 번 백업", "휴대폰을 바꿔도 기록이 남아요",     s_backup,  "08_백업.png", False),
    ("color",   "9. 염색 미리보기",       "사진은 저장도 전송도 안 돼요",      s_color,   "09_염색미리보기.png", False),
]

def serve(root):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
    h.log_message = lambda *a, **k: None
    srv = socketserver.TCPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def record(tmp):
    from playwright.sync_api import sync_playwright
    srv = serve(APP); url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    now = dt.datetime.now(KST)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=2, is_mobile=True, has_touch=True,
                            locale="ko-KR", timezone_id="Asia/Seoul", accept_downloads=True,
                            record_video_dir=tmp, record_video_size={"width": VW * 2, "height": VH * 2},
                            user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36")
        page = ctx.new_page(); r = Recorder(page)
        page.on("dialog", lambda d: d.accept())
        page.goto(url); page.wait_for_load_state("networkidle")
        for key, title, sub, fn, shot, opt in STEPS:
            r.step(key, title, sub, fn, shot, opt)
            if key == "setup":   # 시험용 가짜 손님 넣기(영상에서는 잘려 나감)
                k = page.evaluate(SEED_JS, seed_customers(now))
                if not k: print("  ⚠️ 가짜 손님을 넣지 못했어요(저장 형식이 바뀌었을 수 있음)")
                page.reload(); page.wait_for_load_state("networkidle"); time.sleep(0.6)
        # 설명서용 그림 몇 장 더 (영상에는 안 씀)
        try:
            page.goto(url); page.wait_for_load_state("networkidle")
            tab(r, "설정"); scroll_to(r, "text=휴대폰에 앱으로 설치", "text=홈 화면에 추가")
            page.screenshot(path=os.path.join(SHOTS, "00b_설정_설치버튼.png"))
            r.tap("button:has-text('홈 화면에 추가')", after=1.0)
            page.screenshot(path=os.path.join(SHOTS, "00c_홈화면추가_안내.png"))
            r.tap("text=알겠어요", after=0.6)
            scroll_to(r, "text=백업 파일 불러오기"); page.screenshot(path=os.path.join(SHOTS, "10_백업불러오기.png"))
        except Exception as e:
            print("  · 추가 그림 일부 건너뜀:", str(e)[:100])
        raw = page.video.path(); ctx.close(); b.close()
    srv.shutdown()
    return raw, r.steps, r.skipped

# ── 편집 ─────────────────────────────────────────
def ff(args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode: sys.exit("ffmpeg 오류:\n" + r.stderr[-1500:])

ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]

def seg_clip(raw, bg, start, dur, out, speed=1.0):
    vf = (f"[1:v]setpts=(PTS-STARTPTS)/{speed:.3f},scale={SW}:{SH}:flags=lanczos,setsar=1,fps={FPS}[s];"
          f"[0:v][s]overlay={SX}:{SY}:shortest=1,format=yuv420p[v]")
    ff(["-loop", "1", "-framerate", str(FPS), "-i", bg, "-ss", f"{start:.2f}", "-t", f"{dur * speed + 0.5:.2f}", "-i", raw,
        "-filter_complex", vf, "-map", "[v]", "-t", f"{dur:.2f}", *ENC, out])

def seg_still(png, dur, out):
    ff(["-loop", "1", "-framerate", str(FPS), "-i", png, "-t", f"{dur:.2f}",
        "-vf", "fade=in:st=0:d=0.3", *ENC, out])

def join(parts, out, tmp):
    lst = os.path.join(tmp, os.path.basename(out) + ".txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    ff(["-f", "concat", "-safe", "0", "-i", lst, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", out])

def dur_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

MAXSEG = 9.0   # 한 단계 최대 길이(넘으면 빠르게 재생)

def make_howto(raw, steps, tmp, out):
    parts, chapters, t = [], [], 0.0
    p = os.path.join(tmp, "h_intro.png")
    card_png(p, [("단골 수첩", 120, MAIN), ("3분 사용법", 92, TX), ("", 40, TX), ("동네 미용실 원장님용", 50, SUB), ("큰 글씨 · 무료 · 휴대폰 하나로", 50, SUB)])
    v = os.path.join(tmp, "h00.mp4"); seg_still(p, 3.0, v); parts.append(v); t += 3.0
    for i, s in enumerate(steps):
        d = s["end"] - s["start"] + 0.4; speed = max(1.0, d / MAXSEG); out_d = d / speed
        bg = os.path.join(tmp, f"h_{s['key']}.png"); frame_png(bg, s["title"], s["sub"])
        v = os.path.join(tmp, f"h{i + 1:02}.mp4"); seg_clip(raw, bg, max(0, s["start"] - 0.2), out_d, v, speed)
        parts.append(v); chapters.append({"key": s["key"], "title": s["title"], "start": round(t, 2), "dur": round(out_d, 2)}); t += out_d
    p = os.path.join(tmp, "h_outro.png")
    card_png(p, [("단골 수첩", 110, MAIN), ("손님 기록은 이 휴대폰 안에만", 54, TX), ("일주일에 한 번 백업 잊지 마세요", 54, TX),
                 ("", 30, TX), ("설치 주소: (QR 자리)", 46, SUB)], foot="자세한 방법은 앱 설정의 도움말에서")
    v = os.path.join(tmp, "h99.mp4"); seg_still(p, 4.0, v); parts.append(v)
    join(parts, out, tmp)
    return chapters

TEASER = [  # key, 큰 줄, 작은 줄, 길이(초)
    ("record", "손님별 시술 기록", "약 호수·시간까지 한 번에", 3.5),
    ("sms", "오래 안 오신 손님", "문자 한 번으로 안부 인사", 3.0),
    ("sales", "매출이 한눈에", "오늘·이번 주·이번 달", 3.0),
]

def make_teaser(raw, steps, tmp, out):
    by = {s["key"]: s for s in steps}; parts = []
    p = os.path.join(tmp, "t_intro.png")
    card_png(p, [("원장님,", 96, TX), ("손님 기록", 96, MAIN), ("아직 종이 수첩에", 80, TX), ("하세요?", 80, TX)])
    v = os.path.join(tmp, "t00.mp4"); seg_still(p, 2.5, v); parts.append(v)
    for i, (k, a, b, d) in enumerate(TEASER):
        s = by.get(k)
        if not s: print(f"  ⚠️ 소개 쇼츠: '{k}' 장면이 없어 빠짐"); continue
        src = s["end"] - s["start"]; speed = min(2.5, max(1.0, src / d))
        st = s["start"] + max(0, src - d * speed) * 0.6
        bg = os.path.join(tmp, f"t_{k}.png"); frame_png(bg, a, b, foot="시험용 가짜 손님 화면")
        v = os.path.join(tmp, f"t{i + 1:02}.mp4"); seg_clip(raw, bg, st, d, v, speed); parts.append(v)
    p = os.path.join(tmp, "t_outro.png")
    card_png(p, [("단골 수첩", 120, MAIN), ("무료 · 큰 글씨", 60, TX), ("휴대폰 하나로", 60, TX), ("", 30, TX), ("설치 주소: (QR 자리)", 46, SUB)])
    v = os.path.join(tmp, "t99.mp4"); seg_still(p, 3.0, v); parts.append(v)
    join(parts, out, tmp)

# ── 쇼츠 공장 「기능 30초 소개」 재료 ───────────────────
FACTORY_KEYS = ["record", "voice", "newcust", "sms", "booking", "group", "sales", "backup", "color", "search", "today", "setup"]  # 앞쪽일수록 먼저 고름
CLIP_SEC, BPM = 2.5, 120          # 클립 8개 × 2.5초 = 본문 20초 (배경음악 21.4초 안쪽)

def factory_clips(howto, chapters, dst):
    """사용법 영상에서 기능 8개를 잘라 공장 교차편집(stagemix) 틀에 넣을 클립과 채우기 파일을 만든다.
    stagemix 는 노래 시각 t 에 클립의 (sync + t) 장면을 쓰므로, 클립 k 파일을 (기능 시작 - 그 클립이 나올 시각)부터 잘라 sync=0 으로 맞춘다."""
    os.makedirs(dst, exist_ok=True)
    by = {c["key"]: c for c in chapters}
    keys = sorted([k for k in FACTORY_KEYS if k in by][:8], key=lambda k: by[k]["start"])   # 영상 순서대로
    if len(keys) < 8: print(f"  ⚠️ 공장 클립이 {len(keys)}개뿐이에요(8개 권장)")
    body = len(keys) * CLIP_SEC; total = dur_of(howto); clips, plan, labels = {}, [], []
    for i, k in enumerate(keys):
        c = by[k]; name = chr(65 + i); t_song = i * CLIP_SEC
        o = c["start"] + max(0.0, (c["dur"] - CLIP_SEC) * 0.5)          # 그 기능 장면의 가운데 2.5초
        s0 = max(0.0, o - t_song); f = os.path.join(dst, f"clip_{name}_{k}.mp4")
        ff(["-ss", f"{s0:.2f}", "-i", howto, "-t", f"{body + 0.5:.2f}", "-vf", f"tpad=stop_mode=clone:stop_duration={body:.2f}",
            "-t", f"{body + 0.5:.2f}", *ENC, f])
        clips[name] = [os.path.basename(f), 0.0]; plan.append([name, "cut", int(CLIP_SEC * BPM / 60)]); labels.append(c["title"])
    fill = {"_설명": "수요일 「기능 30초 소개」 빈칸 — make_video.py --factory-clips 가 사용법 영상에서 잘라 만든 것(앱 실제 화면, 시험용 가짜 손님)",
            "이름": "salon_기능소개_샘플", "곡": "기능 한눈에", "숫자": len(keys),
            "클립": clips, "편집": plan, "bpm": BPM, "음원": "assets/bgm_morning.m4a",
            "출처": ["단골 수첩 실제 화면 녹화 · 화면 속 손님은 가짜 이름"],
            "확인": f"{dt.datetime.now(KST):%Y-%m-%d %H:%M} make_video.py 녹화본에서 자름(기능: {', '.join(labels)})",
            "저작권확인": True}
    fp = os.path.join(dst, "fill_수_기능소개.json")
    json.dump(fill, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return fp

def main():
    ap = argparse.ArgumentParser(description="단골 수첩 사용 영상 만들기")
    ap.add_argument("--out-dir", default=SCRATCH); ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--factory-clips", metavar="폴더", help="쇼츠 공장 「기능 30초 소개」 클립·채우기 파일 만들 폴더")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    tmp = os.path.join(a.out_dir, "_salon_video_tmp"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    print("① 앱을 눌러 가며 녹화 중…")
    raw, steps, skipped = record(tmp)
    if len(steps) < 5: sys.exit("❌ 녹화된 단계가 너무 적어요. 앱 화면 글자가 바뀌었는지 확인해 주세요:\n  " + "\n  ".join(skipped))
    print("② 사용법 영상 편집 중…")
    howto = os.path.join(a.out_dir, "salon_howto.mp4"); chapters = make_howto(raw, steps, tmp, howto)
    print("③ 15초 소개 쇼츠 편집 중…")
    teaser = os.path.join(a.out_dir, "salon_teaser.mp4"); make_teaser(raw, steps, tmp, teaser)
    json.dump({"made": f"{dt.datetime.now(KST):%Y-%m-%d %H:%M}", "chapters": chapters, "skipped": skipped},
              open(os.path.join(a.out_dir, "salon_howto_chapters.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if a.factory_clips:
        print("④ 쇼츠 공장 클립 만들기…"); print("  채우기 파일:", factory_clips(howto, chapters, a.factory_clips))
    if a.keep_raw: shutil.copy(raw, os.path.join(a.out_dir, "salon_raw.webm"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n사용법 영상: {howto} ({dur_of(howto):.1f}초)\n소개 쇼츠:   {teaser} ({dur_of(teaser):.1f}초)\n설명서 그림: {SHOTS}")
    for c in chapters: print(f"  {c['start']:5.1f}초  {c['title']}")
    if skipped: print("건너뛴 단계:\n  " + "\n  ".join(skipped))

if __name__ == "__main__":
    main()
