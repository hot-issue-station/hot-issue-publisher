"""제작 표준 v2 공용 연출 도구 (11/11) — expose_factory(쇼츠 A) · stagemix pulse58(쇼츠 B) · longform 몰아보기가 같이 쓴다.
우선순위: ① 언더독스토리 2편 분석(롱폼 기준서 v1·v2.1 기능) ② 안원잘부 분석 ③ 제미나이 기획. docs/제작표준_v2_제미나이프로토콜.md
들어 있는 것
  - 자막 그림: bracket(괄호 드립) / situation([대괄호] 상황 박스) / big(가운데 크게) / sfx(의성어 팝) / narr(내레이션 대신 자막)
  - 반응 말풍선(동네 형): 일러스트 원형 아이콘 + 말풍선 (실존 인물 얼굴 없음)
  - 소리: 까마귀(직접 합성, assets/sfx_crow.wav) · 삐-(1kHz) · 박자 추정(ffmpeg로 소리 → numpy 온셋)
  - 아웃트로 5초 판(가운데 엔딩 컷 + 왼쪽 구독🔔 + 오른쪽 좋아요👍 + 아래 편성 배너)
  - v2 썸네일(① 언더독스토리 제목 방식 + ② 안원잘부 대비 매력, 표는 docs)
  - 금지어 검사
"""
import os, re, math, wave, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FD = "/usr/share/fonts/opentype/noto/"
if os.name == "nt": FD = os.path.join(HERE, "fonts") + os.sep
FB, FM, FK = FD + "NotoSansCJK-Bold.ttc", FD + "NotoSansCJK-Medium.ttc", FD + "NotoSansCJK-Black.ttc"
if not os.path.exists(FK): FK = FB
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
def F(p, s): return ImageFont.truetype(p, int(s), index=1)

WH = (255, 255, 255); Y = (255, 222, 40); BK = (0, 0, 0); RD = (255, 48, 64); NAVY = (14, 12, 40); GR = (200, 204, 220)
STD = json.load(open(os.path.join(HERE, "standard_v2.json"), encoding="utf-8"))   # 표준 수치는 모두 여기서
BANNER = STD["schedule"]["banner"]
BANNED = STD["banned_words"]   # 대표 11/11 20:17 — 제목·썸네일·큰 글씨·우리 자막 금지. 늘리려면 standard_v2.json 또는 spec "banned_words"
CROW = os.path.join(HERE, "assets", "sfx_crow.wav")

# ---------------- 글자 ----------------
NOSTART = set(")）]」』.,!?~…·:")
def _wrap(d, text, fo, maxw):
    """글자 단위 줄바꿈. 닫는 괄호·문장부호가 줄 맨 앞에 혼자 오지 않게 앞 줄로 붙인다. 빈칸이 있으면 빈칸에서 끊기."""
    out = []
    for para in str(text).split("\n"):
        line = ""
        for ch in para:
            if d.textlength(line + ch, font=fo) > maxw and line and ch not in NOSTART:
                sp = line.rfind(" ")
                if sp > len(line) * 0.4: out.append(line[:sp]); line = line[sp + 1:] + ch
                else: out.append(line); line = ch
            else: line += ch
        out.append(line)
    return out

def _paren_runs(line, base, hi):
    """괄호 () 안(괄호 포함)은 hi 색, 나머지는 base 색."""
    runs, buf, depth = [], "", 0
    for ch in line:
        if ch in "(（" and depth == 0:
            if buf: runs.append((buf, base)); buf = ""
            depth = 1; buf = ch; continue
        if ch in ")）" and depth == 1:
            buf += ch; runs.append((buf, hi)); buf = ""; depth = 0; continue
        buf += ch
    if buf: runs.append((buf, hi if depth else base))
    return runs

def _emph_runs(line, base, hi, emph):
    """emph(강조할 말 목록)에 든 부분만 hi 색, 나머지는 base 색 (대표 11/11 21:22 썸네일 강조)."""
    runs, i = [], 0
    while i < len(line):
        hit = None
        for e in emph:
            j = line.find(e, i)
            if j >= 0 and (hit is None or j < hit[0]): hit = (j, e)
        if not hit: runs.append((line[i:], base)); break
        if hit[0] > i: runs.append((line[i:hit[0]], base))
        runs.append((hit[1], hi)); i = hit[0] + len(hit[1])
    return runs

