OC="/home/claude/hot-issue-publisher/scripts/omegacut"
import subprocess, pathlib, numpy as np, wave, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
BGM="/home/claude/hot-issue-publisher/music/suno/6_recap_good_times.mp3"
LOGO="/home/claude/hot-issue-publisher/assets/brand/logo_wordmark.png"
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H,FPS=1920,1080,30; CROP="crop=1332:749:286:211"; MY=520; MH=607
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
import os, json
def run(a): subprocess.run(a,check=True)
def font(p,s): return ImageFont.truetype(p,s)
def fit(d,txt,p,sz,maxw):
    while sz>18:
        f=font(p,sz)
        if d.textlength(txt,font=f)<=maxw: return f
        sz-=2
    return font(p,sz)
# 덕심저장소 #3 롱폼 — 베스티 「연애의 조건」 13년의 이야기 (가로 1920x1080, 약 5분)
B="/home/claude/bestie/"; O=B+"lf/"; pathlib.Path(O).mkdir(exist_ok=True)
MV=B+"c1.mp4"; MV2=B+"c2.mp4"; RS=B+"c3.mp4"; ST=B+"c6.mp4"; DEB=B+"d1.mp4"; MC13=B+"d2.mp4"; MC13B=B+"d3.mp4"; V26=B+"d4.mp4"; FC=B+"d5.mp4"; FIN=B+"d6.mp4"
T_=lambda k,d: float(os.environ.get(k,d))
PORT={RS}
WIDE={MC13B,FC}
TH="/home/claude/hot-issue-publisher/assets/thumbs/"
# 가로로 넓은 장면의 위아래 빈칸: 위=후킹 제목, 아래=실제 응원 댓글(공식 영상 댓글, 닉네임 가림)
WIDEINFO={MC13B:("13년 전, 아무도 몰랐던 그 무대",[("One of the underrated kpop groups ever","16"),("베스티좋아정말좋아","4")]),
          FC:("약 4000일 만에, 네 사람이 다시",[("멤버들끼리 돈독하게 지내는 게 최고인 거다 … 베스티 4인방 앞으로도 포에버!!!!!!","1.8천"),("우리가 알던 원래의 케이팝.","651")])}
