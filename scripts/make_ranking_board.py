"""응원 랭킹 현황판 (대표 결정 10/29, 분석팀): data/ranking/latest.json 으로 인스타 스토리용 현황판(1080×1920)을 만든다.
대표가 매일 아침 스토리로 올리고 프로필 하이라이트 '응원 랭킹'에 모아 두면, 팔로워가 언제든 순위를 확인할 수 있다.

사용법:  python3 scripts/make_ranking_board.py [--src data/ranking/latest.json] --out <폴더>
결과:    <폴더>/board.jpg (스토리 이미지), <폴더>/board.mp4 (6초 정지 영상, 재료함 영상 칸용), <폴더>/board.json(쓴 데이터)
점수 규칙은 rank_comments.py 와 같다: 댓글 단 날마다 1점, 그날 베스트 댓글 +3점. 이름은 가린 이름(re***n) 그대로만 쓴다.
스토리 화면 위 250px·아래 340px 은 Instagram 글자·버튼 자리라 비워 둔다.
"""
import argparse
import datetime as dt
import html
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from make_post import LOGO  # noqa: E402

E = html.escape
BG, INK, MUTED, SOFT, LINE, BOX = "#140F24", "#F6F2FF", "#B3A8CF", "#D6CCF0", "#33285A", "#1E1736"
GOLD, SILVER, BRONZE, ACC, PINK = "#FFC857", "#D9DEE8", "#E0A06B", "#B98CFF", "#FF4FA3"
MEDAL = {1: GOLD, 2: SILVER, 3: BRONZE}


def page(data):
    top = data.get("top") or []
    upd = data.get("updatedAt", "")
    try:
        t = dt.datetime.fromisoformat(upd)
        when = f"{t.month}월 {t.day}일 {t.hour:02d}:{t.minute:02d} 기준"
    except ValueError:
        when = ""
    mx = max([r["score"] for r in top] or [1])
    rows = []
    for r in top[:10]:
        rk = r["rank"]
        col = MEDAL.get(rk, ACC)
        big = rk <= 3
        h = 82 if big else 54
        w = max(6, round(100 * r["score"] / mx))
        rows.append(
            f'<div style="position:relative;height:{h}px;border-radius:{24 if big else 18}px;background:{BOX};overflow:hidden;'
            f'border:{3 if big else 2}px solid {col if big else LINE}">'
            f'<div style="position:absolute;left:0;top:0;bottom:0;width:{w}%;background:linear-gradient(90deg,{col}33,{col}11)"></div>'
            f'<div style="position:relative;height:100%;display:flex;align-items:center;gap:26px;padding:0 34px">'
            f'<div style="width:{60 if big else 44}px;height:{60 if big else 44}px;border-radius:50%;background:{col if big else "transparent"};'
            f'border:{0 if big else 3}px solid {col};color:{BG if big else col};display:flex;align-items:center;justify-content:center;'
            f'font-size:{38 if big else 28}px;font-weight:900">{rk}</div>'
            f'<div style="flex:1;font-size:{44 if big else 32}px;font-weight:{900 if big else 700};letter-spacing:1px">{E(r["name"])}</div>'
            f'<div style="font-size:{46 if big else 32}px;font-weight:900;color:{col}">{r["score"]}<span style="font-size:{30 if big else 26}px;margin-left:4px;color:{SOFT}">점</span></div>'
            f'</div></div>')
    if not rows:
        body = (f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;text-align:center">'
                f'<div style="font-size:64px;font-weight:900;line-height:1.3">아직 순위가 비어 있어요</div>'
                f'<div style="font-size:42px;color:{SOFT};line-height:1.5">오늘 첫 댓글을 남기면<br>1위로 시작해요</div></div>')
    else:
        body = f'<div style="display:flex;flex-direction:column;gap:{8 if len(rows) > 6 else 16}px">{"".join(rows)}</div>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;word-break:keep-all;font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif}}</style></head><body>
<div style="position:relative;width:1080px;height:1920px;overflow:hidden;background:{BG};color:{INK}">
<div style="position:absolute;left:-200px;top:120px;width:700px;height:700px;border-radius:50%;background:radial-gradient({ACC}40,transparent 70%)"></div>
<div style="position:absolute;right:-240px;bottom:260px;width:760px;height:760px;border-radius:50%;background:radial-gradient({PINK}30,transparent 70%)"></div>
<div style="position:absolute;left:84px;right:84px;top:250px;bottom:340px;display:flex;flex-direction:column;gap:20px">
<div style="display:flex;align-items:center;justify-content:space-between">
<div style="display:flex;align-items:center;gap:18px">{LOGO}<div style="font-size:34px;font-weight:700">hot.issue.station</div></div>
<div style="font-size:30px;color:{MUTED}">{E(when)}</div></div>
<div><div style="font-size:40px;font-weight:700;color:{ACC}">🏆 응원 랭킹 현황판</div>
<div style="font-size:68px;font-weight:900;line-height:1.2;margin-top:4px">댓글 한 줄이 점수가 돼요</div></div>
<div style="display:flex;gap:16px">
<div style="flex:1;padding:18px 24px;border-radius:20px;background:{BOX};border:2px solid {LINE};font-size:32px;line-height:1.4"><b style="color:{ACC}">+1점</b> 댓글 단 날마다</div>
<div style="flex:1;padding:18px 24px;border-radius:20px;background:{BOX};border:2px solid {LINE};font-size:32px;line-height:1.4"><b style="color:{GOLD}">+3점</b> 그날 베스트 댓글</div></div>
{body}
<div style="flex:1"></div>
<div style="padding:24px 32px;border-radius:26px;background:linear-gradient(90deg,{ACC}38,{PINK}30);border:2px solid {ACC}">
<div style="font-size:40px;font-weight:900;line-height:1.35">상위 분께 리센느 빵 안에 있는 2차 포카를 드려요</div>
<div style="font-size:28px;color:{SOFT};margin-top:6px;line-height:1.45">수량 소진 시 종료 · 멤버 무작위 · Instagram과 무관 · 아이디는 일부만 보여요</div></div>
</div></div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "data" / "ranking" / "latest.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()
    src = pathlib.Path(a.src)
    data = json.loads(src.read_text(encoding="utf-8")) if src.exists() else {"top": []}
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.set_content(page(data))
        pg.wait_for_timeout(300)
        if pg.evaluate("(() => { const c = document.querySelector('div[style*=\"bottom:340px\"]'); return c.scrollHeight > c.clientHeight + 2; })()"):
            print("주의: 현황판 글이 스토리 안전 영역을 넘쳤어요")
        pg.screenshot(path=str(out / "board.jpg"), type="jpeg", quality=92)
        b.close()
    (out / "board.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.no_video:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(out / "board.jpg"), "-t", "6",
                        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out / "board.mp4")], check=True)
    print("현황판", len(data.get("top") or []), "명 →", out / "board.jpg")


if __name__ == "__main__":
    main()
