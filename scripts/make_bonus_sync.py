import sys,subprocess
sys.path.insert(0,'/home/claude/hot-issue-publisher/scripts')
from make_celebration import F,B,BD,RG,shadow_text,PINK,LAV
from PIL import Image,ImageDraw
W,H=1080,1920
REC="/mnt/user-data/uploads/Videos/2026-11-04 02-55-00.mp4"
TR={1:(44,-32.02,57),2:(103,-24.13,57),3:(160,-24.13,54)}
def pill(img,x,y,t):
    dd=ImageDraw.Draw(img); f=F(BD,26); w=dd.textlength(t,font=f)
    dd.rounded_rectangle([x,y,x+w+36,y+46],radius=23,fill=(0,0,0,170)); dd.text((x+18,y+23),t,font=f,fill=(255,255,255),anchor='lm')
n=int(sys.argv[1]); fan,off,D=TR[n]
top=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(top)
d.rounded_rectangle([W//2-230,40,W//2+230,92],radius=26,fill=(255,120,190,235))
d.text((W//2,66),"덕심저장소 · 推し活アーカイブ",font=F(BD,28),fill=(255,255,255),anchor='mm')
shadow_text(top,(W//2,135),f"리센느닷없이 보너스 트랙 {n}",F(B,56),(255,255,255),anchor='mm')
shadow_text(top,(W//2,184),f"RESCENE 突然のボーナストラック{n} · カムバック1位おめでとう",F(BD,28),LAV,anchor='mm',sw=2)
shadow_text(top,(W//2,230),"“뮤비 보면서 응원법 같이 해요” MVを見ながら一緒に",F(B,30),PINK,anchor='mm',sw=3)
pill(top,24,282,"▶ 공식 MV"); pill(top,24,1428,"공식 응원법")
top.save(f'top{n}.png')
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
end.save(f'end{n}.png')
mvs=1.5+fan+off; fcs=234.7+fan-30
fc=(f"[0:v]crop=1528:860:196:153,scale=1080:608,setpts=PTS-STARTPTS,fps=30[mv];"
 f"[1:v]crop=1528:860:196:153,scale=1080:608,setpts=PTS-STARTPTS,fps=30[fc];"
 f"[1:v]crop=1528:860:196:153,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.25,setpts=PTS-STARTPTS,fps=30[bg];"
 f"[bg][mv]overlay=0:270[a];[a][fc]overlay=0:880[b];[b][2:v]overlay=0:0:shortest=1[c];"
 f"[3:v]format=rgba,fade=t=in:st={D-4}:d=0.6:alpha=1[e];[c][e]overlay=0:0:enable='gte(t,{D-4})':shortest=1,format=yuv420p[v];"
 f"[1:a:0]asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={D-2}:d=2,loudnorm=I=-14:TP=-1.5[aout]")
cmd=['ffmpeg','-v','error','-y','-ss',str(mvs),'-t',str(D),'-i',REC,'-ss',str(fcs),'-t',str(D),'-i',REC,'-loop','1','-i',f'top{n}.png','-loop','1','-i',f'end{n}.png',
 '-filter_complex',fc,'-map','[v]','-map','[aout]','-t',str(D),'-c:v','libx264','-preset','medium','-b:v','1300k','-maxrate','1700k','-bufsize','3400k','-c:a','aac','-b:a','128k','-movflags','+faststart',f'/home/claude/upload_tmp/RSC_bonus{n}.mp4']
subprocess.run(cmd,check=True); print('done',n)
