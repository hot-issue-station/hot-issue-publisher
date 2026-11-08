import asyncio, pathlib, subprocess, html
from playwright.async_api import async_playwright
import base64
D = pathlib.Path(__file__).parent
def B64(f):
    m='png' if str(f).endswith('png') else 'jpeg'
    return f'data:image/{m};base64,'+base64.b64encode(open(f,'rb').read()).decode()
ROOT = D.parent.parent
LOGO = ROOT/"assets/brand/duksim/profile_800.png"
BG1 = ROOT/"outbox/20261108_주간리센느1/photos/p1.jpg"
rows = [  # (이름, 앨범, 만 장, 표시)
 ("BTS","ARIRANG",416.0,"약 416만"),
 ("코르티스","",231.0,"231만"),
 ("엔하이픈","",207.0,"207만"),
 ("NCT WISH","",182.0,"182만"),
 ("투모로우바이투게더","",180.0,"180만"),
 ("블랙핑크","DEADLINE",177.5,"177만"),
 ("리센느","PULSE",45.9,"45만 9천"),
]
MX = 416.0
CSS = """
*{margin:0;box-sizing:border-box}body{width:1080px;height:1920px;background:#140F24;color:#F6F2FF;font-family:'Noto Sans CJK KR','Noto Sans CJK JP',sans-serif;position:relative;overflow:hidden}
.bgp{position:absolute;inset:0;background:url(BGURL) center/cover;filter:blur(40px) brightness(.35);transform:scale(1.2)}
.top{position:absolute;top:70px;left:0;right:0;text-align:center}
.w{font-size:50px;font-weight:900}.y{font-size:66px;font-weight:900;color:#FFD23F;margin-top:10px;line-height:1.2}
.jp{font-size:30px;color:#D6CCF0;margin-top:14px}
.src{position:absolute;right:30px;top:20px;font-size:22px;color:#B3A8CF}
.chart{position:absolute;left:50px;right:50px;top:420px;display:flex;flex-direction:column;gap:26px}
.r{height:112px;border-radius:22px;background:#1E1736;border:2px solid #33285A;position:relative;overflow:hidden}
.r .b{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#7C5CD6,#B98CFF)}
.r.me{border:4px solid #FFD23F}.r.me .b{background:linear-gradient(90deg,#FF4FA3,#FFD23F)}
.r .t{position:absolute;left:28px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;font-size:38px;font-weight:900;text-shadow:0 2px 6px #000}
.r .t small{font-size:24px;font-weight:500;color:#EFE9FF}
.r .n{position:absolute;right:26px;top:0;bottom:0;display:flex;align-items:center;font-size:48px;font-weight:900;color:#FFD23F;text-shadow:0 2px 6px #000}
.r .n i{font-size:26px;font-style:normal;color:#fff;margin-left:6px}
.note{position:absolute;left:50px;right:50px;top:1500px;font-size:30px;color:#D6CCF0;line-height:1.5;text-align:center}
.big{position:absolute;left:50px;right:50px;top:1280px;text-align:center}
.big .a{font-size:46px;font-weight:900}.big .a b{color:#FFD23F;font-size:78px}
.foot{position:absolute;left:40px;right:40px;bottom:60px;font-size:24px;color:#B3A8CF;text-align:center;line-height:1.5}
.badge{position:absolute;left:40px;top:20px;background:#FFD23F;color:#140F24;font-weight:900;font-size:26px;padding:6px 18px;border-radius:14px}
"""
def chart(n_show, title_y="올해 앨범 초동, 리센느는?", scale=True):
    # n_show: 아래(작은 값)부터가 아니라 위(큰 값)부터 아래로 드러냄
    out=[]
    for i,(nm,al,v,disp) in enumerate(rows):
        if i>=n_show: break
        w=max(8, 100*v/MX)
        me = nm=="리센느"
        sub = f"<small>{html.escape(al)}</small>" if al else ""
        out.append(f'<div class="r{" me" if me else ""}"><div class="b" style="width:{w}%"></div><div class="t">{html.escape(nm)}{sub}</div><div class="n">{disp}<i>장</i></div></div>')
    return "".join(out)
def page(body, bgurl):
    return f"<html><head><meta charset=utf-8><style>{CSS.replace('BGURL',bgurl)}</style></head><body><div class=bgp></div>{body}</body></html>"