def text_img(text, size, maxw, base=WH, hi=Y, stroke=None, font=None, box=None, pad=(26, 14), radius=14, shadow=True, emph=None):
    """여러 줄 글 → 꽉 맞는 RGBA. 괄호 부분은 hi 색. emph=[말,...] 이면 그 말만 hi 색. box=(r,g,b,a) 이면 뒤에 상자."""
    font = font or FK; d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while size > 26:
        fo = F(font, size); lines = _wrap(d0, text, fo, maxw)
        if len(lines) <= 3: break
        size -= 4
    size = int(size); sw = int(stroke if stroke is not None else max(4, size // 9)); pad = (int(pad[0]), int(pad[1]))
    lh = int(size * 1.28); widths = [d0.textlength(l, font=fo) for l in lines]
    tw, th = int(max(widths)) + 2 * sw + 2 * pad[0], lh * len(lines) + 2 * sw + 2 * pad[1]
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if box: d.rounded_rectangle([0, 0, tw - 1, th - 1], radius=radius, fill=box)
    if shadow and not box:
        sh = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
        for i, l in enumerate(lines):
            ds.text(((tw - widths[i]) / 2 + 4, pad[1] + sw + lh * i + 6), l, font=fo, fill=(0, 0, 0, 170), stroke_width=sw, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6))); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = (tw - widths[i]) / 2; y = pad[1] + sw + lh * i
        for s, col in (_emph_runs(l, base, hi, emph) if emph else _paren_runs(l, base, hi)):
            d.text((x, y), s, font=fo, fill=col, stroke_width=sw, stroke_fill=BK); x += d.textlength(s, font=fo)
    return im

def caption_img(text, style, W, color=None):
    """우리 자막 모양.
    bracket  : 괄호 드립 — 투박한 굵은 고딕(Black), 흰 글씨 + 검은 두꺼운 테두리, 괄호 부분 노랑 (③ 제미나이 · ① 자료06 괄호 반응)
    situation: [대괄호] 상황 자막 — 화면 위쪽 검은 반투명 상자 + 노란 테두리 (③)
    big      : 가운데 크게(강조) (② 안원잘부 강조 자막 크게 · ① 자료06 중앙 크게)
    sfx      : 효과음·리액션 의성어 — 노랑, 살짝 기울임 (② 효과음 자막 · v2.1 sfx)
    narr     : 내레이션 파일이 없을 때 대신 쓰는 자막 — 아래 띠 (① 자료06 존댓말 내레이션)
    color    : 인물 색(② 안원잘부: 인물별 자막 색) — 바탕 글자색을 바꿈"""
    k = W / 1080
    if style == "situation":
        im = text_img(text, 50 * k, W - 160 * k, base=color or WH, hi=Y, stroke=0, font=FB, box=(10, 8, 24, 215), pad=(int(30 * k), int(16 * k)), shadow=False)
        d = ImageDraw.Draw(im); d.rounded_rectangle([1, 1, im.width - 2, im.height - 2], radius=14, outline=Y + (255,), width=max(3, int(4 * k)))
        return im
    if style == "big": return text_img(text, 112 * k, W - 120 * k, base=color or WH)
    if style == "sfx":
        im = text_img(text, 92 * k, W - 200 * k, base=color or Y, hi=WH)
        return im.rotate(7, resample=Image.BICUBIC, expand=True)
    if style == "narr":
        return text_img(text, 46 * k, W - 160 * k, base=color or WH, hi=Y, stroke=0, font=FB, box=(0, 0, 0, 150), pad=(int(28 * k), int(12 * k)), shadow=False)
    return text_img(text, 70 * k, W - 110 * k, base=color or WH)   # bracket(기본)

def check_banned(texts, extra=()):
    words = list(BANNED) + list(extra); hits = []
    for where, t in texts:
        for w in words:
            if w and w in str(t): hits.append(f"{where}: 「{w}」")
    return hits

