"""단골 수첩 사용 영상 만들기 (앱을 실제로 눌러 가며 화면 녹화 → 자막 붙여 세로 영상)

사용법:
  python3 make_video.py                         # 사용법 영상 + 15초 소개 쇼츠 + 설명서 그림(screenshots/)
  python3 make_video.py --out-dir 폴더          # 결과 폴더 바꾸기
  python3 make_video.py --factory-clips 폴더    # 쇼츠 공장 「기능 30초 소개」용 클립 8개 + 채우기 파일도 만들기
  python3 make_video.py --keep-raw              # 원본 녹화(webm)를 지우지 않고 남기기
  python3 make_video.py --narration-dir 폴더    # 내레이션(n01.wav~n03.wav, 쇼츠 t01.wav)을 넣어 만들기
  python3 make_video.py --narration-md          # 내레이션 대본(narration_howto.md)만 다시 쓰기(녹화 없음)

내레이션: 폴더에 n01.wav… 가 있으면 무음 구간(ffmpeg silencedetect)으로 문장별로 잘라, 각 단계 화면을
내레이션 길이만큼 늘린다(녹화 때 그 화면에 그대로 머무름 → 멈춘 화면이 아니라 살아 있는 같은 화면).
소리는 -14 LUFS 안팎으로 맞춘다. 파일이 없으면 지금처럼 자막만(무음).

- 앱(index.html·color.html)은 고치지 않는다. 읽어서 누르기만 한다.
- 화면 속 손님은 모두 시험용 가짜 이름·가짜 번호(010-0000-xxxx)다. 실존 인물 아님.
- 앱이 바뀌어도 다시 돌리면 새로 나온다. 버튼은 글자로 찾고, 못 찾는 단계는 건너뛰고 알려 준다.
- v3 기능(말로 기록·예약·단체 문자 등)은 화면에 그 버튼이 있을 때만 자동으로 들어간다.
- 배경음악 없음(무음 트랙만). 폰트: 시스템 Noto Sans CJK KR.
필요한 것: python3, playwright(chromium), Pillow, ffmpeg
"""
import argparse, datetime as dt, functools, re, http.server, json, os, shutil, socketserver, subprocess, sys, threading, time
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
    def step(self, key, title, sub, fn, shot=None, optional=False, need=0.0):
        s = self.now()
        try:
            fn(self)
        except Exception as e:
            self.skipped.append(f"{key}: {e.__class__.__name__} {str(e)[:90]}")
            print(("  · 건너뜀(없음): " if optional else "  ⚠️ 건너뜀: ") + key, "-", str(e)[:120])
            return
        if need:   # 내레이션이 더 길면 그 화면에 그대로 머문다(정지 화면이 아니라 실제 화면)
            stay = need - (self.now() - s + 0.4)
            if stay > 0: time.sleep(stay)
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

def s_voice(r):   # v3: 「🎤 말로 기록」 — 처음 안내 화면까지만 보여 주고 닫음(마이크는 켜지 않음)
    loc = r.find("button:has-text('말로 기록')", "text=말로 기록", timeout=800)
    if not loc: raise LookupError("말로 기록 버튼 없음")
    r.show_tap(loc, 0.5); loc.click(); time.sleep(3.2)
    r.page.screenshot(path=os.path.join(SHOTS, "04b_말로기록_안내.png"))
    try: r.page.evaluate("typeof vCancel==='function'&&vCancel()")
    except Exception: pass
    time.sleep(0.4)

def s_search(r):
    tab(r, "손님")
    r.type("5678", "#q", "input[placeholder*='번호']", delay=180)
    time.sleep(1.6)
    r.page.locator("#q").fill("") if r.page.locator("#q").count() else None

def s_sms(r):
    tab(r, "오늘")
    scroll_to(r, "text=다시 오실 때 된 손님", "text=오래 안 오신 손님")
    loc = r.find("#rvBox >> text=문자", "#longList >> text=문자", "a.chip:has-text('문자')", "button:has-text('문자')")
    if loc: r.show_tap(loc, 1.0)
    time.sleep(1.4)

def s_import(r):    # v3: 연락처·엑셀 불러오기 (파일은 고르지 않고 화면만)
    tab(r, "손님")
    r.tap("button:has-text('불러오기')", "text=연락처·엑셀 불러오기", after=2.6)

