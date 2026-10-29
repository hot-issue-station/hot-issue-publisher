"""리센느 응원 랭킹 이벤트 안내 카드 (대표 지시 10/29): 피드 카드 7장(1080×1350, 보랏빛 밤 RS 색).

사용법:  python3 scripts/make_event_cards.py <event.json> --out <폴더>
event.json 형식:
{
  "date": "2026-10-29",
  "photos": {"cover": "경로", "a": "경로", "b": "경로"},   # 대표가 직접 찍은 빵·포카 사진만
  "prize": "리센느 빵 안에 있는 2차 포카",                  # 표기 규칙(대표 10/29): 그냥 '포카'라고 쓰지 않는다
  "have": 2, "goal": "7장 안팎",                            # 지금 모은 수, 컴백 날까지 모을 목표
  "start": "10월 29일(목)", "end": "11월 9일(월) 밤 11:59", "finalize": "11월 3일(화) 컴백 날", "announce": "11월 10일(화)",
  "question": "…"                                          # 7장 댓글 질문
}
결과: <폴더>/01.jpg … 07.jpg, caption.txt
"""
import argparse
import base64
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_post as mp  # noqa: E402

E = html.escape


def uri(p, w=1400):
    from PIL import Image
    import io
    im = Image.open(p).convert("RGB")
    im.thumbnail((w, w))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def cards(ev):
    mp.apply_theme("RS")
    T = mp  # 색 이름(mp.BG 등)은 apply_theme 뒤에 읽는다
    m, d = ev["date"][5:7], ev["date"][8:10]
    label = f"{m}.{d} · 응원 이벤트"
    P = ev["prize"]
    pill = (f'<div style="align-self:flex-start;padding:10px 26px;border:3px solid {T.CYAN};border-radius:999px;color:{T.CYAN};'
            f'font-size:32px;font-weight:700;background:rgba({T.BGRGB},.6)">리센느 응원 이벤트</div>')

    def box(inner, accent=None, pad="40px 48px"):
        return (f'<div style="padding:{pad};border-radius:36px;background:{T.BOX};border:3px solid {accent or T.LINE};'
                f'display:flex;flex-direction:column;gap:14px">{inner}</div>')

    def step(n, title, desc):
        return (f'<div style="display:flex;gap:30px;align-items:flex-start">'
                f'<div style="flex:none;width:84px;height:84px;border-radius:50%;background:{T.CYAN};color:{T.BG};display:flex;'
                f'align-items:center;justify-content:center;font-size:44px;font-weight:900">{n}</div>'
                f'<div style="display:flex;flex-direction:column;gap:8px;padding-top:6px"><div style="font-size:50px;font-weight:900;line-height:1.25">{title}</div>'
                f'<div style="font-size:36px;line-height:1.5;color:{T.SOFT}">{desc}</div></div></div>')

    out = []
    # 1 표지: 위쪽 사진, 아래로 보랏빛에 녹아듦
    ph = 760
    deco = (f'<div style="position:absolute;left:0;top:0;width:1080px;height:{ph}px;background:url({uri(ev["photos"]["cover"])}) 50% 45%/cover no-repeat"></div>'
            f'<div style="position:absolute;left:0;top:0;width:1080px;height:{ph}px;background:linear-gradient(180deg,rgba({T.BGRGB},.9) 0%,rgba({T.BGRGB},.55) 13%,rgba({T.BGRGB},0) 28%,rgba({T.BGRGB},0) 55%,{T.BG} 100%)"></div>'
            f'<div style="position:absolute;right:40px;top:{ph - 120}px;padding:8px 18px;border-radius:999px;background:rgba({T.BGRGB},.7);color:{T.SOFT};font-size:24px">직접 찍은 사진</div>')
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:22px;padding-bottom:24px">
{pill}
<div style="font-size:76px;font-weight:900;line-height:1.2">댓글로 응원하고<br><span style="color:{T.CYAN}">2차 포카</span> 받아 가세요</div>
<div style="font-size:38px;line-height:1.45;color:{T.SOFT}">{E(P)}를 응원 랭킹 상위 분께 나눠 드려요</div></div>""",
                        label, 1, "밀어서 다음 장 →", deco=deco))
    # 2 무엇을 드리나요
    two = (f'<div style="display:flex;gap:24px">'
           f'<div style="flex:1;height:520px;border-radius:30px;background:url({uri(ev["photos"]["a"])}) 50% 50%/cover"></div>'
           f'<div style="flex:1;height:520px;border-radius:30px;background:url({uri(ev["photos"]["b"])}) 50% 50%/cover"></div></div>')
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px">
<div style="font-size:40px;font-weight:700;color:{T.CYAN}">이런 선물을 드려요</div>
<div style="font-size:64px;font-weight:900;line-height:1.25">{E(P)}</div>
{two}
<div style="font-size:36px;line-height:1.5;color:{T.SOFT}">지금 {ev['have']}장을 모았고, 컴백 날까지 매일 하나씩 더 모아 {E(ev['goal'])}을 준비해요. 봉투를 뜯지 않은 미개봉이라 멤버는 무작위예요.</div></div>""",
                        label, 2))
    # 3 참여 방법
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:52px">
<div style="font-size:40px;font-weight:700;color:{T.CYAN}">참여 방법</div>
<div style="font-size:68px;font-weight:900;line-height:1.25">어렵지 않아요,<br>댓글이면 충분해요</div>
<div style="display:flex;flex-direction:column;gap:44px">
{step(1, "@hot.issue.station 팔로우", "팔로우한 분만 선물을 받을 수 있어요")}
{step(2, "아무 게시물에 응원 댓글", "리센느 소식이 아니어도 괜찮아요. 우리 계정 게시물이면 모두 점수가 돼요")}
{step(3, "매일 들러서 한 줄씩", "날마다 댓글을 남길수록 점수가 쌓여요")}</div></div>""", label, 3))
    # 4 점수 규칙
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px">
<div style="font-size:40px;font-weight:700;color:{T.CYAN}">점수는 이렇게 쌓여요</div>
<div style="font-size:62px;font-weight:900;line-height:1.25">많이보다 <span style="color:{T.CYAN}">자주</span>가<br>유리해요</div>
<div style="display:flex;gap:28px">
{box(f'<div style="font-size:104px;font-weight:900;line-height:1;color:{T.CYAN}">+1</div><div style="font-size:42px;font-weight:900">댓글 단 날마다</div><div style="font-size:32px;line-height:1.45;color:{T.SOFT}">하루에 여러 개를 달아도 1점이에요</div>', T.CYAN)}
{box(f'<div style="font-size:104px;font-weight:900;line-height:1;color:#FFC857">+3</div><div style="font-size:42px;font-weight:900">그날 베스트 댓글</div><div style="font-size:32px;line-height:1.45;color:{T.SOFT}">좋아요를 가장 많이 받은 댓글</div>', "#FFC857")}</div>
{box(f'<div style="font-size:34px;color:{T.SOFT}">예를 들면</div><div style="font-size:40px;font-weight:700;line-height:1.5">5일 동안 매일 댓글 <b style="color:{T.CYAN}">5점</b> + 그중 하루 베스트 <b style="color:#FFC857">3점</b> = <b style="font-size:48px">8점</b></div>')}
<div style="font-size:34px;line-height:1.5;color:{T.SOFT}">점수가 같으면 먼저 참여한 분이 앞서요.</div></div>""",
                        label, 4))
    # 5 순위 확인
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px">
<div style="font-size:40px;font-weight:700;color:{T.CYAN}">내 순위는 어디서 보나요</div>
<div style="font-size:68px;font-weight:900;line-height:1.25">프로필 하이라이트<br><span style="color:{T.CYAN}">'응원 랭킹'</span></div>
{box(f'<div style="font-size:40px;font-weight:900">🏆 매일 아침 현황판 업데이트</div><div style="font-size:36px;line-height:1.5;color:{T.SOFT}">1위부터 10위까지 점수를 스토리로 올리고, 하이라이트에 모아 둬요</div>')}
{box(f'<div style="font-size:40px;font-weight:900">🔒 아이디는 일부만 보여요</div><div style="font-size:36px;line-height:1.5;color:{T.SOFT}">앞 두 글자와 끝 글자만 보여요. 예) re***n</div>')}</div>""",
                        label, 5))
    # 6 일정·안내
    rows = [("참여 기간", f"{ev['start']} ~ {ev['end']}"), ("선물 수량 확정", ev["finalize"]), ("결과 발표", f"{ev['announce']} 스토리·하이라이트")]
    sched = "".join(f'<div style="display:flex;justify-content:space-between;gap:20px;padding:22px 0;border-bottom:2px solid {T.LINE}">'
                    f'<div style="font-size:36px;color:{T.SOFT}">{a}</div><div style="font-size:36px;font-weight:700;text-align:right">{E(b)}</div></div>' for a, b in rows)
    notes = ["상위 분께 모은 수량만큼 드려요(수량 소진 시 종료)", "당첨되면 저희가 DM으로 먼저 연락해요. 주소는 DM으로만 받고 보낸 뒤 바로 지워요",
             "돈·카드번호·링크 클릭은 절대 요구하지 않아요", "팬분들을 위한 응원 나눔이에요(판매 아님)", "이 이벤트는 Instagram과 관련이 없어요"]
    nl = "".join(f'<div style="font-size:31px;line-height:1.45;color:{T.BODY}">· {E(x)}</div>' for x in notes)
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px">
<div style="font-size:40px;font-weight:700;color:{T.CYAN}">일정과 안내</div>
<div style="display:flex;flex-direction:column">{sched}</div>
<div style="display:flex;flex-direction:column;gap:12px">{nl}</div></div>""", label, 6))
    # 7 마무리
    out.append(mp.frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px">
<div style="font-size:76px;font-weight:900;line-height:1.25">오늘 첫 댓글이면<br><span style="color:{T.CYAN}">바로 1위</span>로 시작해요</div>
{box(f'<div style="font-size:34px;color:{T.SOFT}">오늘의 질문</div><div style="font-size:50px;font-weight:900;line-height:1.35">{E(ev["question"])}</div>', T.CYAN, "48px 52px")}
<div style="font-size:38px;line-height:1.5;color:{T.SOFT}">11월 3일, 리센느의 컴백을 함께 응원해요</div></div>""",
                        label, 7, "@hot.issue.station"))
    return out


def caption(ev):
    return f"""댓글로 리센느를 응원하고, {ev['prize']} 받아 가세요 💜

리센느 컴백(11월 3일)을 앞두고, 저희 계정에서 응원 랭킹 이벤트를 열어요. 댓글로 점수를 모은 상위 분께 직접 모은 {ev['prize']}를 나눠 드려요.

🏆 참여 방법
1. @hot.issue.station 팔로우
2. 저희 게시물 아무 곳에 응원 댓글
3. 매일 들러서 한 줄씩

점수: 댓글 단 날마다 +1점(하루 여러 개여도 1점), 그날 베스트 댓글(좋아요 최다) +3점. 점수가 같으면 먼저 참여한 분이 앞서요.
순위: 매일 아침 스토리 → 프로필 하이라이트 '응원 랭킹' (아이디 일부만 표시)

📅 참여 {ev['start']} ~ {ev['end']} · 수량 확정 {ev['finalize']} · 발표 {ev['announce']}
🎁 {ev['prize']}, 미개봉(멤버 무작위). 지금 {ev['have']}장, 컴백 날까지 {ev['goal']} 모을 예정이에요.

안내
· 당첨되면 저희가 DM으로 먼저 연락해요. 주소는 DM으로만 받고 보낸 뒤 바로 지워요. 돈·카드번호·링크 클릭은 절대 요구하지 않아요.
· 팬분들을 위한 응원 나눔이에요(판매 아님). 수량 소진 시 종료.
· 이 이벤트는 Instagram과 관련이 없어요.

{ev['question']} 댓글로 알려 주세요. 오늘 첫 댓글이면 바로 1위로 시작해요!

광고·제휴 문의 reaymi.music@gmail.com

#리센느 #RESCENE #리센느빵 #포카나눔 #응원이벤트 #PULSE #이슈브리프 #오늘의이슈"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("event")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ev = json.loads(pathlib.Path(a.event).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mp.LAYOUT = mp.FEED
    over = mp.render(cards(ev), out)
    (out / "caption.txt").write_text(caption(ev), encoding="utf-8")
    print("카드 7장 →", out, "| 넘침:", over or "없음", "| 캡션", len(caption(ev)), "자")


if __name__ == "__main__":
    main()
