import asyncio, base64
from playwright.async_api import async_playwright
S="/tmp/claude-0/-home-claude/eb774544-8081-59eb-9d1c-8cc1d162e9ef/scratchpad/rs2"
def b64(i): return base64.b64encode(open(f'{S}/photos/p{i}.jpg','rb').read()).decode()
cards=[
 ("하루 발자취 #2","리센느의<br><span class='y'>11월 6일</span>","차트 정상, 디즈니, 그리고 오늘 저녁 첫 음악방송 💜",True),
 ("오늘 오전 11시","음원 차트<br><span class='y'>한눈에</span>","멜론 TOP100 1위 · 벅스 2위<br>지니 실시간 3위 · 플로 4위",False),
 ("멜론 TOP100","TOP10에 6곡,<br><span class='y'>21위 안에 10곡</span>","With 1 · LOVE ATTACK 4 · 백화요란 5 · Deja Vu 7<br>Finest Thing 9 · Pretty Girl 10 · MEME 12<br>Dragon 14 · Runaway 16 · Pinball 21",False),
 ("다시 위로","「Pinball」<br><span class='y'>21위까지</span>","11월 4일 멜론 일간 42위였던 「Pinball」이<br>오늘 오전 TOP100 21위까지 올라왔어요.",False),
 ("벅스","벅스에서도<br><span class='y'>100위 안에 10곡</span>","「With」 2위부터 10곡이 함께.<br>「Pinball」은 한 시간 새 7계단 올랐어요.",False),
 ("음반","첫날 13만 장,<br><span class='y'>커리어 하이</span>","「PULSE」 첫날 13만 1,893장(한터차트).<br>전작 「lip bomb」의 일주일 판매량보다 많아요.",False),
 ("디즈니","디즈니 영화에<br><span class='y'>「With」</span>","「헥스: 마녀왕국」 엔딩 크레딧에 「With」가 흘러요.<br>국내 걸그룹 신곡이 디즈니 엔딩을 장식한 건 처음이에요.",False),
 ("오늘 아침 공개","신입 마녀들의<br><span class='y'>촬영 비하인드</span>","디즈니 코리아가 마녀로 변신한 다섯 명의<br>촬영 현장을 공개했어요. 11월 25일 개봉!",False),
 ("어젯밤 공개","재킷 촬영<br><span class='y'>비하인드</span>","「러닝온 러닝온 러닝온 유우우우우🏃‍♀️」<br>공개 13시간 만에 42만 회를 넘었어요.",False),
 ("뮤직비디오","「With」 MV<br><span class='y'>1,263만 회</span>","공개 이틀 만에 1,263만 회.<br>지금도 계속 올라가고 있어요.",False),
 ("평론","끝까지 남을<br><span class='y'>향기</span>","대중음악평론가 김성대는 「PULSE」가<br>\"끝까지 남을 향기\"를 지향한다고 썼어요.",False),
 ("오늘 저녁","「뮤직뱅크」<br><span class='y'>첫 무대</span>","「With」를 음악방송에서 처음 보여 주는 날.<br><b class='q'>다섯 명의 첫 무대, 함께 응원해요 💜</b>",False),
]
def CRED(i): return '디즈니 코리아' if i in (7,8) else '더뮤즈엔터테인먼트'
CSS="""
*{margin:0;box-sizing:border-box}body{width:1080px;height:1350px;background:#0B1220;font-family:'Noto Sans CJK KR',sans-serif;color:#F4F7FF;overflow:hidden;position:relative}
.top{position:absolute;top:44px;left:60px;right:60px;display:flex;justify-content:space-between;font-size:30px;color:#A9B6CF;font-weight:500}
.top b{color:#C9A6FF}
.ph{position:absolute;top:110px;left:60px;right:60px;height:600px;border-radius:28px;overflow:hidden;border:2px solid #2A3A59}.ph img{width:100%;height:100%;object-fit:cover;display:block}
.cover .ph{height:488px}
.tag{position:absolute;left:60px;top:745px;background:#C9A6FF;color:#fff;font-size:32px;font-weight:700;padding:8px 22px;border-radius:999px}
.cover .tag{top:670px;background:#FF4FA3}
h1{position:absolute;left:60px;right:60px;top:810px;font-size:74px;line-height:1.22;font-weight:900;letter-spacing:-1px}
.cover h1{top:750px;font-size:104px;line-height:1.18}
.y{color:#FFC857}
p{position:absolute;left:60px;right:60px;bottom:100px;font-size:36px;line-height:1.5;color:#D6DEEE;font-weight:500}
.cover p{display:none}
.sub{position:absolute;left:60px;right:60px;top:1030px;font-size:50px;color:#D6DEEE;font-weight:500}
.q{color:#35E0FF;display:block;margin-top:8px}
.foot{position:absolute;bottom:40px;left:60px;right:60px;display:flex;justify-content:space-between;font-size:26px;color:#6f7fa0}
"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":1080,"height":1350})
    for i,(tag,h,p,cover) in enumerate(cards,1):
      sub=f"<div class='sub'>{p}</div>" if cover else ""
      doc=f"""<html><head><style>{CSS}</style></head><body class='{"cover" if cover else ""}'>
<div class='top'><span><b>●</b> 덕심저장소</span><span>리센느 하루 발자취 #2 · {i}/12</span></div>
<div class='ph'><img src='data:image/jpeg;base64,{b64(i)}'></div>
<div class='tag'>{tag}</div><h1>{h}</h1><p>{p}</p>{sub}
<div class='foot'><span>이미지 · {CRED(i)}</span><span>출처 멜론·벅스·지니·플로·일간스포츠·YTN 외</span></div></body></html>"""
      await pg.set_content(doc); await pg.wait_for_timeout(100); await pg.screenshot(path=f"{S}/cards/RS2_{i:02d}.png")
    await b.close()
asyncio.run(main())
