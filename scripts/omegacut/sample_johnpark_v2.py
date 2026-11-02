import subprocess, pathlib, numpy as np, wave, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
R2="/mnt/user-data/uploads/Videos/오메가컷/원본/2026-11-03 02-06-25.mp4"
R3="/mnt/user-data/uploads/Videos/오메가컷/원본/2026-11-03 02-20-22.mp4"
BGM="/home/claude/hot-issue-publisher/music/suno/7_rescene_sparkling_dance.mp3"
LOGO="/home/claude/hot-issue-publisher/assets/brand/logo_wordmark.png"
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H,FPS=1080,1920,30; CROP="crop=1332:749:286:211"; MY=520; MH=607
GRN=(70,255,140); YEL=(255,214,10)
HAND=Image.open("hand.png").convert("RGBA"); HAND=HAND.resize((int(HAND.width*1.6),int(HAND.height*1.6)),Image.LANCZOS)
import numpy as _np
_a=_np.array(HAND)[...,3]; _ys,_xs=_np.nonzero(_a>40); TIPX=int(_xs[_ys==_ys.min()].mean()); TIPY=int(_ys.min())
HEART=Image.open("heart.png").convert("RGBA")
PAT=["tap","double","swipe","hold","cursor"]   # 시그니처 손 동작 5가지, 카드마다 돌려 쓰기
def ripple(d,t,t0,cx,cy):
    if t<t0: return
    q=min(1,(t-t0)/0.45); rr=int(40+160*q); d.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],outline=(255,255,255,int(220*(1-q))),width=8)
    if q<0.5: d.ellipse([cx-30,cy-30,cx+30,cy+30],fill=(255,255,255,int(200*(1-2*q))))
def paste_hand(im,cx,cy,dx,dy,rot,sc,al):
    h=HAND.resize((max(1,int(HAND.width*sc)),max(1,int(HAND.height*sc))),Image.LANCZOS)
    if rot: h=h.rotate(rot,expand=True,resample=Image.BICUBIC)
    if al<1: h.putalpha(h.getchannel("A").point(lambda v:int(v*max(0,al))))
    tx=int(TIPX*sc)+(h.width-int(HAND.width*sc))//2; ty=int(TIPY*sc)+(h.height-int(HAND.height*sc))//2
    im.alpha_composite(h,(cx+dx-tx, cy+dy-ty))