# ---------------- 동네 형 반응 말풍선 (몰아보기) ----------------
def hyung_icon(size=150):
    """일러스트 원형 아이콘: 모자 쓴 동글한 캐릭터(실존 인물 아님). 직접 그림."""
    s = size * 4; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=(255, 205, 64, 255), outline=(30, 20, 40, 255), width=s // 28)
    d.ellipse([s * .2, s * .26, s * .8, s * .86], fill=(255, 226, 196, 255), outline=(30, 20, 40, 255), width=s // 40)   # 얼굴
    d.chord([s * .16, s * .08, s * .84, s * .62], 180, 360, fill=(60, 70, 160, 255), outline=(30, 20, 40, 255), width=s // 40)  # 모자
    d.rectangle([s * .16, s * .33, s * .92, s * .38], fill=(60, 70, 160, 255))                    # 챙
    for ex in (.38, .62): d.ellipse([s * ex - s * .04, s * .52, s * ex + s * .04, s * .6], fill=(30, 20, 40, 255))
    d.arc([s * .38, s * .58, s * .62, s * .76], 10, 170, fill=(30, 20, 40, 255), width=s // 36)   # 웃는 입
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).ellipse([0, 0, s - 1, s - 1], fill=255); im.putalpha(Image.composite(im.getchannel("A"), m, m))
    return im.resize((size, size), Image.LANCZOS)

def react_img(text, name="동네 형", W=1920):
    """오른쪽 아래: 원형 아이콘 + 흰 말풍선(이름 + 한두 줄). 실존 인물 얼굴 대신 일러스트(① 관찰자 시점 · ③ MC 콘셉트)."""
    k = W / 1920 * 1.35; ic = hyung_icon(int(130 * k)); fo = F(FB, 38 * k); fn = F(FB, 28 * k)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1))); lines = _wrap(d0, text, fo, 560 * k)[:2]
    bw = int(max(d0.textlength(l, font=fo) for l in lines) + 60 * k); bw = max(bw, int(200 * k))
    bh = int(56 * k + 50 * k * len(lines)); tail = int(26 * k)
    im = Image.new("RGBA", (bw + tail + ic.width + 10, max(bh, ic.height) + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    by = im.height - bh - 5
    d.rounded_rectangle([0, by, bw, by + bh], radius=int(26 * k), fill=(255, 255, 255, 240), outline=(30, 20, 40, 255), width=3)
    d.polygon([(bw - 2, by + bh * .55), (bw + tail, by + bh * .75), (bw - 2, by + bh * .85)], fill=(255, 255, 255, 240))
    d.text((24 * k, by + 10 * k), "▶ " + name, font=fn, fill=(150, 80, 230))
    for i, l in enumerate(lines): d.text((24 * k, by + 46 * k + 50 * k * i), l, font=fo, fill=(30, 20, 60))
    im.alpha_composite(ic, (bw + tail + 4, im.height - ic.height - 2))
    return im

# ---------------- 소리 ----------------
def make_crow(path=CROW, sr=48000):
    """까마귀 '까악' 직접 합성(저작권 없음): 거친 노이즈를 대역 통과 + 900→520Hz 하강 스윕 톱니파, 두 번 '까악 까악'."""
    if os.path.exists(path): return path
    rng = np.random.default_rng(7); out = np.zeros(int(sr * 1.15))
    for start, dur, f0, f1 in ((0.0, 0.42, 950, 560), (0.55, 0.5, 900, 500)):
        n = int(sr * dur); t = np.arange(n) / sr
        f = f0 + (f1 - f0) * (t / dur) ** 0.7
        ph = 2 * np.pi * np.cumsum(f) / sr
        saw = sum(np.sin(k * ph) / k for k in range(1, 9))                       # 거친 배음
        noise = rng.standard_normal(n)
        # 노이즈를 주파수 근처로 끌어오기(간단한 공진: 노이즈 × 사인)
        rasp = noise * np.sin(ph * 2.0) * 0.6
        env = np.minimum(1, t / 0.025) * np.exp(-((t / dur) ** 2) * 2.2) * (1 + 0.35 * np.sin(2 * np.pi * 38 * t))  # 빠른 떨림
        sig = (0.55 * saw + rasp) * env
        sig = np.tanh(sig * 2.2)                                                 # 찢어지는 질감
        s0 = int(sr * start); out[s0:s0 + n] += sig
    out = out / (np.abs(out).max() + 1e-9) * 0.8
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype("<i2").tobytes())
    return path

SFX = {"crow": CROW}   # 이름 → 파일. spec sfx {"name":"crow"} 또는 {"file":"경로"}

def sfx_path(item, base=HERE):
    if item.get("file"): return item["file"] if os.path.isabs(item["file"]) else os.path.join(base, item["file"])
    nm = item.get("name", "crow")
    if nm == "crow": return make_crow()
    p = SFX.get(nm) or os.path.join(HERE, "assets", f"sfx_{nm}.wav")
    return p

def estimate_beat(path, start, dur, lo=70, hi=180):
    """박자 추정(bpm 이 없을 때): ffmpeg로 소리를 꺼내 numpy 스펙트럼 변화량(온셋) → 자기상관으로 bpm, 온셋 합이 큰 쪽으로 첫 박 위치.
    돌려주기: (bpm, 첫 박 초[0~한 박 안], 신뢰도 0~1). 실제 박과 어긋날 수 있으니 bpm 을 아는 곡은 spec 에 bpm 을 쓴다."""
    sr = 11025
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
    if len(x) < sr * 4: return 120.0, 0.0, 0.0
    hop, nf = 256, 1024; n = (len(x) - nf) // hop
    win = np.hanning(nf); frames = np.stack([x[i * hop:i * hop + nf] * win for i in range(n)])
    mag = np.log1p(np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(1); flux = flux - np.convolve(flux, np.ones(16) / 16, "same"); flux = np.maximum(flux, 0)
    fps = sr / hop; ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(int(fps * 60 / hi), int(fps * 60 / lo) + 1)
    best = lags[np.argmax(ac[lags])]; bpm = 60 * fps / best
    conf = float(ac[best] / (ac[0] + 1e-9))
    period = best; scores = [flux[p::period].sum() if p < len(flux) else 0 for p in range(period)]
    phase = int(np.argmax(scores)) / fps
    return round(float(bpm), 2), round(phase, 3), round(conf, 3)

# ---------------- 아웃트로 5초 판 ----------------
def emoji_img(ch, size):
    try:
        fo = ImageFont.truetype(EMOJI, 109); im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=fo, embedded_color=True)
        return im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    except Exception:
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse([0, 0, size - 1, size - 1], fill=Y); return im

def button_img(label, emoji, col, W, txt=WH):
    k = W / 1080; fo = F(FK, 46 * k); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    e = emoji_img(emoji, int(62 * k)); tw = d0.textlength(label, font=fo)
    w, h = int(tw + e.width + 70 * k), int(100 * k)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=col + (255,), outline=WH + (255,), width=4)
    im.alpha_composite(e, (int(24 * k), (h - e.height) // 2))
    d.text((int(30 * k) + e.width, (h - 46 * k) / 2 - 10 * k), label, font=fo, fill=txt)
    return im

def banner_img(text, W):
    k = W / 1080; fo = F(FK, 40 * k); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = text.split("/") if d0.textlength(text, font=fo) > W - 80 * k else [text]
    lines = [l.strip() for l in lines]; lh = int(56 * k)
    w = int(W - 60 * k); h = int(40 * k + lh * len(lines))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(24 * k), fill=(150, 80, 230, 245), outline=Y + (255,), width=4)
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=fo); d.text(((w - tw) / 2, 16 * k + lh * i), l, font=fo, fill=WH)
    return im

