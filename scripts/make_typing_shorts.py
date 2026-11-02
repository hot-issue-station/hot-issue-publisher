"""브리핑 카드 1장 → 쇼츠(9:16): 카메라 이동 + 타자 소리에 맞춰 핵심 키워드가 한 글자씩 입력 (대표 요청 2026-11-02 13:28).

python scripts/make_typing_shorts.py <card.jpg> <out.mp4> --kw "0.6|10월 수출 1,153억 달러" --kw "4.2|반도체가 절반, 564억 달러" --kw "7.6|1조 달러까지 700억" [--series briefing] [--dur 12]
- 키워드는 카드 위쪽 빈 띠(0~285px)에 흰 굵은 글씨로 찍히고, 다음 키워드가 나오면 지워진 뒤 새로 입력된다.
- 타자 소리는 직접 합성(외부 음원 없음). 음악은 config/music_map.json 의 series.
- 카메라: 0~5초 확대한 채 위→아래로 훑기, 6~8초 뒤로 빠져 전체, 이후 정지.
"""
import argparse, json, pathlib, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FPS, W, BAND = 30, 1080, 285
CPS = 0.085          # 한 글자 간격(초)
SR = 44100

ap = argparse.ArgumentParser()
ap.add_argument("card"); ap.add_argument("out")
ap.add_argument("--kw", action="append", required=True, help="시작초|문구")
ap.add_argument("--series", default="briefing"); ap.add_argument("--dur", type=float, default=12)
ap.add_argument("--end", action="append", default=[], help="시작초|마무리 문구(화면 가운데, 어둡게 깔고 입력). 문구 안 / 는 줄바꿈")
ap.add_argument("--pointer", default="", help="시작초|문구 — 마무리 화면에 로고 + 오른쪽 아래를 가리키는 깜빡이는 화살표")
ap.add_argument("--slow", type=float, default=1.0, help="카메라 이동을 이만큼 느리게")
a = ap.parse_args()
kws = [(float(s.split("|", 1)[0]), s.split("|", 1)[1]) for s in a.kw]
ends = [(float(s.split("|", 1)[0]), s.split("|", 1)[1]) for s in a.end]
PT = (float(a.pointer.split("|", 1)[0]), a.pointer.split("|", 1)[1]) if a.pointer else None
END0 = min([e[0] for e in ends], default=1e9)
N = int(a.dur * FPS)
tmp = pathlib.Path(tempfile.mkdtemp())

# 1) 카메라 이동 영상
k = a.slow; P1, P2, P3 = int(150*k), int(180*k), int(70*k)
T = f"min(on/{P1},1)"
Z = f"if(lt(on,{P2}),1.45,if(lt(on,{P2+P3}),1+0.45*(1-((on-{P2})/{P3})*((on-{P2})/{P3})*(3-2*(on-{P2})/{P3})),1))"
Y = f"(ih-ih/zoom)*(0.08+0.84*({T})*({T})*(3-2*({T})))"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.card, "-filter_complex",
    f"[0]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.25,loop={N}:1:0,setpts=N/{FPS}/TB[bg];"
    f"[b]scale=2160:-2,zoompan=z='{Z}':x='(iw-iw/zoom)*0.1':y='{Y}':d={N}:s=1080x1350:fps={FPS}[fg];[bg][fg]overlay=0:285:shortest=1,format=yuv420p",
    "-t", str(a.dur), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(tmp / "base.mp4")], check=True)

# 2) 키워드 글자 프레임 + 타자 시각
font = ImageFont.truetype(FONT, 72)
hits = []
def state(t):
    cur = None
    for i, (st, txt) in enumerate(kws):
        if t >= st: cur = i
    if cur is None or t >= END0: return "", False
    st, txt = kws[cur]
    n = min(len(txt), int((t - st) / CPS) + 1)
    return txt[:n], n < len(txt)
for st, txt in kws + ends + ([PT] if PT else []):
    for j, ch in enumerate(txt):
        if ch not in " /": hits.append(st + j * CPS)
efont = ImageFont.truetype(FONT, 64)
pfont = ImageFont.truetype(FONT, 54)
LOGO = Image.open(ROOT / "assets/brand/logo_wordmark.png").convert("RGBA").crop((180, 120, 1020, 510)).resize((630, 292))
lmask = Image.new("L", LOGO.size, 0); ImageDraw.Draw(lmask).rounded_rectangle([0, 0, *LOGO.size], 36, fill=255); LOGO.putalpha(lmask)
def arrow(d, x0, y0, x1, y1, col, w=26):
    import math
    ang = math.atan2(y1 - y0, x1 - x0); hl = 70
    bx, by = x1 - hl * math.cos(ang), y1 - hl * math.sin(ang)
    d.line([x0, y0, bx, by], fill=col, width=w)
    px, py = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
    d.polygon([(x1, y1), (bx + px * 46, by + py * 46), (bx - px * 46, by - py * 46)], fill=col)
