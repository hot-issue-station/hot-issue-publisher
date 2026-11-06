import asyncio, subprocess, sys, os, importlib.util
S="/tmp/claude-0/-home-claude/eb774544-8081-59eb-9d1c-8cc1d162e9ef/scratchpad"
spec=importlib.util.spec_from_file_location("mc",S+"/make_cards_rs2.py"); src=open(S+"/make_cards_rs2.py").read()
# reuse card data, css, b64 without running main
ns={}; exec(src.split("async def main")[0],ns)
cards,CSS,b64=ns["cards"],ns["CSS"],ns["b64"]
from playwright.async_api import async_playwright
SUB=[
("リセンヌの11月6日 — チャート1位、ディズニー、そして初の音楽番組",),
("午前11時：Melon TOP100 1位・Bugs 2位・Genie 3位・FLO 4位",),
("Melon TOP10に6曲、21位以内に10曲",),
("「Pinball」がTOP100 21位まで上昇",),
("Bugsでも100位以内に10曲",),
("「PULSE」初日13万1,893枚、自己最高",),
("ディズニー映画「HEXED」エンディングに「With」",),
("今朝公開：魔女に変身した5人の撮影ビハインド",),
("昨夜公開：ジャケット撮影ビハインド、13時間で42万回",),
("「With」MV、公開2日で1,263万回",),
("評論家「最後まで残る香り」",),
("今夜「ミュージックバンク」で初ステージ💜",),
]
FPS=30; XF=0.4
DUR=[3.6]+[3.4]*10+[4.0]
PAT=["A","B","C","D","A","B","C","D","A","B","C","D"]
PH={"A":"kbin","B":"panr","C":"popout","D":"diag"}
TX={"A":"rise","B":"slidein","C":"pop","D":"wipe"}
TRANS=["circleopen","slideleft","zoomin","wipeup","hblur","smoothleft","radial","fadeblack"]
ANIM="""
@keyframes kbin{from{transform:scale(1.0)}to{transform:scale(1.16) translate(-2%,-2%)}}
@keyframes panr{from{transform:scale(1.18) translate(-5%,0)}to{transform:scale(1.18) translate(5%,0)}}
@keyframes popout{from{transform:scale(1.45)}to{transform:scale(1.02)}}
@keyframes diag{from{transform:scale(1.2) translate(-4%,-3%)}to{transform:scale(1.2) translate(4%,3%)}}
@keyframes rise{from{opacity:0;transform:translateY(50px)}to{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-120px)}to{opacity:1;transform:none}}
@keyframes pop{0%{opacity:0;transform:scale(.8)}70%{opacity:1;transform:scale(1.05)}100%{opacity:1;transform:scale(1)}}
@keyframes wipe{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes flash{0%{opacity:.55}100%{opacity:0}}
html,body{margin:0;width:1080px;height:1920px;background:#060a14;overflow:hidden;font-family:'Noto Sans CJK KR',sans-serif}
.band{position:absolute;top:0;left:0;right:0;height:360px;background:#060a14;padding:70px 60px 0}
.band .src{font-size:26px;color:#7f8db0;margin-bottom:18px}
.band .w{font-size:50px;font-weight:700;color:#F4F7FF}
.band .y{font-size:68px;font-weight:900;color:#FFC857;margin-top:6px;letter-spacing:-1px}
.prog{position:absolute;top:350px;left:0;height:8px;background:#C9A6FF}
.wrap{position:absolute;top:372px;left:54px;width:1080px;height:1350px;transform:scale(.9);transform-origin:0 0;border-radius:30px;overflow:hidden}
.sb{position:absolute;left:0;right:0;bottom:0;padding:70px 26px 18px;background:linear-gradient(transparent,rgba(0,0,0,.82) 45%);text-align:center}
.sb .jp{font-family:'Noto Sans CJK JP';font-size:32px;font-weight:700;color:#fff;line-height:1.3}
.sb .th{font-family:'Noto Sans Thai';font-size:31px;font-weight:600;color:#FFE7A3;line-height:1.35;margin-top:6px}
.fl{position:absolute;inset:0;background:#fff;pointer-events:none}
"""
TITLE=("[출처] 멜론·벅스·지니·플로·일간스포츠·YTN · 이미지 더뮤즈·디즈니 코리아","리센느 하루 발자취 #2","차트 정상, 디즈니, 첫 음악방송")
def page(i,card,total_t0,total):
    tag,h,p,cover=card; pat=PAT[i-1]
    inner_css=CSS.replace("body{","#c{").replace("*{margin:0;box-sizing:border-box}","").replace(".cover ",".cv ")
    phanim=f"animation:{PH[pat]} {DUR[i-1]}s linear forwards;"
    ta="" if cover else f"opacity:0;animation:{TX[pat]} .6s cubic-bezier(.2,.7,.2,1) forwards;"
    sub=f"<div class='sub'>{p}</div>" if cover else ""
    sbst="" if cover else "opacity:0;animation:rise .6s ease-out .3s forwards;"
    def d(x): return "" if cover else f"animation-delay:{x}s;"
    return f"""<html><head><style>*{{margin:0;box-sizing:border-box}}{ANIM}{inner_css}
.ph img{{{phanim}}}
</style></head><body>
<div class='band'><div class='src'>{TITLE[0]}</div><div class='w'>{TITLE[1]}</div><div class='y'>{TITLE[2]}</div></div>
<div class='prog' id='pg'></div>
<div class='wrap'><div id='c' class='{"cv" if cover else ""}' style='position:relative;width:1080px;height:1350px;background:#0B1220;color:#F4F7FF'>
<div class='top'><span><b>●</b> 덕심저장소</span><span>리센느 하루 발자취 #2 · {i}/12</span></div>
<div class='ph'><img src='data:image/jpeg;base64,{b64(i)}'><div class='sb' style='{sbst}'><div class='jp'>🇯🇵 {SUB[i-1][0]}</div></div></div>
<div class='tag' style='{ta}{d(.25)}'>{tag}</div><h1 style='{ta}{d(.45)}'>{h}</h1><p style='{ta}{d(.85)}'>{p}</p>{sub}
<div class='foot'><span>이미지 · {ns['CRED'](i)}</span><span>출처 멜론·벅스·지니·플로·일간스포츠·YTN 외</span></div></div>
{"<div class='fl' style='animation:flash .35s ease-out forwards'></div>" if i in (2,7) else ""}
</div></body></html>"""
async def main():
    out=S+"/rs2/reel"; os.makedirs(out,exist_ok=True)
    total=sum(DUR)-XF*(len(DUR)-1); t0=0
    async with async_playwright() as pw:
        b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":1080,"height":1920})
        for i,card in enumerate(cards,1):
            await pg.set_content(page(i,card,t0,total)); await pg.wait_for_timeout(150)
            n=int(DUR[i-1]*FPS)
            ff=subprocess.Popen(["ffmpeg","-v","error","-y","-f","image2pipe","-framerate",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",f"{out}/c{i}.mp4"],stdin=subprocess.PIPE)
            for f in range(n):
                t=f/FPS; gt=t0+t
                await pg.evaluate(f"""()=>{{document.getAnimations().forEach(a=>{{a.pause();a.currentTime={t*1000}}});document.getElementById('pg').style.width=({gt}/{total}*1080)+'px'}}""")
                ff.stdin.write(await pg.screenshot(type="jpeg",quality=92))
            ff.stdin.close(); ff.wait(); t0+=DUR[i-1]-XF
        await b.close()
    # xfade chain
    ins=[]; [ins.extend(["-i",f"{out}/c{i}.mp4"]) for i in range(1,13)]
    f=[]; prev="0:v"; off=0
    for k in range(1,12):
        off+=DUR[k-1]-XF; o=f"x{k}" if k<11 else "vx"
        f.append(f"[{prev}][{k}:v]xfade=transition={TRANS[(k-1)%len(TRANS)]}:duration={XF}:offset={off:.3f}[{o}]"); prev=o
    subprocess.run(["ffmpeg","-v","error","-y",*ins,"-filter_complex",";".join(f),"-map","[vx]","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-r","30",f"{out}/reel_silent.mp4"],check=True)
    print("done",total); import json; json.dump({"off":total-0.4},open(out+"/len.json","w"))
asyncio.run(main())