# 멤버별 지금 활동 스틸(공식 영상 화면): (이미지, 자막, 일본어, 출처)
NOW={
 "혜연":[(TH+"bst_hyeyeon2.jpg","[혜연] 트로트 가수로 — 「현역가왕」 무대 (2023)","［ヘヨン］トロット歌手として『現役歌王』（2023）","MBN MUSIC · 강혜연 - 인생｜현역가왕 3회"),
         (TH+"bst_hyeyeon.jpg","[혜연] 그리고 지금 — 「현역가왕3」 「꽃바람」","［ヘヨン］そして今『現役歌王3』「花の風」","MBN MUSIC · 강혜연 – 꽃바람｜현역가왕3 10회")],
 "유지":[(TH+"bst_yuji2.jpg","[유지] 뮤지컬 「노트르담 드 파리」 무대 (2018)","［ユジ］ミュージカル『ノートルダム・ド・パリ』（2018）","KBS Kpop · 열린음악회 20180610"),
         (TH+"bst_yuji.jpg","[유지] 그리고 지금 — 「겨울왕국」 넘버 라이브","［ユジ］そして今『アナと雪の女王』ナンバー","MBC RADIO 므흐즈 · [ALLIVE] 정유지X박진주")],
 "해령":[(TH+"bst_haeryung.jpg","[해령] 배우 나해령 — KBS 「내 마음의 꽃비」","［ヘリョン］俳優ナ・ヘリョン『私の心の花雨』","KBS Drama · 내 마음의 꽃비 20160616")],
 "다혜":[(TH+"bst_dahye.jpg","[다혜] 그리고 지금 — 직접 운영하는 유튜브 채널","［ダヘ］そして今、自身のYouTubeチャンネル","다혜가다했다DAHYE · 26년'도'생일 브이로그")],
}
SRC_ST="MBCkpop · Show! MusicCore 261031"
# (chapter, [cards], video) ; card=(l1,l2,jp,dur) ; video=(src,start,dur,caption,jpcap,source)
SC=[
 ("2013 · 데뷔",[("2013년 7월, 네 명의 소녀가 데뷔했어요","베스티(BESTie) 데뷔곡 「두근두근」","2013年7月、4人組BESTieがデビュー曲「ドキドキ」で登場",4.2)],
   (DEB,T_("DEB_T",2),14,"데뷔곡 「두근두근」 뮤직비디오 (2013)","デビュー曲「ドキドキ」MV（2013）","1theK (원더케이) · [MV] BESTie _ Pitapat")),
 ("2013 · 연애의 조건",[("같은 해 10월 17일","두 번째 싱글 「연애의 조건」 발매","同じ年の10月17日、2ndシングル「恋愛の条件」発売",4.0)],
   (MC13,T_("MC13_T",20),22,"발매 당일 엠카운트다운 무대 (2013.10.17)","発売当日のM COUNTDOWN（2013.10.17）","Mnet K-POP · Love Options by BESTie of Mcountdown 2013.10.17")),
 ("2013 · 연애의 조건",[("\"활동할 때 TOP100에 정말 들고 싶었어요\"","유지가 남긴 그때의 마음","「活動当時、TOP100に本当に入りたかった」ユジが語った当時の思い",4.6)],
   (MV,4.0,14,"원곡 뮤직비디오","原曲MV","1theK (원더케이) · [MV] BESTie _ Love Options")),
 ("2013 · 연애의 조건",[("하지만 그때 이 노래는","차트에 오르지 못했어요","しかし当時、この曲はチャートに届きませんでした",3.8)],
   (MC13B,T_("MC13B_T",8),14,"2013년 음악중심 무대","2013年 音楽中心のステージ","MBCkpop · Music Core 20131019")),
 ("2017–2018 · 흩어진 네 사람",[("2017년 9월, 다혜가 팀을 떠나고","2018년, 베스티는 해체했어요","2017年9月にダヘが脱退、2018年にBESTieは解散",4.4),
                          ("그리고 네 사람은","각자의 길을 걸었어요","そして4人はそれぞれの道を歩みました",3.6)],
   (MV2,2.0,10,"「연애의 조건」 뮤직비디오 中","「恋愛の条件」MVより","1theK (원더케이) · [MV] BESTie _ Love Options")),
 ("각자의 길 · 혜연",[("혜연은 트로트 가수로","'미스트롯2'에도 도전했어요","ヘヨンはトロット歌手に。『ミストロット2』にも挑戦",4.2)],
   (ST,33.0,8.5,"[혜연] 2026년, 다시 선 무대","［ヘヨン］2026年、再びのステージ",SRC_ST)),
 ("각자의 길 · 유지",[("유지는","가수이자 뮤지컬 배우로 무대를 지켰어요","ユジは歌手・ミュージカル俳優として舞台に立ち続けました",4.0)],
   (ST,18.0,8.0,"[유지] 2026년, 다시 선 무대","［ユジ］2026年、再びのステージ",SRC_ST)),
 ("각자의 길 · 해령",[("막내 해령은","배우로 활동을 넓혔어요","末っ子ヘリョンは俳優として活動の幅を広げました",4.0)],
   (ST,25.0,8.0,"[해령] 2026년, 다시 선 무대","［ヘリョン］2026年、再びのステージ",SRC_ST)),
 ("각자의 길 · 다혜",[("다혜는 유튜브에 커버 영상을 올리다","2023년 '환승연애3'에 출연했어요","ダヘはカバー動画を経て、2023年『乗り換え恋愛3』に出演",4.4)],
   (ST,40.4,7.5,"[다혜] 2026년, 다시 선 무대","［ダヘ］2026年、再びのステージ",SRC_ST)),
 ("2026 · 다시 불려 나온 노래",[("2026년 여름, 숏폼에서","이 노래가 다시 퍼지기 시작했어요","2026年夏、ショート動画でこの曲が再び広がり始めました",4.2),
                              ("하츠투하츠 '레몬탱' 안무와 섞은 팬 영상","'레몬탱 행진'이 시작이었어요","Hearts2Heartsの振付と合わせたファン動画「レモンタン行進」がきっかけ",4.4),
                              ("그리고 리센느도","챌린지에 참여했어요","そしてRESCENEもチャレンジに参加",3.6)],
   (RS,0.0,12.0,"리센느의 「연애의 조건」 챌린지","RESCENEの「恋愛の条件」チャレンジ","RESCENE 공식 유튜브 쇼츠")),
 ("2026 · 다시 불려 나온 노래",[("8월 27일, 멜론 일간 차트 첫 진입","13년 만에 처음으로 차트에","8/27、メロン日間チャート初登場。13年越しの初チャートイン",4.2),
                              ("\"이렇게 시간이 지나 차트에 오를 줄","상상도 못 했어요\" — 유지","「こんなに時間が経ってチャートに入るなんて想像もしなかった」ユジ",4.6)],
   (MV,20.0,9.0,"원곡 뮤직비디오","原曲MV","1theK (원더케이) · [MV] BESTie _ Love Options")),
 ("13주년의 약속",[("10월 17일, 발매 13주년","네 사람이 재결합을 알렸어요","10/17、発売13周年に4人が再結成を発表",4.2),
                 ("10월 29일","2026 버전 안무 영상 공개","10/29、2026年ver.の振付動画を公開",3.6)],
   (V26,T_("V26_T",4),20,"「연애의 조건」 2026 버전 안무 영상","「恋愛の条件」2026年ver. 振付動画","다혜가다했다DAHYE · 연애의 조건 안무영상 2026.ver")),
 ("10.31 · 약 4000일 만의 무대",[("10월 31일, MBC '쇼! 음악중심'","네 사람이 완전체로 다시 섰어요","10/31、MBC『ショー！音楽中心』に4人揃って再び",4.2)],
   (ST,0.0,16.0,"약 4000일 만의 완전체 음악방송","約4000日ぶりの完全体での音楽番組",SRC_ST)),
 ("10.31 · 약 4000일 만의 무대",[("13년 전과 같은 노래","네 사람의 지금","13年前と同じ歌、4人の今",3.4)],
   (FC,T_("FC_T",50),24,"음악중심 풀캠 (2026.10.31)","音楽中心フルカメラ（2026.10.31）","MBCkpop · [#음중풀캠] BESTie – 연애의 조건 FullCam")),
 ("10.31 · 약 4000일 만의 무대",[("그리고 마지막 순간까지","","そして最後の瞬間まで",3.0)],
   (FIN,T_("FIN_T",72),28,"다시, 네 사람의 무대","再び、4人のステージ",SRC_ST)),
]
TITLE="베스티 「연애의 조건」 13년의 이야기"
JPTITLE="BESTie「恋愛の条件」13年の物語"
GRN=(70,255,140); YEL=(255,214,10); JPC=(205,215,235)
LOGO_IM=Image.open(LOGO).convert("RGBA").crop((180,120,1020,510)).resize((220,102))
def still(src,t):
    p=O+f"st_{abs(hash((src,t)))%10**8}.png"
    run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",src,"-frames:v","1",p]); return Image.open(p).convert("RGB")