fr = tmp / "fr"; fr.mkdir()
for f in range(N):
    t = f / FPS
    txt, typing = state(t)
    im = Image.new("RGBA", (W, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if t >= END0:
        al = min(1, (t - END0) / 0.5); d.rectangle([0, 0, W, 1920], fill=(8, 12, 22, int(215 * al)))
        la = min(1, (t - END0) / 0.6)
        lg = LOGO.copy(); lg.putalpha(lg.getchannel("A").point(lambda v: int(v * la)))
        im.alpha_composite(lg, ((W - LOGO.width) // 2, 330))
        y = 700
        live = max(i for i, e in enumerate(ends) if t >= e[0]) if t >= ends[0][0] else -1
        for ei, (est, etxt) in enumerate(ends):
            if t < est: continue
            n = min(len(etxt), int((t - est) / CPS) + 1); done = n == len(etxt)
            for li, line in enumerate(etxt[:n].split("/")):
                tw = d.textlength(line, font=efont); d.text(((W - tw) / 2, y), line, font=efont, fill="white" if ei == 0 else (255, 200, 69))
                last = (W + tw) / 2; ly = y; y += 92
            if ei == live and not (PT and t >= PT[0]) and (not done or int(t * 2) % 2 == 0): d.rectangle([last + 10, ly + 10, last + 19, ly + 78], fill=(255, 200, 69))
            y += 60
        if PT and t >= PT[0]:
            on = int((t - PT[0]) * 3) % 2 == 0          # 초당 1.5번 깜빡
            col = (255, 200, 69) if on else (255, 120, 80)
            n = min(len(PT[1]), int((t - PT[0]) / CPS) + 1)
            for li, line in enumerate(PT[1][:n].split("/")):
                tw = d.textlength(line, font=pfont); d.text((W - 60 - tw, 1290 + li * 76), line, font=pfont, fill=col)
            if n == len(PT[1]):
                off = 0 if on else 24
                arrow(d, 720 + off, 1480 + off, 960 + off, 1720 + off, col)
                if on: d.ellipse([930, 1690, 1050, 1810], outline=col, width=10)
    if txt:
        tw = d.textlength(txt, font=font); x = max(40, (W - tw) / 2); y = 100
        d.rounded_rectangle([x - 28, y - 18, x + tw + 52, y + 98], 18, fill=(11, 18, 32, 215))
        d.text((x, y), txt, font=font, fill="white")
        if typing or int(t * 2) % 2 == 0:   # 입력 중엔 커서 고정, 끝나면 깜빡
            cx = x + tw + 10; d.rectangle([cx, y + 12, cx + 10, y + 86], fill=(255, 200, 69))
    im.save(fr / f"{f:04d}.png")

# 3) 타자 소리(합성)
rng = np.random.default_rng(3)
aud = np.zeros(int((a.dur + 1) * SR))
for h in hits:
    n = int(0.045 * SR); tt = np.arange(n) / SR
    click = rng.uniform(-1, 1, n) * np.exp(-tt * 140)
    click = np.convolve(click, [1, -0.85], "same")                          # 고음 위주 '딸깍'
    click += 0.6 * np.sin(2 * np.pi * rng.uniform(1700, 2300) * tt) * np.exp(-tt * 220)
    i = int(h * SR); aud[i:i + n] += click * rng.uniform(0.55, 0.8)
aud = aud[: int(a.dur * SR)]; aud /= max(1e-9, np.abs(aud).max()) / 0.7
with wave.open(str(tmp / "type.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((aud * 32767).astype("<i2").tobytes())

# 4) 합치기: 글자 → 음악 → 타자 소리
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "base.mp4"), "-framerate", str(FPS), "-i", str(fr / "%04d.png"),
    "-filter_complex", "[0][1]overlay=0:0,fade=t=in:st=0:d=0.4,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(tmp / "v.mp4")], check=True)
subprocess.run(["python3", str(ROOT / "scripts/add_music.py"), str(tmp / "v.mp4"), a.series, str(tmp / "m.mp4")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "m.mp4"), "-i", str(tmp / "type.wav"), "-filter_complex",
    "[0:a]volume=0.75[m];[1:a]volume=1.0,aformat=channel_layouts=stereo[k];[m][k]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", a.out], check=True)
print("완료:", a.out)
