import subprocess, pathlib, numpy as np, wave, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
R2="/mnt/user-data/uploads/Videos/오메가컷/원본/2026-11-03 02-06-25.mp4"
R3="/mnt/user-data/uploads/Videos/오메가컷/원본/2026-11-03 02-20-22.mp4"
BGM="/home/claude/hot-issue-publisher/music/suno/7_rescene_sparkling_dance.mp3"
LOGO="/home/claude/hot-issue-publisher/assets/brand/logo_wordmark.png"
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H,FPS=1080,1920,30; CROP="crop=1332:749:286:211"; MY=520; MH=607
GRN=(70,255,140); YEL=(255,214,10)
def run(a): subprocess.run(a,check=True)
def font(p,s): return ImageFont.truetype(p,s)
def fit(d,txt,p,sz,maxw):
    while sz>36:
        f=font(p,sz)
        if d.textlength(txt,font=f)<=maxw: return f
        sz-=2
    return font(p,sz)
# scenes: (kind, ...)
V=[ # src, start, dur, caption, source
 (R3,16.38+0.1,5.4,"원이 등장 (Guest)","존이냐박이냐 · 리센느와 멜론 1위 기우제 지냈습니다"),
 (R3,4.25+0.1,7.8,"함께 부른 「LOVE ATTACK」","존이냐박이냐 · 리센느와 멜론 1위 기우제 지냈습니다"),
 (R2,81.81+0.1,5.8,"존박 ver. 1,035만 회","존이냐박이냐 · LOVE ATTACK (존박 ver.)"),
 (R2,16.85+0.1,6.4,"\"이 영상 보신 적 있으세요?\"","존이냐박이냐 · 맥도날드에서 랩으로 주문하는 존박"),
 (R2,109.93+0.1,4.8,"맥도날드 빅아치 광고","한국 맥도날드 · BIG ARCH 빅아치(30s)"),
]
CARDS=[ # before each video: (line1, line2)
 ("6월, 역주행 중이던 리센느","존박이 리센느를 초대했어요"),
 ("그리고 그 자리에서","함께 부른 노래"),
 ("이 무대를 담은 존박 버전은","1,000만 회를 넘었어요"),
 ("10월, 이번엔 맥도날드에서","'랩'으로 주문을?"),
 ("알고 보니 맥도날드 신메뉴","'빅아치' 홍보 영상이었어요"),
]
def still(src,t):
    p=f"st_{abs(hash((src,t)))%10**8}.png"
    run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",src,"-frames:v","1","-vf",f"{CROP},scale=1080:{MH}",p]); return Image.open(p).convert("RGB")
def frame_base(bgimg):
    bg=bgimg.resize((W, int(W*bgimg.height/bgimg.width))).resize((int(H*bgimg.width/bgimg.height),H))
    x=(bg.width-W)//2; bg=bg.crop((x,0,x+W,H)).filter(ImageFilter.GaussianBlur(28)); bg=ImageEnhance.Brightness(bg).enhance(0.45)
    return bg.convert("RGBA")
