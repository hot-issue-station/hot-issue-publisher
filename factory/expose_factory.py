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


def narr_pitch(path):
    """내레이션 한 줄의 목소리 높이(Hz, 중앙값) — 줄마다 다른 목소리로 만들어졌는지 찾는 데 씀."""
    import wave
    w = wave.open(path); sr = w.getframerate(); ch = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)[::ch]; ps = []
    for i in range(0, len(x) - 1024, 512):
        fr = x[i:i + 1024]
        if np.sqrt(np.mean(fr ** 2)) < 500: continue
        fr = fr - fr.mean(); ac = np.correlate(fr, fr, "full")[1023:]; lo, hi = sr // 400, sr // 80; k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.3 * ac[0]: ps.append(sr / k)
    return float(np.median(ps)) if ps else 0.0

def narr_even(path, tmp):
    """줄마다 따로 만든 내레이션의 크기를 -16 LUFS로 맞춘 사본(wav)."""
    out = os.path.join(tmp, "narr_" + os.path.basename(path).rsplit(".", 1)[0] + ".wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "48000", "-ac", "1", out], check=True)
    return out

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

def focus_state(focus, t):
    """멤버 부각(대표 11/12 02:13): at 부터 0.6초 동안 천천히 (x,y) 쪽으로 scale 배 확대 → dur 끝 0.3초 동안 원래대로."""
    for f in focus:
        a = f["at"]; d = f.get("dur", 2.0); s = f.get("scale", 1.6)
        if a <= t < a + d:
            u = min(1, (t - a) / 0.6, max(0, (a + d - t) / 0.3)); e = u * u * (3 - 2 * u)
            return 1 + (s - 1) * e, 0.5 + (f["x"] - 0.5) * e, 0.5 + (f["y"] - 0.5) * e
    return 1.0, 0.5, 0.5

def transition(kind, A, B, u):
    """장면 넘김(대표 11/12 02:26 '영상과 영상이 잘 넘어가게'). A=앞 장면, B=새 장면, u=0→1.
    dissolve 겹침 / slide 밀어내기(다른 날·다른 방송) / whip 빠른 휙(흐림) / zoom 확대하며 통과(감정 고조) / flash 흰 번쩍(반전·발표)."""
    H, W = A.shape[:2]; e = u * u * (3 - 2 * u)
    if kind == "slide" or kind == "whip":
        dx = int(W * e); out = np.empty_like(A); out[:, :W - dx] = A[:, dx:]; out[:, W - dx:] = B[:, :dx]
        if kind == "whip":
            k = int(1 + 60 * math.sin(math.pi * u)); k += (k % 2 == 0)
            if k > 1: out = cv2.blur(out, (k, 1))
        return out
    if kind == "zoom":
        if u < 0.5: return zoom_at(A, 0.5, 0.5, 1 + 0.8 * (u / 0.5) ** 2)
        return zoom_at(B, 0.5, 0.5, 1 + 0.8 * ((1 - u) / 0.5) ** 2)
    if kind == "flash":
        base = A if u < 0.5 else B; w_ = 1 - abs(u - 0.5) * 2
        return cv2.addWeighted(base, 1 - 0.85 * w_, np.full_like(base, 255), 0.85 * w_, 0)
    return cv2.addWeighted(B, u, A, 1 - u, 0)

class Split:
    """한 화면 두 영상(대표 11/12 02:13): 위 = 본 클립, 아래 = split 영상. 둘 다 가로 통째(16:9) + 흐린 배경 + 칸마다 이름표."""
    def __init__(self, W, H, first, gap=14):
        self.W, self.H = W, H; self.fh = round(W * 9 / 16 / 2) * 2; self.gap = gap
        self.y_top = H // 2 - self.fh - gap // 2 - 40; self.y_bot = H // 2 + gap // 2 - 40
        self.bg = Layout(W, H, "fit", 16, 9, first=first).bg
    def place(self, a, b):
        out = self.bg.copy()
        out[self.y_top:self.y_top + self.fh] = cv2.resize(a, (self.W, self.fh), interpolation=cv2.INTER_AREA)
        out[self.y_bot:self.y_bot + self.fh] = cv2.resize(b, (self.W, self.fh), interpolation=cv2.INTER_AREA)
        return out

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

def caption_ov(c, W, H, t_base, layout_y=None, video_top=None):
    """자막 하나 → Ov. 위치: situation 위쪽 / big 가운데 / sfx pos / bracket 은 영상 바로 아래(원본 자막 안 가리게) 또는 pos=[x,y](얼굴 옆, ② 안원잘부 강조 배치)."""
    st = c.get("style", "bracket"); im = fx.caption_img(c["text"], st, W, tuple(c["color"]) if c.get("color") else None, c.get("emph"), tuple(c["hi"]) if c.get("hi") else None)
    if c.get("pos"): x = int(c["pos"][0] * W - im.width / 2); y = int(c["pos"][1] * H - im.height / 2)
    elif st == "situation": x, y = (W - im.width) // 2, int(H * 0.215)
    elif st == "big": x, y = (W - im.width) // 2, (H - im.height) // 2
    elif st == "upper": x, y = (W - im.width) // 2, int((video_top or H * 0.36) - im.height - 18)
    elif st == "lower": x, y = (W - im.width) // 2, (layout_y if layout_y else int(H * 0.70))
    elif st == "sfx": x, y = int(W * 0.62 - im.width / 2), int(H * 0.30)
    else: x, y = (W - im.width) // 2, (layout_y if layout_y else int(H * 0.70))
    x = max(10, min(W - im.width - 10, x)); y = max(10, min(H - im.height - 10, y))
    t0 = t_base + c["at"]; return Ov(im, x, y, t0, t0 + c.get("dur", 1.8), pop=0.14 if st in ("big", "sfx", "bracket", "upper", "lower") else 0, slide=(0, -30, 0.18) if st == "situation" else None)

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
        tk = spec.get("title_emph"); im = fx.text_img(spec["title"], 66, W - 80, base=fx.WH, hi=fx.OR if tk else fx.Y, emph=tk); fixed.append(Ov(im, (W - im.width) // 2, 150, 0, body, fade=0))
    if spec.get("series_name"):
        if spec.get("series_box"):   # 대표 11/12: 시리즈 이름도 색으로 눈에 띄게(보라 상자 + 흰 글씨)
            im = fx.text_img(spec["series_name"], 34, W - 120, base=fx.WH, hi=fx.Y, stroke=0, font=fx.FB, box=fx.PU + (240,), pad=(22, 8), shadow=False); fixed.append(Ov(im, (W - im.width) // 2, 78, 0, body, fade=0))
        else:
            im = fx.text_img(spec["series_name"], 36, W - 80, base=fx.GR, stroke=3, font=fx.FB); fixed.append(Ov(im, (W - im.width) // 2, 92, 0, body, fade=0))
    if spec.get("test_label"):
        im = fx.text_img(spec["test_label"], 34, W, base=fx.WH, stroke=0, font=fx.FB, box=(200, 0, 0, 220), shadow=False); fixed.append(Ov(im, 20, 20, 0, total + 1, fade=0))
    ovs = list(fixed); aud, bleeps, extra, narr = [], [], [], []
    # 내레이션(58-N·40-N, Veda): 영상 전체 시각 기준 [{at, file?, text}] — 파일이 있으면 소리(원음 덕킹), 없으면 narr 자막
    for n_ in spec.get("narration", []) if T["narration"] else []:
        f_ = n_.get("file"); f_ = (f_ if not f_ or os.path.isabs(f_) else os.path.join(base, f_))
        if f_ and os.path.exists(f_):
            f_ = narr_even(f_, tmp)   # 대표 11/12 13:44 "앞뒤 목소리가 다르게 느껴진다" → 줄마다 크기를 같게 맞춤
            narr.append((f_, n_["at"], ffprobe_dur(f_), n_.get("volume", 1.0)))
        if n_.get("text") and (not (f_ and os.path.exists(f_)) or spec.get("narration_subs", True)):
            im = fx.caption_img(n_["text"], "narr", W); d_ = n_.get("sec") or round(0.8 + len(n_["text"]) * 0.14, 2)
            ovs.append(Ov(im, (W - im.width) // 2, int(H * 0.80), n_["at"], n_["at"] + d_, fade=0.15, fadein=0.12))
    if spec.get("narration") and not T["narration"]: print("⚠️ 이 템플릿은 내레이션 없는 판 — narration 무시")
    t = 0.0
    vpath = os.path.join(tmp, "v.mp4"); wr = open_writer(vpath, W, H)
    def write(fr): wr.stdin.write(fr.tobytes())
    brand_done = False; prev = None
    for ci, c in enumerate(clips):
        n = round((c["out"] - c["in"]) * FPS); d = n / FPS
        sw, sh = ffprobe_wh(c["file"]); mode = c.get("layout", spec.get("layout", STD["style_A"]["layout_default"]))
        first = grab(c["file"], c["in"]); L = Layout(W, H, mode, sw, sh, c.get("x_center", spec.get("x_center", 0.5)), first)
        cap_y = (L.y0 + L.fh + 24) if mode != "crop" else int(H * 0.70)
        # 출처(오른쪽 아래 작게, ① 언더독 자료15) — 클립마다 credit 있으면 그것
        cr = c.get("credit") or spec.get("source_line", "")
        if cr:
            im = fx.text_img(cr, 28, W - 60, base=fx.GR, hi=fx.GR, stroke=2, font=fx.FM, shadow=False); ovs.append(Ov(im, W - im.width - 16, H - im.height - 150, t, t + d, fade=0))
        if c.get("split"):   # 두 영상 칸: 자막은 위 칸 위 / 아래 칸 아래
            fh_ = round(W * 9 / 16 / 2) * 2; ytop = H // 2 - fh_ - 7 - 40; cap_y = H // 2 + 7 - 40 + fh_ + 20
            for cap in c.get("captions", []): ovs.append(caption_ov(cap, W, H, t, cap_y, ytop))
        else:
            for cap in c.get("captions", []): ovs.append(caption_ov(cap, W, H, t, cap_y, L.y0 if mode != "crop" else None))
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
        nx = clips[ci + 1].get("xfade", 0) if ci + 1 < len(clips) else 0   # 다음 클립과 겹치는 초(겹침 전환)
        rd = Reader(c["file"], c["in"], d + nx); zooms = c.get("zooms", []); focus = c.get("focus", [])
        sp = c.get("split"); SP = rd2 = None
        if sp:
            sf = sp["file"] if os.path.isabs(sp["file"]) else os.path.join(base, sp["file"])
            SP = Split(W, H, first); rd2 = Reader(sf, sp["in"], d + nx)
            for k_, lab in enumerate(sp.get("labels", [])):
                if lab:
                    im = fx.text_img(lab, 38, W - 80, base=fx.WH, hi=fx.Y, stroke=0, font=fx.FB, box=(fx.OR if k_ == 0 else fx.PU) + (235,), pad=(18, 6), shadow=False)
                    yy = (SP.y_top + 14) if k_ == 0 else (SP.y_bot + 14)
                    ovs.append(Ov(im, 20, yy, t, t + d, fade=0.1, slide=(-W // 2, 0, 0.25)))
        for f in focus:
            if f.get("name"):
                im = fx.text_img(f["name"], 46, W - 80, base=fx.WH, hi=fx.Y, stroke=0, font=fx.FB, box=fx.PU + (235,), pad=(22, 8), shadow=False)
                yv = (SP.y_top + SP.fh - im.height - 16) if SP else ((L.y0 + L.fh - im.height - 16) if mode != "crop" else int(H * 0.62))
                ovs.append(Ov(im, int(min(max(f["x"] * W - im.width / 2, 20), W - im.width - 20)), yv, t + f["at"] + 0.3, t + f["at"] + f.get("dur", 2.0) - 0.2, pop=0.14))
        def frame_of(img, img2, tl, zooms=zooms, focus=focus, SP=SP, sp=sp, L=L):
            s_, zx, zy = crash_zoom_state(zooms, tl)
            if s_ <= 1.001: s_, zx, zy = focus_state(focus, tl)
            img = zoom_at(img, zx, zy, s_)
            if SP is not None:
                s2 = sp.get("focus")
                if s2: s3, x3, y3 = focus_state(s2, tl); img2 = zoom_at(img2, x3, y3, s3)
                return SP.place(img, img2)
            return L.place(img)
        X = round(c.get("xfade", 0) * FPS) if prev else 0
        for i in range(n):
            tl = i / FPS; img = rd.read(); img2 = rd2.read() if rd2 else None
            fr = frame_of(img, img2, tl)
            if i < X:   # 겹침 전환: 앞 클립이 계속 재생되며 사라짐
                p_ = prev; pi = p_["rd"].read(); pi2 = p_["rd2"].read() if p_["rd2"] else None
                pf = p_["frame_of"](pi, pi2, p_["d"] + tl); a_ = (i + 1) / (X + 1)
                fr = transition(c.get("xfade_type", "dissolve"), pf, fr, a_)
            for o in ovs: o.draw(fr, t + tl)
            write(fr)
        if prev:
            prev["rd"].close()
            if prev["rd2"]: prev["rd2"].close()
        prev = {"rd": rd, "rd2": rd2, "frame_of": frame_of, "d": d} if nx else None
        if not nx:
            rd.close()
            if rd2: rd2.close()
        t += d
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
    nf = [n.get("file") for n in spec.get("narration", []) if n.get("file")]
    nf = [f if os.path.isabs(f) else os.path.join(spec["_base"], f) for f in nf]; nf = [f for f in nf if os.path.exists(f)]
    if len(nf) >= 2:   # 대표 11/12: 앞뒤 목소리가 다르게 들리면 안 됨 — 줄마다 목소리 높이 비교
        ps = [narr_pitch(f) for f in nf]; lo, hi = min(p for p in ps if p) if any(ps) else 0, max(ps)
        same = lo and hi / lo < 1.18
        lines.append(("✅" if same else "❌") + f" 내레이션 목소리 높이 {', '.join(str(round(p)) for p in ps)}Hz" + ("" if same else " — 줄마다 목소리가 달라요. 모든 줄을 한 번에 같은 목소리로 다시 만들기"))
        ok = ok and bool(same)
    print("영상: " + " / ".join(vids) + f"\n썸네일: {th}"); print("\n".join(lines)); print("→ 표준 v2 점검 통과" if ok else "→ ❌ 부터 고치기")
    return vids, th, lines, ok

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
