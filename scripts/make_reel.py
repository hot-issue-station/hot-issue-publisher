"""카드로 릴스 영상(9:16, 1080×1920)을 만든다.

python scripts/make_reel.py posts/20261028_PM [--music pulse]
결과: posts/<묶음>/reel.mp4 (H.264 + AAC, 약 23초)
- 화면: make_post.py --reel 이 그린 릴스 전용 세로 화면(reel_01.jpg~reel_07.jpg)을 쓴다.
  Instagram 화면의 글자·버튼 자리(위 240px, 아래 440px, 오른쪽 160px)를 비워 둔 디자인이다.
  없으면 피드 카드(01.jpg~)를 가운데 놓고 위아래를 남색으로 채운다.
- 역동적인 효과: 장마다 살짝 당겨졌다 자리 잡는 확대 효과, 장마다 다른 전환, 박자에 맞춘 넘김,
  위쪽 진행 막대(청록→분홍).
- 음악: music/<이름>.m4a (기본 pulse, 118BPM). 넘김은 이 박자에 맞춘다.
"""
import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAVY = "0x0B1220"
BPM = {"pulse": 118, "bright": 104, "warm": 84, "calm": 70}
TRANSITIONS = ["slideleft", "circleopen", "smoothleft", "wipeup", "slideleft", "radial"]


def build(folder, music="pulse", fps=30):
    folder = pathlib.Path(folder)
    reel = [folder / f"reel_{i:02d}.jpg" for i in range(1, 8)]
    feed = [folder / f"{i:02d}.jpg" for i in range(1, 8)]
    imgs, native = (reel, True) if all(p.exists() for p in reel) else (feed, False)
    if not all(p.exists() for p in imgs):
        raise SystemExit(f"{folder}: 카드 이미지 7장이 모두 있어야 합니다")
    track = ROOT / "music" / f"{music}.m4a"
    if not track.exists():
        music, track = "pulse", ROOT / "music" / "pulse.m4a"
    beat = 60 / BPM.get(music, 118)
    # 박자에 맞춘 장 길이: 표지 8박, 나머지 6박 (118BPM이면 약 4.1초 / 3.1초)
    beats = [8, 6, 6, 6, 6, 6, 7]
    starts = [0.0]
    for b in beats[:-1]:
        starts.append(starts[-1] + b * beat)
    total = starts[-1] + beats[-1] * beat
    xf = round(beat / 2, 3)                    # 전환은 반 박자
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    f = []
    for k, p in enumerate(imgs):
        seg = (starts[k + 1] - starts[k] + xf) if k < 6 else (total - starts[k])
        frames = int(round(seg * fps))
        args += ["-i", str(p)]
        base = f"[{k}:v]scale=2160:-1" if native else f"[{k}:v]scale=1080:1350,pad=1080:1920:0:285:color={NAVY},scale=2160:-1"
        # 들어올 때 1.06배에서 시작해 1.0으로 자리 잡는 확대 효과(박자감)
        f.append(f"{base},zoompan=z='max(1.0,1.06-0.06*on/{max(1, int(fps * 0.6))})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                 f":d={frames}:s=1080x1920:fps={fps},setsar=1,format=yuv420p[v{k}]")
    args += ["-i", str(track)]
    prev = "v0"
    for k in range(1, 7):
        out = f"x{k}" if k < 6 else "vx"
        f.append(f"[{prev}][v{k}]xfade=transition={TRANSITIONS[k - 1]}:duration={xf}:offset={starts[k]:.3f}[{out}]")
        prev = out
    # 진행 막대: 화면 아래 안전 구역 바로 위(y=205), 시간에 따라 왼쪽에서 오른쪽으로 찬다
    f.append(f"color=c=0x2A3A59:s=900x8:r={fps}:d={total:.3f}[track]")
    f.append(f"color=c=0x35E0FF:s=900x8:r={fps}:d={total:.3f}[fill]")
    f.append(f"[vx][track]overlay=x=90:y=205:shortest=1[vt]")
    f.append(f"[vt][fill]overlay=x='90-900+900*t/{total:.3f}':y=205:shortest=1[vbar]")
    f.append(f"[vbar]drawbox=x=0:y=205:w=90:h=8:color={NAVY}:t=fill,drawbox=x=990:y=205:w=90:h=8:color={NAVY}:t=fill[vout]")
    f.append(f"[7:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.2,afade=t=out:st={total - 1.2:.3f}:d=1.2,"
             f"loudnorm=I=-14:TP=-1.5:LRA=9[aout]")
    out = folder / "reel.mp4"
    args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)]
    subprocess.run(args, check=True)
    return out, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--music", default="pulse")
    a = ap.parse_args()
    out, total = build(a.folder, a.music)
    print(f"완료: {out} ({total:.1f}초, 음악 {a.music}, {out.stat().st_size // 1024}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
