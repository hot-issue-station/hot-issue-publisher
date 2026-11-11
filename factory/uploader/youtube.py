"""유튜브 Studio 쇼츠 예약 (한국어 화면 기준 뼈대)

사람이 하던 흐름(11/10): Studio → 만들기 → 동영상 업로드 → 제목·설명·썸네일 → 아동용 아님 → 태그
→ 다음 ×3 → 공개 상태 '예약' → 날짜·시간 → [예약] ← 여기 직전에서 멈춤(확인 모드)
첫 댓글 고정은 예약 영상이 공개된 뒤 사람이 확인하고 단다(공개 전에는 댓글을 달 수 없음).

TODO 표시 = 실제 화면에서 아직 확인 못 한 선택자. 첫 실행 때 logs/ 스크린샷을 보고 고친다.
"""
import os, re

URL = "https://studio.youtube.com"


def _thumb_for_youtube(path, s):
    """유튜브 썸네일은 2MB 이하. 넘으면 같은 폴더 logs에 JPG로 줄여 쓴다."""
    if not path or not os.path.exists(path): return None
    if os.path.getsize(path) <= 2 * 1024 * 1024: return path
    from PIL import Image
    out = os.path.join(s.dir, "thumb_youtube.jpg")
    Image.open(path).convert("RGB").save(out, quality=90)
    s.log(f"썸네일이 2MB를 넘어 JPG로 줄임: {out}")
    return out


def _date_text(d):  # '2026. 11. 12.' 형식 — TODO: 한국어 Studio 날짜 칸 형식 확인('2026. 11. 12.' 또는 '2026년 11월 12일')
    y, m, dd = d.split("-"); return f"{int(y)}. {int(m)}. {int(dd)}."


def _time_text(t):  # '오후 12:00' 형식 — TODO: 시간 목록 표기 확인
    h, m = map(int, t.split(":")); ap = "오전" if h < 12 else "오후"; h12 = h % 12 or 12
    return f"{ap} {h12}:{m:02d}"


def run(page, plan, s):
    it = plan["sites"]["youtube"]; sc = plan["schedule"]
    page.goto(URL, wait_until="domcontentloaded"); page.wait_for_timeout(3000)
    s.guard(page, "스튜디오 열기"); s.shot(page, "스튜디오_첫화면")

    # 1) 업로드 창 열기
    s.click(page, "만들기", [
        lambda p: p.get_by_role("button", name=re.compile(r"^만들기$")),
        lambda p: p.locator("#create-icon"),  # TODO: 화면 확인
    ])
    s.click(page, "동영상 업로드", [
        lambda p: p.get_by_role("menuitem", name=re.compile("동영상 업로드")),
        lambda p: p.get_by_text("동영상 업로드", exact=True),
    ])
    # 2) 파일 넣기
    s.upload_file(page, "영상 파일 넣기", [lambda p: p.locator("input[type=file][name=Filedata]"),
                                         lambda p: p.locator("input[type=file]")], plan["video"],
                  [lambda p: p.get_by_role("button", name=re.compile("파일 선택"))])
    page.wait_for_timeout(5000)

    # 3) 세부정보: 제목·설명
    s.type_into(page, "제목", [
        lambda p: p.get_by_role("textbox", name=re.compile("제목")),
        lambda p: p.locator("#title-textarea #textbox"),  # TODO: 화면 확인
    ], it["title"])
    s.type_into(page, "설명", [
        lambda p: p.get_by_role("textbox", name=re.compile("설명|시청자에게")),
        lambda p: p.locator("#description-textarea #textbox"),  # TODO
    ], it["description"])

    # 4) 썸네일
    th = _thumb_for_youtube(it.get("thumb"), s)
    if th:
        s.upload_file(page, "썸네일", [lambda p: p.locator("input#file-loader")],  # TODO: 썸네일용 file 입력 확인
                      th, [lambda p: p.get_by_role("button", name=re.compile("썸네일 업로드|파일 업로드")),
                           lambda p: p.get_by_text(re.compile("썸네일 업로드"))])

    # 5) 시청자층: 아동용 아님
    s.click(page, "아동용 아님", [
        lambda p: p.get_by_role("radio", name=re.compile(r"아니요.*아동용")),
        lambda p: p.locator("tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]"),  # TODO
    ])

    # 6) 태그(자세히 보기 안에 있음)
    if it.get("tags"):
        s.click(page, "자세히 보기", [lambda p: p.get_by_role("button", name=re.compile("자세히 보기|더보기"))], optional=True)
        s.type_into(page, "태그", [
            lambda p: p.get_by_role("textbox", name=re.compile("태그")),
            lambda p: p.get_by_placeholder(re.compile("태그")),  # TODO
        ], ",".join(it["tags"]) + ",", clear=False)

    # 7) 다음 ×3 (세부정보 → 동영상 요소 → 검토 → 공개 상태)
    for k in range(3):
        s.click(page, f"다음 {k + 1}", [lambda p: p.get_by_role("button", name=re.compile(r"^다음$")),
                                       lambda p: p.locator("#next-button")])
        page.wait_for_timeout(1500)

    # 8) 공개 상태: 예약
    s.click(page, "예약 열기", [
        lambda p: p.get_by_role("radio", name=re.compile(r"^예약")),
        lambda p: p.locator("#second-container-expand-button"),  # TODO: '예약' 펼치기 단추
        lambda p: p.get_by_text("예약", exact=True),
    ])
    # 날짜
    s.click(page, "날짜 칸", [lambda p: p.locator("#datepicker-trigger"),  # TODO
                            lambda p: p.get_by_role("button", name=re.compile(r"\d{4}\. ?\d"))])
    s.type_into(page, f"날짜 {sc['date']}", [
        lambda p: p.locator("tp-yt-paper-dialog input").first,  # TODO: 날짜 입력칸
        lambda p: p.get_by_role("textbox", name=re.compile("날짜")),
    ], _date_text(sc["date"]))
    page.keyboard.press("Enter")
    # 시간
    s.type_into(page, f"시간 {sc['time']}", [
        lambda p: p.locator("#time-of-day-container input"),  # TODO
        lambda p: p.get_by_role("combobox", name=re.compile("시간")),
    ], _time_text(sc["time"]))
    page.keyboard.press("Enter"); page.wait_for_timeout(800)
    s.shot(page, "예약시각_입력후(화면에서 날짜·시간 확인)")

    # 9) 업로드·확인 완료 대기(확인 모드에선 기다리지 않아도 되지만 화면 기록용)
    s.wait_text(page, "업로드 상태", re.compile("업로드 완료|확인 완료|처리 완료|검사 완료"), timeout=180000)

    # 10) 최종 [예약] — 기본은 누르지 않고 멈춤
    ok = s.final(page, "예약", [lambda p: p.locator("#done-button"),
                               lambda p: p.get_by_role("button", name=re.compile(r"^예약$"))])
    if ok:
        s.log(f"첫 댓글은 {sc['date']} {sc['time']} 공개 후 대표가 확인하고 달아 고정: \"{it['first_comment']}\"")
    return ok