def band(im,step,n):
    d=ImageDraw.Draw(im); d.rectangle([0,0,W,470],fill=(0,0,0,255)); d.rectangle([0,MY+MH,W,H],fill=(0,0,0,235))
    tf=font(F,78); l1,l2="리센느 노래 부르던 존박,","이번엔 맥도날드에서 랩?"
    w1=d.textlength(l1,font=tf); d.rectangle([(W-w1)/2-14,150,(W+w1)/2+14,250],fill=GRN); d.text(((W-w1)/2,152),l1,font=tf,fill="black")
    w2=d.textlength(l2,font=tf); d.text(((W-w2)/2,282),l2,font=tf,fill="white")
    bw=(W-80-8*(n-1))/n
    for k in range(n):
        x=40+k*(bw+8); d.rounded_rectangle([x,420,x+bw,430],5,fill=GRN if k<=step else (255,255,255,70))
    lg=Image.open(LOGO).convert("RGBA").crop((180,120,1020,510)).resize((300,139)); im.alpha_composite(lg,((W-300)//2,1660))
    df=font(FB,34); t="덕심저장소 #1"; tw=d.textlength(t,font=df); d.text(((W-tw)/2,1815),t,font=df,fill=(200,160,255))
N=len(V)+2
def card_clip(i,l1,l2,st,dur=2.8,out=None,tapon=True):
    frames=int(dur*FPS); base=frame_base(st)
    tmp=pathlib.Path(f"cf{i}"); tmp.mkdir(exist_ok=True)
    for k in range(frames):
        t=k/FPS; im=base.copy(); d=ImageDraw.Draw(im)
        # media still (dim) with gentle zoom
        z=1+0.03*t/dur; s=st.resize((int(1080*z),int(MH*z))); s=s.crop(((s.width-1080)//2,(s.height-MH)//2,(s.width-1080)//2+1080,(s.height-MH)//2+MH))
        dim=0.55 if (not tapon or t<dur-0.45) else 0.55+0.45*min(1,(t-(dur-0.45))/0.3)
        im.paste(ImageEnhance.Brightness(s).enhance(dim),(0,MY))
        band(im,i+1,N); d=ImageDraw.Draw(im)
        # card text (types in)
        a=min(1,t/0.35)
        f1=fit(d,l1,FB,54,980); f2=fit(d,l2,F,70,1000)
        w=d.textlength(l1,font=f1); d.text(((W-w)/2,1190+20*(1-a)),l1,font=f1,fill=(255,255,255,int(255*a)))
        a2=min(1,max(0,(t-0.25)/0.35)); w=d.textlength(l2,font=f2); d.text(((W-w)/2,1270+20*(1-a2)),l2,font=f2,fill=(*YEL,int(255*a2)),stroke_width=3,stroke_fill="black")
        # play button + tap
        cx,cy=W//2,MY+MH//2; tap=dur-0.75
        if tapon and t<dur-0.3:
            pr=60; pa=int(230*min(1,t/0.4)); d.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],fill=(0,0,0,int(pa*0.55)),outline=(255,255,255,pa),width=5)
            d.polygon([(cx-20,cy-32),(cx-20,cy+32),(cx+34,cy)],fill=(255,255,255,pa))
        if tapon and tap-0.35<=t<tap:   # finger approaching
            q=(t-(tap-0.35))/0.35; fx=int(cx+170-140*q); fy=int(cy+190-160*q); d.ellipse([fx-34,fy-34,fx+34,fy+34],fill=(255,255,255,170),outline=(0,0,0,120),width=3)
        if tapon and t>=tap:            # ripple
            q=min(1,(t-tap)/0.45); rr=int(40+160*q); d.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],outline=(255,255,255,int(220*(1-q))),width=8)
            if q<0.5: d.ellipse([cx-30,cy-30,cx+30,cy+30],fill=(255,255,255,int(200*(1-2*q))))
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-shortest","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac",out])
    return dur, dur-0.75
def video_clip(i,src,stt,du,cap,srcname,out):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); band(ov,i+1,N); d=ImageDraw.Draw(ov)
    cf=fit(d,cap,F,62,960); cw=d.textlength(cap,font=cf)
    d.rounded_rectangle([(W-cw)/2-28,1200,(W+cw)/2+28,1300],18,fill=(20,20,20,255)); d.text(((W-cw)/2,1208),cap,font=cf,fill=YEL,stroke_width=4,stroke_fill="black")
    sf=font(FB,30); s="출처: "+srcname; sw=d.textlength(s,font=sf); d.text(((W-sw)/2,1335),s,font=sf,fill=(170,180,200))
    p=f"vo{i}.png"; ov.save(p)
    run(["ffmpeg","-v","error","-y","-ss",str(stt),"-t",str(du),"-i",src,"-i",p,"-filter_complex",
      f"[0:v]{CROP},split[a][b];[a]scale=1080:-2,boxblur=28:2,eq=brightness=-0.4,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[b]scale=1080:{MH}[fg];[bg][fg]overlay=0:{MY}[v0];[v0][1]overlay=0:0,fps={FPS},format=yuv420p[v];[0:a]afade=t=in:st=0:d=0.12,afade=t=out:st={du-0.25}:d=0.25,aresample=48000,aformat=channel_layouts=stereo[a2]",
      "-map","[v]","-map","[a2]","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac","-b:a","192k",out])
