"""영상형 쇼츠 만들기 (대표 결정 2026-11-02: 공개 영상 + 위 두 줄 제목 + 자막 + 내레이션 + 수노 음악).

python scripts/make_video_short.py shorts/<이름>.json /home/claude/reels/<이름>.mp4

shorts/<이름>.json:
{ "titleBar": ["흰 줄", "노란 줄"],
  "clips": [{"file": "assets/video/a.mp4", "start": 0, "end": 22}, ...],   # 이어 붙여 내레이션 길이만큼 씀(모자라면 처음부터 반복)
  "voice": "assets/voice/<이름>",        # make_voice.py 결과(NN.wav + lines.json, 자막 = lines[].text)
  "music": "world",                      # config/music_map.json 시리즈, 내레이션 밑에 작게 깔림
  "credit": "영상: NASA 고다드우주비행센터 · 자료: …",
  "crop": "center",
  "en": ["English line 1", ...] }         # (선택) 해외편 영어 자막 — 내레이션 줄과 같은 개수, 한국어 자막 아래 작게
쓸 수 있는 영상은 docs/make_quick.md 0장의 영상 사용 규칙(공개 영상만)을 따른다.
화면: 위 제목 띠(make_reel_motion 과 같은 모양) / 가운데 영상(정사각형으로 잘라 1080×1080) / 아래 자막 / 맨 아래 출처.
"""
import html, json, re, pathlib, subprocess, sys, tempfile, wave

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from make_reel_motion import band_png, BAND_H, W, H  # noqa: E402

LEAD, GAP, TAIL = 0.6, 0.35, 1.6     # 처음 여유, 줄 사이, 끝 여유(초)
VID_Y = BAND_H + 40                  # 영상 칸 위치
SUB_Y = VID_Y + 1080 + 30            # 자막 칸 위치
SUB_HTML = """<html><head><meta charset="utf-8"><style>
body{margin:0;width:1080px;height:340px;background:transparent;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;
font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;word-break:keep-all}
.s{font-weight:800;font-size:52px;line-height:1.32;color:#fff;text-align:center;padding:0 60px;
text-shadow:0 0 12px rgba(0,0,0,.9),0 3px 0 #000}
.e{margin-top:14px;font-weight:600;font-size:32px;line-height:1.28;color:#c9d3e3;text-align:center;padding:0 70px;
font-family:'Noto Sans','Noto Sans CJK KR',sans-serif;text-shadow:0 0 10px rgba(0,0,0,.9)}
</style></head><body><div class="s">%s</div>%s</body></html>"""
CREDIT_HTML = """<html><head><meta charset="utf-8"><style>
body{margin:0;width:1080px;height:60px;background:transparent;display:flex;align-items:center;justify-content:center;
font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif}
.c{font-size:24px;color:#9aa4b5;font-weight:600}</style></head><body><div class="c">%s</div></body></html>"""


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


