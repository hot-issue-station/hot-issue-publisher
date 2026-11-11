"""덕심저장소 쇼츠 예약 업로드 — 실행기 (대표 데스크톱, 윈도우)

사용: run_confirm.bat 위에 기획 JSON 파일을 끌어다 놓기 (= python run.py 기획.json)
  python run.py 기획.json --slot 점심 --sites youtube,tiktok
  python run.py 기획.json --final-click      # (권장 안 함) 예약 단추까지 프로그램이 누름
  python run.py --plan outbox/<꾸러미>/upload_plan.json   # 게시 꾸러미(package.py)의 계획 파일로 바로 진행

순서: 업로드 계획 점검(5줄 점검표 포함) → ❌ 있으면 여기서 끝 → 대표 확인 → 크롬(업로드 전용 프로필) 열기
→ 사이트마다 새 탭에서 진행 → 예약 단추 직전에서 멈춤 → 대표가 보고 직접 누름 → 기록(logs/) 남김
"""
import argparse, importlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upload_plan as up  # noqa: E402
import common  # noqa: E402

ORDER = ["youtube", "tiktok", "meta", "x"]


def main(argv=None):
    if os.name == "nt":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    ap = argparse.ArgumentParser(description="덕심저장소 쇼츠 예약 업로드(기본: 확인 모드)")
    ap.add_argument("spec", nargs="?"); ap.add_argument("--plan", help="package.py 가 만든 upload_plan.json")
    ap.add_argument("--slot"); ap.add_argument("--date"); ap.add_argument("--sites")
    ap.add_argument("--profile", default=common.DEFAULT_PROFILE, help="업로드 전용 크롬 프로필 폴더")
    ap.add_argument("--final-click", action="store_true", help="예약 단추까지 누름(기본은 직전 정지)")
    a = ap.parse_args(argv)
    if a.plan:   # 게시 꾸러미: 계획 파일을 다시 점검하고 그대로 씀(올릴 곳은 계획에 든 곳)
        sys.path.insert(0, os.path.dirname(HERE)); import package
        plan, probs = package.check_plan(a.plan)
        if plan: up.show(plan)
        if probs:
            print("\n계획 파일 점검을 통과하지 못해 업로드하지 않습니다:\n  - " + "\n  - ".join(probs)); return 1
        sites = list(plan["sites"])
        if a.sites: sites = [x.strip() for x in a.sites.split(",") if x.strip() in plan["sites"]]
    elif not a.spec: ap.error("기획 JSON 또는 --plan 을 주세요")
    elif a.sites: sites = [x.strip() for x in a.sites.split(",")]
    elif sys.stdin.isatty():  # 끌어다 놓기로 실행했을 때: 올릴 곳을 번호로 고름
        pick = common.ask("올릴 곳을 골라 주세요. 엔터 = 전부 / 번호 여러 개 가능(예: 1 또는 13)\n"
                          "  1) 유튜브  2) 틱톡  3) 인스타·페이스북  4) X")
        sites = [ORDER[int(c) - 1] for c in pick if c in "1234"] or ORDER
    else: sites = ORDER

    if not a.plan:
        plan = up.build_plan(a.spec, a.slot, a.date, sites, ask=(a.slot is None and a.date is None and sys.stdin.isatty()))
        up.show(plan); up.save(plan)
    if not plan["ok"]:
        print("\n점검을 통과하지 못해 업로드하지 않습니다."); return 1

    mode = "자동 예약(예약 단추까지 누름)" if a.final_click else "확인 모드(예약 단추 직전에서 멈춤)"
    if a.final_click:
        if common.ask("자동 예약 모드입니다. 계정 제한 위험이 더 큽니다. 정말 진행하려면 '예'를 입력하세요.") != "예":
            a.final_click = False; mode = "확인 모드(예약 단추 직전에서 멈춤)"
    if common.ask(f"위 내용으로 {', '.join(up.SITE_KO[s] for s in sites)} 예약을 시작할까요? [{mode}]\n"
                  "시작하려면 엔터, 그만두려면 '중단'") in ("중단", "q"):
        return 1

    from playwright.sync_api import sync_playwright
    results = {}
    with sync_playwright() as pw:
        ctx = common.open_browser(pw, a.profile)
        for site in [s for s in ORDER if s in sites]:
            mod = importlib.import_module(site)
            s = common.Session(site, plan, final_click=a.final_click)
            page = ctx.new_page()
            try:
                mod.run(page, plan, s)
            except common.Stopped as e:
                s.result = f"중단: {e}"
            except Exception as e:  # 한 사이트가 실패해도 다음 사이트로
                s.shot(page, "오류"); s.result = f"오류: {e.__class__.__name__}: {e}"
            finally:
                s.close(); results[site] = s.result
        common.ask("모든 사이트를 마쳤습니다. 크롬 창을 확인하신 뒤 엔터를 누르면 창을 닫습니다.")
        ctx.close()

    print("\n■ 결과")
    for k, v in results.items(): print(f"  {up.SITE_KO[k]}: {v}")
    print(f"  유튜브 첫 댓글: 공개({plan['schedule']['date']} {plan['schedule']['time']}) 뒤 대표가 확인하고 달아 고정")
    rp = os.path.join(common.LOG_ROOT, f"{plan['name']}_결과.json")
    json.dump({"schedule": plan["schedule"], "results": results}, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  결과 파일: {rp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
