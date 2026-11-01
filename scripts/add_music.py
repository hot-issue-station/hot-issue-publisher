"""릴스 영상에 시리즈별 자작곡(config/music_map.json)을 입힌다.
python scripts/add_music.py <영상.mp4> <series: news|calm|briefing|world|legend|emotion|recap|rescene> <결과.mp4> [--start 초]
곡 앞부분(또는 --start 부터)을 영상 길이만큼 잘라 끝 1.8초를 부드럽게 줄이고 음량을 -16 LUFS로 맞춘다."""
import argparse, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("series"); ap.add_argument("out"); ap.add_argument("--start", type=float, default=0)
a = ap.parse_args()
m = json.loads((ROOT / "config/music_map.json").read_text(encoding="utf-8"))[a.series]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video]).strip())
fo = max(0.0, dur - 1.8)
af = f"[1:a]atrim={a.start}:{a.start + dur},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,afade=t=out:st={fo:.2f}:d=1.8,loudnorm=I=-16:TP=-1.5[a]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-i", str(ROOT / m["file"]), "-filter_complex", af,
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", a.out], check=True)
print("완료:", a.out, "←", m["title"])
