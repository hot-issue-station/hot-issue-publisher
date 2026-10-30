"""음악 없는 릴스용 영상(9:16, 1080x1920, 약 17초)을 카드 7장으로 만든다. 대표가 인스타그램 앱에서 음악만 골라 올린다(대표 결정 10/28).

python scripts/make_reel_silent.py posts/<묶음> /tmp/<이름>.mp4
- 영상은 저장소 밖에 만든다(용량). 효과: 장마다 밀기·당기기·훑기, 장마다 다른 전환, 위쪽 진행 막대, 무음 오디오 트랙.
- (10/30 개선, 건너뛰기 94.8%·평균 1초 대응) rounds/<폴더 이름>.json 이 있으면 세로 전체 화면(1080x1920) 카드로 다시 그려 쓴다.
  첫 장면은 0초부터 표지 전체가 또렷하게 보이게(흰 번쩍임·확대 시작 없음), 표지는 2.4초로 짧게.
"""
import subprocess, sys, pathlib
SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); W, H, FPS = 1080, 1920, 30
import tempfile
work = pathlib.Path(tempfile.mkdtemp(prefix="reel_"))
def run(cmd): subprocess.run(cmd, check=True, capture_output=True)
ROOT = pathlib.Path(__file__).resolve().parent.parent
FULL = False
rj = ROOT / "rounds" / f"{SRC.name}.json"
if rj.exists():
    try:
        import json
        sys.path.insert(0, str(ROOT / "scripts"))
        import make_post
        r = json.loads(rj.read_text(encoding="utf-8"))
        make_post.LAYOUT = make_post.REEL
        make_post.render(make_post.cards(r), work, h=H, prefix="full_")
        make_post.LAYOUT = make_post.FEED
        FULL = all((work / f"full_{i:02d}.jpg").exists() for i in range(1, 8))
    except Exception as e:
        print("세로 카드 만들기 실패, 기존 방식 사용:", e)
# 장별 (길이초, 효과, 초점x, 초점y, 시작배율, 끝배율)  초점은 9:16 화면 기준 비율
plan = [
 (2.4, 0.50, 0.50, 1.00, 1.05),   # 1 표지: 0초부터 전체가 보이고 살짝 밀어 들어가기(10/30)
 (2.6, 0.50, 0.50, 1.00, 1.08),   # 2 요약: 천천히 밀어 들어가기
 (2.6, 0.35, 0.40, 1.00, 1.12),   # 3 사실: 제목 쪽으로 포커스
 (2.6, 0.50, 0.40, 1.10, 1.10),   # 4 사실: 위→아래로 훑기(팬)
 (2.6, 0.50, 0.50, 1.12, 1.00),   # 5 사실: 당겨서 빠지기
 (3.0, 0.50, 0.46, 1.35, 1.00),   # 6 해석: 문장에 포커스 → 천천히 공개
 (3.0, 0.50, 0.50, 1.00, 1.06),   # 7 마무리
]
trans = ["zoomin", "slideup", "smoothleft", "fadeblack", "circleopen", "hblur"]
T = 0.45
clips = []
for i, (dur, fx, fy, z0, z1) in enumerate(plan, 1):
    card = SRC / f"{i:02d}.jpg"
    comp = work / f"comp{i}.png"
    if FULL:
        comp = work / f"full_{i:02d}.jpg"
    else:
        # 9:16 화면: 같은 카드를 흐리게 깔고 가운데 카드
        run(["ffmpeg","-y","-i",str(card),"-filter_complex",
             f"[0]scale=-1:{H},crop={W}:{H},gblur=sigma=40,eq=brightness=-0.18[bg];[0]scale={W}:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2",
             "-frames:v","1",str(comp)])
    n = int(dur*FPS)
    # 부드러운 움직임(ease-out): p = 1-(1-t)^3
    p = f"(1-pow(1-on/{n},3))"
    z = f"{z0}+({z1}-{z0})*{p}"
    if i == 4:  # 위에서 아래로 훑기
        y = f"(ih-ih/zoom)*(0.15+0.7*{p})"
    else:
        y = f"max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2))"
    x = f"max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2))"
    clip = work / f"clip{i}.mp4"
    run(["ffmpeg","-y","-loop","1","-i",str(comp),"-vf",
         f"scale={W*2}:{H*2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
         "-frames:v",str(n),"-c:v","libx264","-preset","veryfast","-crf","18",str(clip)])
    clips.append((clip, dur))
# 전환 이어 붙이기
inputs, fc, prev, off = [], [], "[0:v]", 0.0
for c,_ in clips: inputs += ["-i", str(c)]
for k in range(1, len(clips)):
    off += clips[k-1][1] - T
    lab = f"[v{k}]"
    fc.append(f"{prev}[{k}:v]xfade=transition={trans[k-1]}:duration={T}:offset={off:.3f}{lab}")
    prev = lab
total = sum(d for _,d in clips) - T*(len(clips)-1)
# 위쪽 진행 막대 (첫 흰 번쩍임은 10/30에 뺌)
fc.append(f"{prev}drawbox=x=0:y=0:w=iw:h=10:color=white@0.15:t=fill,drawbox=x=0:y=0:w='iw*t/{total:.3f}':h=10:color=0x35E0FF@0.95:t=fill[out]")
run(["ffmpeg","-y",*inputs,"-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-filter_complex",";".join(fc),
     "-map","[out]","-map",f"{len(clips)}:a","-t",f"{total:.3f}","-c:v","libx264","-preset","veryfast","-crf","20",
     "-pix_fmt","yuv420p","-c:a","aac","-b:a","64k","-movflags","+faststart",str(OUT)])
print(f"done {total:.1f}s -> {OUT}" + (" (세로 전체 화면 카드)" if FULL else " (피드 카드 합성)"))
