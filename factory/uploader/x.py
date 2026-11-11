"""X(트위터) 게시물 예약 (한국어 화면 기준 뼈대)

사람이 하던 흐름(11/10): 게시하기 → 글 → 영상 첨부 → 예약(달력 단추) → 날짜·시간 → 확인 → [예약하기] ← 직전 정지
X는 이용약관에서 API 밖의 자동 조작을 특히 엄격하게 금지한다. 위험이 가장 큰 곳이라 확인 모드로만 쓰기를 권장.
TODO 표시 = 실제 화면에서 아직 확인 못 한 선택자.
"""
import re

URL = "https://x.com/compose/post"


def run(page, plan, s):
    it = plan["sites"]["x"]; sc = plan["schedule"]
    page.goto(URL, wait_until="domcontentloaded"); page.wait_for_timeout(4000)
    s.guard(page, "X 열기"); s.shot(page, "게시하기_첫화면")

    # 1) 글
    s.type_into(page, "글", [
        lambda p: p.get_by_role("textbox", name=re.compile("게시물 텍스트|무슨 일이")),
        lambda p: p.locator("[data-testid=tweetTextarea_0]"),
    ], it["text"])

    # 2) 영상 첨부 + 처리 대기
    s.upload_file(page, "영상 첨부", [lambda p: p.locator("input[data-testid=fileInput]"),
                                    lambda p: p.locator("input[type=file]")], plan["video"])
    s.wait_text(page, "영상 처리", re.compile("업로드됨|100%|Uploaded"), timeout=120000)  # TODO: 처리 완료 표시 확인

    # 3) 예약 창
    s.click(page, "예약 단추", [
        lambda p: p.get_by_role("button", name=re.compile("게시물 예약|예약하기|예약")),
        lambda p: p.locator("[data-testid=scheduleOption]"),
    ])
    y, m, d = sc["date"].split("-"); hh, mm = map(int, sc["time"].split(":"))
    # 날짜·시간은 고르는 목록(select). 보이는 이름(월/일/연도/시/분/오전·오후)으로 고름 — TODO: 목록 이름 확인
    picks = [("월", rf"^{int(m)}월$|^{int(m)}$"), ("일", rf"^{int(d)}$"), ("연도", rf"^{y}$"),
             ("시", rf"^{hh % 12 or 12}$"), ("분", rf"^{mm:02d}$|^{mm}$"), ("오전/오후", "^오전$|^AM$" if hh < 12 else "^오후$|^PM$")]
    for label, pat in picks:
        loc = s.find(page, f"예약 {label}", [lambda p, l=label: p.get_by_role("combobox", name=re.compile(l)),
                                            lambda p, l=label: p.get_by_label(re.compile(l))], 3000)
        if loc is None: s.log(f"예약 {label} 목록 못 찾음 — 화면에서 직접 맞춰 주세요"); continue
        try:
            opts = loc.locator("option").all_inner_texts()
            want = next((o for o in opts if re.search(pat, o.strip())), None)
            if want: loc.select_option(label=want)
            else: s.log(f"예약 {label}: 맞는 값 없음 {pat}")
        except Exception as e: s.log(f"예약 {label} 고르기 실패({e})")
    s.shot(page, f"예약시각_입력후(목표 {sc['date']} {sc['time']} — 화면 확인)")
    s.click(page, "예약 확인", [lambda p: p.get_by_role("button", name=re.compile(r"^확인$")),
                              lambda p: p.locator("[data-testid=scheduledConfirmationPrimaryAction]")])

    # 4) 최종 [예약하기] — 기본은 누르지 않고 멈춤
    return s.final(page, "예약하기", [lambda p: p.locator("[data-testid=tweetButton]"),
                                    lambda p: p.get_by_role("button", name=re.compile(r"^예약하기$"))])
