"""헤드라인 릴스(하루 1개, 야근 퇴근길 21:50, 대표 결정 2026-10-28).

벤치마킹: 큰 제목 3줄 표지 + 기사형 긴 캡션. 이슈브리프 색깔: 인물·뉴스 사진 대신 큰 숫자와 그림, 따뜻한 마지막 한 줄.

python scripts/make_headline.py rounds/<날짜>_HL_auto.json --out posts/<날짜>_HL
결과: cover.jpg(1080x1920), headline.mp4(약 8초, 무음), caption.txt(긴 캡션), post.json(게시하지 않음)

round JSON:
{
  "date": "2026-10-28", "topic": "…",
  "kicker": "오늘의 헤드라인",            # 위쪽 작은 딱지(선택)
  "number": "61", "unit": "골",          # 큰 숫자(선택), 단위
  "icon": "ball",                        # trophy ball wave shark star heart globe chart music
  "lines": ["케인, 51경기 61골", "*25년 만의* 잉글랜드 발롱도르", "꾸준함이 만든 트로피"],   # 3줄. *단어*는 노란 강조
  "caption": "…기사형 긴 캡션(800~1500자)…",
  "sources": [{"outlet","title","date","url"}]
}
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import make_post as mp  # 글꼴·아이콘·로고를 같이 쓴다

W, H = 1080, 1920
BG, INK, MUTED, YELLOW, CYAN, PINK = "#0B1220", "#F4F7FF", "#A9B6CF", "#FFC857", "#35E0FF", "#FF4FA3"


def hl(line):
    return re.sub(r"\*(.+?)\*", lambda m: f'<span style="color:{YELLOW}">{m.group(1)}</span>', mp.E(line))


def page(r):
    m, d = r["date"][5:7], r["date"][8:10]
    num = ""
    if r.get("number"):
        num = (f'<div style="display:flex;align-items:flex-end;gap:16px"><div style="font-size:260px;font-weight:900;line-height:.9;color:{CYAN}">{mp.E(r["number"])}</div>'
               f'<div style="font-size:72px;font-weight:900;color:{CYAN};padding-bottom:18px">{mp.E(r.get("unit", ""))}</div>'
               f'<div style="margin-left:auto">{mp.ICONS.get(r.get("icon", ""), "")}</div></div>')
    elif r.get("icon"):
        num = f'<div style="transform:scale(1.8);transform-origin:left top;height:220px">{mp.ICONS.get(r["icon"], "")}</div>'
    lines = r["lines"][:3]
    sizes = [96, 78, 66]
    body = "".join(f'<div style="font-size:{sizes[i]}px;font-weight:900;line-height:1.28;color:{INK if i != 2 else YELLOW if "*" not in l else INK}">{hl(l)}</div>'
                   for i, l in enumerate(lines))
    # 릴스 화면: 위 240px·아래 440px·오른쪽 160px은 Instagram 글자·버튼 자리라 비운다
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;word-break:keep-all;font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif}}</style></head><body>
<div style="position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{BG};color:{INK}">
<div style="position:absolute;inset:0;background:radial-gradient(900px 700px at 85% 20%, rgba(53,224,255,.16), transparent 60%),radial-gradient(800px 600px at 10% 90%, rgba(255,79,163,.14), transparent 60%)"></div>
<div style="position:relative;box-sizing:border-box;height:100%;padding:240px 160px 440px 90px;display:flex;flex-direction:column;gap:44px">
<div style="display:flex;align-items:center;gap:18px">{mp.LOGO}<div style="font-size:34px;font-weight:700">hot.issue.station</div><div style="margin-left:auto;font-size:30px;color:{MUTED}">{m}.{d}</div></div>
<div style="align-self:flex-start;padding:10px 26px;background:{PINK};color:#fff;font-size:38px;font-weight:900;letter-spacing:.04em">{mp.E(r.get("kicker", "오늘의 헤드라인"))}</div>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px">{num}<div style="display:flex;flex-direction:column;gap:22px">{body}</div></div>
<div style="font-size:34px;color:{MUTED}">자세한 이야기는 캡션에서 →</div>
</div></div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("round_json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = json.loads(pathlib.Path(a.round_json).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(page(r)); pg.wait_for_timeout(300)
        over = pg.evaluate("Array.from(document.querySelectorAll('div')).some(d => d.style.flex.startsWith('1') && d.scrollHeight > d.clientHeight + 2)")
        pg.screenshot(path=str(out / "cover.jpg"), type="jpeg", quality=92); b.close()
    # 8초 영상: 천천히 다가가는 움직임 + 첫 0.3초 밝아짐, 무음 트랙(대표가 앱에서 음악을 고름)
    n = 8 * 30
    vf = (f"scale={W*2}:{H*2},zoompan=z='1+0.06*(1-pow(1-on/{n},2))':x='iw/2-iw/zoom/2':y='ih*0.45-ih/zoom/2':d={n}:s={W}x{H}:fps=30,"
          f"fade=t=in:st=0:d=0.3,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(out / "cover.jpg"), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-vf", vf, "-frames:v", str(n), "-t", "8", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", str(out / "headline.mp4")], check=True)
    (out / "caption.txt").write_text(r["caption"], encoding="utf-8")
    meta = {"version": 1, "date": r["date"], "slot": "HL", "topic": r.get("topic", ""), "headline": True,
            "auto": {"id": r.get("id", "")}, "caption": r["caption"], "sources": r.get("sources", []),
            "note": "헤드라인 릴스 재료 전용. 게시하지 않음(publishAt 없음)"}
    (out / "post.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료: {out} · 캡션 {len(r['caption'])}자")
    if over:
        print("주의: 제목이 화면 밖으로 넘칩니다. 줄을 줄이세요."); return 2
    if not 500 <= len(r["caption"]) <= 2200:
        print("주의: 캡션은 500~2200자로 써 주세요."); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
