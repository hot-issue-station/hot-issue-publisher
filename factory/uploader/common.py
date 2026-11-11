"""사이트별 업로드 모듈이 같이 쓰는 도구 (Playwright, 대표 데스크톱의 크롬)

지키는 것
- 비밀번호를 다루지 않는다. 로그인 화면이 보이면 멈추고 대표에게 넘긴다.
- 봇 확인·캡차·문자 인증 화면이 보이면 멈추고 대표에게 넘긴다. 우회하지 않는다.
- 자동화 흔적을 숨기는 설정(스텔스 등)을 쓰지 않는다.
- 단계마다 스크린샷을 logs/에 남긴다.
- 기본은 '확인 모드': 최종 예약 버튼 바로 앞에서 멈추고 대표가 화면을 보고 직접 누른다.
"""
import datetime as dt, os, re, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_ROOT = os.path.join(HERE, "logs")
# 업로드 전용 크롬 프로필 폴더(평소 쓰는 크롬 프로필과 따로). login_once.bat이 같은 폴더를 쓴다.
DEFAULT_PROFILE = os.environ.get("DUKSIM_PROFILE") or os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "DuksimUploader", "chrome_profile")

# 로그인 화면 표시(주소 일부)
LOGIN_URL_HINTS = ["accounts.google.com", "/signin", "/login", "/i/flow/login", "facebook.com/login",
                   "tiktok.com/login", "instagram.com/accounts/login"]
# 봇 확인·캡차·본인 확인 표시
CAPTCHA_FRAME_HINTS = ["recaptcha", "hcaptcha", "arkoselabs", "funcaptcha", "captcha", "challenge"]
CAPTCHA_TEXT = re.compile(r"로봇이 아닙니다|보안 문자|보안 확인|본인 확인|인증 코드|인증번호|퍼즐|슬라이더를|"
                          r"I'm not a robot|verify (that )?you are human|security check|Verify it's you|"
                          r"unusual activity|비정상적인 활동|자동화된 활동", re.I)


def ask(msg):
    """대표에게 묻고 엔터를 기다린다(데스크톱 창에서)."""
    print("\n" + "=" * 70 + "\n" + msg + "\n" + "=" * 70)
    try: return input("> ").strip()
    except EOFError: return ""


class Stopped(Exception):
    """대표가 멈추라고 했거나 더 진행하면 안 되는 상황."""