def bgfrom(st,blur=26,bright=0.42):
    r=max(W/st.width,H/st.height); bg=st.resize((int(st.width*r)+1,int(st.height*r)+1))
    x=(bg.width-W)//2; y=(bg.height-H)//2; bg=bg.crop((x,y,x+W,y+H)).filter(ImageFilter.GaussianBlur(blur))
    return ImageEnhance.Brightness(bg).enhance(bright).convert("RGBA")
def chrome(im,chapter,step,n):
    d=ImageDraw.Draw(im)
    f=font(FB,30); tw=d.textlength(chapter,font=f)
    d.rounded_rectangle([40,36,40+tw+40,92],14,fill=(0,0,0,170)); d.rectangle([40,36,48,92],fill=GRN); d.text((68,44),chapter,font=f,fill="white")
    im.alpha_composite(LOGO_IM,(W-260,24))
    bw=(W-80-6*(n-1))/n
    for k in range(n):
        x=40+k*(bw+6); d.rounded_rectangle([x,H-14,x+bw,H-8],3,fill=GRN if k<=step else (255,255,255,60))
def jpl(d,t,y,sz,a=255,maxw=1600):
    if not t: return
    f=fit(d,t,FB,sz,maxw); w=d.textlength(t,font=f); d.text(((W-w)/2,y),t,font=f,fill=(*JPC,a),stroke_width=2,stroke_fill="black")
