"""카드 문구(round JSON)로 카드 7장(JPG)과 게시 묶음을 만든다.

사용법:  python scripts/make_post.py rounds/20261028_PM.json [--approve3 "대표 (채팅 승인)"]
결과:    posts/YYYYMMDD_SLOT/01.jpg … 07.jpg, caption.txt, post.json

round JSON 형식(모든 문구는 승인 2를 거친 최종 문구):
{
  "date": "2026-10-28", "slot": "PM",            # AM 07:00 · PM 15:00 · NT 23:30
  "category": "국내",                             # 1장 분야 태그
  "hook": "…", "sub": "…",                        # 1장
  "summary": "…",                                 # 2장
  "facts": [{"title": "…", "desc": "…", "source": "경향신문 · 2026.10.27"}, ×3],   # 3~5장
  "interp": "…", "interpSub": "…",                # 6장
  "sources": [{"outlet": "…", "title": "…", "date": "2026.10.27", "url": "https://…"}],  # 7장
  "cta": "… 저장해 두세요",                        # 7장 유도 문구
  "caption": "…",                                 # 해시태그 포함 캡션 전체
  "topic": "…"
}
카드 모양은 카드 템플릿 캔버스(케인 AM 시험 카드)와 같다. 글꼴: Noto Sans CJK KR.
"""
import argparse
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLOTS = {"AM": ("아침", "07:00"), "PM": ("오후", "15:00"), "NT": ("밤", "23:30")}
NAVY, CYAN, PINK, VIOLET = "#0B1220", "#35E0FF", "#FF4FA3", "#6C7BFF"
LOGO = ('<svg width="68" height="68" viewBox="0 0 68 68" style="display:block">'
        '<path d="M25.51 43.51 A12 12 0 0 1 42.49 43.51" fill="none" stroke="#35E0FF" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M18.44 36.44 A22 22 0 0 1 49.56 36.44" fill="none" stroke="#6C7BFF" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M11.37 29.37 A32 32 0 0 1 56.63 29.37" fill="none" stroke="#FF4FA3" stroke-width="5" stroke-linecap="round"/>'
        '<circle cx="34" cy="52" r="5" fill="#FFC857"/></svg>')
E = html.escape


def frame(inner, date_label, page, footer_right="", light=False, deco=""):
    bg, fg, muted = (CYAN, NAVY, "#123049") if light else (NAVY, "#F4F7FF", "#A9B6CF")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;word-break:keep-all;font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif}}</style></head><body>
