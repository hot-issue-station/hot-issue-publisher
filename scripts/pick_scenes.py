"""오메가컷(OmegaCut) 1단계 — 롱폼 영상 → 하이라이트 후보 장면 (이름: 대표 결정 2026-11-02 14:20, 원칙: AI는 초안, 장면은 사람이 고른다).

python scripts/pick_scenes.py <영상.mp4> <출력폴더> [--n 10] [--len 6]
- 화면 전환(장면 바뀜)과 소리 크기(웃음·리액션·함성) 를 같이 보고 점수를 매긴다.
- 출력: <출력폴더>/candidates.json  [{no, start, end, score, why}],  <출력폴더>/sheet.jpg (후보 10장 한 장 모음, 번호 표시)
- 대표가 번호를 고르면 make_long_summary 단계에서 이어 붙인다. 허락받은 영상만 넣는다.
"""
import argparse, json, pathlib, re, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--n", type=int, default=10); ap.add_argument("--len", type=float, default=6.0)
a = ap.parse_args()
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video],
                           capture_output=True, text=True).stdout.strip())

# 1) 장면 전환 시각
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-vf", "scale=320:-2,select='gt(scene,0.32)',showinfo", "-an", "-f", "null", "-"],
                   capture_output=True, text=True)
cuts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]

# 2) 1초 단위 소리 크기(RMS, dB)
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
x = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
sec = max(1, int(len(x) / 8000))
rms = np.array([np.sqrt(np.mean(x[i * 8000:(i + 1) * 8000] ** 2) + 1e-9) for i in range(sec)])
db = 20 * np.log10(rms); base = np.median(db)

# 3) 초마다 점수: 평소보다 큰 소리 + 근처 장면 전환 밀도(빠른 편집 = 재밌는 구간인 경우가 많음)
score = np.zeros(sec)
for i in range(sec):
    loud = max(0, db[i] - base)                                  # 평소 대비 dB
    jump = max(0, db[i] - db[max(0, i - 2)])                     # 갑자기 커짐(웃음·함성)
    dens = sum(1 for c in cuts if i - 3 <= c < i + 3)
    score[i] = loud * 1.0 + jump * 1.5 + dens * 0.8
L = int(a.len); picks = []
order = np.argsort(-score)
for i in order:
    if i < 3 or i > sec - 3: continue                            # 처음·끝 인사 구간 제외
    if any(abs(i - p) < L * 1.5 for p in picks): continue        # 서로 겹치지 않게
    picks.append(int(i))
    if len(picks) == a.n: break
picks.sort()
cands = []
for k, p in enumerate(picks, 1):
    st = max(0, p - L * 0.4); en = min(dur, st + L)
    why = []
    if db[p] - base > 6: why.append("소리 크게 터짐")
    if db[p] - db[max(0, p - 2)] > 6: why.append("갑자기 커짐(웃음·리액션?)")
    if sum(1 for c in cuts if p - 3 <= c < p + 3) >= 2: why.append("빠른 편집")
    cands.append({"no": k, "start": round(st, 1), "end": round(en, 1), "score": round(float(score[p]), 1), "why": " · ".join(why) or "무난"})
(out / "candidates.json").write_text(json.dumps({"video": a.video, "duration": dur, "candidates": cands}, ensure_ascii=False, indent=1), encoding="utf-8")

# 4) 후보 모음 이미지(번호·시각 표시) — 대표가 보고 번호로 고른다
tiles = []
for c in cands:
    t = (c["start"] + c["end"]) / 2; f = out / f"c{c['no']:02d}.jpg"
    lab = f"{c['no']}  {int(c['start'] // 60)}:{int(c['start'] % 60):02d}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", a.video, "-frames:v", "1", "-vf",
                    f"scale=480:-2,drawbox=x=0:y=0:w=200:h=56:color=black@0.7:t=fill,drawtext=fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc:text='{lab}':x=12:y=8:fontsize=36:fontcolor=yellow",
                    str(f)], check=True)
    tiles.append(str(f))
cols = 2
inputs = sum([["-i", t] for t in tiles], [])
rows = [f"[{i}][{i+1}]hstack[r{i//cols}]" if i + 1 < len(tiles) else f"[{i}]pad=iw*2:ih[r{i//cols}]" for i in range(0, len(tiles), cols)]
nr = (len(tiles) + 1) // cols
fc = ";".join(rows) + ";" + "".join(f"[r{j}]" for j in range(nr)) + f"vstack=inputs={nr}" if nr > 1 else ";".join(rows)
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, str(out / "sheet.jpg")], check=True)
print("후보", len(cands), "개 →", out / "candidates.json", out / "sheet.jpg")