parts=[]; timeline=[]; taps=[]; T=0
# hook card
hook=still(R3,4.4)
d0,_=card_clip(-1,"오늘의 덕심저장소","존박 × 리센느 이야기",hook,2.6,"c_hook.mp4",tapon=False); parts.append("c_hook.mp4"); timeline.append(("card",T,T+d0)); T+=d0
for i,((src,stt,du,cap,sn),(l1,l2)) in enumerate(zip(V,CARDS)):
    st=still(src,stt+0.05)
    cd,tp=card_clip(i,l1,l2,st,2.8,f"c{i}.mp4"); parts.append(f"c{i}.mp4"); taps.append(T+tp); timeline.append(("card",T,T+cd)); T+=cd
    video_clip(i,src,stt,du,cap,sn,f"v{i}.mp4"); parts.append(f"v{i}.mp4"); timeline.append(("video",T,T+du)); T+=du
# end card
e=frame_base(hook); band(e,N-1,N); d=ImageDraw.Draw(e)
e.paste(ImageEnhance.Brightness(hook).enhance(0.35),(0,MY)); band(e,N-1,N); d=ImageDraw.Draw(e)
for y,t,c,f in [(MY+150,"10월 28일엔 맥도날드 광고에",(255,255,255),font(FB,54)),(MY+240,"'존박 세트'까지 등장",YEL,font(F,72)),(1200,"노래로, 랩으로…",(255,255,255),font(FB,56)),(1280,"존박의 다음 무대는?",GRN,font(F,72))]:
    w=d.textlength(t,font=f); d.text(((W-w)/2,y),t,font=f,fill=c,stroke_width=2,stroke_fill="black")
sf=font(FB,28); s="출처: 엑스포츠뉴스(10/30) · OSEN(11/2)"; w=d.textlength(s,font=sf); d.text(((W-w)/2,1400),s,font=sf,fill=(170,180,200))
e.convert("RGB").save("end.png")
ED=4.0
run(["ffmpeg","-v","error","-y","-loop","1","-t",str(ED),"-i","end.png","-f","lavfi","-t",str(ED),"-i","anullsrc=r=48000:cl=stereo","-vf","fade=t=in:st=0:d=0.25,fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac","-shortest","end.mp4"])
parts.append("end.mp4"); timeline.append(("card",T,T+ED)); T+=ED
pathlib.Path("list2.txt").write_text("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","list2.txt","-c:v","copy","-c:a","aac","-ar","48000","body.mp4"])
# BGM ducking: volume expression
expr=[]
for k,(kind,a,b) in enumerate(timeline):
    pass
def vol_at(t):
    for kind,a,b in timeline:
        if a<=t<b:
            if kind=="card": return 0.55
            # ramp down 0.3s in, up 0.3s at end
            if t-a<0.3: return 0.55-(0.55-0.10)*(t-a)/0.3
            if b-t<0.3: return 0.10+(0.55-0.10)*(1-(b-t)/0.3)
            return 0.10
    return 0.55
SR=48000
bg=subprocess.run(["ffmpeg","-v","error","-i",BGM,"-t",str(T),"-ac","2","-ar",str(SR),"-f","s16le","-"],capture_output=True).stdout
x=np.frombuffer(bg,dtype="<i2").reshape(-1,2).astype(np.float32)/32768
n=len(x); tt=np.arange(n)/SR
g=np.array([vol_at(t) for t in np.arange(0,T+0.01,0.01)]); gi=np.interp(tt,np.arange(len(g))*0.01,g)
x=x*gi[:,None]; fo=int(1.2*SR); x[-fo:]*=np.linspace(1,0,fo)[:,None]
# tap clicks
for tp in taps:
    i0=int(tp*SR); m=int(0.06*SR); q=np.arange(m)/SR; c=(np.random.default_rng(1).uniform(-1,1,m)*np.exp(-q*90)+0.8*np.sin(2*np.pi*1500*q)*np.exp(-q*120))*0.5
    x[i0:i0+m]+=c[:,None]
with wave.open("bgm.wav","wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x,-1,1)*32767).astype("<i2").tobytes())
run(["ffmpeg","-v","error","-y","-i","body.mp4","-i","bgm.wav","-filter_complex","[0:a]volume=1.0[v];[1:a]volume=1.0[m];[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","johnpark_sample_v2.mp4"])
print("T",round(T,2),timeline)
