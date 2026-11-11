"""틱톡 Studio 예약 (한국어 화면 기준 뼈대)

사람이 하던 흐름(11/10): TikTok Studio 업로드 → 영상 선택 → 설명 → 게시 시간 '예약' → 날짜·시간 → [예약] ← 직전 정지
틱톡은 지금부터 15분 뒤 ~ 10일 안에서만 예약된다(사이트 안내 기준, 바뀔 수 있음).
TODO 표시 = 실제 화면에서 아직 확인 못 한 선택자.
"""
import re

URL = "https://www.tiktok.com/tiktokstudio/upload?from=upload"


def run(page, plan, s):
    it = plan["sites"]["tiktok"]; sc = plan["schedule"]
    page.goto(URL, wait_until="domcontentloaded"); page.wait_for_timeout(4000)
    s.guard(page, "스튜디오 열기"); s.shot(page, "업로드_첫화면")

    # 1) 영상 넣기
    s.upload_file(page, "영상 파일 넣기", [lambda p: p.locator("input[type=file][accept*=video]"),
                                         lambda p: p.locator("input[type=file]")], plan["video"],
                  [lambda p: p.get_by_role("button", name=re.compile("동영상 선택|파일 선택"))])
    s.wait_text(page, "업로드 완료", re.compile("업로드됨|업로드 완료|Uploaded"), timeout=300000)

    # 2) 설명 — 파일 이름이 미리 들어가 있으므로 지우고 넣음
    s.type_into(page, "설명", [
        lambda p: p.locator("div[contenteditable=true]").first,  # TODO: 설명 편집기 확인(DraftJS)
        lambda p: p.get_by_role("textbox", name=re.compile("설명")),
    ], it["caption"])
    page.keyboard.press("Escape")  # 해시태그 추천 목록 닫기 — TODO: '#태그'가 해시태그로 바뀌었는지 화면 확인

    # 3) 게시 시간: 예약
    s.click(page, "예약 선택", [
        lambda p: p.get_by_role("radio", name=re.compile(r"^예약")),
        lambda p: p.get_by_text("예약", exact=True),  # TODO
    ])
    # 처음 예약할 때 뜨는 안내창(허용/확인)
    s.click(page, "예약 안내창 확인", [lambda p: p.get_by_role("button", name=re.compile(r"^(허용|확인)$"))],
            timeout=3000, optional=True)

    # 4) 날짜·시간 — 틱톡은 달력·시계 고르기 방식이라 입력이 까다로움
    #    TODO: 날짜 칸 클릭 → 달력에서 날짜 숫자 클릭, 시간 칸 클릭 → 시/분 목록에서 고르기
    y, m, d = sc["date"].split("-"); hh, mm = sc["time"].split(":")
    s.click(page, "날짜 칸", [lambda p: p.locator("input[value*='-']").first,  # TODO (값 예: 2026-11-12)
                            lambda p: p.get_by_role("textbox", name=re.compile("날짜"))], optional=True)
    s.click(page, f"날짜 {int(d)}일", [lambda p: p.get_by_role("button", name=re.compile(rf"^{int(d)}$")),  # TODO
                                     lambda p: p.get_by_text(str(int(d)), exact=True)], optional=True)
    s.click(page, "시간 칸", [lambda p: p.locator("input[value*=':']").first], optional=True)  # TODO (값 예: 12:00)
    s.click(page, f"시 {hh}", [lambda p: p.get_by_text(hh, exact=True)], optional=True)  # TODO: 시 목록
    s.click(page, f"분 {mm}", [lambda p: p.get_by_text(mm, exact=True).last], optional=True)  # TODO: 분 목록
    s.shot(page, f"예약시각_입력후(목표 {sc['date']} {sc['time']} — 화면 확인)")
    print(f"\n※ 틱톡 날짜·시간 고르기는 아직 확실하지 않습니다. 화면에 {sc['date']} {sc['time']}이 맞는지 꼭 봐 주세요.")

    # 5) 최종 [예약] — 기본은 누르지 않고 멈춤
    return s.final(page, "예약", [
        lambda p: p.get_by_role("button", name=re.compile(r"^예약$")),
        lambda p: p.get_by_role("button", name=re.compile(r"^(게시|예약하기)$")),  # TODO
    ])
