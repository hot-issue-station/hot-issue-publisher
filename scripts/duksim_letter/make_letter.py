import asyncio, base64, json, sys
from playwright.async_api import async_playwright
cfg=json.load(open(sys.argv[1])); S=cfg["dir"]; N=len(cfg["cards"])
def b64(i): return base64.b64encode(open(f'{S}/photos/p{i}.jpg','rb').read()).decode()
A=cfg.get("accent","#C9A6FF")
CSS=f"""*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;background:#0E1222;font-family:'Noto Sans CJK KR',sans-serif;color:#F4F7FF;overflow:hidden;position:relative}}
.top{{position:absolute;top:40px;left:60px;right:60px;display:flex;justify-content:space-between;font-size:28px;color:#A9B6CF;font-weight:500}}.top b{{color:{A}}}
.ph{{position:absolute;top:98px;left:60px;right:60px;height:560px;border-radius:28px;overflow:hidden;border:2px solid #2A3A59}}.ph img{{width:100%;height:100%;object-fit:cover;object-position:{cfg.get('pos','center 35%')};display:block}}
.tag{{position:absolute;left:60px;top:690px;background:{A};color:#140b22;font-size:30px;font-weight:900;padding:6px 22px;border-radius:999px}}
.fact{{position:absolute;left:60px;right:60px;top:752px;font-size:46px;line-height:1.32;font-weight:900;letter-spacing:-1px}}
.fact .y{{color:#FFC857}}.fact.sm{{font-size:37px;line-height:1.38}}
.paper{{position:absolute;left:60px;right:60px;top:930px;height:330px;background:#FFF6EA;border-radius:26px;padding:40px 46px 30px 46px;color:#3B2A35;box-shadow:0 10px 30px rgba(0,0,0,.35)}}
.paper:before{{content:'💌';position:absolute;top:-30px;left:34px;font-size:52px}}
.paper .t{{font-size:39px;line-height:1.55;font-weight:500;letter-spacing:-.5px}}
.paper .from{{position:absolute;right:44px;bottom:26px;font-size:30px;color:#C2577E;font-weight:700}}
.foot{{position:absolute;bottom:30px;left:60px;right:60px;display:flex;justify-content:space-between;font-size:22px;color:#6f7fa0}}
.cv .ph{{height:600px}}
.badge{{position:absolute;left:60px;top:705px;background:#FF4FA3;color:#fff;font-size:34px;font-weight:900;padding:8px 26px;border-radius:999px}}
.big{{position:absolute;left:60px;right:40px;top:775px;font-size:112px;font-weight:900;letter-spacing:-3px;line-height:1.1;color:#FFC857}}
.subl{{position:absolute;left:60px;right:60px;top:925px;font-size:44px;line-height:1.4;font-weight:700}}
.cvfrom{{position:absolute;left:60px;top:1080px;font-size:40px;color:#FF8FC0;font-weight:900}}
.cvinfo{{position:absolute;left:60px;top:1150px;font-size:34px;color:#A9B6CF;font-weight:500}}
"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":1080,"height":1350})
    for i,c in enumerate(cfg["cards"],1):
      top=f"<div class='top'><span><b>●</b> 덕심저장소</span><span>💌 덕심 편지 #{cfg['no']} · {i}/{N}</span></div>"
      foot=f"<div class='foot'><span>이미지 · {cfg['img']}</span><span>출처 {cfg['src']}</span></div>"
      ph=f"<div class='ph'><img src='data:image/jpeg;base64,{b64(i)}'></div>"
      if c.get("cover"):
        body=f"<body class='cv'>{top}{ph}<div class='badge'>💌 덕심 편지 #{cfg['no']}</div><div class='big'>{cfg['to']}에게</div><div class='subl'>{c['sub']}</div><div class='cvfrom'>From. {cfg['fandom']}</div><div class='cvinfo'>{c['info']}</div>{foot}</body>"
      else:
        fr=f"<div class='from'>{c['from']}</div>" if c.get('from') else ""
        body=f"<body>{top}{ph}<div class='tag'>{c['tag']}</div><div class='fact{" sm" if c.get("sm") else ""}'>{c['fact']}</div><div class='paper'><div class='t'>{c['letter']}</div>{fr}</div>{foot}</body>"
      await pg.set_content(f"<html><head><style>{CSS}</style></head>{body}</html>"); await pg.wait_for_timeout(120)
      await pg.screenshot(path=f"{S}/cards/{cfg['prefix']}_{i:02d}.png")
    await b.close()
asyncio.run(main())