def main():
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2]); out.parent.mkdir(parents=True, exist_ok=True)
    vdir = ROOT / spec["voice"]
    lines = json.loads((vdir / "lines.json").read_text(encoding="utf-8"))
    # 1) 자막 시각표
    t, cues = LEAD, []
    for ln in lines:
        cues.append((t, t + ln["sec"], ln["text"], vdir / f"{ln['i']:02d}.wav"))
        t += ln["sec"] + GAP
    total = t - GAP + TAIL
    work = pathlib.Path(tempfile.mkdtemp(prefix="vshort_"))
    # 2) 그림(제목 띠·자막·출처) PNG
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        band_png(list(spec["titleBar"]), work / "band.png", pg)
        en = spec.get("en") or []
        for k, (_, _, txt, _) in enumerate(cues):
            pg.set_viewport_size({"width": W, "height": 340})
            ed = f'<div class="e">{html.escape(en[k])}</div>' if k < len(en) and en[k] else ""
            pg.set_content(SUB_HTML % (re.sub(r"(\d[\d,.]*[천만억조]?) (?=\S)", "\\1&nbsp;", html.escape(txt)), ed)); pg.wait_for_timeout(120)
            pg.screenshot(path=str(work / f"sub{k:02d}.png"), omit_background=True)
        pg.set_viewport_size({"width": W, "height": 60})
        pg.set_content(CREDIT_HTML % html.escape(spec.get("credit", ""))); pg.wait_for_timeout(120)
        pg.screenshot(path=str(work / "credit.png"), omit_background=True)
        b.close()
    # 3) 영상 이어 붙이기(정사각형 1080) — 내레이션 길이만큼, 모자라면 반복
    segs, have = [], 0.0
    while have < total:
        for c in spec["clips"]:
            f = ROOT / c["file"]; st = float(c.get("start", 0)); en = float(c.get("end", dur(f)))
            take = min(en - st, total - have)
            if take <= 0.05: break
            sp = work / f"seg{len(segs):02d}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{st}", "-t", f"{take:.2f}", "-i", str(f), "-an",
                            "-vf", "crop=ih:ih:(iw-ih)/2:0,scale=1080:1080,fps=30,setsar=1", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", str(sp)], check=True)
            segs.append(sp); have += take
            if have >= total: break
    (work / "list.txt").write_text("".join(f"file '{s}'\n" for s in segs))
    body = work / "body.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "list.txt"), "-c", "copy", str(body)], check=True)
    # 4) 소리: 내레이션(제 시각에) + 음악(작게, 끝 페이드)
    mm = json.loads((ROOT / "config/music_map.json").read_text(encoding="utf-8"))[spec.get("music", "news")]
    ins = ["-i", str(ROOT / mm["file"])]
    amix = []
    for k, (st, _, _, wf) in enumerate(cues):
        ins += ["-i", str(wf)]
        amix.append(f"[{k + 1}:a]adelay={int(st * 1000)}|{int(st * 1000)},aresample=44100,aformat=channel_layouts=stereo[n{k}]")
    fo = total - 1.8
    af = (f"[0:a]atrim=0:{total:.2f},asetpts=PTS-STARTPTS,volume=0.16,afade=t=out:st={fo:.2f}:d=1.8,aresample=44100,aformat=channel_layouts=stereo[m];"
          + ";".join(amix) + ";" + "[m]" + "".join(f"[n{k}]" for k in range(len(cues)))
          + f"amix=inputs={len(cues) + 1}:normalize=0,loudnorm=I=-16:TP=-1.5[a]")
    audio = work / "audio.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", af, "-map", "[a]", "-t", f"{total:.2f}", "-c:a", "aac", "-b:a", "192k", str(audio)], check=True)
    # 5) 합치기: 검은 바탕 + 영상 + 제목 띠 + 자막(시각별) + 출처
    vin = ["-f", "lavfi", "-i", f"color=c=0x05070c:s={W}x{H}:r=30:d={total:.2f}", "-i", str(body), "-i", str(work / "band.png"),
           "-i", str(work / "credit.png")]
    for k in range(len(cues)):
        vin += ["-i", str(work / f"sub{k:02d}.png")]
    fl = [f"[0:v][1:v]overlay=0:{VID_Y}:shortest=1[v0]", f"[v0][2:v]overlay=0:0[v1]", f"[v1][3:v]overlay=0:{H - 80}[v2]"]
    last = "v2"
    for k, (st, en, _, _) in enumerate(cues):
        nl = f"s{k}"
        fl.append(f"[{last}][{k + 4}:v]overlay=0:{SUB_Y}:enable='between(t,{st:.2f},{en + GAP:.2f})'[{nl}]"); last = nl
    vin += ["-i", str(audio)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *vin, "-filter_complex", ";".join(fl), "-map", f"[{last}]", "-map", f"{len(cues) + 4}:a",
                    "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", str(out)], check=True)
    print(f"done {total:.1f}s -> {out}")


if __name__ == "__main__":
    main()
