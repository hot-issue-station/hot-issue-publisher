"""Meta 비즈니스 스위트 릴스 예약 — 인스타그램 + 페이스북 동시 (한국어 화면 기준 뼈대)

사람이 하던 흐름(11/10): 비즈니스 스위트 → 릴스 만들기 → 게시 위치(페이스북·인스타 둘 다) → 동영상 추가
→ 설명 → (커버) → 다음 → 예약 → 날짜·시간 → [예약] ← 직전 정지
비즈니스 스위트는 최대 29일 뒤까지 예약된다(사이트 안내 기준, 바뀔 수 있음).
TODO 표시 = 실제 화면에서 아직 확인 못 한 선택자.
"""
import re

URL = "https://business.facebook.com/latest/reels_composer"  # TODO: 안 열리면 홈 → '릴스 만들기'


def _date_text(d):  # TODO: 날짜 칸 형식 확인 (예: 2026. 11. 12.)
    y, m, dd = d.split("-"); return f"{int(y)}. {int(m)}. {int(dd)}."


def _time_text(t):  # TODO: 시간 칸 형식 확인 (예: 오후 12:00 / 12:00)
    h, m = map(int, t.split(":")); return f"{'오전' if h < 12 else '오후'} {h % 12 or 12}:{m:02d}"


def run(page, plan, s):
    it = plan["sites"]["meta"]; sc = plan["schedule"]
    page.goto(URL, wait_until="domcontentloaded"); page.wait_for_timeout(5000)
    s.guard(page, "비즈니스 스위트 열기"); s.shot(page, "릴스_만들기_첫화면")
    if "reels_composer" not in page.url:
        s.click(page, "릴스 만들기", [lambda p: p.get_by_role("button", name=re.compile("릴스 만들기")),
                                    lambda p: p.get_by_text("릴스 만들기", exact=True)])

    # 1) 게시 위치: 페이스북 + 인스타그램 둘 다 켜져 있는지
    for name in ("Facebook|페이스북", "Instagram|인스타그램"):
        loc = s.find(page, f"게시 위치 {name}", [lambda p, n=name: p.get_by_role("checkbox", name=re.compile(n))], 4000)
        if loc is not None:
            try:
                if not loc.is_checked(): loc.check(); s.log(f"게시 위치 {name} 켬")
            except Exception: pass
    s.shot(page, "게시 위치(페이스북·인스타 둘 다 선택됐는지 확인)")  # TODO: 체크 상자가 아닌 목록 선택일 수 있음

    # 2) 동영상 추가
    s.upload_file(page, "동영상 추가", [lambda p: p.locator("input[type=file][accept*=video]"),
                                      lambda p: p.locator("input[type=file]")], plan["video"],
                  [lambda p: p.get_by_role("button", name=re.compile("동영상 추가|영상 추가"))])
    page.wait_for_timeout(5000)

    # 3) 설명
    s.type_into(page, "설명", [
        lambda p: p.get_by_role("textbox", name=re.compile("설명|릴스 설명")),
        lambda p: p.locator("div[contenteditable=true]").first,  # TODO
    ], it["caption"])

    # 4) 커버(썸네일) — 선택 단계. 인스타 커버 업로드가 안 되면 영상 프레임 중 하나를 사람이 고름
    if it.get("thumb"):
        s.upload_file(page, "커버 이미지", [lambda p: p.locator("input[type=file][accept*=image]")], it["thumb"],
                      [lambda p: p.get_by_role("button", name=re.compile("썸네일|커버|이미지 업로드"))])  # TODO

    # 5) 다음 → 예약
    s.click(page, "다음", [lambda p: p.get_by_role("button", name=re.compile(r"^다음$"))])
    s.click(page, "예약 선택", [
        lambda p: p.get_by_role("radio", name=re.compile(r"^예약")),
        lambda p: p.get_by_text(re.compile(r"^예약(하기)?$")),  # TODO
    ])
    s.type_into(page, f"날짜 {sc['date']}", [
        lambda p: p.get_by_role("textbox", name=re.compile("날짜")),
        lambda p: p.get_by_placeholder(re.compile(r"yyyy|년|\d{4}")),  # TODO
    ], _date_text(sc["date"]))
    s.type_into(page, f"시간 {sc['time']}", [
        lambda p: p.get_by_role("textbox", name=re.compile("시간")),  # TODO: 시·분·오전오후가 따로일 수 있음
    ], _time_text(sc["time"]))
    page.keyboard.press("Tab")
    s.shot(page, f"예약시각_입력후(목표 {sc['date']} {sc['time']} — 화면 확인)")

    # 6) 최종 [예약] — 기본은 누르지 않고 멈춤
    return s.final(page, "예약", [lambda p: p.get_by_role("button", name=re.compile(r"^예약(하기)?$"))])
