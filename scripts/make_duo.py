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
I0 = 2.6                   # 손이 천천히 들어와 위를 탭(여유)
A = C["top"]["dur"]        # 위 재생 길이
SW = 1.4                   # 전환(멈춤 + "이제 ○○ 노래를 들어볼까?" + 아래 탭)
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
last = "v5"
fc += f";[{last}][7:v]overlay=0:{BY - 145}:enable='between(t,{I0 + A - 0.1},{I0 + A + SW + 0.6})'[sw]"; last = "sw"
# 시그니처 손(omegacut/hand.png): 위 탭 → 미나미 시작 / 위 탭 → 멈춤 / 아래로 내려와 탭 → 리브 시작
import numpy as np, math
HAND = Image.open("/home/claude/hot-issue-publisher/scripts/omegacut/hand.png").convert("RGBA")
HAND = HAND.resize((int(HAND.width * 1.6), int(HAND.height * 1.6)), Image.LANCZOS)
_a = np.array(HAND)[..., 3]; _ys, _xs = np.nonzero(_a > 40); TIPX = int(_xs[_ys == _ys.min()].mean()); TIPY = int(_ys.min())
def ease(q): q = min(1, max(0, q)); return q * q * (3 - 2 * q)
def paste_hand(im, cx, cy, dx, dy, rot, sc, al):
    h = HAND.resize((max(1, int(HAND.width * sc)), max(1, int(HAND.height * sc))), Image.LANCZOS)
    if rot: h = h.rotate(rot, expand=True, resample=Image.BICUBIC)
    if al < 1: h.putalpha(h.getchannel("A").point(lambda v: int(v * max(0, al))))
    tx = int(TIPX * sc) + (h.width - int(HAND.width * sc)) // 2; ty = int(TIPY * sc) + (h.height - int(HAND.height * sc)) // 2
    im.alpha_composite(h, (int(cx + dx - tx), int(cy + dy - ty)))
def ripple(d, t, t0, cx, cy):
    if t < t0 or t > t0 + 0.45: return
    q = (t - t0) / 0.45; rr = int(40 + 160 * q); d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(255, 255, 255, int(220 * (1 - q))), width=8)
    if q < 0.5: d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(255, 255, 255, int(200 * (1 - 2 * q))))
TX, TYc = W // 2, TY + PH // 2; BX, BYc = W // 2, BY + PH // 2
tA = I0 - 0.4; tB = I0 + A; tC = I0 + A + SW - 0.3
def hand_frame(t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for tt, (cx, cy) in ((tA, (TX, TYc)), (tB, (TX, TYc)), (tC, (BX, BYc))): ripple(d, t, tt, cx, cy)
    press = any(tt <= t < tt + 0.12 for tt in (tA, tB, tC)); dy, sc = (8, 0.9) if press else (0, 1)
    if t < tA - 1.7: pass
    elif t < tA - 0.5:   # 천천히 들어와서
        q = ease((t - (tA - 1.7)) / 1.2); paste_hand(im, TX, TYc, int(260 * (1 - q)), int(320 * (1 - q)), -15 * (1 - q), 1, min(1, (t - (tA - 1.7)) / 0.4))
    elif t < tA:          # 잠깐 멈칫(살짝 들었다가)
        q = (t - (tA - 0.5)) / 0.5; paste_hand(im, TX, TYc, 0, int(-14 * math.sin(math.pi * q)), 0, 1, 1)
    elif t < tA + 0.45: paste_hand(im, TX, TYc, 0, dy, 0, sc, 1)
    elif t < tA + 0.95: q = ease((t - tA - 0.45) / 0.5); paste_hand(im, TX, TYc, int(120 * q), int(160 * q), -10 * q, 1, 1 - q)
    elif t < tB - 0.5: pass
    elif t < tB: q = ease((t - (tB - 0.5)) / 0.45); paste_hand(im, TX, TYc, int(200 * (1 - q)), int(240 * (1 - q)), -15 * (1 - q), 1, min(1, (t - (tB - 0.5)) / 0.2))
    elif t < tB + 0.2: paste_hand(im, TX, TYc, 0, dy, 0, sc, 1)
    elif t < tC - 0.05: q = ease((t - tB - 0.2) / (tC - 0.05 - tB - 0.2)); paste_hand(im, TX, TYc + (BYc - TYc) * q, 0, 0, 0, 1, 1)
    elif t < tC + 0.25: paste_hand(im, BX, BYc, 0, dy, 0, sc, 1)
    elif t < tC + 0.55: q = ease((t - tC - 0.25) / 0.3); paste_hand(im, BX, BYc, int(120 * q), int(160 * q), -10 * q, 1, 1 - q)
    return im
HD = O + "/hand"; os.makedirs(HD, exist_ok=True)
segs = [(max(0, tA - 1.8), tA + 1.0), (tB - 0.6, tC + 0.6)]; hidx = []
for j, (s0, s1) in enumerate(segs):
    for f in os.listdir(HD):
        if f.startswith(f"h{j}_"): os.remove(f"{HD}/{f}")
    n = int(round((s1 - s0) * 30))
    for k in range(n): hand_frame(s0 + k / 30).save(f"{HD}/h{j}_{k:04d}.png")
    hidx.append(len(inputs) // 2)  # placeholder
for i in range(len(cms)):
    k = i // 2; a, b = k * seg, (k + 1) * seg; yy = CY + (i % 2) * 215
    fc += f";[{last}][{8 + i}:v]overlay=0:{yy}:enable='between(t,{a:.2f},{b:.2f})'[c{i}]"; last = f"c{i}"
base_n = 8 + len(cms)
for j, (s0, s1) in enumerate(segs):
    inputs += ["-framerate", "30", "-i", f"{HD}/h{j}_%04d.png"]
    fc += f";[{base_n + j}:v]format=rgba,setpts=PTS-STARTPTS+{s0}/TB[hh{j}];[{last}][hh{j}]overlay=0:0:eof_action=pass[hv{j}]"; last = f"hv{j}"
fc += f";[{last}]trim=0:{TOT},format=yuv420p[vout]"
fc += (f";[0:a]atrim=0:{A},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={A - 0.8}:d=0.8,adelay={int(I0 * 1000)}|{int(I0 * 1000)}[aa];"
       f"[1:a]atrim=0:{B},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={B - 1.2}:d=1.2,adelay={int((I0 + A + SW) * 1000)}|{int((I0 + A + SW) * 1000)}[ab];"
       f"[aa][ab]amix=inputs=2:duration=longest:normalize=0,atrim=0:{TOT},loudnorm=I=-14:TP=-1.5[aout]")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", str(TOT), O + "/full.mp4"])
print("ok", O + "/full.mp4", round(TOT, 2))
