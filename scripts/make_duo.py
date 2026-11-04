#!/usr/bin/env python3
"""위(미나미)·아래(리브) 이어 부르기 쇼츠. 위를 탭하면 위가 부르고, 멈춘 뒤 아래를 탭하면 아래가 이어 부른다."""
import json, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
C = json.load(open(sys.argv[1], encoding="utf-8"))
W, H = 1080, 1920
F = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
O = C["out_dir"]; os.makedirs(O, exist_ok=True)
PW, PH = 1080, 520
TY, BY = 330, 900          # 위·아래 패널 y
CY = 1460                  # 댓글 칸 y
I0 = 0.6                   # 첫 탭
A = C["top"]["dur"]        # 위 재생 길이
SW = 1.2                   # 전환(멈춤 + "이제 ○○ 노래를 들어볼까?" + 아래 탭)
B = C["bot"]["dur"]
TOT = I0 + A + SW + B
def font(p, s): return ImageFont.truetype(p, s)
def run(a): subprocess.run(a, check=True)

# 틀
fr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
d.rectangle([0, 0, W, TY - 16], fill=(14, 10, 26, 235))
d.text((W / 2, 52), C["src_line"], font=font(FB, 30), fill=(190, 185, 210), anchor="mm")
d.text((W / 2, 122), C["white_line"], font=font(F, 58), fill=(255, 255, 255), anchor="mm")
d.text((W / 2, 210), C["big_line"], font=font(F, 76), fill=tuple(C["color"]), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
d.text((W / 2, 285), C["jp_line"], font=font(FM, 28), fill=(205, 200, 225), anchor="mm")
def label(y, t, col):
    f = font(F, 34); w = d.textlength(t, font=f)
    d.rounded_rectangle([24, y + 16, 24 + w + 40, y + 70], 27, fill=col); d.text((44, y + 22), t, font=f, fill=(255, 255, 255))
label(TY, C["top"]["label"], (255, 110, 170, 235)); label(BY, C["bot"]["label"], (110, 150, 255, 235))
sf = font(FB, 22)
for y, s in ((TY, C["top"]["credit"]), (BY, C["bot"]["credit"])):
    w = d.textlength(s, font=sf); d.rounded_rectangle([W - w - 52, y + 14, W - 20, y + 50], 9, fill=(0, 0, 0, 170)); d.text((W - w - 36, y + 18), s, font=sf, fill=(220, 220, 235))
d.rectangle([0, CY - 20, W, H], fill=(14, 10, 26, 200))
fr.save(O + "/frame.png")

# 어둡게 덮개, 탭 물결, 전환 문구
dim = Image.new("RGBA", (PW, PH), (0, 0, 0, 150)); dim.save(O + "/dim.png")
def ripple(name, r):
    im = Image.new("RGBA", (260, 260), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.ellipse([130 - r, 130 - r, 130 + r, 130 + r], outline=(255, 255, 255, 230), width=8)
    g.ellipse([110, 110, 150, 150], fill=(255, 255, 255, 240)); im.save(f"{O}/{name}.png")
for i, r in enumerate((40, 70, 100)): ripple(f"rp{i}", r)
sw = Image.new("RGBA", (W, 150), (0, 0, 0, 0)); g = ImageDraw.Draw(sw)
f = font(F, 52); t = C["switch"]; w = g.textlength(t, font=f)
g.rounded_rectangle([(W - w) / 2 - 40, 20, (W + w) / 2 + 40, 130], 30, fill=(255, 255, 255, 245))
g.text((W / 2, 75), t, font=f, fill=(30, 20, 50), anchor="mm"); sw.save(O + "/switch.png")

# 댓글 (두 개씩)
def small(i, text, who):
    im = Image.new("RGBA", (W, 210), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    f = font(FB, 38); lines = []; cur = ""
    for ch in text:
        if g.textlength(cur + ch, font=f) > W - 190: lines.append(cur); cur = ch
        else: cur += ch
    lines.append(cur); lines = lines[:2]; h = 70 + 54 * len(lines)
    g.rounded_rectangle([40, 8, W - 40, 8 + h], 28, fill=(255, 255, 255, 238))
    g.ellipse([68, 30, 106, 68], fill=(200, 190, 230)); g.rounded_rectangle([118, 40, 240, 58], 9, fill=(215, 210, 225))
    g.text((256, 34), who, font=font(FM, 24), fill=(130, 120, 150))
    y = 78
    for ln in lines: g.text((72, y - 4), ln, font=f, fill=(30, 28, 40)); y += 54
    p = f"{O}/s{i}.png"; im.save(p); return p
cms = [small(i, t, w) for i, (t, w) in enumerate(C["comments"])]
slots = (len(cms) + 1) // 2; seg = TOT / slots

# 합성
T, Bs = C["top"], C["bot"]
inputs = ["-ss", str(T["start"]), "-t", str(A + 0.2), "-i", T["src"], "-ss", str(Bs["start"]), "-t", str(B + 0.2), "-i", Bs["src"]]
def loop(p): return ["-loop", "1", "-t", str(TOT), "-i", p]
for p in ["frame.png", "dim.png", "rp0.png", "rp1.png", "rp2.png", "switch.png"]: inputs += loop(f"{O}/{p}")
for p in cms: inputs += loop(p)
tx, ty, tw, th = T["crop"]; bx, by, bw, bh = Bs["crop"]
fc = (f"[0:v]crop={tw}:{th}:{tx}:{ty},scale={PW}:{PH},setsar=1,fps=30,setpts=PTS-STARTPTS,split[ta][tb];"
      f"[ta]trim=0:{A},setpts=PTS-STARTPTS,tpad=start_mode=clone:start_duration={I0}:stop_mode=clone:stop_duration={SW + B + 0.5}[top];"
      f"[tb]trim=0:{A},setpts=PTS-STARTPTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:3,eq=brightness=-0.4,tpad=start_mode=clone:start_duration={I0}:stop_mode=clone:stop_duration={SW + B + 0.5}[bg];"
      f"[1:v]crop={bw}:{bh}:{bx}:{by},scale={PW}:{PH},setsar=1,fps=30,setpts=PTS-STARTPTS,trim=0:{B},setpts=PTS-STARTPTS,tpad=start_mode=clone:start_duration={I0 + A + SW}:stop_mode=clone:stop_duration=0.5[bot];"
      f"[bg][top]overlay=0:{TY}[v0];[v0][bot]overlay=0:{BY}[v1];[v1][2:v]overlay=0:0[v2];"
      f"[v2][3:v]overlay=0:{BY}:enable='lt(t,{I0 + A})'[v3];[v3][3:v]overlay=0:{TY}:enable='gte(t,{I0 + A})'[v4];"
      f"[v4][3:v]overlay=0:{TY}:enable='lt(t,{I0})'[v5]")
last = "v5"; idx = 4
tapT = (W // 2 - 130, TY + PH // 2 - 130); tapB = (W // 2 - 130, BY + PH // 2 - 130)
for k in range(3):
    a = 0.05 + k * 0.17; b = a + 0.17
    fc += f";[{last}][{idx + k}:v]overlay={tapT[0]}:{tapT[1]}:enable='between(t,{a:.2f},{b:.2f})'[t{k}]"; last = f"t{k}"
    a2 = I0 + A + 0.55 + k * 0.17; b2 = a2 + 0.17
    fc += f";[{last}][{idx + k}:v]overlay={tapB[0]}:{tapB[1]}:enable='between(t,{a2:.2f},{b2:.2f})'[u{k}]"; last = f"u{k}"
fc += f";[{last}][7:v]overlay=0:{BY - 145}:enable='between(t,{I0 + A - 0.1},{I0 + A + SW + 0.6})'[sw]"; last = "sw"
for i in range(len(cms)):
    k = i // 2; a, b = k * seg, (k + 1) * seg; yy = CY + (i % 2) * 215
    fc += f";[{last}][{8 + i}:v]overlay=0:{yy}:enable='between(t,{a:.2f},{b:.2f})'[c{i}]"; last = f"c{i}"
fc += f";[{last}]trim=0:{TOT},format=yuv420p[vout]"
fc += (f";[0:a]atrim=0:{A},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={A - 0.8}:d=0.8,adelay={int(I0 * 1000)}|{int(I0 * 1000)}[aa];"
       f"[1:a]atrim=0:{B},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={B - 1.2}:d=1.2,adelay={int((I0 + A + SW) * 1000)}|{int((I0 + A + SW) * 1000)}[ab];"
       f"[aa][ab]amix=inputs=2:duration=longest:normalize=0,atrim=0:{TOT},loudnorm=I=-14:TP=-1.5[aout]")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", str(TOT), O + "/full.mp4"])
print("ok", O + "/full.mp4", round(TOT, 2))
