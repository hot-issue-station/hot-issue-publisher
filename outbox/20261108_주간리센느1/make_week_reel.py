import asyncio, subprocess, sys, os, json, base64
from playwright.async_api import async_playwright
cfg=json.load(open(sys.argv[1])); S=cfg["dir"]; P=cfg["prefix"]; N=len(cfg["cards"]); SUB=cfg["subs"]; FL=cfg.get("subflag","🇺🇸")
FPS=30; XF=0.4; DUR=[3.6]+[4.3]*(N-2)+[4.6]
TRANS=["fade","slideleft","smoothleft","fadeblack","circleopen","slideleft","hblur","smoothleft","radial","fade","fadeblack"]
def b(p): return base64.b64encode(open(p,"rb").read()).decode()
def page(i):
  img=b(f"{S}/cards/{P}_{i:02d}.png")
  return f"""<html><head><style>*{{margin:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;background:#070a16;overflow:hidden;font-family:'Noto Sans CJK KR'}}
@keyframes z{{from{{transform:scale(.9)}}to{{transform:scale(.93)}}}}
@keyframes up{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:none}}}}
.band{{position:absolute;top:0;left:0;right:0;height:330px;padding:60px 60px 0}}
.src{{font-size:25px;color:#7f8db0;margin-bottom:16px}} .w{{font-size:46px;font-weight:700;color:#F4F7FF}} .w b{{color:#FF8FC0}}
.y{{font-size:76px;font-weight:900;color:#FFC857;margin-top:4px;letter-spacing:-2px}}
.prog{{position:absolute;top:322px;left:0;height:8px;background:#FF8FC0}}
.card{{position:absolute;top:350px;left:0;width:1080px;height:1350px;transform-origin:50% 0;animation:z {DUR[i-1]}s linear forwards}}
.card img{{width:1080px;height:1350px;border-radius:34px}}
.sb{{position:absolute;left:50px;right:50px;top:1615px;text-align:center;font-size:33px;line-height:1.35;color:#fff;font-weight:700;font-family:'Noto Sans CJK KR';opacity:0;animation:up .6s ease-out .5s forwards}}
</style></head><body><div class='band'><div class='src'>{cfg['bandsrc']}</div><div class='w'>📅 주간 리센느 #{cfg['no']} · <b>이번 주 총정리</b></div><div class='y'>리센느, 이번 주</div></div>
<div class='prog' id='pg'></div><div class='card'><img src='data:image/png;base64,{img}'></div><div class='sb'><div>🇯🇵 {cfg['subs_jp'][i-1]}</div><div style='margin-top:10px'>🇺🇸 {SUB[i-1]}</div></div></body></html>"""
async def main():
  out=f"{S}/reel"; os.makedirs(out,exist_ok=True); total=sum(DUR)-XF*(N-1); t0=0
  async with async_playwright() as pw:
    br=await pw.chromium.launch(); pg=await br.new_page(viewport={"width":1080,"height":1920})
    for i in range(1,N+1):
      await pg.set_content(page(i)); await pg.wait_for_timeout(150)
      ff=subprocess.Popen(["ffmpeg","-v","error","-y","-f","image2pipe","-framerate",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",f"{out}/c{i}.mp4"],stdin=subprocess.PIPE)
      for f in range(int(DUR[i-1]*FPS)):
        t=f/FPS; gt=t0+t
        await pg.evaluate(f"()=>{{document.getAnimations().forEach(a=>{{a.pause();a.currentTime={t*1000}}});document.getElementById('pg').style.width=({gt}/{total}*1080)+'px'}}")
        ff.stdin.write(await pg.screenshot(type="jpeg",quality=92))
      ff.stdin.close(); ff.wait(); t0+=DUR[i-1]-XF
    await br.close()
  ins=[]; [ins.extend(["-i",f"{out}/c{i}.mp4"]) for i in range(1,N+1)]
  f=[]; prev="0:v"; off=0
  for k in range(1,N):
    off+=DUR[k-1]-XF; o=f"x{k}" if k<N-1 else "vx"
    f.append(f"[{prev}][{k}:v]xfade=transition={TRANS[(k-1)%len(TRANS)]}:duration={XF}:offset={off:.3f}[{o}]"); prev=o
  subprocess.run(["ffmpeg","-v","error","-y",*ins,"-filter_complex",";".join(f),"-map","[vx]","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-r","30",f"{out}/reel_silent.mp4"],check=True)
  json.dump({"off":total-0.4},open(f"{out}/len.json","w")); print("done",total)
asyncio.run(main())