def card(idx,chapter,step,n,l1,l2,jp,st,dur,tap,out,big=False):
    frames=int(dur*FPS); base=bgfrom(st); tmp=pathlib.Path(O+f"cf{idx}"); tmp.mkdir(exist_ok=True)
    for k in range(frames):
        t=k/FPS; im=base.copy(); z=1+0.04*t/dur
        # 가운데 작은 화면(정지 장면) + 재생 버튼
        sw,sh=int(720*z),int(405*z); s=st.resize((sw,sh)); dim=0.6 if (not tap or t<dur-0.45) else 0.6+0.4*min(1,(t-(dur-0.45))/0.35)
        sx,sy=(W-sw)//2, 170-(sh-405)//2
        im.paste(ImageEnhance.Brightness(s).enhance(dim),(sx,sy))
        d=ImageDraw.Draw(im); d.rectangle([sx-3,sy-3,sx+sw+3,sy+sh+3],outline=(255,255,255,90),width=3)
        a=min(1,t/0.4); f1=fit(d,l1,FB,58 if not big else 64,1700); w=d.textlength(l1,font=f1)
        d.text(((W-w)/2,640+18*(1-a)),l1,font=f1,fill=(255,255,255,int(255*a)),stroke_width=2,stroke_fill="black")
        if l2:
            a2=min(1,max(0,(t-0.3)/0.4)); f2=fit(d,l2,F,78 if not big else 88,1760); w=d.textlength(l2,font=f2)
            d.text(((W-w)/2,722+18*(1-a2)),l2,font=f2,fill=(*YEL,int(255*a2)),stroke_width=4,stroke_fill="black")
        jpl(d,jp,850,34,int(255*min(1,max(0,(t-0.5)/0.4))))
        cx,cy=W//2,170+202
        if tap and t<dur-0.3:
            pr=54; pa=int(230*min(1,t/0.4)); d.ellipse([cx-pr,cy-pr,cx+pr,cy+pr],fill=(0,0,0,int(pa*0.55)),outline=(255,255,255,pa),width=5)
            d.polygon([(cx-18,cy-29),(cx-18,cy+29),(cx+31,cy)],fill=(255,255,255,pa))
        if tap: draw_tap(PAT[idx%5],im,t,dur-0.55,cx,cy)
        chrome(im,chapter,step,n)
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-shortest","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac",out])
def vclip(idx,chapter,step,n,src,stt,du,cap,jpcap,srcname,out):
    port=src in PORT
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    # 아래 자막 띠
    cf=fit(d,cap,F,50,1400); cw=d.textlength(cap,font=cf)
    d.rounded_rectangle([(W-cw)/2-30,880,(W+cw)/2+30,962],16,fill=(10,10,10,215)); d.text(((W-cw)/2,886),cap,font=cf,fill=YEL,stroke_width=3,stroke_fill="black")
    jpl(d,jpcap,972,30)
    sf=font(FB,24); s="출처: "+srcname; sw=d.textlength(s,font=sf); d.rounded_rectangle([W-sw-64,108,W-36,148],10,fill=(0,0,0,150)); d.text((W-sw-50,113),s,font=sf,fill=(200,205,220))
    if src in WIDEINFO:
        hook,cms=WIDEINFO[src]
        hf=fit(d,hook,F,60,1100); hw=d.textlength(hook,font=hf); d.text(((W-hw)/2,62),hook,font=hf,fill=(255,255,255),stroke_width=4,stroke_fill="black")
        d.rectangle([(W-hw)/2,140,(W+hw)/2,146],fill=GRN)
        y=798; cfn=font(FB,26)
        for i,(ctext,likes) in enumerate(cms[:1]):
            line="“"+ctext+"”   좋아요 "+likes; mf=fit(d,line,FB,30,1500); mw=d.textlength(line,font=mf)
            d.rounded_rectangle([(W-mw)/2-60,y,(W+mw)/2+24,y+60],30,fill=(255,255,255,235))
            d.ellipse([(W-mw)/2-50,y+10,(W-mw)/2-10,y+50],fill=(150,150,165)); d.text(((W-mw)/2+6,y+12),line,font=mf,fill=(25,25,30))
        d.text((40,1020),"실제 시청자 댓글 · 닉네임은 가렸어요 · 출처 영상 댓글란",font=font(FB,20),fill=(170,175,190))
    chrome(ov,chapter,step,n)
    p=O+f"vo{idx}.png"; ov.save(p)
    if not port:
        fc=(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[v0]" if src not in WIDE else f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.45[bg];[b]scale=1600:-2[fg];[bg][fg]overlay=160:158[v0]")
    else:
        fc=f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.35[bg];[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0[v0]"
    run(["ffmpeg","-v","error","-y","-ss",str(stt),"-t",str(du),"-i",src,"-i",p,"-filter_complex",
      fc+f";[v0][1]overlay=0:0,fps={FPS},format=yuv420p[v];[0:a]afade=t=in:st=0:d=0.3,afade=t=out:st={du-0.5}:d=0.5,aresample=48000,aformat=channel_layouts=stereo[a2]",
      "-map","[v]","-map","[a2]","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac","-b:a","192k",out])
def photo_clip(idx,chapter,step,n,img,cap,jpcap,srcname,out,dur=4.8):
    ph=Image.open(img).convert("RGB"); base=bgfrom(ph,30,0.38); tmp=pathlib.Path(O+f"pf{idx}"); tmp.mkdir(exist_ok=True)
    for k in range(int(dur*FPS)):
        t=k/FPS; im=base.copy(); z=1.0+0.06*t/dur
        fw=int(1280*z); fh=int(fw*ph.height/ph.width); fg=ph.resize((fw,fh))
        a=min(1,t/0.35); x=(W-fw)//2; y=118+(720-fh)//2
        fgm=fg.convert("RGBA"); 
        if a<1: fgm.putalpha(int(255*a))
        im.alpha_composite(fgm,(x,y))
        d=ImageDraw.Draw(im); d.rectangle([x-3,y-3,x+fw+3,y+fh+3],outline=(255,255,255,int(110*a)),width=3)
        cf=fit(d,cap,F,48,1500); cw=d.textlength(cap,font=cf)
        d.rounded_rectangle([(W-cw)/2-30,880,(W+cw)/2+30,960],16,fill=(10,10,10,215)); d.text(((W-cw)/2,886),cap,font=cf,fill=YEL,stroke_width=3,stroke_fill="black")
        jpl(d,jpcap,972,30)
        sf=font(FB,24); s_="출처: "+srcname+" (영상 화면)"; sw=d.textlength(s_,font=sf); d.rounded_rectangle([W-sw-64,108,W-36,148],10,fill=(0,0,0,150)); d.text((W-sw-50,113),s_,font=sf,fill=(200,205,220))
        chrome(im,chapter,step,n)
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-shortest","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac",out])
    return dur
parts=[]; timeline=[]; taps=[]; T=0; N=len(SC)+2
# 시작 화면
intro_st=still(MC13,T_("MC13_T",20)+3)
def intro(out,dur=5.5):
    frames=int(dur*FPS); base=bgfrom(intro_st,30,0.35); tmp=pathlib.Path(O+"cfi"); tmp.mkdir(exist_ok=True)
    for k in range(frames):
        t=k/FPS; im=base.copy(); d=ImageDraw.Draw(im)
        a=min(1,t/0.6); f1=font(FB,52); l1="13년 전, 차트에 오르지 못한 노래가 있었습니다"; w=d.textlength(l1,font=f1); d.text(((W-w)/2,360),l1,font=f1,fill=(255,255,255,int(255*a)))
        a2=min(1,max(0,(t-1.0)/0.6)); f2=font(F,96); w=d.textlength(TITLE,font=f2)
        d.rectangle([(W-w)/2-24,450,(W+w)/2+24,580],fill=(*GRN,int(255*a2))); d.text(((W-w)/2,456),TITLE,font=f2,fill=(0,0,0,int(255*a2)))
        jpl(d,"13年前、チャートに届かなかった歌がありました — "+JPTITLE,610,34,int(255*a2))
        a3=min(1,max(0,(t-2.0)/0.6)); f3=font(FB,32); l3="덕심저장소 #3 · 공식 영상만 사용 · 출처는 화면에 표기"; w=d.textlength(l3,font=f3); d.text(((W-w)/2,700),l3,font=f3,fill=(200,160,255,int(255*a3)))
        im.alpha_composite(LOGO_IM,(W-260,24))
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-shortest","-vf","fade=t=in:st=0:d=0.6,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac",out])
    return dur
d=intro(O+"intro.mp4"); parts.append(O+"intro.mp4"); timeline.append(("card",T,T+d)); T+=d
ci=0; chapters=[]
for step,(chap,cards,(src,stt,du,cap,jc,sn)) in enumerate(SC):
    st=still(src,stt+0.4)
    if not chapters or chapters[-1][1]!=chap: chapters.append((T,chap))
    for j,(l1,l2,jp,cd) in enumerate(cards):
        last=(j==len(cards)-1)
        card(ci,chap,step+1,N,l1,l2,jp,st,cd,last,O+f"k{ci}.mp4"); parts.append(O+f"k{ci}.mp4"); timeline.append(("card",T,T+cd))
        if last: taps.append(T+cd-0.55)
        T+=cd; ci+=1
    mem=chap.split("· ")[-1] if chap.startswith("각자의 길") else None
    for pi,(img,pc,pj,ps) in enumerate(NOW.get(mem,[])):
        pd_=photo_clip(f"{step}_{pi}",chap,step+1,N,img,pc,pj,ps,O+f"p{step}_{pi}.mp4"); parts.append(O+f"p{step}_{pi}.mp4"); timeline.append(("card",T,T+pd_)); T+=pd_
    vclip(step,chap,step+1,N,src,stt,du,cap,jc,sn,O+f"v{step}.mp4"); parts.append(O+f"v{step}.mp4"); timeline.append(("video",T,T+du)); T+=du
# 마무리 화면
end_st=still(FIN,T_("FIN_T",72)+20)
ED=9.0
def ending(out):
    frames=int(ED*FPS); base=bgfrom(end_st,26,0.35); tmp=pathlib.Path(O+"cfe"); tmp.mkdir(exist_ok=True)
    LK=(W//2-190,820); SB=(W//2+190,820); tL,tS=5.4,6.8; bf=font(F,44)
    lines=[(230,"11월 2일, 멜론 TOP100 25위 · 벅스 9위",(255,255,255),font(FB,52)),(320,"\"어디까지 올라가는 거예요\" — 해령",YEL,font(F,74)),(450,"13년 만에 닿은, 그때의 꿈",GRN,font(F,70))]
    for k in range(frames):
        t=k/FPS; im=base.copy(); d=ImageDraw.Draw(im)
        for n_,(y,tx,c,f) in enumerate(lines):
            a=min(1,max(0,(t-0.4-0.9*n_)/0.5)); w=d.textlength(tx,font=f); d.text(((W-w)/2,y+14*(1-a)),tx,font=f,fill=(*c,int(255*a)),stroke_width=3,stroke_fill="black")
        jpl(d,"11/2 メロン25位・Bugs9位「どこまで上がるの？」（ヘリョン）13年越しに届いた夢",550,32,int(255*min(1,max(0,(t-2.6)/0.5))))
        sf=font(FB,24); s="출처: 톱스타뉴스(11/2) · 코리아타임스(9/16) · 위키트리·인사이트(10/17) · iMBC연예(10/29) · 일간스포츠(10/17) · 스포티비뉴스(2023.12.29)"; w=d.textlength(s,font=sf); d.text(((W-w)/2,620),s,font=sf,fill=(180,185,200,int(255*min(1,max(0,(t-2.6)/0.5)))))
        a=ease((t-3.8)/0.5)
        if a>0:
            oy=int(30*(1-a)); al=int(255*a)
            liked=t>=tL; x,y=LK; d.rounded_rectangle([x-160,y-46+oy,x+160,y+46+oy],46,fill=((140,90,255,al) if liked else (255,255,255,al)))
            tx="좋아요 ♥" if liked else "좋아요"; w=d.textlength(tx,font=bf); d.text((x-w/2,y-30+oy),tx,font=bf,fill=((255,255,255,al) if liked else (20,20,20,al)))
            subd=t>=tS; x,y=SB; d.rounded_rectangle([x-160,y-46+oy,x+160,y+46+oy],46,fill=((90,90,90,al) if subd else (230,20,30,al)))
            tx="구독중 ✓" if subd else "구독"; w=d.textlength(tx,font=bf); d.text((x-w/2,y-30+oy),tx,font=bf,fill=(255,255,255,al))
            t2="덕심저장소는 공식 영상으로 이야기를 모아요 · 구독으로 함께해 주세요"; f2=fit(d,t2,FB,34,1600); w=d.textlength(t2,font=f2); d.text(((W-w)/2,900+oy),t2,font=f2,fill=(220,220,235,al))
        if t>=tL-0.6 and t<tL+0.7:
            ripple(d,t,tL,*LK); draw_hand(im,t,tL,*LK)
        if t>=tS-0.6: ripple(d,t,tS,*SB); draw_hand(im,t,tS,*SB)
        im.alpha_composite(LOGO_IM,(W-260,24))
        im.convert("RGB").save(tmp/f"{k:04d}.png")
    run(["ffmpeg","-v","error","-y","-framerate",str(FPS),"-i",str(tmp/"%04d.png"),"-f","lavfi","-t",str(ED),"-i","anullsrc=r=48000:cl=stereo","-shortest","-vf","fade=t=in:st=0:d=0.5,fade=t=out:st=8.2:d=0.8,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac",out])
    return tL,tS
eL,eS=ending(O+"end.mp4"); taps+=[T+eL,T+eS]; parts.append(O+"end.mp4"); timeline.append(("card",T,T+ED)); T+=ED
pathlib.Path(O+"list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",O+"list.txt","-c:v","copy","-c:a","aac","-ar","48000",O+"body.mp4"])
# 배경음악: 우리 곡 두 곡 이어 붙이기(잔잔하게) — 5_emotion → 1_calm, 4초 겹침
M1="/home/claude/hot-issue-publisher/music/suno/5_emotion_remembering_you.mp3"; M2="/home/claude/hot-issue-publisher/music/suno/1_calm_evening_briefing.mp3"
run(["ffmpeg","-v","error","-y","-i",M1,"-i",M2,"-filter_complex","[0:a][1:a]acrossfade=d=4:c1=tri:c2=tri,aresample=48000,aformat=channel_layouts=stereo[a]","-map","[a]","-t",str(T),O+"bgm_src.wav"])
CARDV,VIDV=0.42,0.08
def vol_at(t):
    for kind,a,b in timeline:
        if a<=t<b:
            if kind=="card": return CARDV
            if t-a<0.5: return CARDV-(CARDV-VIDV)*(t-a)/0.5
            if b-t<0.5: return VIDV+(CARDV-VIDV)*(1-(b-t)/0.5)
            return VIDV
    return CARDV
SR=48000
bg=subprocess.run(["ffmpeg","-v","error","-i",O+"bgm_src.wav","-ac","2","-ar",str(SR),"-f","s16le","-"],capture_output=True).stdout
x=np.frombuffer(bg,dtype="<i2").reshape(-1,2).astype(np.float32)/32768
need=int(T*SR)
if len(x)<need: x=np.concatenate([x,np.zeros((need-len(x),2),np.float32)])
x=x[:need]; tt=np.arange(need)/SR
g=np.array([vol_at(t) for t in np.arange(0,T+0.01,0.01)]); gi=np.interp(tt,np.arange(len(g))*0.01,g)
x=x*gi[:,None]; fo=int(3*SR); x[-fo:]*=np.linspace(1,0,fo)[:,None]
for tp in taps:
    i0=int(tp*SR); m=int(0.06*SR); q=np.arange(m)/SR; c=(np.random.default_rng(1).uniform(-1,1,m)*np.exp(-q*90)+0.8*np.sin(2*np.pi*1500*q)*np.exp(-q*120))*0.35
    if i0+m<len(x): x[i0:i0+m]+=c[:,None]
with wave.open(O+"bgm.wav","wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x,-1,1)*32767).astype("<i2").tobytes())
run(["ffmpeg","-v","error","-y","-i",O+"body.mp4","-i",O+"bgm.wav","-filter_complex","[0:a][1:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",B+"20261104_bestie_ep3_longform_v2.mp4"])
json.dump({"T":T,"chapters":[(round(a,1),c) for a,c in chapters]},open(O+"chapters.json","w"),ensure_ascii=False)
print("T",round(T,1)); print(chapters)