def draw_tap(p,im,t,tap,cx,cy):
    d=ImageDraw.Draw(im)
    if p=="tap":
        ripple(d,t,tap,cx,cy); draw_hand(im,t,tap,cx,cy)
    elif p=="double":
        t1=tap-0.28
        for tt in (t1,tap):
            if tt<=t<tt+0.35: ripple(d,t,tt,cx,cy)
        if t>=tap:   # 하트 팝
            q=min(1,(t-tap)/0.5); sc=0.6+0.9*ease(q); hh=HEART.resize((int(HEART.width*sc),int(HEART.height*sc)))
            hh.putalpha(hh.getchannel("A").point(lambda v:int(v*(1-max(0,q-0.6)/0.4))))
            im.alpha_composite(hh,(cx-hh.width//2,cy-hh.height//2-int(60*q)))
        if t<t1-0.5: return
        if t<t1: q=ease((t-(t1-0.5))/0.45); paste_hand(im,cx,cy,int(200*(1-q)),int(240*(1-q)),-15*(1-q),1,min(1,(t-(t1-0.5))/0.2))
        elif t<tap+0.25:
            press=any(tt<=t<tt+0.1 for tt in (t1,tap)); paste_hand(im,cx,cy,0,8 if press else 0,0,0.9 if press else 1,1)
        else: q=ease((t-tap-0.25)/0.3); paste_hand(im,cx,cy,int(120*q),int(160*q),-10*q,1,1-q)
    elif p=="swipe":
        y0,y1=cy+220,cy-40
        if t<tap-0.75: return
        if t<tap-0.35: q=ease((t-(tap-0.75))/0.35); paste_hand(im,cx,y0,int(160*(1-q)),int(60*(1-q)),-12*(1-q),1,q)
        elif t<tap:
            q=ease((t-(tap-0.35))/0.35); y=int(y0+(y1-y0)*q)
            for k in range(4):   # 위로 쓸어 올리는 잔상
                yy=y+30+k*34; d.line([cx-60+k*8,yy,cx+60-k*8,yy],fill=(255,255,255,int(150*(1-k/4)*q)),width=6)
            paste_hand(im,cx,y,0,0,0,1,1)
        else:
            q=ease((t-tap)/0.4); d.polygon([(cx,y1-80-40*q),(cx-46,y1-20-40*q),(cx+46,y1-20-40*q)],fill=(255,255,255,int(220*(1-q))))
            paste_hand(im,cx,y1,0,int(-40*q),0,1,1-q)
    elif p=="hold":
        t0=tap-0.7
        if t<t0-0.35: return
        if t<t0: q=ease((t-(t0-0.35))/0.35); paste_hand(im,cx,cy,int(200*(1-q)),int(240*(1-q)),-15*(1-q),1,q); return
        if t<tap:   # 꾹 누르는 동안 테두리가 차오름
            q=(t-t0)/(tap-t0); r=92; d.arc([cx-r,cy-r,cx+r,cy+r],-90,-90+360*q,fill=(70,255,140,255),width=12)
            paste_hand(im,cx,cy,0,10,0,0.9,1)
        else:
            ripple(d,t,tap,cx,cy); q=ease((t-tap)/0.35); paste_hand(im,cx,cy,int(120*q),int(160*q),-10*q,1,1-q)
    elif p=="cursor":
        if t<tap-0.6: return
        q=ease((t-(tap-0.6))/0.55) if t<tap else 1
        x=int(cx+300*(1-q)); y=int(cy+200*(1-q))
        pr=0.85 if tap<=t<tap+0.12 else 1
        pts=[(0,0),(0,62),(16,48),(28,76),(40,70),(28,44),(48,44)]
        pts=[(x+int(px*1.4*pr),y+int(py*1.4*pr)) for px,py in pts]
        al=255 if t<tap+0.35 else int(255*max(0,1-(t-tap-0.35)/0.25))
        d.polygon(pts,fill=(255,255,255,al),outline=(0,0,0,al)); d.line(pts+[pts[0]],fill=(0,0,0,al),width=3)
        if t>=tap:   # 클릭 불꽃
            qq=min(1,(t-tap)/0.3)
            import math as _m
            for k in range(8):
                ang=k*_m.pi/4; r0=30+40*qq; r1=r0+28
                d.line([cx+r0*_m.cos(ang),cy+r0*_m.sin(ang),cx+r1*_m.cos(ang),cy+r1*_m.sin(ang)],fill=(255,214,10,int(255*(1-qq))),width=6)
def ease(q): q=max(0,min(1,q)); return q*q*(3-2*q)
def draw_hand(im,t,tap,cx,cy):
    # 시그니처 손가락 탭 (대표 결정 11/3 02:28)
    if t<tap-0.6: return
    if t<tap:                      # 오른쪽 아래에서 다가오기
        q=ease((t-(tap-0.6))/0.55); dx=int(230*(1-q)); dy=int(280*(1-q)); rot=-18*(1-q); sc=1.0; al=min(1,(t-(tap-0.6))/0.2)
    elif t<tap+0.12:               # 누르기
        q=(t-tap)/0.12; dx=0; dy=int(8*q); rot=0; sc=1-0.12*q; al=1
    elif t<tap+0.3:                # 떼기
        q=(t-tap-0.12)/0.18; dx=0; dy=int(8*(1-q)); rot=0; sc=0.88+0.12*q; al=1
    else:                          # 빠지기
        q=ease((t-tap-0.3)/0.3); dx=int(120*q); dy=int(160*q); rot=-10*q; sc=1; al=1-q
    h=HAND.resize((max(1,int(HAND.width*sc)),max(1,int(HAND.height*sc))),Image.LANCZOS)
    if rot: h=h.rotate(rot,expand=True,resample=Image.BICUBIC)
    if al<1: h.putalpha(h.getchannel("A").point(lambda v:int(v*al)))
    tx=int(TIPX*sc)+(h.width-int(HAND.width*sc))//2; ty=int(TIPY*sc)+(h.height-int(HAND.height*sc))//2
    im.alpha_composite(h,(cx+dx-tx, cy+dy-ty))
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
        dim=0.55 if (not tapon or t<dur-0.45) else 0.55+0.45*min(1,(t-(dur-0.45))/0.35)
        im.paste(ImageEnhance.Brightness(s).enhance(dim),(0,MY))
        band(im,i+1,N); d=ImageDraw.Draw(im)
        # card text (types in)
        a=min(1,t/0.35)
        f1=fit(d,l1,FB,54,980); f2=fit(d,l2,F,70,1000)
        w=d.textlength(l1,font=f1); d.text(((W-w)/2,1190+20*(1-a)),l1,font=f1,fill=(255,255,255,int(255*a)))
        a2=min(1,max(0,(t-0.25)/0.35)); w=d.textlength(l2,font=f2); d.text(((W-w)/2,1270+20*(1-a2)),l2,font=f2,fill=(*YEL,int(255*a2)),stroke_width=3,stroke_fill="black")
        # play button + tap
        cx,cy=W//2,MY+MH//2; tap=dur-0.55
        if tapon and t<dur-0.3:
            pr=60; pa=int(230*min(1,t/0.4)); d.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],fill=(0,0,0,int(pa*0.55)),outline=(255,255,255,pa),width=5)
            d.polygon([(cx-20,cy-32),(cx-20,cy+32),(cx+34,cy)],fill=(255,255,255,pa))
        if tapon: draw_tap(PAT[(i+5)%5],im,t,tap,cx,cy)
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-shortest","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac",out])
    return dur, dur-0.55
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
d0,_=card_clip(-1,"오늘 18시 리센느 「PULSE」 컴백!","1위를 기원하며, 존박 × 리센느",hook,2.6,"c_hook.mp4",tapon=False); parts.append("c_hook.mp4"); timeline.append(("card",T,T+d0)); T+=d0
for i,((src,stt,du,cap,sn),(l1,l2)) in enumerate(zip(V,CARDS)):
    st=still(src,stt+0.05)
    cd,tp=card_clip(i,l1,l2,st,2.8,f"c{i}.mp4"); parts.append(f"c{i}.mp4"); taps.append(T+tp); timeline.append(("card",T,T+cd)); T+=cd
    video_clip(i,src,stt,du,cap,sn,f"v{i}.mp4"); parts.append(f"v{i}.mp4"); timeline.append(("video",T,T+du)); T+=du
# end card
e=frame_base(hook); band(e,N-1,N); d=ImageDraw.Draw(e)
e.paste(ImageEnhance.Brightness(hook).enhance(0.35),(0,MY)); band(e,N-1,N); d=ImageDraw.Draw(e)
for y,t,c,f in [(MY+150,"10월 28일엔 맥도날드 광고에",(255,255,255),font(FB,54)),(MY+240,"'존박 세트'까지 등장",YEL,font(F,72)),(1190,"오늘 18시 리센느 「PULSE」",(255,255,255),font(FB,56)),(1270,"이번에도 1위 가자 💜".replace(" 💜",""),GRN,font(F,72))]:
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
