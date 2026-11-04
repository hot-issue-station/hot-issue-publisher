MC13_T=float(__import__("os").environ.get("MC13_T","20"));MC13B_T=float(__import__("os").environ.get("MC13B_T","10"));V26_T=float(__import__("os").environ.get("V26_T","10"));FIN_T=float(__import__("os").environ.get("FIN_T","70"))
OC="/home/claude/hot-issue-publisher/scripts/omegacut"
import subprocess, pathlib, numpy as np, wave, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
BGM="/home/claude/hot-issue-publisher/music/suno/6_recap_good_times.mp3"
LOGO="/home/claude/hot-issue-publisher/assets/brand/logo_wordmark.png"
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H,FPS=1080,1920,30; CROP="crop=1332:749:286:211"; MY=520; MH=607
GRN=(70,255,140); YEL=(255,214,10)
HAND=Image.open(OC+"/hand.png").convert("RGBA"); HAND=HAND.resize((int(HAND.width*1.6),int(HAND.height*1.6)),Image.LANCZOS)
import numpy as _np
_a=_np.array(HAND)[...,3]; _ys,_xs=_np.nonzero(_a>40); TIPX=int(_xs[_ys==_ys.min()].mean()); TIPY=int(_ys.min())
HEART=Image.open(OC+"/heart.png").convert("RGBA")
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
    while sz>20:
        f=font(p,sz)
        if d.textlength(txt,font=f)<=maxw: return f
        sz-=2
    return font(p,sz)
# 덕심저장소 #3 베스티 「연애의 조건」 — 원본: 노트북 OBS 녹화(11/4 09:48), 공식 채널만
B="/home/claude/bestie/"
MV=B+"c1.mp4"; RS=B+"c3.mp4"; ST=B+"c6.mp4"; MC13=B+"d2.mp4"; MC13B=B+"d3.mp4"; V26=B+"d4.mp4"; FIN=B+"d6.mp4"
PORT={RS}
PW,PH,PY=540,960,480
SRC_MV="1theK (원더케이) · [MV] BESTie _ Love Options"; SRC_ST="MBCkpop · Show! MusicCore 261031"
V=[ # src, start, dur, caption, jpcap, source
 (MC13,MC13_T,6.5,"발매 당일 첫 무대 (2013.10.17)","発売当日の初ステージ（2013.10.17）","Mnet K-POP · Love Options by BESTie of Mcountdown 2013.10.17"),
 (MV,6.0,5.5,"원곡 뮤직비디오","原曲MV","1theK (원더케이) · [MV] BESTie _ Love Options"),
 (MC13B,MC13B_T,5.5,"2013년 음악중심","2013年 音楽中心","MBCkpop · Music Core 20131019"),
 (ST,33.2,6.5,"[혜연] 트로트 가수로","［ヘヨン］トロット歌手に",SRC_ST),
 (ST,18.2,6.5,"[유지] 가수·뮤지컬 배우로","［ユジ］歌手・ミュージカル俳優に",SRC_ST),
 (ST,25.2,6.5,"[해령] 배우로","［ヘリョン］俳優に",SRC_ST),
 (ST,40.6,6.5,"[다혜] '환승연애3'으로","［ダヘ］『乗り換え恋愛3』に",SRC_ST),
 (RS,0.0,7.5,"리센느의 「연애의 조건」 챌린지","RESCENEの「恋愛の条件」チャレンジ","RESCENE 공식 유튜브 쇼츠"),
 (V26,V26_T,6.5,"2026 버전 안무 영상","2026年ver. 振付動画","다혜가다했다DAHYE · 연애의 조건 안무영상 2026.ver"),
 (ST,0.2,7.0,"약 4000일 만의 음악방송","約4000日ぶりの音楽番組",SRC_ST),
 (FIN,FIN_T,8.0,"다시, 네 사람의 무대","再び、4人のステージ",SRC_ST),
]
CARDS=[
 ("2013년 7월 데뷔한 4인조 베스티","10월 17일, 두 번째 싱글 「연애의 조건」","2013年7月デビューのBESTie、10/17に2ndシングル「恋愛の条件」"),
 ("\"TOP100에 정말 들고 싶었어요\" — 유지","하지만 차트엔 오르지 못했어요","「TOP100に本当に入りたかった」でもチャートには届かず"),
 ("2017년 다혜가 팀을 떠나고","2018년, 베스티는 해체했어요","2017年にダヘが脱退、2018年にBESTieは解散"),
 ("그 뒤 네 사람은 각자의 길로","혜연은 트로트 가수가 되어","その後4人はそれぞれの道へ。ヘヨンはトロット歌手に"),
 ("유지는","가수이자 뮤지컬 배우로","ユジは歌手・ミュージカル俳優に"),
 ("해령은","배우로 활동을 넓혔고","ヘリョンは俳優に"),
 ("다혜는 유튜브 커버 영상을 올리다","2023년 '환승연애3'에 출연했어요","ダヘはカバー動画を経て、2023年『乗り換え恋愛3』に出演"),
 ("2026년 여름, 숏폼에서 다시 퍼진 노래","리센느도 챌린지에 참여!","2026年夏、ショート動画で再ブレイク。RESCENEもチャレンジに参加"),
 ("8월 27일 멜론 차트 첫 진입","10월 17일, 발매 13주년에 재결합","8/27メロン初チャートイン、10/17発売13周年に再結成"),
 ("그리고 10월 31일","네 사람이 다시 음악중심 무대에","そして10/31、4人で再び音楽中心のステージへ"),
 ("13년 전 그 노래로","마지막까지 함께한 무대","13年前のあの歌で、最後まで一緒に"),
]
TITLE1,TITLE2="해체 8년 만에 다시 모였다는","베스티 「연애의 조건」"
JPT="解散から8年、再び集まったBESTie「恋愛の条件」"
JPC=(205,215,235)
def jpline(d,t,y,sz=38,maxw=1000,a=255):
    f=fit(d,t,FB,sz,maxw); w=d.textlength(t,font=f); d.text(((W-w)/2,y),t,font=f,fill=(*JPC,a),stroke_width=2,stroke_fill="black")