def s_group(r):     # v3: 단체 문자 도우미 (문자는 보내지 않음)
    tab(r, "손님")
    r.tap("button:has-text('단체 문자')", "text=단체 문자", after=2.4)

def s_booking(r):   # v3: 예약 잡기
    tab(r, "오늘")
    r.tap("button:has-text('예약 추가')", "button:has-text('예약 잡기')", after=1.0)
    r.type("김미소", "#bkQ", "input[placeholder*='찾기']", delay=120)
    r.tap("#bkFound >> text=고르기", "#bkFound button", after=0.8)
    try:
        r.tap("#bkDayChips button >> nth=1", after=0.6)
        r.tap("#bkTimeChips button >> nth=2", after=0.6)
    except LookupError: pass
    r.tap("text=예약 저장", after=1.8)
    loc = r.find("button:has-text('예약 알림 문자')", "text=예약 알림 문자", timeout=800)
    if loc: r.show_tap(loc, 1.2)

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

STEPS = [  # key, 자막 큰 줄(번호는 자동), 자막 작은 줄, 동작, 설명서 그림 파일, v3 기능(없으면 조용히 건너뜀)
    ("setup",   "처음 한 번만",          "업종 고르고 가게 이름 적기",          s_setup,   "01_업종고르기.png", False),
    ("today",   "'오늘' 화면",           "오늘 손님·매출·예약이 한눈에",        s_today,   "02_오늘화면.png", False),
    ("newcust", "새 손님 등록",          "이름·번호·메모 적고 동의 체크",       s_newcust, "03_새손님.png", False),
    ("record",  "시술 기록",             "메뉴를 누르면 금액이 저절로",         s_record,  "04_시술기록.png", False),
    ("voice",   "말로 기록",             "처음 한 번, 말소리가 어디로 가는지 안내", s_voice, None, True),
    ("search",  "손님 찾기",             "이름이나 번호 뒷자리로",              s_search,  "05_손님찾기.png", False),
    ("import",  "연락처·엑셀 불러오기",  "다른 곳 손님 목록을 한 번에",         s_import,  "05b_불러오기.png", True),
    ("group",   "단체 문자 도우미",      "한 분씩 확인하고 보내요",             s_group,   "05c_단체문자.png", True),
    ("sms",     "다시 오실 때 알림",     "때가 된 손님께 문자 한 번",           s_sms,     "06_다시오실때.png", False),
    ("booking", "예약 잡기",             "날짜·시각 누르고 저장",               s_booking, "06b_예약.png", True),
    ("sales",   "매출 보기",             "달마다 그래프 · 기간별 합계",         s_sales,   "07_매출.png", False),
    ("backup",  "일주일에 한 번 백업",   "휴대폰을 바꿔도 기록이 남아요",       s_backup,  "08_백업.png", False),
    ("color",   "염색 미리보기",         "사진은 이 휴대폰 안에서만 써요",      s_color,   "09_염색미리보기.png", False),
]

def serve(root):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=root)
    srv = socketserver.TCPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def record(tmp, need=None):
    """need = {단계 key: 그 단계에 필요한 최소 길이(초)} — 내레이션이 있을 때만."""
    need = need or {}
    from playwright.sync_api import sync_playwright
    shutil.rmtree(SHOTS, ignore_errors=True); os.makedirs(SHOTS)
    srv = serve(APP); url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    now = dt.datetime.now(KST)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=2, is_mobile=True, has_touch=True,
                            locale="ko-KR", timezone_id="Asia/Seoul", accept_downloads=True,
                            record_video_dir=tmp, record_video_size={"width": VW, "height": VH},
                            user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36")
        page = ctx.new_page(); r = Recorder(page)
        page.on("dialog", lambda d: d.accept())
        page.goto(url); page.wait_for_load_state("networkidle")
        for key, title, sub, fn, shot, opt in STEPS:
            r.step(key, title, sub, fn, shot, opt, need.get(key, 0.0))
            if key == "voice":   # 안내 창이 남아 있으면 닫기(영상에서는 잘려 나감)
                page.reload(); page.wait_for_load_state("networkidle"); time.sleep(0.5)
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
ENC_FAST = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]   # 공장 재료(중간 파일)

