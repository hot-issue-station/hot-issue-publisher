import asyncio, subprocess, base64, os
import tempfile; S=tempfile.gettempdir(); R="/home/claude/hot-issue-station/hot-issue-publisher"
from playwright.async_api import async_playwright
from PIL import Image
def b(p): return base64.b64encode(open(p,"rb").read()).decode()
Image.open(R+"/assets/brand/logo_wordmark.png").crop((180,120,1020,510)).save(S+"/ib_logo.png")
LOGOS={"ig":(S+"/ib_logo.png","width:640px;border-radius:24px"),"dk":(R+"/assets/brand/duksim/profile_800.png","width:360px;border-radius:50%")}
V={
 "yt":("dk",["좋은 소식,/덕심저장소가 계속 모아 올게요","구독·좋아요·알림은/큰 힘이 돼요 💜"],"여기 눌러 채널로!/구독·좋아요·알림 꾹"),
 "ig":("ig",["자세한 이야기는/게시물 글에서","좋아요·저장·팔로우는/큰 힘이 돼요 💜"],"오른쪽 버튼으로/좋아요·저장 꾹"),
 "tt":("dk",["다음 소식은/프로필에서 이어 보기","팔로우·좋아요는/큰 힘이 돼요 💜"],"프로필 눌러/팔로우 꾹"),
}
DUR=5.0; FPS=30
import json,sys
D=sys.argv[1]; PFX=sys.argv[2]; MUS=sys.argv[3]
OFF=float(json.load(open(D+"/reel/len.json"))["off"])
async def main():
  async with async_playwright() as pw:
    br=await pw.chromium.launch()
    bg=b(D+"/photos/p1.jpg")
    for k,(lg,lines,ptr) in V.items():
      lp,ls=LOGOS[lg]
      L="".join(f"<div class='ln' data-t='{0.7+i*1.1}' style='color:{'#fff' if i==0 else '#FFC857'}'>{x}</div>" for i,x in enumerate(lines))
      html=f"""<html><head><style>*{{margin:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden;background:#060a14;font-family:'Noto Sans CJK KR',sans-serif}}
.bg{{position:absolute;inset:-40px;background:url(data:image/jpeg;base64,{bg}) center/cover;filter:blur(28px) brightness(.35)}}
.lg{{position:absolute;top:360px;left:0;right:0;text-align:center}}.lg img{{{ls};opacity:0}}
.lines{{position:absolute;top:820px;left:0;right:0;text-align:center}}
.ln{{font-size:66px;font-weight:900;line-height:1.3;margin-bottom:60px;white-space:pre-line}}
.ptr{{position:absolute;right:60px;top:1290px;text-align:right;font-size:54px;font-weight:900;white-space:pre-line}}
.ar{{position:absolute;right:70px;top:1480px;width:260px;height:260px}}
</style></head><body><div class='bg'></div><div class='lg'><img id='lg' src='data:image/png;base64,{b(lp)}'></div><div class='lines'>{L}</div>
<div class='ptr' id='pt' data-t='2.5'>{ptr}</div>
<svg class='ar' id='ar' viewBox='0 0 260 260'><line x1='20' y1='20' x2='220' y2='220' stroke='currentColor' stroke-width='22' stroke-linecap='round'/><polyline points='120,225 225,225 225,120' fill='none' stroke='currentColor' stroke-width='22' stroke-linecap='round' stroke-linejoin='round'/></svg>
<script>
const full=[...document.querySelectorAll('[data-t]')].map(e=>[e,e.textContent.replace(/\\//g,'\\n'),+e.dataset.t]);
window.F=(t)=>{{document.getElementById('lg').style.opacity=Math.min(1,t/0.5);
 document.getElementById('lg').style.transform='scale('+(0.8+0.2*Math.min(1,t/0.5))+')';
 for(const [e,s,st] of full){{const n=Math.max(0,Math.min(s.length,Math.floor((t-st)/0.05)+1)); e.textContent=t<st?'':s.slice(0,n);}}
 const on=Math.floor((t-2.5)*3)%2==0, ar=document.getElementById('ar'), pt=document.getElementById('pt');
 const col=on?'#FFC857':'#FF7850'; pt.style.color=col; ar.style.color=col;
 const n=full[full.length-1][1].length; const done=t>2.5+n*0.05;
 ar.style.display=done?'block':'none'; ar.style.transform=on?'none':'translate(24px,24px)';}}
</script></body></html>"""
      pg=await br.new_page(viewport={"width":1080,"height":1920}); await pg.set_content(html); await pg.wait_for_timeout(200)
      ff=subprocess.Popen(["ffmpeg","-v","error","-y","-f","image2pipe","-framerate",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",f"{D}/reel/end_{k}.mp4"],stdin=subprocess.PIPE)
      for f in range(int(DUR*FPS)):
        await pg.evaluate(f"F({f/FPS})"); ff.stdin.write(await pg.screenshot(type="jpeg",quality=92))
      ff.stdin.close(); ff.wait()
      subprocess.run(["ffmpeg","-v","error","-y","-i",f"{D}/reel/reel_silent.mp4","-i",f"{D}/reel/end_{k}.mp4","-filter_complex",f"[0:v][1:v]xfade=transition=fadeblack:duration=0.4:offset={OFF}[v]","-map","[v]","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-r","30",f"{D}/reel/silent_{k}.mp4"],check=True)
      subprocess.run(["python3",R+"/scripts/add_music.py",f"{D}/reel/silent_{k}.mp4",MUS,f"{D}/reel/{PFX}_{k}.mp4","--start","8"],check=True,cwd=R)
    await br.close()
asyncio.run(main())