<div style="position:relative;width:1080px;height:1350px;overflow:hidden;background:{bg};color:{fg}">{deco}
<div style="position:relative;width:100%;height:100%;box-sizing:border-box;padding:96px;display:flex;flex-direction:column">
<div style="display:flex;justify-content:space-between;align-items:center">
<div style="display:flex;align-items:center;gap:20px">{LOGO}<div style="font-size:36px;font-weight:700;color:{fg}">hot.issue.station</div></div>
<div style="font-size:32px;color:{muted}">{date_label}</div></div>
{inner}
<div style="display:flex;justify-content:space-between;align-items:center;font-size:32px;color:{muted}">
<div>{page} / 7</div><div>{footer_right}</div></div></div></div></body></html>"""


def rings(colors, sizes, offset_ratio=0.5):
    out = ""
    for c, s in zip(colors, sizes):
        off = int(s * offset_ratio)
        out += (f'<div style="position:absolute;right:-{off}px;bottom:-{off}px;width:{s}px;height:{s}px;'
                f'box-sizing:border-box;border-radius:50%;border:6px solid {c}"></div>')
    return out


def dots(i):
    return "".join(f'<div style="width:24px;height:24px;border-radius:50%;background:{CYAN if k == i else "#2A3A59"}"></div>'
                   for k in range(3))


def cards(r):
    m, d = r["date"][5:7], r["date"][8:10]
    label = f"{m}.{d} · {SLOTS[r['slot']][0]}"
    out = []
    # 1 훅
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:48px">
<div style="align-self:flex-start;padding:14px 32px;border:3px solid {CYAN};border-radius:999px;color:{CYAN};font-size:36px;font-weight:700">{E(r['category'])}</div>
<div style="font-size:108px;font-weight:900;line-height:1.25">{E(r['hook']).replace(', ', ',<br>', 1) if len(r['hook']) > 9 else E(r['hook'])}</div>
<div style="display:flex;gap:12px"><div style="width:160px;height:16px;border-radius:8px;background:{CYAN}"></div><div style="width:48px;height:16px;border-radius:8px;background:{PINK}"></div></div>
<div style="font-size:52px;font-weight:500;line-height:1.5;color:#C9D4EA;max-width:820px">{E(r['sub'])}</div></div>""",
                     label, 1, "밀어서 다음 장 →", deco=rings([VIOLET, PINK, CYAN], [900, 680, 460])))
    # 2 요약
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px">
<div style="display:flex;align-items:center;gap:20px"><div style="width:64px;height:8px;border-radius:4px;background:{PINK}"></div><div style="font-size:44px;font-weight:700;color:{CYAN}">한 줄 요약</div></div>
<div style="padding:80px 72px;border:3px solid #2A3A59;border-radius:40px;background:#151F33"><div style="font-size:72px;font-weight:700;line-height:1.45">{E(r['summary'])}</div></div>
<div style="font-size:44px;line-height:1.5;color:#C9D4EA">이어서 핵심 사실 3가지를 알려드려요 →</div></div>""", label, 2))
    # 3~5 사실
    for i, f in enumerate(r["facts"][:3]):
        out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:32px">
<div style="display:flex;align-items:baseline;gap:24px"><div style="font-size:140px;font-weight:900;line-height:1;color:{CYAN}">{i + 1:02d}</div><div style="font-size:40px;font-weight:700;color:#A9B6CF">핵심 사실</div></div>
<div style="font-size:68px;font-weight:900;line-height:1.35">{E(f['title'])}</div>
<div style="width:100%;height:2px;background:#2A3A59"></div>
<div style="font-size:48px;line-height:1.65;color:#D7E0F2">{E(f['desc'])}</div>
<div style="font-size:36px;color:#A9B6CF">출처 {E(f['source'])}</div></div>""",
                         label, 3 + i, f'<div style="display:flex;gap:16px">{dots(i)}</div>'))
    # 6 해석
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="font-size:48px;font-weight:900">그래서, 나에게는?</div>
<div style="font-size:84px;font-weight:900;line-height:1.35">{E(r['interp'])}</div>
<div style="font-size:46px;font-weight:500;line-height:1.55;color:#123049">{E(r['interpSub'])}</div></div>""",
                     label, 6, light=True, deco=rings([NAVY] * 3, [640, 440, 240])))
    # 7 출처
    nums = "①②③④"
    src = "".join(f'<div style="padding:22px 0;border-bottom:2px solid #2A3A59;font-size:36px;line-height:1.4;color:#D7E0F2">'
                  f'{nums[k]} {E(s["outlet"])} · {E(s["title"])} · {E(s["date"])}</div>' for k, s in enumerate(r["sources"][:4]))
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="display:flex;align-items:center;gap:20px"><div style="width:64px;height:8px;border-radius:4px;background:{PINK}"></div><div style="font-size:44px;font-weight:700;color:{CYAN}">출처</div></div>
<div style="display:flex;flex-direction:column">{src}</div>
<div style="padding:56px 64px;border:3px solid {CYAN};border-radius:40px;background:#151F33;display:flex;flex-direction:column;gap:32px">
<div style="font-size:60px;font-weight:900;line-height:1.35">{E(r['cta'])}</div>
<div style="display:flex;gap:24px"><div style="padding:20px 56px;border-radius:999px;background:{CYAN};color:{NAVY};font-size:48px;font-weight:900">저장</div>
<div style="padding:20px 56px;border-radius:999px;background:{PINK};color:{NAVY};font-size:48px;font-weight:900">팔로우</div></div></div>
<div style="font-size:32px;line-height:1.5;color:#A9B6CF">광고·협찬 없음</div></div>""", label, 7, "매일 따뜻한 이슈는 @hot.issue.station"))
    return out


def render(pages, outdir):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        overflow = []
        for i, h in enumerate(pages, 1):
            pg.set_content(h)
            pg.wait_for_timeout(200)
            # 글이 칸을 넘치면(세로 넘침) 알려 준다
            if pg.evaluate("Array.from(document.querySelectorAll('div')).some(d => d.style.flex.startsWith('1') && d.scrollHeight > d.clientHeight + 2)"):
                overflow.append(i)
            pg.screenshot(path=str(outdir / f"{i:02d}.jpg"), type="jpeg", quality=92)
        b.close()
    return overflow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("round_json")
    ap.add_argument("--approve3", help="대표의 발행 직전 승인(승인 3)을 기록할 때 승인자 표기")
    ap.add_argument("--out", help="출력 폴더 (기본 posts/YYYYMMDD_SLOT)")
    a = ap.parse_args()
    r = json.loads(pathlib.Path(a.round_json).read_text(encoding="utf-8"))
    ymd = r["date"].replace("-", "")
    out = pathlib.Path(a.out) if a.out else ROOT / "posts" / f"{ymd}_{r['slot']}"
    out.mkdir(parents=True, exist_ok=True)
    over = render(cards(r), out)
    (out / "caption.txt").write_text(r["caption"], encoding="utf-8")
    import datetime as dt
    meta = {"version": 1, "date": r["date"], "slot": r["slot"],
            "publishAt": f"{r['date']}T{SLOTS[r['slot']][1]}:00+09:00", "topic": r.get("topic", r["hook"]),
            "images": [f"{i:02d}.jpg" for i in range(1, 8)], "caption": r["caption"],
            "sources": r["sources"]}
    if a.approve3:
        meta["approval3"] = {"approved": True, "at": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="seconds"),
                             "by": a.approve3}
    (out / "post.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료: {out} (예약 {meta['publishAt']}, 승인 3 {'있음' if a.approve3 else '없음'})")
    if over:
        print(f"주의: {over}장에서 글이 카드 밖으로 넘칩니다. 문구를 줄이세요.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
