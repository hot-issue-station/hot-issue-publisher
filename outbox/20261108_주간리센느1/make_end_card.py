import asyncio,base64
from playwright.async_api import async_playwright
D="outbox/20261108_주간리센느1"
lg=base64.b64encode(open("assets/brand/duksim/profile_800.png","rb").read()).decode()
bg=base64.b64encode(open(f"{D}/photos/p1.jpg","rb").read()).decode()
H=f"""<html><head><style>*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;background:#0E1222;font-family:'Noto Sans CJK KR',sans-serif;color:#F4F7FF;overflow:hidden;position:relative;text-align:center}}
.bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{bg}) center/cover;filter:blur(28px) brightness(.35);transform:scale(1.15)}}
.top{{position:absolute;top:40px;left:60px;right:60px;display:flex;justify-content:space-between;font-size:28px;color:#A9B6CF;font-weight:500;text-align:left}}.top b{{color:#C9A6FF}}
.lg{{position:absolute;top:190px;left:0;right:0}}.lg img{{width:330px;border-radius:50%}}
.s{{position:absolute;top:570px;left:0;right:0;font-size:40px;font-weight:700;color:#E6EAF5}}
.t{{position:absolute;top:630px;left:0;right:0;font-size:104px;font-weight:900;color:#FFC857;letter-spacing:-3px}}
.w{{position:absolute;top:820px;left:0;right:0;font-size:46px;font-weight:900}}
.c{{position:absolute;top:900px;left:0;right:0;font-size:46px;font-weight:900;color:#FFC857}}
.n{{position:absolute;top:1060px;left:0;right:0;font-size:34px;color:#C9A6FF;font-weight:700}}
.foot{{position:absolute;bottom:30px;left:60px;right:60px;display:flex;justify-content:space-between;font-size:22px;color:#6f7fa0}}
</style></head><body><div class='bg'></div><div class='top'><span><b>●</b> 덕심저장소</span><span>📅 주간 리센느 #1 · 끝</span></div>
<div class='lg'><img src='data:image/png;base64,{lg}'></div><div class='s'>좋아하는 마음을 저장하는 곳</div><div class='t'>덕심저장소</div>
<div class='w'>📅 주간 리센느, 매주 일요일 아침 9시</div><div class='c'>구독 · 좋아요 · 알림 설정</div><div class='n'>다음 주에도 여기서 만나요 💜</div>
<div class='foot'><span>이미지 · KBS·Spotify Korea 화면</span><span>youtube.com/@hot.issue.station</span></div></body></html>"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={"width":1080,"height":1350})
    await pg.set_content(H);await pg.wait_for_timeout(200);await pg.screenshot(path=f"{D}/cards/WK_12_end.png");await b.close()
asyncio.run(m())
