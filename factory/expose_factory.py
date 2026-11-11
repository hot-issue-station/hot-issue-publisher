"""쇼츠 스타일 A 「예능 폭로형」 공장 (제작 표준 v2, 11/11) — template:"expose"
사용법: python3 expose_factory.py 기획.json [결과폴더]
템플릿 "shorts_template": 58-N(기본, 정확히 58.0초: [0~3 훅][3~5 반전][5~25 폭로1][25~45 폭로2][45~53 브랜딩][53~58 아웃트로])
  / 40-N(40.0초: [0~3 훅][3~35 본문 body][35~40 아웃트로]) · 1080x1920 · 30fps · 48kHz · 현장음 loudnorm
  narration:[{at(영상 전체 초), file(Veda 내레이션, 없으면 text 를 자막으로), text}]
기획(JSON) 예: docs/제작표준_v2_사용법.md, samples/expose_anwon_test.json
  clips:[{file,in,out,role:"hook|twist|expose1|expose2|brand", layout:"fit|crop", x_center,
          zooms:[{at,x,y,scale,hold}], bleeps:[{at,dur}], sfx:[{at,name|file,volume}], captions:[{at,dur,text,style,pos,color}],
          audio_lead(초, 기본 0.5 — 첫 클립 0), volume, credit}]
  source_line, series_name, title, outro:{ask,next,banner,frame:{file,t}}, thumb:{quote,hook,tag,frame:{file,t}},
  clean_ranges:[[a,b],...](본편 구간), forbidden_ranges:[[a,b],...](쓰면 안 되는 구간), banned_words, test_label
모든 시각(at)은 그 클립 시작부터의 초. 재사용: shorts_factory._clip_geom 배치(fit/crop), v2.1 J컷(audio_lead)·효과음 자막·출처 줄.
"""
import json, os, sys, subprocess, math
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v2_fx as fx
import check_standard as cs

STD = fx.STD   # standard_v2.json
FPS = STD["shorts"]["fps"]; SR = STD["shorts"]["audio_hz"]
TOL = STD["shorts"]["tolerance_sec"]   # 템플릿별 길이·구간은 standard_v2.json shorts_templates(58-N / 40-N), check_standard.tconf
CZ = STD["style_A"]["crash_zoom"]; LEAD = STD["style_A"]["audio_lead_sec"]