head = '<div class="badge">📊 숫자로 본 TOP</div><div class="src">자료 · 한터차트 · 11/8 기준</div><div class="top"><div class="w">올해 앨범 초동 숫자로 보면</div><div class="y">리센느는<br>어디쯤일까?</div><div class="jp">リセネは今年のアルバム初動でどのあたり？</div></div>'
foot = '<div class="foot">한터차트 기준 · 리센느는 11/7 14시 실시간 집계 · 초동 마감 11/9<br>BTS·코르티스 등은 한터 상반기 결산(7/24, 7/8) · 일부 그룹만 표시</div>'
frames=[]
def add(name, body, dur): frames.append((name,body,dur))
add("f0", head+'<div class="note" style="top:900px;font-size:44px;font-weight:700">올해 가장 많이 팔린 앨범들과<br>나란히 놓아 봤어요</div>', 2.6)
for k in range(1,7):
    add(f"f{k}", head+f'<div class="chart">{chart(k)}</div>'+foot, 1.5)
add("f7", head+f'<div class="chart">{chart(7)}</div>'+foot, 2.2)
big = '<div class="big" style="top:1420px"><div class="a">PULSE 첫 주 <b>45만 9천 장</b></div><div class="a" style="font-size:36px;color:#D6CCF0;margin-top:10px">전작 「lip bomb」 첫 주 10만 4천 장의 <b style="font-size:46px">4배 넘게</b></div><div class="a" style="font-size:34px;color:#D6CCF0;margin-top:8px">하프 밀리언까지 약 4만 1천 장 · 집계 중</div></div>'
add("f8", head+f'<div class="chart" style="opacity:.85">{chart(7)}</div>'.replace('top:420px','top:420px')+big.replace('top:1280px','top:1420px')+foot, 4.2)
end = '''<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;text-align:center">
<img src="LOGO" style="width:280px;border-radius:50%"><div style="font-size:58px;font-weight:900">덕심저장소가 계속 지켜볼게요 💜</div>
<div style="display:flex;flex-direction:column;gap:22px;margin-top:20px">
<div style="background:#FFD23F;color:#140F24;font-size:54px;font-weight:900;padding:22px 80px;border-radius:26px">👍 좋아요</div>
<div style="background:#FFD23F;color:#140F24;font-size:54px;font-weight:900;padding:22px 80px;border-radius:26px">➕ 구독</div>
<div style="background:#FFD23F;color:#140F24;font-size:54px;font-weight:900;padding:22px 80px;border-radius:26px">🔔 알림 설정</div></div>
<div style="font-size:36px;color:#D6CCF0;margin-top:20px">초동 마감 11/9(월) 뒤 최종 숫자도 알려 드려요</div></div>'''.replace("LOGO", B64(LOGO))
add("f9", end, 3.4)
thumb = '<div class="badge">📊 숫자로 본 TOP</div><div class="top" style="top:150px"><div class="w" style="font-size:64px">올해 앨범 초동 순위 속</div><div class="y" style="font-size:120px;margin-top:30px">리센느는<br>어디쯤?</div></div><div class="big" style="top:900px"><div class="a" style="font-size:60px">PULSE 첫 주</div><div class="a"><b style="font-size:190px;-webkit-text-stroke:6px #140F24;paint-order:stroke fill">45만 9천 장</b></div><div class="a" style="font-size:54px;margin-top:10px">전작의 <b style="font-size:80px">4배 넘게</b></div></div><div class="foot" style="font-size:28px">한터차트 11/7 14시 실시간 · 초동 집계 중</div>'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width":1080,"height":1920})
        for name,body,dur in frames:
            await pg.set_content(page(body, B64(BG1).join(["url(",")"]) if False else B64(BG1)))
            await pg.wait_for_timeout(250)
            await pg.screenshot(path=str(D/f"{name}.png"))
        await pg.set_content(page(thumb, B64(BG1))); await pg.wait_for_timeout(250)
        await pg.screenshot(path=str(D/"thumb.png"))
        await b.close()
asyncio.run(main())
lines=[]
for name,_,dur in frames:
    lines.append(f"file '{(D/(name+'.png')).as_posix()}'\nduration {dur}")
lines.append(f"file '{(D/(frames[-1][0]+'.png')).as_posix()}'")
(D/"list.txt").write_text("\n".join(lines))
tot=sum(d for *_,d in frames); print("총", tot)
