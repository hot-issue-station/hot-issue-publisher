import sys,subprocess
sys.path.insert(0,'/home/claude/hot-issue-publisher/scripts')
from make_celebration import F,B,BD,RG,shadow_text,PINK,LAV,comment_card,wrap
from PIL import Image,ImageDraw
W,H=1080,1920
REC="/mnt/user-data/uploads/Videos/2026-11-04 02-55-00.mp4"
TR={1:(44,-32.02,57),2:(103,-24.13,57),3:(160,-24.13,54)}
CM={1:[(0.5,{"likes":"846","text":"전례없는 초대박치자 리센느","jp":"前例のない大ヒットを打とう、リセンヌ"}),
       (18,{"likes":"23","text":"와;; 나이 53살에 걸그룹 응원법을 배우게 될 줄이야;;😅","jp":"53歳でガールズグループの掛け声を覚えることになるとは…"}),
       (36,{"likes":"12","text":"日本から応援してるよ！！","kr_tr":"일본에서 응원하고 있어요!! (일본 팬)"})],
    2:[(0.5,{"likes":"79","text":"진짜 대세로 굳고나서 응원법영상보니까 예전 활동때부터 응원법영상이랑 겹쳐보여서 내가 다 뿌듯함 ㅜㅜ 승승장구하자 리센느","jp":"前の活動の掛け声動画と重なって、私まで誇らしい。勝ち進もう！"}),
       (18,{"likes":"300","text":"와 처음인 리마인들 많아서 응원법 진짜 쉽게 해준거같다... 감동😢","jp":"初めてのリマインが多いから掛け声を簡単にしてくれたみたい…感動"}),
       (36,{"likes":"27","text":"今度はオリジナルの新曲を出した直後に見事１位を取ってみんなが泣く時😢","kr_tr":"이번엔 오리지널 신곡을 내자마자 1위를 해서 다 같이 우는 순간 (일본 팬)"})],
    3:[(0.5,{"likes":"299","text":"5명의 서사가 여기까지 오게 만들었다. 이번 활동 다치지말고 1등 하자!","jp":"5人の物語がここまで連れてきた。ケガせず1位取ろう！"}),
       (21,{"likes":"48","text":"정원이 진경은 미나미 이예빈 김가영 리마인 함!께!해!줘!","jp":"メンバーの本名コール＋「リマイン、一緒にして！」"}),
       (35,{"likes":"438","text":"와 1시간만에 2위 그리고 5,7,9,11위 진짜 눈물난다 ㅠㅠ리마인들 고마워","jp":"1時間で2位、そして5・7・9・11位…涙出る。リマインありがとう"})]}
def pill(img,x,y,t):
    dd=ImageDraw.Draw(img); f=F(BD,24); w=dd.textlength(t,font=f)
    dd.rounded_rectangle([x,y,x+w+32,y+42],radius=21,fill=(0,0,0,170)); dd.text((x+16,y+21),t,font=f,fill=(255,255,255),anchor='lm')