def outro_layers(W, H, end_frame_bgr, cfg):
    """아웃트로 판 재료: (배경 BGR, 엔딩 컷 RGBA, 구독, 좋아요, 배너, 위 글) — 움직임은 각 공장이 시간에 맞춰 얹는다.
    cfg: {"ask": 댓글 질문(① 자료07), "next": 다음 편 한 줄, "banner": 편성 문구}"""
    import cv2
    bg = cv2.resize(end_frame_bgr, (W, H) if end_frame_bgr.shape[1] / end_frame_bgr.shape[0] < W / H else (int(H * end_frame_bgr.shape[1] / end_frame_bgr.shape[0]), H))
    x0 = (bg.shape[1] - W) // 2; y0 = (bg.shape[0] - H) // 2; bg = bg[max(0, y0):max(0, y0) + H, max(0, x0):max(0, x0) + W]
    bg = cv2.resize(bg, (W, H)); bg = cv2.GaussianBlur(bg, (0, 0), 30); bg = (bg * 0.42).astype(np.uint8)
    k = W / 1080; cw = int(W * (0.86 if W < H else 0.5)); ch = int(cw * end_frame_bgr.shape[0] / end_frame_bgr.shape[1])
    cut = Image.fromarray(cv2.cvtColor(cv2.resize(end_frame_bgr, (cw, ch), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)).convert("RGBA")
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=int(30 * k), fill=255)
    fr = Image.new("RGBA", (cw + 16, ch + 16), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle([0, 0, cw + 15, ch + 15], radius=int(36 * k), fill=WH + (255,))
    fr.paste(cut, (8, 8), m)
    sub = button_img("구독", "🔔", (230, 30, 40), W); like = button_img("좋아요", "👍", (40, 40, 60), W)
    ban = banner_img(cfg.get("banner", BANNER), W)
    tops = []
    if cfg.get("ask"): tops.append(caption_img(cfg["ask"], "bracket", W))
    if cfg.get("next"): tops.append(caption_img(cfg["next"], "situation", W))
    return bg, fr, sub, like, ban, tops

# ---------------- v2 썸네일 ----------------
def thumb_v2(photo_rgb, cfg, size, out):
    """v2 썸네일(docs 표 근거): 실제 장면 한 장(밝게) + 실제로 한 말 한 줄을 큰따옴표로(① 자료09 제목 “천막 치울 수 있을까요?”)
    + 대비·반전 한 줄(② 이유1 갸루×시골 대비, ① 자료03 '1위보다 놀라운') + 시리즈 꼬리표 + 아래 작은 출처(① 자료15).
    cfg: {"quote": 실제 대사(따옴표 없이), "emph": 대사 안 강조할 말(노랑), "hook": 대비 한 줄, "tag": 시리즈, "source": 출처, "test": 시험 표시}"""
    W, H = size; img = ImageOps.fit(photo_rgb.convert("RGB"), (W, H), Image.LANCZOS, centering=(0.5, 0.4)).convert("RGBA")
    k = min(W, H) / 1080 if W < H else H / 720 * 0.72
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
    for y in range(H):
        a = int(200 * max(0, (y - H * .55) / (H * .45)) ** 1.1) + int(150 * max(0, 1 - y / (H * .22)) ** 1.5)
        o.line([(0, y), (W, y)], fill=(8, 6, 20, min(235, a)))
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
    if cfg.get("tag"):
        t = text_img(cfg["tag"], 40 * k * (1.15 if W > H else 1), W, base=WH, stroke=0, font=FB, box=(230, 30, 40, 240), shadow=False)
        img.alpha_composite(t, (int(30 * k), int(30 * k)))
    em = cfg.get("emph"); em = [em] if isinstance(em, str) else em    # 강조할 말(예: "용인도 서울") → 노랑
    if cfg.get("quote"):
        q = "“" + cfg["quote"] + "”"; qi = text_img(q, (110 if W < H else 92) * k * (1.15 if W > H else 1), W * 0.92, base=WH, hi=Y, emph=em)
        hk = text_img(cfg.get("hook", ""), (78 if W < H else 64) * k * (1.15 if W > H else 1), W * 0.92, base=Y, hi=WH) if cfg.get("hook") else None
    else:   # 실제 대사가 없는 무대 쇼츠: 한 줄(hook)을 크게, 강조 말만 노랑
        qi = text_img(cfg.get("hook", ""), (110 if W < H else 92) * k * (1.15 if W > H else 1), W * 0.92, base=WH, hi=Y, emph=em); hk = None
    yb = H - int(70 * k) - qi.height - (hk.height if hk else 0)
    if hk: img.alpha_composite(hk, ((W - hk.width) // 2, yb)); yb += hk.height
    img.alpha_composite(qi, ((W - qi.width) // 2, yb))
    if cfg.get("source"):
        fo = F(FM, 26 * k * (1.1 if W > H else 1)); d = ImageDraw.Draw(img); tw = d.textlength(cfg["source"], font=fo)
        d.text((W - tw - 20 * k, H - 44 * k * (1.1 if W > H else 1)), cfg["source"], font=fo, fill=GR, stroke_width=2, stroke_fill=BK)
    if cfg.get("test"):
        t = text_img(cfg["test"], 44 * k * (1.15 if W > H else 1), W, base=WH, stroke=0, font=FB, box=(200, 0, 0, 230), shadow=False)
        img.alpha_composite(t, (W - t.width - int(30 * k), int(30 * k)))
    img.convert("RGB").save(out); return out
