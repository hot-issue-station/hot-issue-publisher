#!/usr/bin/env python3
"""리브 리무진서비스 노래 쇼츠 (새 스타일, 1분 연속 하이라이트). 사용: make_liv.py <config.json>"""
import json, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
C = json.load(open(sys.argv[1], encoding="utf-8"))
W, H = 1080, 1920
F = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
O = C["out_dir"]; os.makedirs(O, exist_ok=True)
SRC, SS, DUR = C["src"], C["start"], C["dur"]
CX0, CY0, CX1, CY1 = C["crop"]
VW = W; VH = round((CY1 - CY0) * W / (CX1 - CX0) / 2) * 2
VY = 500
END = 3.5
TOT = DUR + END

def font(p, s): return ImageFont.truetype(p, s)
def run(a): subprocess.run(a, check=True)

# 1) 고정 틀(위 띠 + 아래 댓글 칸 제목)
base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(base)
d.rectangle([0, 0, W, VY - 20], fill=(14, 10, 26, 235))
d.text((W / 2, 70), C["src_line"], font=font(FB, 32), fill=(190, 185, 210), anchor="mm")
d.text((W / 2, 150), C["white_line"], font=font(F, 62), fill=(255, 255, 255), anchor="mm")
d.text((W / 2, 262), C["big_line"], font=font(F, 104), fill=tuple(C["color"]), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
d.text((W / 2, 362), C["sub_line"], font=font(FB, 36), fill=(225, 220, 240), anchor="mm")
d.text((W / 2, 425), C["jp_line"], font=font(FM, 30), fill=(200, 196, 220), anchor="mm")
d.rectangle([0, VY + VH + 20, W, H], fill=(14, 10, 26, 200))
sf = font(FB, 26); s = "출처: " + C["credit"]
sw = d.textlength(s, font=sf)
d.rounded_rectangle([W - sw - 60, VY + 14, W - 24, VY + 54], 10, fill=(0, 0, 0, 160))
d.text((W - sw - 42, VY + 18), s, font=sf, fill=(215, 215, 230))
base.save(O + "/frame.png")

# 2) 댓글 상자들 (아래 칸, 차례로)
def comment_png(i, text, likes, jp=""):
    im = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.rounded_rectangle([50, 20, W - 50, 400], 36, fill=(255, 255, 255, 240))
    g.ellipse([90, 60, 150, 120], fill=(200, 190, 230))
    g.rounded_rectangle([170, 72, 340, 104], 12, fill=(215, 210, 225))
    g.text((360, 74), "· 리무진서비스 댓글", font=font(FM, 28), fill=(130, 125, 145))
    f = font(FB, 44); lines = []; cur = ""
    for ch in text:
        if g.textlength(cur + ch, font=f) > W - 200: lines.append(cur); cur = ch
        else: cur += ch
    lines.append(cur)
    y = 150
    for ln in lines[:4]:
        g.text((95, y), ln, font=f, fill=(30, 28, 40)); y += 62
    if jp: g.text((95, y + 4), jp, font=font(FM, 30), fill=(110, 100, 150))
    g.text((95, 340), ("좋아요 " + likes) if likes else "", font=font(FM, 30), fill=(120, 115, 135))
    p = f"{O}/c{i}.png"; im.save(p); return p

def small_png(i, text):
    im = Image.new("RGBA", (W, 200), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    f = font(FB, 40); lines = []; cur = ""
    for ch in text:
        if g.textlength(cur + ch, font=f) > W - 190: lines.append(cur); cur = ch
        else: cur += ch
    lines.append(cur); lines = lines[:2]
    h = 70 + 56 * len(lines)
    g.rounded_rectangle([40, 10, W - 40, 10 + h], 30, fill=(255, 255, 255, 238))
    g.ellipse([70, 34, 110, 74], fill=(200, 190, 230)); g.rounded_rectangle([124, 44, 260, 64], 9, fill=(215, 210, 225))
    y = 82
    for ln in lines: g.text((75, y - 4), ln, font=f, fill=(30, 28, 40)); y += 56
    p = f"{O}/s{i}.png"; im.save(p); return p
STREAM = C.get("stream")
if STREAM:
    cps = [small_png(i, t) for i, t in enumerate(STREAM)]
    seg = DUR / ((len(cps) + 1) // 2)
else:
    cps = [comment_png(i, *c) for i, c in enumerate(C["comments"])]
    seg = DUR / len(cps)

# 3) 흰 상자 리액션 자막, 가운데 큰 키워드
def white_box(i, text):
    f = font(F, 50); tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f)
    im = Image.new("RGBA", (int(tw) + 80, 100), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.rounded_rectangle([0, 0, im.width - 1, 99], 18, fill=(255, 255, 255, 245))
    g.text((40, 18), text, font=f, fill=(20, 20, 30)); p = f"{O}/w{i}.png"; im.save(p); return p
def keyword(i, text):
    f = font(F, 120); tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f)
    im = Image.new("RGBA", (int(tw) + 60, 180), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.text((30, 10), text, font=f, fill=tuple(C["color"]), stroke_width=8, stroke_fill=(255, 255, 255))
    p = f"{O}/k{i}.png"; im.save(p); return p
wps = [(white_box(i, t), a, b) for i, (t, a, b) in enumerate(C["reactions"])]
kps = [(keyword(i, t), a, b) for i, (t, a, b) in enumerate(C["keywords"])]

# 4) 마지막 안내 카드
end = Image.new("RGB", (W, H), (14, 10, 26)); g = ImageDraw.Draw(end)
g.text((W / 2, 700), "전곡은 원본에서", font=font(F, 84), fill=(255, 255, 255), anchor="mm")
g.text((W / 2, 820), C["end_src"], font=font(FB, 46), fill=tuple(C["color"]), anchor="mm")
g.text((W / 2, 900), "리브의 무대 전체를 들어 보세요", font=font(FB, 40), fill=(220, 215, 235), anchor="mm")
g.text((W / 2, 1150), "구독 · 좋아요 · 알림 설정", font=font(F, 60), fill=(255, 255, 255), anchor="mm")
g.text((W / 2, 1240), "매일 이슈를 짧고 따뜻하게, 이슈브리프", font=font(FB, 38), fill=(200, 195, 220), anchor="mm")
g.text((W / 2, 1320), "フル視聴は原曲動画で", font=font(FM, 32), fill=(180, 175, 200), anchor="mm")
end.save(O + "/end.png")

# 5) 합성
inputs = ["-ss", str(SS), "-t", str(DUR), "-i", SRC, "-loop", "1", "-t", str(DUR), "-i", O + "/frame.png"]
for p in cps: inputs += ["-loop", "1", "-t", str(DUR), "-i", p]
for p, a, b in wps + kps: inputs += ["-loop", "1", "-t", str(DUR), "-i", p]
cw, ch = CX1 - CX0, CY1 - CY0
fc = (f"[0:v]crop={cw}:{ch}:{CX0}:{CY0},split[a][b];"
      f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.35[bg];"
      f"[b]scale={VW}:{VH}[fg];[bg][fg]overlay=0:{VY}[v0];[v0][1:v]overlay=0:0[v1]")
last = "v1"; idx = 2; CY = VY + VH + 60
for i in range(len(cps)):
    if STREAM:
        k = i // 2; a, b = k * seg, (k + 1) * seg; yy = CY - 30 + (i % 2) * 215
    else:
        a, b = i * seg, (i + 1) * seg; yy = CY
    fc += f";[{last}][{idx}:v]overlay=0:{yy}:enable='between(t,{a:.2f},{b:.2f})'[c{i}]"; last = f"c{i}"; idx += 1
for j, (p, a, b) in enumerate(wps):
    fc += f";[{last}][{idx}:v]overlay=60:{VY + 80}:enable='between(t,{a},{b})'[w{j}]"; last = f"w{j}"; idx += 1
for j, (p, a, b) in enumerate(kps):
    fc += f";[{last}][{idx}:v]overlay=(W-w)/2:{VY + VH // 2 - 90}:enable='between(t,{a},{b})'[k{j}]"; last = f"k{j}"; idx += 1
fc += f";[{last}]fps=30,format=yuv420p[vout];[0:a]afade=t=in:d=0.4,afade=t=out:st={DUR - 1.2}:d=1.2[aout]"
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", O + "/body.mp4"])
run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(END), "-i", O + "/end.png", "-f", "lavfi", "-t", str(END), "-i", "anullsrc=r=48000:cl=stereo",
     "-vf", "fps=30,fade=t=in:d=0.4,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", O + "/end.mp4"])
open(O + "/list.txt", "w").write(f"file '{O}/body.mp4'\nfile '{O}/end.mp4'\n")
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", O + "/list.txt", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "160k", O + "/full.mp4"])
print("ok", O + "/full.mp4", TOT)