N=len(V)+2
def band(im,step,port=False):
    d=ImageDraw.Draw(im); d.rectangle([0,0,W,470],fill=(0,0,0,255))
    if not port: d.rectangle([0,MY+MH,W,H],fill=(0,0,0,235))
    else: d.rectangle([0,PY+PH,W,H],fill=(0,0,0,235))
    tf=font(F,78)
    w1=d.textlength(TITLE1,font=tf); d.rectangle([(W-w1)/2-14,150,(W+w1)/2+14,250],fill=GRN); d.text(((W-w1)/2,152),TITLE1,font=tf,fill="black")
    w2=d.textlength(TITLE2,font=tf); d.text(((W-w2)/2,276),TITLE2,font=tf,fill="white")
    jpline(d,JPT,370,34,1000)
    bw=(W-80-8*(N-1))/N
    for k in range(N):
        x=40+k*(bw+8); d.rounded_rectangle([x,446,x+bw,454],5,fill=GRN if k<=step else (255,255,255,70))
    lg=Image.open(LOGO).convert("RGBA").crop((180,120,1020,510)).resize((300,139)); im.alpha_composite(lg,((W-300)//2,1660))
    df=font(FB,34); t="덕심저장소 #3"; tw=d.textlength(t,font=df); d.text(((W-tw)/2,1815),t,font=df,fill=(200,160,255))
def still(src,t):
    p=f"/home/claude/bestie/st_{abs(hash((src,t)))%10**8}.png"
    run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",src,"-frames:v","1",p]); return Image.open(p).convert("RGB")
def frame_base(bgimg):
    bg=bgimg.resize((int(H*bgimg.width/bgimg.height),H)) if bgimg.width/bgimg.height>W/H else bgimg.resize((W,int(W*bgimg.height/bgimg.width)))
    x=(bg.width-W)//2; y=(bg.height-H)//2; bg=bg.crop((x,y,x+W,y+H)).filter(ImageFilter.GaussianBlur(28)); bg=ImageEnhance.Brightness(bg).enhance(0.45)
    return bg.convert("RGBA")
def media(st):
    # 카드 화면 가운데 그림: 가로 영상은 1080xMH, 세로 영상은 가운데에 맞춤
    box=Image.new("RGB",(1080,MH),(0,0,0))
    if st.width>=st.height: return st.resize((1080,MH))
    h=MH; w=int(st.width*h/st.height); box.paste(st.resize((w,h)),((1080-w)//2,0)); return box
def card_clip(i,l1,l2,st,dur=2.8,out=None,tapon=True,jp=''):
    frames=int(dur*FPS); base=frame_base(st); mimg=media(st)
    tmp=pathlib.Path(O+f"cf{i}"); tmp.mkdir(exist_ok=True)
    for k in range(frames):
        t=k/FPS; im=base.copy(); d=ImageDraw.Draw(im)
        z=1+0.03*t/dur; s=mimg.resize((int(1080*z),int(MH*z))); s=s.crop(((s.width-1080)//2,(s.height-MH)//2,(s.width-1080)//2+1080,(s.height-MH)//2+MH))
        dim=0.55 if (not tapon or t<dur-0.45) else 0.55+0.45*min(1,(t-(dur-0.45))/0.35)
        im.paste(ImageEnhance.Brightness(s).enhance(dim),(0,MY))
        band(im,i+1); d=ImageDraw.Draw(im)
        a=min(1,t/0.35)
        f1=fit(d,l1,FB,54,980); f2=fit(d,l2,F,70,1000)
        w=d.textlength(l1,font=f1); d.text(((W-w)/2,1190+20*(1-a)),l1,font=f1,fill=(255,255,255,int(255*a)))
        a2=min(1,max(0,(t-0.25)/0.35)); w=d.textlength(l2,font=f2); d.text(((W-w)/2,1270+20*(1-a2)),l2,font=f2,fill=(*YEL,int(255*a2)),stroke_width=3,stroke_fill="black")
        if jp: jpline(d,jp,1372,34,1000,int(255*min(1,max(0,(t-0.45)/0.35))))
        cx,cy=W//2,MY+MH//2; tap=dur-0.55
        if tapon and t<dur-0.3:
            pr=60; pa=int(230*min(1,t/0.4)); d.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],fill=(0,0,0,int(pa*0.55)),outline=(255,255,255,pa),width=5)
            d.polygon([(cx-20,cy-32),(cx-20,cy+32),(cx+34,cy)],fill=(255,255,255,pa))
        if tapon: draw_tap(PAT[(i+5)%5],im,t,tap,cx,cy)
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-shortest","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac",out])
    return dur, dur-0.55
def video_clip(i,src,stt,du,cap,jpcap,srcname,out):
    port=src in PORT
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); band(ov,i+1,port); d=ImageDraw.Draw(ov)
    cy0=1200 if not port else 1458
    cf=fit(d,cap,F,62 if not port else 54,960); cw=d.textlength(cap,font=cf)
    d.rounded_rectangle([(W-cw)/2-28,cy0,(W+cw)/2+28,cy0+(100 if not port else 86)],18,fill=(20,20,20,255)); d.text(((W-cw)/2,cy0+8),cap,font=cf,fill=YEL,stroke_width=4,stroke_fill="black")
    jpline(d,jpcap,cy0+(118 if not port else 96),34 if not port else 30,1000)
    sf=font(FB,30 if not port else 26); s="출처: "+srcname; sw=d.textlength(s,font=sf); d.text(((W-sw)/2,cy0+(200 if not port else 140)),s,font=sf,fill=(170,180,200))
    p=O+f"vo{i}.png"; ov.save(p)
    if not port:
        fc=f"[0:v]split[a][b];[a]scale=1080:-2,boxblur=28:2,eq=brightness=-0.4,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[b]scale=1080:{MH}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:{MY}+({MH}-h)/2[v0]"
    else:
        fc=f"[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:2,eq=brightness=-0.4[bg];[b]scale={PW}:{PH}[fg];[bg][fg]overlay={(W-PW)//2}:{PY}[v0]"
    run(["ffmpeg","-v","error","-y","-ss",str(stt),"-t",str(du),"-i",src,"-i",p,"-filter_complex",
      fc+f";[v0][1]overlay=0:0,fps={FPS},format=yuv420p[v];[0:a]afade=t=in:st=0:d=0.12,afade=t=out:st={du-0.25}:d=0.25,aresample=48000,aformat=channel_layouts=stereo[a2]",
      "-map","[v]","-map","[a2]","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac","-b:a","192k",out])
O="/home/claude/bestie/s2/"; pathlib.Path(O).mkdir(exist_ok=True)
parts=[]; timeline=[]; taps=[]; T=0
hook=still(MC13,MC13_T+2)
d0,_=card_clip(-1,"13년 전, 차트에 오르지 못한 노래","네 사람의 13년 이야기",hook,2.8,O+"c_hook.mp4",tapon=False,jp="13年前チャート圏外だった歌、4人の13年の物語"); parts.append(O+"c_hook.mp4"); timeline.append(("card",T,T+d0)); T+=d0
for i,((src,stt,du,cap,jc,sn),(l1,l2,jp)) in enumerate(zip(V,CARDS)):
    st=still(src,stt+0.3)
    cd,tp=card_clip(i,l1,l2,st,2.8,O+f"k{i}.mp4",jp=jp); parts.append(O+f"k{i}.mp4"); taps.append(T+tp); timeline.append(("card",T,T+cd)); T+=cd
    video_clip(i,src,stt,du,cap,jc,sn,O+f"v{i}.mp4"); parts.append(O+f"v{i}.mp4"); timeline.append(("video",T,T+du)); T+=du
endst=still(FIN,FIN_T+6)
e=frame_base(endst); e.paste(ImageEnhance.Brightness(media(endst)).enhance(0.35),(0,MY)); band(e,N-1); d=ImageDraw.Draw(e)
for y,t,c,f in [(MY+130,"11/2 멜론 TOP100 25위 · 벅스 9위",(255,255,255),font(FB,52)),(MY+220,"\"어디까지 올라가는 거예요\"",YEL,font(F,64)),(1190,"13년 만에 닿은 그때의 꿈",(255,255,255),font(FB,56)),(1270,"함께 응원해 주세요",GRN,font(F,72))]:
    w=d.textlength(t,font=f); d.text(((W-w)/2,y),t,font=f,fill=c,stroke_width=2,stroke_fill="black")
jpline(d,"11/2 メロン25位・Bugs9位「どこまで上がるの？」（ヘリョン）",MY+320,32,1000)
jpline(d,"13年越しに届いたあの頃の夢、一緒に応援してください",1372,34,1000)
s="출처: 톱스타뉴스(11/2) · 코리아타임스(9/16) · 위키트리·인사이트(10/17) · iMBC(10/29)"; sf=fit(d,s,FB,28,1020); w=d.textlength(s,font=sf); d.text(((W-w)/2,1440),s,font=sf,fill=(170,180,200))
e.convert("RGB").save(O+"end.png")
ED=5.2
def end_clip(out):
    base=Image.open(O+"end.png").convert("RGBA"); frames=int(ED*FPS); tmp=pathlib.Path(O+"cfe"); tmp.mkdir(exist_ok=True)
    LK=(W//2-180,975+40); SB=(W//2+180,975+40); tL,tS=2.0,3.4
    bf=font(F,44)
    for k in range(frames):
        t=k/FPS; im=base.copy(); d=ImageDraw.Draw(im)
        a=ease((t-0.5)/0.4)
        if a>0:
            oy=int(30*(1-a)); al=int(255*a)
            liked=t>=tL; x,y=LK; d.rounded_rectangle([x-150,y-44+oy,x+150,y+44+oy],44,fill=((140,90,255,al) if liked else (255,255,255,al)))
            tx="좋아요 ♥" if liked else "좋아요"; w=d.textlength(tx,font=bf); d.text((x-w/2,y-30+oy),tx,font=bf,fill=((255,255,255,al) if liked else (20,20,20,al)))
            subd=t>=tS; x,y=SB; d.rounded_rectangle([x-150,y-44+oy,x+150,y+44+oy],44,fill=((90,90,90,al) if subd else (230,20,30,al)))
            tx="구독중 ✓" if subd else "구독"; w=d.textlength(tx,font=bf); d.text((x-w/2,y-30+oy),tx,font=bf,fill=(255,255,255,al))
        if t>=tL-0.6 and t<tL+0.7:
            ripple(d,t,tL,*LK); draw_hand(im,t,tL,*LK)
            if t>=tL:
                q=min(1,(t-tL)/0.5); sc=0.5+0.7*ease(q); hh=HEART.resize((int(HEART.width*sc),int(HEART.height*sc)))
                hh.putalpha(hh.getchannel("A").point(lambda v:int(v*(1-q))))
                im.alpha_composite(hh,(LK[0]-hh.width//2,LK[1]-hh.height//2-int(90*q)))
        if t>=tS-0.6: ripple(d,t,tS,*SB); draw_hand(im,t,tS,*SB)
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(ED),"-i","anullsrc=r=48000:cl=stereo","-shortest","-vf","fade=t=in:st=0:d=0.25,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac",out])
    return tL,tS
eL,eS=end_clip(O+"end.mp4"); taps+=[T+eL,T+eS]
parts.append(O+"end.mp4"); timeline.append(("card",T,T+ED)); T+=ED
pathlib.Path(O+"list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",O+"list.txt","-c:v","copy","-c:a","aac","-ar","48000",O+"body.mp4"])
def vol_at(t):
    for kind,a,b in timeline:
        if a<=t<b:
            if kind=="card": return 0.55
            if t-a<0.3: return 0.55-(0.45)*(t-a)/0.3
            if b-t<0.3: return 0.10+(0.45)*(1-(b-t)/0.3)
            return 0.10
    return 0.55
SR=48000
bg=subprocess.run(["ffmpeg","-v","error","-i",BGM,"-t",str(T),"-ac","2","-ar",str(SR),"-f","s16le","-"],capture_output=True).stdout
x=np.frombuffer(bg,dtype="<i2").reshape(-1,2).astype(np.float32)/32768
n=len(x); tt=np.arange(n)/SR
g=np.array([vol_at(t) for t in np.arange(0,T+0.01,0.01)]); gi=np.interp(tt,np.arange(len(g))*0.01,g)
x=x*gi[:,None]; fo=int(1.2*SR); x[-fo:]*=np.linspace(1,0,fo)[:,None]
for tp in taps:
    i0=int(tp*SR); m=int(0.06*SR); q=np.arange(m)/SR; c=(np.random.default_rng(1).uniform(-1,1,m)*np.exp(-q*90)+0.8*np.sin(2*np.pi*1500*q)*np.exp(-q*120))*0.5
    x[i0:i0+m]+=c[:,None]
with wave.open(O+"bgm.wav","wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x,-1,1)*32767).astype("<i2").tobytes())
run(["ffmpeg","-v","error","-y","-i",O+"body.mp4","-i",O+"bgm.wav","-filter_complex","[0:a]volume=1.0[v];[1:a]volume=1.0[m];[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",O+"20261104_bestie_ep3_v2_shorts.mp4"])
print("T",round(T,2))
