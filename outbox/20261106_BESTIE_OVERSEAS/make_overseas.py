import asyncio, subprocess, base64, os, json
from playwright.async_api import async_playwright
S=os.path.dirname(os.path.abspath(__file__)); R="/home/claude/hot-issue-station/hot-issue-publisher"
def b(p): return base64.b64encode(open(p,"rb").read()).decode()
# (frame, big, sub, jp, comment index or None)
SEG=[
 (10,"그 무대 이후,<br>해외가 움직였다","10/31 약 4000일 만의 완전체 무대, 그 뒤 이야기","10/31の完全体ステージ、その後の話",None),
 (0,"대만 스포티파이 <b>1위</b>","전날 3위에서 1위로 (11/5 기준)","台湾Spotify 1位",0),
 (1,"대만 아이튠즈 <b>1위</b>","애플뮤직은 대만 2위","台湾iTunes 1位・Apple Music 2位",0),
 (2,"홍콩 아이튠즈 <b>3위</b>","애플뮤직 홍콩 5위","香港iTunes 3位・Apple Music 5位",1),
 (3,"말레이시아 아이튠즈 <b>6위</b>","아시아 곳곳으로 번지는 역주행","マレーシアiTunes 6位",1),
 (4,"샤잠, 아시아 <b>7개국 TOP10</b>","필리핀·베트남·중국·일본·싱가포르·태국·한국","Shazam アジア7か国でTOP10",1),
 (5,"무대 영상 합산 <b>756만 회</b>","무대·풀캠 댓글은 약 1만 4000개","ステージ映像 合計756万回",2),
 (6,"댓글창에도<br><b>여러 나라 말</b>","대만에서, 독일에서","台湾から、ドイツから",2),
 (7,"13년 전 노래가<br><b>아시아로</b>","2013년 발표, 활동 당시엔 차트에 못 올랐던 곡","2013年の曲が、今アジアへ",3),
 (8,"네 사람의 목소리,<br><b>국경을 넘다</b>","혜연·해령·유지·다혜","4人の声が国境を越えて",3),
 (9,"다음 무대는<br><b>어디일까요?</b>","해외 팬들의 \"우리나라에도 와 줘\"","次のステージはどこ？",3),
 (11,"13년의 이야기는<br><b>롱폼에서</b>","▶ 아래 관련 영상: 「연애의 조건」 13년 서사","13年の物語はロングフォームで",None),
]
CM=[
 ("621","국내 반응도 좋은데 해외반응이 진짜 거의 폭발수준이네... 여태 역주행한 걸그룹들 보면 해외반응까지 나오진 않았는데 이건 좀 특이하다",None),
 ("11","一定要來臺灣舉辦活動或是見面會也好 … 大家都在聽BESTie第一名的歌 … 今年是BESTie年","꼭 대만에서 행사나 팬미팅 해 주세요 … 다들 1위 한 베스티 노래 들어요 … 올해는 베스티의 해"),
 ("11","greetings from Germany. This song slaps!!!!","독일에서 인사드려요. 이 노래 최고예요!!!!"),
 ("12","해외 공연 함 불러줘라.. 항공권 및 숙박 제공하고..",None),
]
FPS=30; D=4.3; XF=0.35; N=len(SEG); DUR=[D]*N; DUR[-1]=4.6
SRC="출처 MBCkpop 쇼! 음악중심(261031) · 톱스타뉴스·스포츠월드·마이데일리(11/5)"
def page(i):
  fr,big,sub,jp,ci=SEG[i]; img=b(f"{S}/ph/f{fr:02d}.jpg")
  cmt=""
  if ci is not None:
    lk,tx,tr=CM[ci]
    trh=f"<div class='tr'>↳ {tr}</div>" if tr else ""
    cmt=f"""<div class='cm'><div class='lab'>음악중심 공식 무대 영상 댓글</div><div class='row'><div class='av'></div><div class='bd'><div class='nm'></div><div class='tx'>{tx}</div>{trh}<div class='lk'>👍 {lk}</div></div></div></div>"""
  return f"""<html><head><style>*{{margin:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden;background:#0a0710;font-family:'Noto Sans CJK KR'}}
@keyframes kb{{from{{transform:scale(1.0)}}to{{transform:scale(1.08)}}}}
@keyframes up{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:none}}}}
.bg{{position:absolute;inset:-60px;background:url(data:image/jpeg;base64,{img}) center/cover;filter:blur(36px) brightness(.38)}}
.band{{position:absolute;top:0;left:0;right:0;padding:52px 56px 0}}
.src{{font-size:22px;color:#9a8fb0}} .w{{font-size:44px;font-weight:700;color:#fff;margin-top:14px}}
.big{{font-size:76px;font-weight:900;color:#fff;line-height:1.15;margin-top:8px;letter-spacing:-2px;opacity:0;animation:up .5s ease-out .1s forwards}} .big b{{color:#FFD23F}}
.sub{{font-size:36px;color:#e9dcff;margin-top:12px;font-weight:600;opacity:0;animation:up .5s ease-out .35s forwards}}
.jp{{font-size:30px;color:#c8b8e8;margin-top:8px;font-family:'Noto Sans CJK JP';opacity:0;animation:up .5s ease-out .5s forwards}}
.vid{{position:absolute;top:640px;left:0;width:1080px;height:608px;overflow:hidden}} .vid img{{width:100%;height:100%;object-fit:cover;animation:kb {DUR[i]}s linear forwards}}
.cm{{position:absolute;left:60px;right:60px;top:1310px;opacity:0;animation:up .5s ease-out .6s forwards}}
.lab{{font-size:24px;color:#b9a8d8;margin-bottom:12px}}
.row{{display:flex;gap:20px;background:#0f0f0f;border-radius:22px;padding:26px 28px}}
.av{{width:58px;height:58px;border-radius:50%;background:#555;filter:blur(3px);flex:none}}
.nm{{width:190px;height:22px;background:#444;border-radius:6px;filter:blur(4px);margin-bottom:12px}}
.tx{{font-size:34px;line-height:1.42;color:#f1f1f1}} .tr{{font-size:27px;line-height:1.35;color:#aaa;margin-top:10px}}
.lk{{font-size:26px;color:#aaa;margin-top:12px}}
.prog{{position:absolute;top:1252px;left:0;height:7px;background:#FFD23F}}
</style></head><body><div class='bg'></div>
<div class='band'><div class='src'>{SRC}</div><div class='w'>베스티 「연애의 조건」 · 해외 반응</div><div class='big'>{big}</div><div class='sub'>{sub}</div><div class='jp'>🇯🇵 {jp}</div></div>
<div class='vid'><img src='data:image/jpeg;base64,{img}'></div><div class='prog' id='pg'></div>{cmt}</body></html>"""
async def main():
  out=S+"/reel"; os.makedirs(out,exist_ok=True); total=sum(DUR)-XF*(N-1); t0=0
  async with async_playwright() as pw:
    br=await pw.chromium.launch(); pg=await br.new_page(viewport={"width":1080,"height":1920})
    for i in range(N):
      await pg.set_content(page(i)); await pg.wait_for_timeout(150)
      ff=subprocess.Popen(["ffmpeg","-v","error","-y","-f","image2pipe","-framerate",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",f"{out}/c{i}.mp4"],stdin=subprocess.PIPE)
      for f in range(int(DUR[i]*FPS)):
        t=f/FPS; gt=t0+t
        await pg.evaluate(f"()=>{{document.getAnimations().forEach(a=>{{a.pause();a.currentTime={t*1000}}});document.getElementById('pg').style.width=({gt}/{total}*1080)+'px'}}")
        ff.stdin.write(await pg.screenshot(type="jpeg",quality=92))
      ff.stdin.close(); ff.wait(); t0+=DUR[i]-XF
    await br.close()
  ins=[]; [ins.extend(["-i",f"{out}/c{i}.mp4"]) for i in range(N)]
  f=[]; prev="0:v"; off=0
  for k in range(1,N):
    off+=DUR[k-1]-XF; o=f"x{k}" if k<N-1 else "vx"
    f.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[{o}]"); prev=o
  subprocess.run(["ffmpeg","-v","error","-y",*ins,"-filter_complex",";".join(f),"-map","[vx]","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-r","30",f"{out}/silent.mp4"],check=True)
  print("total",total)
asyncio.run(main())