class Session:
    def __init__(self, site, plan, final_click=False):
        self.site, self.plan, self.final_click = site, plan, final_click
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dir = os.path.join(LOG_ROOT, f"{stamp}_{plan.get('name', 'shorts')}_{site}")
        os.makedirs(self.dir, exist_ok=True)
        self.n = 0
        self.logf = open(os.path.join(self.dir, "기록.txt"), "a", encoding="utf-8")
        self.result = "진행 중"

    # ---- 기록 ----
    def log(self, msg):
        line = f"[{dt.datetime.now():%H:%M:%S}] [{self.site}] {msg}"
        print(line); self.logf.write(line + "\n"); self.logf.flush()

    def shot(self, page, name):
        self.n += 1
        safe = re.sub(r"[^\w가-힣-]+", "_", name)[:40]
        p = os.path.join(self.dir, f"{self.n:02d}_{safe}.png")
        try: page.screenshot(path=p, full_page=False)
        except Exception as e: self.log(f"스크린샷 실패({e})")
        self.log(f"단계 {self.n:02d}: {name}  (화면 저장: {os.path.basename(p)})")
        return p

    # ---- 멈춤 장치 ----
    def guard(self, page, where=""):
        """로그인·캡차 화면이면 멈추고 대표에게 넘긴다. 대표가 끝내면 다시 확인 후 계속."""
        while True:
            why = self._blocked(page)
            if not why: return
            self.shot(page, f"멈춤_{why}")
            if why == "로그인":
                msg = (f"[{self.site}] 로그인 화면이 나왔습니다. 대표님이 이 크롬 창에서 직접 로그인해 주세요.\n"
                       "프로그램은 비밀번호를 입력하지 않습니다. 로그인이 끝나 원래 화면이 보이면 엔터를 눌러 주세요.\n"
                       "(그만두려면 '중단' 입력)")
            else:
                msg = (f"[{self.site}] 봇 확인/보안 확인 화면이 나왔습니다. 프로그램은 여기서 멈춥니다(우회하지 않음).\n"
                       "대표님이 직접 확인을 마치시고 엔터를 눌러 주세요. 자주 나오면 이 사이트는 자동 진행을 쉬는 게 안전합니다.\n"
                       "(그만두려면 '중단' 입력)")
            if ask(msg) in ("중단", "q", "stop"): raise Stopped(f"{why} 화면에서 대표가 중단")

    def _blocked(self, page):
        url = (page.url or "").lower()
        if any(h in url for h in LOGIN_URL_HINTS): return "로그인"
        try:
            if page.locator("input[type=password]:visible").count() > 0: return "로그인"
        except Exception: pass
        try:
            if any(any(h in (f.url or "").lower() for h in CAPTCHA_FRAME_HINTS) for f in page.frames[1:]): return "봇확인"
            if page.get_by_text(CAPTCHA_TEXT).count() > 0: return "봇확인"
        except Exception: pass
        return None

    def human_step(self, page, label, why="찾지 못했습니다"):
        """화면 문구가 바뀌어 단추를 못 찾으면, 대표가 그 단계만 직접 하고 엔터 → 이어서 진행."""
        self.shot(page, f"직접_{label}")
        a = ask(f"[{self.site}] '{label}' 단계를 {why}(화면 문구가 바뀌었을 수 있음).\n"
                f"대표님이 크롬 창에서 '{label}'을(를) 직접 해 주시고 엔터를 눌러 주세요. (건너뛰기: '건너뛰기', 그만두기: '중단')")
        if a in ("중단", "q", "stop"): raise Stopped(f"'{label}' 단계에서 대표가 중단")
        self.log(f"'{label}' 단계: 대표가 직접 처리" + (" (건너뜀)" if a == "건너뛰기" else ""))

    # ---- 찾기·누르기·쓰기 ----
    def find(self, page, label, candidates, timeout=8000):
        """후보(화면 글자 기준 선택자)를 차례로 시도해 처음 보이는 것을 돌려준다. 없으면 None."""
        self.guard(page, label)
        per = max(1500, timeout // max(1, len(candidates)))
        for make in candidates:
            try:
                loc = make(page).first
                loc.wait_for(state="visible", timeout=per)
                return loc
            except Exception:
                continue
        return None

    def click(self, page, label, candidates, timeout=8000, optional=False):
        loc = self.find(page, label, candidates, timeout)
        if loc is None:
            if optional: self.log(f"'{label}' 없음(선택 단계라 넘어감)"); return False
            self.human_step(page, label); return False
        loc.click(); page.wait_for_timeout(800)
        self.shot(page, label); return True

    def type_into(self, page, label, candidates, text, clear=True, timeout=10000):
        """글 넣기. 비밀번호 칸이면 절대 쓰지 않는다."""
        loc = self.find(page, label, candidates, timeout)
        if loc is None: self.human_step(page, label + " 입력"); return False
        try:
            if (loc.get_attribute("type") or "").lower() == "password":
                raise Stopped("비밀번호 칸에 글을 쓰려 함 — 프로그램이 멈춤(설계상 금지)")
        except Stopped: raise
        except Exception: pass
        loc.click()
        if clear:
            page.keyboard.press("Control+A"); page.keyboard.press("Delete")
        page.keyboard.insert_text(text)  # 한 번에 붙여 넣기(한글 입력기 문제 피함)
        page.wait_for_timeout(500)
        self.shot(page, label); return True

    def upload_file(self, page, label, input_candidates, path, button_candidates=None, timeout=15000):
        """파일 넣기: 숨은 <input type=file>이 있으면 바로, 없으면 단추를 눌러 파일 선택 창으로."""
        self.guard(page, label)
        for make in input_candidates:
            try:
                loc = make(page)
                if loc.count() > 0:
                    loc.first.set_input_files(path); page.wait_for_timeout(1500)
                    self.shot(page, label); return True
            except Exception: continue
        for make in (button_candidates or []):
            try:
                with page.expect_file_chooser(timeout=timeout) as fc:
                    make(page).first.click()
                fc.value.set_files(path); page.wait_for_timeout(1500)
                self.shot(page, label); return True
            except Exception: continue
        self.human_step(page, f"{label} ({os.path.basename(path)})"); return False

    def wait_text(self, page, label, pattern, timeout=600000):
        """업로드·처리 완료 같은 글자가 뜰 때까지 기다림(못 보면 기록만 하고 진행)."""
        try:
            page.get_by_text(pattern).first.wait_for(state="visible", timeout=timeout)
            self.shot(page, label); return True
        except Exception:
            self.log(f"'{label}' 표시를 못 봄 — 화면을 확인해 주세요"); self.shot(page, label + "_미확인"); return False

    # ---- 마지막 단추 ----
    def final(self, page, label, candidates):
        """최종 예약 단추. 기본(확인 모드)은 누르지 않고 멈춘다."""
        loc = self.find(page, label, candidates, 10000)
        sc = self.plan["schedule"]
        if loc is not None:
            try: loc.evaluate("e => { e.style.outline = '4px solid #ff2d55'; e.scrollIntoView({block:'center'}); }")
            except Exception: pass
        self.shot(page, f"최종확인_{label}")
        if not self.final_click or loc is None:
            a = ask(f"[{self.site}] 확인 모드: '{label}' 단추 바로 앞에서 멈췄습니다(빨간 테두리).\n"
                    f"예약 시각 {sc['date']} {sc['time']}(서울), 제목·설명·파일·썸네일을 화면에서 확인해 주세요.\n"
                    f"맞으면 대표님이 직접 '{label}'을(를) 누르고 '완료'를 입력, 그만두려면 '중단'을 입력해 주세요.")
            self.result = "대표가 직접 예약 완료" if a == "완료" else "예약 안 함(대표 중단/미확인)"
            self.shot(page, "최종_후"); self.log(self.result); return a == "완료"
        loc.click(); page.wait_for_timeout(3000)
        self.shot(page, "최종_후")
        self.guard(page, "예약 후")
        self.result = "프로그램이 예약 단추를 누름(화면에서 예약 목록 확인 필요)"; self.log(self.result)
        return True

    def close(self):
        self.log(f"끝: {self.result}  (기록 폴더: {self.dir})"); self.logf.close()


def open_browser(pw, profile_dir=DEFAULT_PROFILE):
    """대표 데스크톱의 크롬(설치된 것)을 업로드 전용 프로필로 연다. 다른 크롬 창이 이 프로필을 쓰고 있으면 실패하니 닫고 실행."""
    os.makedirs(profile_dir, exist_ok=True)
    if os.path.exists(os.path.join(profile_dir, "SingletonLock")) and os.name != "nt":
        print("알림: 같은 프로필 크롬이 이미 열려 있을 수 있습니다. 닫고 다시 실행하세요.")
    return pw.chromium.launch_persistent_context(
        user_data_dir=profile_dir, channel="chrome", headless=False,
        locale="ko-KR", timezone_id="Asia/Seoul", no_viewport=True,
        args=["--start-maximized"], accept_downloads=False,
    )


def copy_profile(src, dst):
    """(대안, 권장하지 않음) 평소 크롬 프로필 복사. 윈도우 크롬은 로그인 정보가 원래 위치·계정에 묶여 암호화돼
    복사본에서는 로그인이 풀리는 경우가 많다. 기본은 login_once.bat로 업로드 전용 프로필에 한 번 로그인하는 방식."""
    if os.path.exists(dst): raise SystemExit(f"이미 있음: {dst}")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("Cache", "Code Cache", "GPUCache", "Service Worker",
                                                             "Singleton*", "*.lock"))