def ffprobe_wh(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", f], capture_output=True, text=True).stdout
    return tuple(int(x) for x in r.strip().split(",")[:2])

def ffprobe_dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout
    try: return float(r.strip())
    except ValueError: return 0.0

def grab(file, t):
    """원본 한 장(BGR)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", file, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)

class Reader:
    """원본 구간을 30fps BGR 프레임으로 차례로 읽는다(모자라면 마지막 장 반복)."""
    def __init__(self, file, t0, dur):
        self.w, self.h = ffprobe_wh(file); self.n = round(dur * FPS); self.last = None
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{max(0, t0):.3f}", "-i", file, "-t", f"{dur + 0.2:.3f}", "-an",
                                   "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    def read(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3: self.last = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
        return self.last
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass

# ---------------- 프레임 효과 ----------------
def zoom_at(img, x, y, s):
    """(x,y) 비율 지점을 가운데 쪽으로 s배 확대(크롭 후 원래 크기)."""
    if s <= 1.001: return img
    h, w = img.shape[:2]; cw, ch = w / s, h / s
    cx = min(max(x * w, cw / 2), w - cw / 2); cy = min(max(y * h, ch / 2), h - ch / 2)
    M = np.float32([[s, 0, -(cx - cw / 2) * s], [0, s, -(cy - ch / 2) * s]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR)

def crash_zoom_state(zooms, t):
    """크래시 줌: at 에서 0.15초 만에 scale 까지 급확대 → hold 초 유지 → 0.08초 만에 원래대로. (x,y 는 0.15초 동안 가운데→얼굴로)."""
    for z in zooms:
        a = z["at"]; ramp = z.get("ramp", CZ["ramp_sec"]); hold = z.get("hold", CZ["hold_sec"]); s = z.get("scale", CZ["scale"])
        if a <= t < a + ramp + hold + 0.08:
            u = min(1, (t - a) / ramp) if t < a + ramp + hold else max(0, 1 - (t - a - ramp - hold) / 0.08)
            e = 1 - (1 - u) ** 3
            return 1 + (s - 1) * e, 0.5 + (z["x"] - 0.5) * e, 0.5 + (z["y"] - 0.5) * e
    return 1.0, 0.5, 0.5

def rotate_shake(img, deg, scale=1.0, dx=0, dy=0):
    h, w = img.shape[:2]; M = cv2.getRotationMatrix2D((w / 2, h / 2), deg, scale); M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

class Layout:
    """원본 → 세로 캔버스. fit = 원본 가로를 가운데 통째로 + 위아래 흐린 '멈춘' 배경(클립 첫 장) / crop = 세로로 꽉 차게(x_center).
    (shorts_factory._clip_geom 과 같은 배치 규칙)"""
    def __init__(self, W, H, mode, sw, sh, x_center=0.5, first=None):
        self.W, self.H, self.mode = W, H, mode; self.sw, self.sh = sw, sh
        self.fh = round(W * sh / sw / 2) * 2; self.y0 = (H - self.fh) // 2
        if mode == "crop":
            xc = x_center / sw if x_center > 1 else x_center
            self.sw2 = round(sw * H / sh); self.cx = int(max(0, min(self.sw2 - W, xc * self.sw2 - W / 2)))
        self.bg = None
        if mode != "crop" and first is not None: self.bg = self.blur_bg(first)
    def blur_bg(self, img):
        s = max(self.W / img.shape[1], self.H / img.shape[0]); r = cv2.resize(img, (int(img.shape[1] * s) + 1, int(img.shape[0] * s) + 1))
        y0 = (r.shape[0] - self.H) // 2; x0 = (r.shape[1] - self.W) // 2; r = r[y0:y0 + self.H, x0:x0 + self.W]
        small = cv2.resize(r, (self.W // 8, self.H // 8)); small = cv2.GaussianBlur(small, (0, 0), 6)
        return (cv2.resize(small, (self.W, self.H)) * 0.62).astype(np.uint8)
    def place(self, img):
        if self.mode == "crop":
            r = cv2.resize(img, (self.sw2, self.H), interpolation=cv2.INTER_AREA); return np.ascontiguousarray(r[:, self.cx:self.cx + self.W])
        out = self.bg.copy(); out[self.y0:self.y0 + self.fh] = cv2.resize(img, (self.W, self.fh), interpolation=cv2.INTER_AREA); return out

# ---------------- 얹기(overlay) ----------------
class Ov:
    """RGBA 그림을 t0~t1 동안 (x,y)에. pop=커지며 등장 초, fade=사라짐 초, slide=(dx,dy,초) 들어오기."""
    def __init__(self, im, x, y, t0, t1, pop=0.0, fade=0.12, slide=None, fadein=0.0):
        a = np.array(im.convert("RGBA")); self.rgb = a[:, :, 2::-1].astype(np.float32); self.al = a[:, :, 3:4].astype(np.float32) / 255
        self.x, self.y, self.t0, self.t1, self.pop, self.fade, self.slide, self.fadein = int(x), int(y), t0, t1, pop, fade, slide, fadein
        self.h, self.w = a.shape[:2]
    def draw(self, fr, t):
        if not (self.t0 <= t < self.t1): return
        rgb, al, x, y = self.rgb, self.al, self.x, self.y
        u = t - self.t0; k = 1.0
        if self.fadein: k *= min(1, u / self.fadein)
        if self.fade and t > self.t1 - self.fade: k *= max(0, (self.t1 - t) / self.fade)
        if self.slide:
            dx, dy, d = self.slide; e = 1 - (1 - min(1, u / d)) ** 3; x += int(dx * (1 - e)); y += int(dy * (1 - e))
        if self.pop and u < self.pop:
            s = 1.35 - 0.35 * (1 - (1 - u / self.pop) ** 2)
            nw, nh = max(1, int(self.w * s)), max(1, int(self.h * s))
            rgb = cv2.resize(rgb, (nw, nh)); al = cv2.resize(al, (nw, nh))[:, :, None]; x -= (nw - self.w) // 2; y -= (nh - self.h) // 2
        blend(fr, rgb, al * k, x, y)

def blend(fr, rgb, al, x, y):
    H, W = fr.shape[:2]; h, w = rgb.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1: return
    sr = rgb[y0 - y:y1 - y, x0 - x:x1 - x]; sa = al[y0 - y:y1 - y, x0 - x:x1 - x]
    roi = fr[y0:y1, x0:x1].astype(np.float32); fr[y0:y1, x0:x1] = (sr * sa + roi * (1 - sa)).astype(np.uint8)

def caption_ov(c, W, H, t_base, layout_y=None):
    """자막 하나 → Ov. 위치: situation 위쪽 / big 가운데 / sfx pos / bracket 은 영상 바로 아래(원본 자막 안 가리게) 또는 pos=[x,y](얼굴 옆, ② 안원잘부 강조 배치)."""
    st = c.get("style", "bracket"); im = fx.caption_img(c["text"], st, W, tuple(c["color"]) if c.get("color") else None)
    if c.get("pos"): x = int(c["pos"][0] * W - im.width / 2); y = int(c["pos"][1] * H - im.height / 2)
    elif st == "situation": x, y = (W - im.width) // 2, int(H * 0.215)
    elif st == "big": x, y = (W - im.width) // 2, (H - im.height) // 2
    elif st == "sfx": x, y = int(W * 0.62 - im.width / 2), int(H * 0.30)
    else: x, y = (W - im.width) // 2, (layout_y if layout_y else int(H * 0.70))
    x = max(10, min(W - im.width - 10, x)); y = max(10, min(H - im.height - 10, y))
    t0 = t_base + c["at"]; return Ov(im, x, y, t0, t0 + c.get("dur", 1.8), pop=0.14 if st in ("big", "sfx", "bracket") else 0, slide=(0, -30, 0.18) if st == "situation" else None)

# ---------------- 소리 ----------------
def build_audio(events, total, out, bleeps=(), extra=(), narr=(), loudnorm=True):
    """events: [(file, src_in, src_dur, place_at, volume, fade_in, fade_out)] 원음 조각 → 섞고, bleeps 구간 원음을 줄이고 1kHz 삐-, extra: [(file, at, volume)] 효과음.
    마지막에 정확히 total 초로 자르고 채운다."""
    inp, fl, labs = [], [], []
    for i, (f, si, sd, at, vol, fi, fo) in enumerate(events):
        inp += ["-ss", f"{max(0, si):.3f}", "-t", f"{sd:.3f}", "-i", f]
        fl.append(f"[{i}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,volume={vol},"
                  f"afade=t=in:d={fi:.3f},afade=t=out:st={max(0, sd - fo):.3f}:d={fo:.3f},adelay={int(at * 1000)}:all=1[e{i}]"); labs.append(f"[e{i}]")
    n = len(events)
    fl.append("".join(labs) + f"amix=inputs={n}:normalize=0:duration=longest[raw]" if n > 1 else f"{labs[0]}anull[raw]")
    cur = "raw"
    if narr:   # 내레이션 나오는 동안 원음 덕킹(standard_v2 narration.duck_db)
        G = 10 ** (STD["narration"]["duck_db"] / 20); m = "0"
        for f, a, ln, vol in narr: m = f"max({m},clip(min((t-{a - 0.25:.3f})/0.25,({a + ln + 0.4:.3f}-t)/0.4),0,1))"
        fl.append(f"[{cur}]volume='1-{1 - G:.4f}*{m}':eval=frame[dk]"); cur = "dk"
    for j, (a, d) in enumerate(bleeps):   # 원음 줄이기
        fl.append(f"[{cur}]volume=0.04:enable='between(t,{a:.3f},{a + d:.3f})'[bd{j}]"); cur = f"bd{j}"
    mix = [f"[{cur}]"]; k = n
    for j, (a, d) in enumerate(bleeps):
        inp += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", f"sine=frequency={STD['style_A']['bleep_hz']}:sample_rate={SR}"]
        fl.append(f"[{k}:a]aformat=sample_fmts=fltp:channel_layouts=stereo,volume=0.32,afade=t=in:d=0.01,afade=t=out:st={max(0, d - 0.02):.3f}:d=0.02,adelay={int(a * 1000)}:all=1[bp{j}]")
        mix.append(f"[bp{j}]"); k += 1
    for j, (f, a, ln, vol) in enumerate(narr):
        inp += ["-i", f]
        fl.append(f"[{k}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,volume={vol},adelay={int(a * 1000)}:all=1[nr{j}]"); mix.append(f"[nr{j}]"); k += 1
    for j, (f, a, vol) in enumerate(extra):
        inp += ["-i", f]
        fl.append(f"[{k}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,volume={vol},adelay={int(a * 1000)}:all=1[sx{j}]"); mix.append(f"[sx{j}]"); k += 1
    L_ = STD["loudnorm"]; ln_ = f"loudnorm=I={L_['I']}:TP={L_['TP']}:LRA={L_['LRA']},aresample={SR}," if loudnorm else ""   # 현장음 loudnorm
    fl.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=longest,{ln_}apad=whole_dur={total:.4f},atrim=0:{total:.4f},alimiter=limit=0.95[aout]"
              if len(mix) > 1 else f"{mix[0]}{ln_}apad=whole_dur={total:.4f},atrim=0:{total:.4f}[aout]")
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inp, "-filter_complex", ";".join(fl), "-map", "[aout]", "-c:a", "pcm_s16le", "-ar", str(SR), out], capture_output=True, text=True)
    if r.returncode: sys.exit("소리 만들기 오류:\n" + r.stderr[-1500:])

def open_writer(out_noaudio, W, H):
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out_noaudio], stdin=subprocess.PIPE)

def mux(v, a, out, total):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                        "-t", f"{total:.3f}", "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode: sys.exit("합치기 오류:\n" + r.stderr[-1500:])

def outro_render(write, W, H, t0, dur, frame_bgr, cfg, extra_ovs=()):
    """아웃트로(dur초): 가운데 엔딩 컷(천천히 1.0→1.04) + 왼쪽 구독🔔 + 오른쪽 좋아요👍(0.3초 간격 팝) + 아래 편성 배너(아래에서 올라옴, 숨쉬듯 깜빡임)."""
    bg, cut, sub, like, ban, tops = fx.outro_layers(W, H, frame_bgr, cfg)
    cy = int(H * 0.42) - cut.height // 2
    ovs = [Ov(sub, int(W * 0.06), cy + cut.height + int(H * 0.03), t0 + 0.25, t0 + dur + 1, pop=0.18, fade=0),
           Ov(like, W - like.width - int(W * 0.06), cy + cut.height + int(H * 0.03), t0 + 0.55, t0 + dur + 1, pop=0.18, fade=0)]
    yb = H - ban.height - int(H * 0.06)
    ty = int(H * 0.06)
    for k, im in enumerate(tops): ovs.append(Ov(im, (W - im.width) // 2, ty, t0 + 0.1 * k, t0 + dur + 1, fade=0, fadein=0.2)); ty += im.height + 10
    cut_a = np.array(cut); n = round(dur * FPS)
    for i in range(n):
        t = t0 + i / FPS; u = i / max(1, n - 1); fr = bg.copy()
        s = 1.0 + 0.04 * u; cw, ch = int(cut.width * s), int(cut.height * s)
        c = cv2.resize(cut_a, (cw, ch)); blend(fr, c[:, :, 2::-1].astype(np.float32), c[:, :, 3:4].astype(np.float32) / 255, (W - cw) // 2, cy - (ch - cut.height) // 2)
        for o in ovs: o.draw(fr, t)
        e = 1 - (1 - min(1, (t - t0) / 0.35)) ** 3; pulse = 0.85 + 0.15 * (0.5 + 0.5 * math.sin((t - t0) * 2 * math.pi * 1.2))   # 배너 모션
        ba = np.array(ban); blend(fr, ba[:, :, 2::-1].astype(np.float32), ba[:, :, 3:4].astype(np.float32) / 255 * pulse, (W - ban.width) // 2, int(yb + (1 - e) * 220))
        for o in extra_ovs: o.draw(fr, t)
        write(fr)
    return n

# ---------------- 스타일 A ----------------
def render_expose(spec, outdir, total=None, suffix=""):
    """템플릿 길이(standard_v2.json shorts_templates) 영상 하나 렌더. total 을 따로 주면 폭로 1·2를 비례로 늘림(check_standard.stretch_clips)."""
    base = spec.get("_base", os.getcwd()); W, H = STD["shorts"]["size"]
    T = cs.tconf(spec); total = total or T["total_sec"]
    name = spec["out"] + suffix; os.makedirs(outdir, exist_ok=True); tmp = os.path.join(outdir, "_tmp_" + name); os.makedirs(tmp, exist_ok=True)
    for c in spec["clips"]:
        if not os.path.isabs(c["file"]): c["file"] = os.path.join(base, c["file"])
    clips = cs.stretch_clips(spec, total)
    body = sum(round((c["out"] - c["in"]) * FPS) for c in clips) / FPS
    END = total - body
    # 위 고정 줄(시리즈·제목) + 출처 줄 + 시험 표시
    fixed = []
    if spec.get("title"):
        im = fx.text_img(spec["title"], 66, W - 80, base=fx.WH, hi=fx.Y); fixed.append(Ov(im, (W - im.width) // 2, 150, 0, body, fade=0))
    if spec.get("series_name"):
        im = fx.text_img(spec["series_name"], 36, W - 80, base=fx.GR, stroke=3, font=fx.FB); fixed.append(Ov(im, (W - im.width) // 2, 92, 0, body, fade=0))
    if spec.get("test_label"):
        im = fx.text_img(spec["test_label"], 34, W, base=fx.WH, stroke=0, font=fx.FB, box=(200, 0, 0, 220), shadow=False); fixed.append(Ov(im, 20, 20, 0, total + 1, fade=0))
    ovs = list(fixed); aud, bleeps, extra, narr = [], [], [], []
    # 내레이션(58-N·40-N, Veda): 영상 전체 시각 기준 [{at, file?, text}] — 파일이 있으면 소리(원음 덕킹), 없으면 narr 자막
    for n_ in spec.get("narration", []) if T["narration"] else []:
        f_ = n_.get("file"); f_ = (f_ if not f_ or os.path.isabs(f_) else os.path.join(base, f_))
        if f_ and os.path.exists(f_): narr.append((f_, n_["at"], ffprobe_dur(f_), n_.get("volume", 1.0)))
        if n_.get("text") and (not (f_ and os.path.exists(f_)) or spec.get("narration_subs", True)):
            im = fx.caption_img(n_["text"], "narr", W); d_ = n_.get("sec") or round(0.8 + len(n_["text"]) * 0.14, 2)
            ovs.append(Ov(im, (W - im.width) // 2, int(H * 0.80), n_["at"], n_["at"] + d_, fade=0.15, fadein=0.12))
    if spec.get("narration") and not T["narration"]: print("⚠️ 이 템플릿은 내레이션 없는 판 — narration 무시")
    t = 0.0
    vpath = os.path.join(tmp, "v.mp4"); wr = open_writer(vpath, W, H)
    def write(fr): wr.stdin.write(fr.tobytes())
    brand_done = False
    for ci, c in enumerate(clips):
        n = round((c["out"] - c["in"]) * FPS); d = n / FPS
        sw, sh = ffprobe_wh(c["file"]); mode = c.get("layout", spec.get("layout", STD["style_A"]["layout_default"]))
        first = grab(c["file"], c["in"]); L = Layout(W, H, mode, sw, sh, c.get("x_center", spec.get("x_center", 0.5)), first)
        cap_y = (L.y0 + L.fh + 24) if mode != "crop" else int(H * 0.70)
        # 출처(오른쪽 아래 작게, ① 언더독 자료15) — 클립마다 credit 있으면 그것
        cr = c.get("credit") or spec.get("source_line", "")
        if cr:
            im = fx.text_img(cr, 28, W - 60, base=fx.GR, hi=fx.GR, stroke=2, font=fx.FM, shadow=False); ovs.append(Ov(im, W - im.width - 16, H - im.height - 150, t, t + d, fade=0))
        for cap in c.get("captions", []): ovs.append(caption_ov(cap, W, H, t, cap_y))
        if c.get("role") == "brand" and spec.get("brand") and not brand_done:   # 시리즈 브랜딩 띠(브랜딩 구간 내내)
            bdur = sum(round((x["out"] - x["in"]) * FPS) for x in clips if x.get("role") == "brand") / FPS
            b = spec["brand"]; bt = fx.text_img(b.get("title", ""), 64, W - 100, base=fx.Y, hi=fx.WH, box=(150, 80, 230, 235), stroke=0, font=fx.FK, shadow=False)
            bs = fx.text_img(b.get("sub", ""), 36, W - 100, base=fx.WH, stroke=3, font=fx.FB) if b.get("sub") else None
            ovs.append(Ov(bt, (W - bt.width) // 2, int(H * 0.215), t, t + bdur, slide=(-W, 0, 0.3), fade=0))
            if bs: ovs.append(Ov(bs, (W - bs.width) // 2, int(H * 0.215) + bt.height + 8, t + 0.2, t + bdur, slide=(W, 0, 0.3), fade=0))
            brand_done = True
        for b in c.get("bleeps", []): bleeps.append((t + b["at"], b.get("dur", 0.5)))
        for s in c.get("sfx", []): extra.append((fx.sfx_path(s, base), t + s["at"], s.get("volume", 0.9)))
        lead = c.get("audio_lead", 0.0 if ci == 0 else LEAD)                  # 오디오 오버랩(J컷 = ① 오디오 브리지): 다음 장면 소리 먼저
        aud.append((c["file"], c["in"] - lead, d + lead, t - lead, c.get("volume", 1.0), 0.06 if ci == 0 else lead, 0.5 if ci < len(clips) - 1 else 0.3))
        rd = Reader(c["file"], c["in"], d); zooms = c.get("zooms", [])
        for i in range(n):
            tl = i / FPS; img = rd.read()
            s, zx, zy = crash_zoom_state(zooms, tl); img = zoom_at(img, zx, zy, s)
            fr = L.place(img)
            for o in ovs: o.draw(fr, t + tl)
            write(fr)
        rd.close(); t += d
    # 아웃트로
    oc = dict(spec.get("outro", {})); of = oc.get("frame") or {"file": clips[-1]["file"], "t": clips[-1]["out"] - 0.5}
    ofile = of["file"] if os.path.isabs(of["file"]) else os.path.join(base, of["file"])
    outro_render(write, W, H, t, END, grab(ofile, of["t"]), oc, [o for o in fixed if o.t1 > total])
    wr.stdin.close(); wr.wait()
    if spec.get("bgm"):
        bg = spec["bgm"] if os.path.isabs(spec["bgm"]) else os.path.join(base, spec["bgm"])
        aud.append((bg, 0, END + 0.3, t - 0.3, spec.get("bgm_volume", 0.45), 0.3, 1.2))
    apath = os.path.join(tmp, "a.wav"); build_audio(aud, total, apath, bleeps, extra, narr, T.get("loudnorm", True))
    out = os.path.join(outdir, name + ".mp4"); mux(vpath, apath, out, total)
    return out

def thumbnail(spec, outdir):
    """v2 썸네일(standard_v2.json thumbnail_v2). thumb.zoom=[x,y,배율] 이면 인물 쪽으로 확대."""
    th = spec.get("thumb") or {}; base = spec.get("_base", os.getcwd())
    fr = th.get("frame") or {"file": spec["clips"][0]["file"], "t": spec["clips"][0]["in"] + 1}
    f = fr["file"] if os.path.isabs(fr["file"]) else os.path.join(base, fr["file"])
    bgr = grab(f, fr["t"])
    if th.get("zoom"): bgr = zoom_at(bgr, *th["zoom"])
    img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    if img.width > img.height:   # 세로 썸네일: 인물 쪽으로 자르기
        xc = th.get("x_center", 0.5); cw = int(img.height * 9 / 16); x0 = int(max(0, min(img.width - cw, xc * img.width - cw / 2)))
        img = img.crop((x0, 0, x0 + cw, img.height))
    out = os.path.join(outdir, spec["out"] + "_thumb.png")
    return fx.thumb_v2(img, dict(th, source=th.get("source", spec.get("source_line", "")), test=spec.get("test_label")), tuple(STD["shorts"]["size"]), out)

def main(path, outdir=None):
    """템플릿 길이(58-N 58.0 / 40-N 40.0) 영상 하나(모든 플랫폼 공용) + 썸네일 → check_standard 자동 점검."""
    spec = json.load(open(path, encoding="utf-8")); spec["_base"] = os.path.dirname(os.path.abspath(path))
    outdir = os.path.abspath(outdir or os.path.join(spec["_base"], "out"))
    vids = [render_expose(spec, outdir)]
    th = thumbnail(spec, outdir)
    lines, ok = cs.run(spec, vids)
    print("영상: " + " / ".join(vids) + f"\n썸네일: {th}"); print("\n".join(lines)); print("→ 표준 v2 점검 통과" if ok else "→ ❌ 부터 고치기")
    return vids, th, lines, ok

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