def seg_clip(raw, bg, start, dur, out, speed=1.0):
    vf = (f"[1:v]setpts=(PTS-STARTPTS)/{speed:.3f},scale={SW}:{SH}:flags=lanczos,setsar=1,fps={FPS},"
          f"tpad=stop_mode=clone:stop_duration=60[s];"   # 녹화가 모자라면 마지막 화면 유지(보통은 녹화 때 머물러서 안 씀)
          f"[0:v][s]overlay={SX}:{SY}:shortest=1,format=yuv420p[v]")
    ff(["-loop", "1", "-framerate", str(FPS), "-i", bg, "-ss", f"{start:.2f}", "-t", f"{dur * speed + 0.5:.2f}", "-i", raw,
        "-filter_complex", vf, "-map", "[v]", "-t", f"{dur:.2f}", *ENC, out])

def seg_still(png, dur, out):
    ff(["-loop", "1", "-framerate", str(FPS), "-i", png, "-t", f"{dur:.2f}",
        "-vf", "fade=in:st=0:d=0.3", *ENC, out])

def join(parts, out, tmp, audio=None):
    """audio = 장면 길이에 맞춰 만든 내레이션 wav(없으면 무음 트랙)."""
    lst = os.path.join(tmp, os.path.basename(out) + ".txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    src = ["-i", audio] if audio else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    ff(["-f", "concat", "-safe", "0", "-i", lst, *src, "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k" if audio else "96k", "-ac", "2", "-shortest", "-movflags", "+faststart", out])

def dur_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

MAXSEG = 7.0   # 한 단계 최대 길이(넘으면 빠르게 재생)

def make_howto(raw, steps, tmp, out, narr=None):
    """narr = {key: [문장 wav, ...]} (내레이션이 있을 때). 각 장면 길이를 내레이션 길이 이상으로 맞춘다."""
    narr = narr or {}; need = lambda k, base: max(base, scene_need(narr.get(k)))
    parts, chapters, t, track = [], [], 0.0, []
    p = os.path.join(tmp, "h_intro.png")
    card_png(p, [("단골 수첩", 120, MAIN), ("3분 사용법", 92, TX), ("", 40, TX), ("동네 미용실 원장님용", 50, SUB), ("큰 글씨 · 무료 · 휴대폰 하나로", 50, SUB)])
    d0 = need("intro", 2.5); v = os.path.join(tmp, "h00.mp4"); seg_still(p, d0, v); parts.append(v); track.append((v, narr.get("intro"))); t += dur_of(v)
    for i, s in enumerate(steps):
        d = s["end"] - s["start"] + 0.4; want = scene_need(narr.get(s["key"]))
        speed = max(1.0, d / max(MAXSEG, want)); out_d = max(d / speed, want)
        s["title"] = f"{i + 1}. {s['title']}"
        bg = os.path.join(tmp, f"h_{s['key']}.png"); frame_png(bg, s["title"], s["sub"])
        v = os.path.join(tmp, f"h{i + 1:02}.mp4"); seg_clip(raw, bg, max(0, s["start"] - 0.2), out_d, v, speed)
        parts.append(v); track.append((v, narr.get(s["key"])))
        real = dur_of(v); chapters.append({"key": s["key"], "title": s["title"], "start": round(t, 2), "dur": round(real, 2)}); t += real
    p = os.path.join(tmp, "h_outro.png")
    card_png(p, [("단골 수첩", 110, MAIN), ("손님 기록은 이 휴대폰 안에만", 54, TX), ("일주일에 한 번 백업 잊지 마세요", 54, TX),
                 ("", 30, TX), ("설치 주소: (QR 자리)", 46, SUB)], foot="자세한 방법은 앱 설정의 도움말에서")
    v = os.path.join(tmp, "h99.mp4"); seg_still(p, need("outro", 3.5), v); parts.append(v); track.append((v, narr.get("outro")))
    join(parts, out, tmp, build_track(track, os.path.join(tmp, "howto_voice.wav")) if narr else None)
    return chapters

TEASER = [  # key, 큰 줄, 작은 줄, 길이(초)
    ("record", "손님별 시술 기록", "약 호수·시간까지 한 번에", 3.5),
    ("sms", "다시 오실 때 된 손님", "문자 한 번으로 안부 인사", 3.0),
    ("sales", "매출이 한눈에", "오늘·이번 주·이번 달", 3.0),
]

def make_teaser(raw, steps, tmp, out, narr=None):
    narr = narr or {}; by = {s["key"]: s for s in steps}; parts, track = [], []
    p = os.path.join(tmp, "t_intro.png")
    card_png(p, [("원장님,", 96, TX), ("손님 기록", 96, MAIN), ("아직 종이 수첩에", 80, TX), ("하세요?", 80, TX)])
    v = os.path.join(tmp, "t00.mp4"); seg_still(p, max(2.5, scene_need(narr.get("intro"), 0.2, 0.3)), v); parts.append(v); track.append((v, narr.get("intro")))
    for i, (k, a, b, d) in enumerate(TEASER):
        s = by.get(k)
        if not s: print(f"  ⚠️ 소개 쇼츠: '{k}' 장면이 없어 빠짐"); continue
        d = max(d, scene_need(narr.get(k), 0.2, 0.3))
        src = s["end"] - s["start"]; speed = min(2.5, max(1.0, src / d))
        st = s["start"] + max(0, src - d * speed) * 0.6
        bg = os.path.join(tmp, f"t_{k}.png"); frame_png(bg, a, b, foot="시험용 가짜 손님 화면")
        v = os.path.join(tmp, f"t{i + 1:02}.mp4"); seg_clip(raw, bg, st, d, v, speed); parts.append(v); track.append((v, narr.get(k)))
    p = os.path.join(tmp, "t_outro.png")
    card_png(p, [("단골 수첩", 120, MAIN), ("무료 · 큰 글씨", 60, TX), ("휴대폰 하나로", 60, TX), ("", 30, TX), ("설치 주소: (QR 자리)", 46, SUB)])
    v = os.path.join(tmp, "t99.mp4"); seg_still(p, max(3.0, scene_need(narr.get("outro"), 0.2, 0.5)), v); parts.append(v); track.append((v, narr.get("outro")))
    join(parts, out, tmp, build_track(track, os.path.join(tmp, "teaser_voice.wav"), lead=0.2, gap=0.2) if narr else None)

# ── 내레이션 ─────────────────────────────────────
# 대본은 여기 한 곳에만 둔다. narration_howto.md 는 --narration-md 로 여기서 만들어진다.
# (파일 이름, [(장면 key, 문장), ...]) — 한 파일 = AI Studio에 한 번에 붙여 넣는 덩어리(500자 안팎).
# 앱 v3.1 실제 화면 글자와 맞춤: 번호 없이 등록, 지난번 카드, 말로 기록, 예약 알림 문자, 다시 오실 때, 장보기.
NARR_HOWTO = [
    ("n01.wav", [
        ("intro",   "원장님, 안녕하세요."),
        ("intro",   "휴대폰 하나로 쓰는 손님 기록 앱, 단골 수첩 쓰는 법을 차근차근 알려 드릴게요."),
        ("setup",   "처음 한 번만, 가게 업종을 고르고 가게 이름을 적어 주세요."),
        ("setup",   "업종을 고르시면 시술 메뉴와 가격이 저절로 들어가고, 가격은 나중에 얼마든지 바꾸실 수 있어요."),
        ("today",   "'오늘' 화면에서는 오늘 손님과 매출, 예약이 한눈에 보여요."),
        ("today",   "맨 위 장보기 버튼을 누르면, 필요한 물건을 말로 찾고 제일 싼 곳을 고를 수 있어요."),
        ("newcust", "새 손님은 이름이나 별명, 특징 가운데 하나만 적어도 저장돼요."),
        ("newcust", "전화번호는 여쭙기 어려우면 비워 두셔도 되고, 번호나 사진을 적을 때만 동의 칸에 체크해 주세요."),
        ("record",  "시술 기록은 메뉴만 누르면 금액이 저절로 채워져요."),
        ("record",  "약 호수와 시간을 메모해 두시면, 다음에 손님을 열었을 때 맨 위 '지난번' 카드에 그대로 보여요."),
    ]),
    ("n02.wav", [
        ("voice",   "손이 바쁘실 땐 말로 기록 버튼을 한 번 누르고, 김영희 커트 이만원처럼 말씀하시면 돼요."),
        ("voice",   "처음 한 번은 말소리가 어디로 가는지 안내가 나오고, 싫으시면 '쓰지 않을래요'를 누르시면 돼요."),
        ("search",  "손님은 이름이나 별명, 번호 뒷자리로 찾아요."),
        ("search",  "옆의 마이크를 눌러 말로 찾으셔도 돼요."),
        ("import",  "다른 곳에 있던 손님 목록은 연락처나 엑셀 파일로 한 번에 불러올 수 있어요."),
        ("import",  "잘못 불러왔으면 '방금 불러온 것 되돌리기'를 누르시면 돼요."),
        ("group",   "여러 분께 보낼 문자도, 한 분씩 확인하면서 차례로 보내 드려요."),
        ("sms",     "'오늘' 화면 아래에는 다시 오실 때가 된 손님이 모여 있어요."),
        ("sms",     "문자 버튼을 누르면 안부 인사 문구가 미리 채워져서 열려요."),
    ]),
    ("n03.wav", [
        ("booking", "예약은 손님을 고르고, 날짜와 시각만 누르면 저장돼요."),
        ("booking", "예약 전날에는 '내일 예약 알림 문자' 버튼으로 한 분씩 알려 드릴 수 있어요."),
        ("sales",   "매출 화면에서는 오늘, 이번 주, 이번 달 합계를 눌러서 바로 보실 수 있어요."),
        ("backup",  "손님 기록은 이 휴대폰 안에만 저장돼요."),
        ("backup",  "그래서 일주일에 한 번, 설정에서 백업 파일로 저장해 두시면 휴대폰을 바꾸셔도 안심이에요."),
        ("color",   "손님 사진으로 염색 색을 미리 보여 드릴 수도 있어요."),
        ("color",   "사진은 이 휴대폰 안에서만 쓰여요."),
        ("outro",   "손님 한 분 한 분을 기억해 주시는 원장님 곁에서, 단골 수첩이 함께할게요."),
        ("outro",   "자세한 방법은 앱 안의 사용법에서 언제든 다시 보실 수 있어요."),
    ]),
]
NARR_TEASER = [
    ("t01.wav", [
        ("intro",  "원장님, 손님 기록 아직 종이 수첩에 하세요?"),
        ("record", "시술 기록은 메뉴만 누르면 끝나요."),
        ("sms",    "다시 오실 때 된 손님께는 문자 한 번."),
        ("sales",  "매출도 한눈에 보여요."),
        ("outro",  "무료 앱 단골 수첩, 휴대폰 하나면 돼요."),
    ]),
]
NARR_STYLE = ("따뜻하고 또박또박, 동네 미용실 원장님께 옆에서 차근차근 알려 드리듯 읽어 주세요. "
              "조금 천천히, 문장이 끝날 때마다 1초쯤 쉬어 주세요.")
LEAD, GAP, TAIL = 0.35, 0.35, 0.6       # 장면 시작 뒤 첫 문장까지 · 문장 사이 · 마지막 문장 뒤
SR = 48000

def scene_need(files, lead=LEAD, tail=TAIL, gap=GAP):
    """그 장면 문장들을 다 읽는 데 필요한 길이(초). 문장이 없으면 0."""
    if not files: return 0.0
    return lead + sum(dur_of(f) for f in files) + gap * (len(files) - 1) + tail

def silences(wav, noise="-35dB", d=0.25):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    out, cur = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m: cur = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and cur is not None: out.append([cur, float(m.group(1))]); cur = None
    if cur is not None: out.append([cur, dur_of(wav)])     # 파일 끝까지 조용함
    return out

def split_chunk(wav, sents, dst, prefix):
    """덩어리 wav 하나를 문장 수만큼 자른다. 가장 긴 무음 (문장 수 - 1)곳을 경계로 쓴다(쉼표 쉼은 짧아서 안 잘림).
    무음이 모자라면 글자 수 비율로 나누고 알려 준다."""
    total = dur_of(wav); sil = silences(wav); n = len(sents)
    head = sil[0][1] if sil and sil[0][0] <= 0.05 else 0.0
    tail = sil[-1][0] if sil and sil[-1][1] >= total - 0.05 else total
    inner = [s for s in sil if s[0] > head + 0.05 and s[1] < tail - 0.05]
    warn = None
    if len(inner) >= n - 1:
        cuts = sorted(sorted(inner, key=lambda s: s[0] - s[1])[:n - 1])
        bounds = [(head if i == 0 else cuts[i - 1][1], tail if i == n - 1 else cuts[i][0]) for i in range(n)]
    else:
        warn = f"{os.path.basename(wav)}: 문장 {n}개인데 쉬는 곳이 {len(inner)}곳뿐 → 글자 수 비율로 나눔(문장 사이를 조금 더 쉬어 다시 녹음하면 정확해요)"
        lens = [len(t) for _, t in sents]; acc, bounds = 0, []
        for L in lens:
            a = head + (tail - head) * acc / sum(lens); acc += L
            bounds.append((a, head + (tail - head) * acc / sum(lens)))
    out = []
    for i, ((a, b), (key, text)) in enumerate(zip(bounds, sents)):
        a, b = max(0.0, a - 0.04), min(total, b + 0.12)
        f = os.path.join(dst, f"{prefix}_{i + 1:02}_{key}.wav")
        ff(["-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", wav, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", f])
        out.append({"key": key, "text": text, "file": f, "dur": round(dur_of(f), 2), "from": round(a, 2), "to": round(b, 2)})
    return out, warn

def load_narration(folder, script, dst, label):
    """폴더의 덩어리 wav 들을 문장별로 잘라 {장면 key: [문장 wav...]} 로 돌려준다. 파일이 하나도 없으면 None."""
    if not folder: return None
    os.makedirs(dst, exist_ok=True); by, report, found = {}, [], 0
    for fname, sents in script:
        src = os.path.join(folder, fname)
        if not os.path.exists(src):
            alt = [p for p in (src[:-4] + e for e in (".mp3", ".m4a", ".ogg", ".flac")) if os.path.exists(p)]
            if not alt: print(f"  · {label} 내레이션 {fname} 없음 → 그 장면들은 자막만"); continue
            src = alt[0]
        found += 1
        parts, warn = split_chunk(src, sents, dst, fname[:-4])
        if warn: print("  ⚠️", warn)
        for p in parts:
            by.setdefault(p["key"], []).append(p["file"]); report.append(p)
            print(f"  · {fname} {p['dur']:4.1f}초  [{p['key']}] {p['text'][:28]}…")
    if not found: return None
    json.dump(report, open(os.path.join(dst, "문장_자른결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return by

def build_track(scenes, out, lead=LEAD, gap=GAP):
    """scenes = [(장면 mp4, [문장 wav] 또는 None)]. 장면 실제 길이에 맞춰 문장을 놓고 -14 LUFS 로 맞춘 wav 를 만든다."""
    import array, wave
    pcm = array.array("h")
    for vid, files in scenes:
        n = int(round(dur_of(vid) * SR)); seg = array.array("h", bytes(2 * n)); pos = int(lead * SR)
        for f in files or []:
            with wave.open(f) as w: a = array.array("h", w.readframes(w.getnframes()))
            a = a[:max(0, n - pos)]; seg[pos:pos + len(a)] = a; pos += len(a) + int(gap * SR)
        pcm.extend(seg)
    raw = out[:-4] + "_raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    # 2단계 loudnorm: 먼저 재고, 잰 값으로 고르게(linear) 맞춘다 → -14 LUFS 안팎, 최고 -1.5 dBTP
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    try:
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    except Exception:
        af = "loudnorm=I=-14:TP=-1.5:LRA=11"
    ff(["-i", raw, "-af", af, "-ar", str(SR), "-ac", "2", out])
    return out

def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None

def narration_md(path):
    """NARR_HOWTO·NARR_TEASER 로 대표용 대본 문서를 쓴다."""
    L = ["# 단골 수첩 사용법 영상 — 내레이션 대본 (Veda)", "",
         "> `make_video.py --narration-md` 로 만들어진 문서예요. 대본을 고치려면 make_video.py 의 `NARR_HOWTO`·`NARR_TEASER` 를 고친 뒤 다시 만들어 주세요(영상과 대본이 어긋나지 않게 한 곳에서만 관리).",
         "> 앱 v3.1 실제 화면 글자와 맞췄어요. 화면 속 손님은 모두 시험용 가짜 이름이에요.", "",
         "## 목소리 설정 (Google AI Studio · 무료)", "",
         "- 목소리: **Veda** (여성) — 남성이 필요하면 Finn",
         f"- 스타일 지시(Style instructions 칸에 그대로): `{NARR_STYLE}`",
         "- 한 번에 덩어리 하나(500자 안팎)씩 붙여 넣고, 받은 파일 이름을 아래 **파일 이름** 그대로 바꿔 한 폴더에 모아 주세요.",
         "- 문장 사이를 1초쯤 쉬어야 영상 프로그램이 문장별로 정확히 잘라요(쉼표 쉼은 짧아서 안 잘려요).", ""]
    def block(title, script, note):
        L.extend([f"## {title}", "", note, ""])
        for fname, sents in script:
            text = " ".join(t for _, t in sents)
            L.extend([f"### 파일 이름: `{fname}` — {len(text)}자 · 문장 {len(sents)}개", "", "붙여 넣을 글:", "", "```", text, "```", "",
                      "| # | 장면 | 문장 |", "|---|---|---|"])
            L.extend(f"| {i + 1} | {k} | {t} |" for i, (k, t) in enumerate(sents))
            L.append("")
    names = {k: f"{i + 1}. {t}" for i, (k, t, *_ ) in enumerate(STEPS)}; names.update(intro="제목 화면", outro="끝 화면")
    block("사용법 영상 (세로 1080×1920 · 13단계)", NARR_HOWTO,
          "장면 key → 영상 단계: " + " · ".join(f"{k}={v}" for k, v in names.items()))
    block("15초 소개 쇼츠", NARR_TEASER, "장면: intro=첫 화면(질문) · record=시술 기록 · sms=다시 오실 때 · sales=매출 · outro=끝 화면. "
          "내레이션이 15초보다 길면 쇼츠가 그만큼 늘어나요(지금 대본 기준 약 15~17초).")
    L.extend(["## 영상 만들기", "", "```", "python3 make_video.py --narration-dir 내레이션폴더", "```", "",
              "- 폴더에 `n01.wav`~`n03.wav`(사용법), `t01.wav`(쇼츠)가 있으면 넣고, 없으면 그 부분은 지금처럼 자막만 나와요.",
              "- mp3·m4a 로 받았어도 같은 이름이면 돼요(예: n01.mp3).",
              "- 문장별로 자른 결과는 결과 폴더 `_narration/문장_자른결과.json` 에 남아요(문장 길이 확인용).", ""])
    open(path, "w", encoding="utf-8").write("\n".join(L))
    return path

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
        # 사용법 영상의 번호 붙은 자막(예: "3. 새 손님 등록")을 번호 없는 자막으로 덮는다(홍보 영상에선 번호가 어색함)
        title = re.sub(r"^\d+\.\s*", "", c["title"]); sub = next((st[2] for st in STEPS if st[0] == k), "")
        band = os.path.join(dst, f"_band_{name}.png"); frame_png(band, title, sub, foot=None)
        Image.open(band).crop((0, 0, W, SY - 10)).save(band)
        ff(["-ss", f"{s0:.2f}", "-i", howto, "-i", band, "-filter_complex",
            f"[0:v][1:v]overlay=0:0,tpad=stop_mode=clone:stop_duration={body:.2f}[v]", "-map", "[v]",
            "-t", f"{body + 0.5:.2f}", *ENC_FAST, f]); os.remove(band)
        clips[name] = [os.path.join(os.path.basename(dst), os.path.basename(f)), 0.0]; plan.append([name, "cut", int(CLIP_SEC * BPM / 60)]); labels.append(c["title"])
    fill = {"_설명": "수요일 「기능 30초 소개」 빈칸 — make_video.py --factory-clips 가 사용법 영상에서 잘라 만든 것(앱 실제 화면, 시험용 가짜 손님)",
            "이름": "salon_기능소개_샘플", "곡": "기능 한눈에", "숫자": len(keys),
            "클립": clips, "편집": plan, "bpm": BPM, "음원": "assets/bgm_morning.m4a",
            "출처": ["단골 수첩 실제 화면 녹화 · 화면 속 손님은 가짜 이름"],
            "확인": f"{dt.datetime.now(KST):%Y-%m-%d %H:%M} make_video.py 녹화본에서 자름(기능: {', '.join(labels)})",
            "저작권확인": True}
    fp = os.path.join(os.path.dirname(os.path.abspath(dst)), "fill_수_기능소개.json")   # 클립 폴더 바로 위(경로는 채우기 파일 기준)
    json.dump(fill, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return fp

def main():
    ap = argparse.ArgumentParser(description="단골 수첩 사용 영상 만들기")
    ap.add_argument("--out-dir", default=SCRATCH); ap.add_argument("--keep-raw", action="store_true")
    ap.add_argument("--factory-clips", metavar="폴더", help="쇼츠 공장 「기능 30초 소개」 클립 폴더(채우기 파일은 그 바로 위에). 예: ../../factory/templates_salon/fills/기능소개_클립")
    ap.add_argument("--clips-only", action="store_true", help="녹화 없이, 이미 만든 사용법 영상·장면 기록(salon_howto_chapters.json)으로 공장 클립만")
    ap.add_argument("--narration-dir", metavar="폴더", help="내레이션 폴더(n01.wav~n03.wav 사용법, t01.wav 쇼츠). 없으면 자막만")
    ap.add_argument("--narration-md", action="store_true", help="대본 문서 narration_howto.md 만 다시 쓰고 끝")
    a = ap.parse_args()
    if a.narration_md:
        print("대본:", narration_md(os.path.join(HERE, "narration_howto.md"))); return
    os.makedirs(a.out_dir, exist_ok=True)
    if a.clips_only:
        if not a.factory_clips: sys.exit("--clips-only 는 --factory-clips 폴더와 함께 써 주세요")
        ch = json.load(open(os.path.join(a.out_dir, "salon_howto_chapters.json"), encoding="utf-8"))["chapters"]
        print("채우기 파일:", factory_clips(os.path.join(a.out_dir, "salon_howto.mp4"), ch, a.factory_clips)); return
    tmp = os.path.join(a.out_dir, "_salon_video_tmp"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    narr_h = narr_t = None
    if a.narration_dir:
        print("⓪ 내레이션 문장별로 자르는 중…")
        nd = os.path.join(a.out_dir, "_narration"); shutil.rmtree(nd, ignore_errors=True)
        narr_h = load_narration(a.narration_dir, NARR_HOWTO, nd, "사용법")
        narr_t = load_narration(a.narration_dir, NARR_TEASER, nd, "쇼츠")
        if not (narr_h or narr_t): print("  · 내레이션 파일이 없어 자막만으로 만들어요")
    need = {k: scene_need(v) for k, v in (narr_h or {}).items()}
    for k, v in (narr_t or {}).items():    # 쇼츠 장면도 녹화본에서 잘라 쓰므로 그만큼은 머문다
        need[k] = max(need.get(k, 0.0), scene_need(v, 0.2, 0.3))
    print("① 앱을 눌러 가며 녹화 중…")
    raw, steps, skipped = record(tmp, need)
    if len(steps) < 5: sys.exit("❌ 녹화된 단계가 너무 적어요. 앱 화면 글자가 바뀌었는지 확인해 주세요:\n  " + "\n  ".join(skipped))
    print("② 사용법 영상 편집 중…")
    howto = os.path.join(a.out_dir, "salon_howto.mp4"); chapters = make_howto(raw, steps, tmp, howto, narr_h)
    print("③ 15초 소개 쇼츠 편집 중…")
    teaser = os.path.join(a.out_dir, "salon_teaser.mp4"); make_teaser(raw, steps, tmp, teaser, narr_t)
    if narr_h or narr_t:
        for p in (howto, teaser): print(f"  · {os.path.basename(p)} 소리 크기: {loudness(p)} LUFS (목표 -14 안팎)")
    json.dump({"made": f"{dt.datetime.now(KST):%Y-%m-%d %H:%M}", "narration": bool(narr_h), "chapters": chapters, "skipped": skipped},
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
