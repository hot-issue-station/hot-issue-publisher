import asyncio,base64
from playwright.async_api import async_playwright
S="/tmp/claude-0/-home-claude/eb774544-8081-59eb-9d1c-8cc1d162e9ef/scratchpad/rs2"
b=base64.b64encode(open(S+"/photos/p1.jpg","rb").read()).decode()
H=f"""<html><head><style>*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1920px;background:#0B1220;font-family:'Noto Sans CJK KR';overflow:hidden;position:relative}}
.bg{{position:absolute;top:0;left:0;right:0;height:380px;background:url(data:image/jpeg;base64,{b}) center/cover;filter:blur(30px) brightness(.8)}}
.ph{{position:absolute;top:372px;left:0;right:0;height:720px;background:url(data:image/jpeg;base64,{b}) center 30%/cover}}
.ph:after{{content:'';position:absolute;left:0;right:0;bottom:0;height:200px;background:linear-gradient(transparent,#0B1220)}}
.tag{{position:absolute;left:70px;top:1060px;background:#C9A6FF;color:#1b1030;font-size:46px;font-weight:900;padding:10px 32px;border-radius:999px}}
h1{{position:absolute;left:70px;top:1170px;font-size:150px;line-height:1.08;font-weight:900;color:#FFC857;letter-spacing:-3px}}
.s{{position:absolute;left:70px;top:1540px;font-size:58px;line-height:1.45;color:#fff;font-weight:700}}
</style></head><body><div class='bg'></div><div class='ph'></div><div class='tag'>리센느 하루 발자취 #2</div>
<h1>멜론 1위,<br>디즈니까지</h1><div class='s'>멜론 TOP10에 6곡 · 핀볼 21위<br>오늘 저녁 뮤뱅 첫 무대</div></body></html>"""
async def m():
  async with async_playwright() as p:
    br=await p.chromium.launch();pg=await br.new_page(viewport={"width":1080,"height":1920})
    await pg.set_content(H);await pg.wait_for_timeout(200);await pg.screenshot(path=S+"/reel/thumb_rs2.jpg",type="jpeg",quality=92);await br.close()
asyncio.run(m())
