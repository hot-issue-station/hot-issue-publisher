import asyncio,base64,sys
from playwright.async_api import async_playwright
D="outbox/20261108_주간리센느1"
b=lambda p:base64.b64encode(open(p,"rb").read()).decode()
H=f"""<html><head><style>*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1920px;overflow:hidden;background:#0E1222;font-family:'Noto Sans CJK KR';position:relative}}
.ph{{position:absolute;top:0;left:0;right:0;height:1000px;background:url(data:image/jpeg;base64,{b(D+'/photos/p1.jpg')}) 30% 0/auto 1000px no-repeat;top:120px}}
.gr{{position:absolute;top:760px;left:0;right:0;height:560px;background:linear-gradient(transparent,#0E1222)}}
.bd{{position:absolute;top:60px;left:60px;background:#C9A6FF;color:#140b22;font-size:44px;font-weight:900;padding:10px 30px;border-radius:999px}}
.y{{position:absolute;top:1180px;left:50px;right:40px;font-size:150px;font-weight:900;color:#FFD23F;line-height:1.05;letter-spacing:-5px;-webkit-text-stroke:6px #000;paint-order:stroke fill}}
.w{{position:absolute;top:1560px;left:60px;right:60px;font-size:66px;font-weight:900;color:#fff;-webkit-text-stroke:4px #000;paint-order:stroke fill}}
.c{{position:absolute;bottom:70px;left:60px;font-size:40px;color:#C9A6FF;font-weight:700}}
</style></head><body><div class='ph'></div><div class='gr'></div><div class='bd'>📅 주간 리센느 #1</div>
<div class='y'>컴백·1위<br>4관왕까지</div><div class='w'>이번 주 리센느 총정리</div><div class='c'>● 덕심저장소</div></body></html>"""
async def m():
  async with async_playwright() as p:
    br=await p.chromium.launch();pg=await br.new_page(viewport={"width":1080,"height":1920})
    await pg.set_content(H);await pg.wait_for_timeout(200);await pg.screenshot(path=D+"/thumb_주간리센느1.jpg",type="jpeg",quality=92);await br.close()
asyncio.run(m())