n=int(sys.argv[1]); fan,off,D=TR[n]
MVY,FCY,CY=215,826,1446
top=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(top)
d.rounded_rectangle([W//2-220,18,W//2+220,64],radius=23,fill=(255,120,190,235))
d.text((W//2,41),"덕심저장소 · 推し活アーカイブ",font=F(BD,26),fill=(255,255,255),anchor='mm')
shadow_text(top,(W//2,102),f"리센느닷없이 보너스 트랙 {n}",F(B,54),(255,255,255),anchor='mm')
shadow_text(top,(W//2,150),f"RESCENE 突然のボーナストラック{n} · カムバック1位おめでとう",F(BD,26),LAV,anchor='mm',sw=2)
shadow_text(top,(W//2,190),"“뮤비 보면서 응원법 같이 해요” MVを見ながら一緒に",F(B,28),PINK,anchor='mm',sw=3)
pill(top,20,MVY+12,"▶ 공식 MV"); pill(top,20,FCY+608-54,"공식 응원법")
top.save(f't2_{n}.png')
end=Image.new('RGBA',(W,H),(10,0,20,140))
if n<3:
    shadow_text(end,(W//2,860),f"▶ 리센느닷없이 보너스 트랙 {n+1}로 이어져요",F(B,46),(255,255,255),anchor='mm')
    shadow_text(end,(W//2,950),f"突然のボーナストラック{n+1}に続きます",F(BD,36),LAV,anchor='mm',sw=2)
else:
    shadow_text(end,(W//2,820),"다음 무대에선",F(B,64),(255,255,255),anchor='mm')
    shadow_text(end,(W//2,910),"우리가 같이 외쳐요!",F(B,64),PINK,anchor='mm')
    shadow_text(end,(W//2,990),"次のステージでは一緒に叫ぼう！",F(BD,36),LAV,anchor='mm',sw=2)
shadow_text(end,(W//2,1080),"리센느 컴백 1위 축하 영상 · 덕심저장소",F(BD,32),(255,235,150),anchor='mm',sw=2)
shadow_text(end,(W//2,1140),"이슈브리프 · @hot.issue.station",F(BD,28),(230,230,240),anchor='mm',sw=2)
end.save(f'e2_{n}.png')
cards=[]
for k,(st,c) in enumerate(CM[n]):
    img=Image.new('RGBA',(W,H-CY),(0,0,0,0)); cd=comment_card(c,500+10*n+k); img.alpha_composite(cd,(44,0))
    tr=c.get('jp') or c.get('kr_tr'); dd=ImageDraw.Draw(img); yy=cd.size[1]+10
    for ln in wrap(dd,tr,F(RG,28),880)[:2]:
        shadow_text(img,(54,yy),ln,F(RG,28),(220,205,255),sw=2,glow=6); yy+=38
    img.save(f'c2_{n}_{k}.png')
    en=CM[n][k+1][0]+0.5 if k+1<len(CM[n]) else D-4
    cards.append((st,en))
mvs=1.5+fan+off; fcs=234.7+fan-30
fc=(f"[0:v]crop=1528:860:196:153,scale=1080:608,setpts=PTS-STARTPTS,fps=30[mv];"
 f"[1:v]crop=1528:860:196:153,scale=1080:608,setpts=PTS-STARTPTS,fps=30[fc];"
 f"[1:v]crop=1528:860:196:153,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.3,setpts=PTS-STARTPTS,fps=30[bg];"
 f"[bg][mv]overlay=0:{MVY}[a];[a][fc]overlay=0:{FCY}[b];[b][2:v]overlay=0:0:shortest=1[c0];")
ins=['-loop','1','-i',f't2_{n}.png','-loop','1','-i',f'e2_{n}.png']
prev='c0'
for k,(st,en) in enumerate(cards):
    ins+=['-loop','1','-i',f'c2_{n}_{k}.png']; idx=4+k
    fc+=f"[{idx}:v]format=rgba,fade=t=in:st={st}:d=0.6:alpha=1,fade=t=out:st={en-0.6}:d=0.6:alpha=1[k{k}];[{prev}][k{k}]overlay=0:{CY}:enable='between(t,{st},{en})':shortest=1[c{k+1}];"
    prev=f'c{k+1}'
fc+=(f"[3:v]format=rgba,fade=t=in:st={D-4}:d=0.6:alpha=1[e];[{prev}][e]overlay=0:0:enable='gte(t,{D-4})':shortest=1,format=yuv420p[v];"
 f"[1:a:0]asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={D-2}:d=2,loudnorm=I=-14:TP=-1.5[aout]")
cmd=['ffmpeg','-v','error','-y','-ss',str(mvs),'-t',str(D),'-i',REC,'-ss',str(fcs),'-t',str(D),'-i',REC]+ins+[
 '-filter_complex',fc,'-map','[v]','-map','[aout]','-t',str(D),'-c:v','libx264','-preset','medium','-b:v','1200k','-maxrate','1600k','-bufsize','3400k','-c:a','aac','-b:a','128k','-movflags','+faststart',f'/home/claude/upload_tmp/RSC_bonus{n}.mp4']
subprocess.run(cmd,check=True); print('done',n)
