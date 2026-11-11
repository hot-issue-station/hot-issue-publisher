"""덕심저장소 쇼츠 공장 v1
사용법: python factory.py 기획.json
기획 파일(JSON) 하나만 쓰면 아래가 자동으로 나온다.
  - 쇼츠 영상(유튜브·인스타·틱톡·X·페이스북 공용, 1080x1920, 48kHz)
  - 썸네일(11/10 대표 확정 표준)
  - 다섯 곳 게시 문구 파일
  - 5줄 점검표 자동 확인 결과
틀(template): "rank"(순위표가 하나씩 등장) / "cards"(문장 카드가 차례로 등장)
끝 화면(구독·좋아요·알림)과 배경음악은 항상 자동으로 들어간다. 빼는 옵션은 없다.
"""
import json, os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/noto/"
if os.name == "nt":  # 데스크톱(윈도우)에서 돌릴 때
    FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + os.sep
FB, FM, FK = FD + "NotoSansCJK-Bold.ttc", FD + "NotoSansCJK-Medium.ttc", FD + "NotoSansCJK-Black.ttc"
if not os.path.exists(FK): FK = FB
def F(p, s): return ImageFont.truetype(p, s, index=1)

Y = (255, 214, 64); WH = (255, 255, 255); GR = (185, 190, 215); PU = (206, 160, 255)
RD = (255, 70, 90); PB = (150, 80, 230); NAVY = (14, 12, 40)

def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def ct(d, y, t, fo, fill=WH, stroke=0):
    w = d.textlength(t, font=fo)
    d.text(((W - w) / 2, y), t, font=fo, fill=fill, stroke_width=stroke, stroke_fill=(10, 6, 30))
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def put(fr, L, a, dx=0, dy=0):
    if a <= 0: return fr
    if a < 1:
        r, g, b, al = L.split(); al = al.point(lambda v: int(v * a)); L = Image.merge("RGBA", (r, g, b, al))
    if dx or dy:
        M2 = layer(); M2.paste(L, (int(dx), int(dy)), L); L = M2
    return Image.alpha_composite(fr, L)
def man(n):
    m, r = divmod(int(n), 10000)
    return f"{m}만 {r:,}" if m and r else (f"{m}만" if m else f"{r:,}")
def wrap(d, text, fo, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            t = (line + " " + word).strip()
            if d.textlength(t, font=fo) <= maxw: line = t
            else: out.append(line); line = word
        out.append(line)
    return out

def background(path, dark=True):
    ph = Image.open(path).convert("RGB")
    base = ImageOps.fit(ph, (W, H), Image.LANCZOS, centering=(0.5, 0.6)).filter(ImageFilter.GaussianBlur(2)).convert("RGBA")
    sh = layer(); sd = ImageDraw.Draw(sh)
    for y in range(H): sd.line([(0, y), (W, y)], fill=NAVY + (175 if 400 < y < 1700 else 215,))
    return Image.alpha_composite(base, sh)

def end_card(cfg):
    L = layer(); d = ImageDraw.Draw(L)
    d.rectangle([0, 0, W, H], fill=NAVY + (220,))
    ct(d, 640, cfg.get("thanks", "오늘도 봐 주셔서 고마워요"), F(FM, 46), GR)
    ct(d, 730, cfg.get("channel", "덕심저장소"), F(FB, 96))
    for j, (lab, col) in enumerate([("구독", (255, 64, 64)), ("좋아요", WH), ("알림 설정", Y)]):
        yy = 930 + j * 150; d.rounded_rectangle([240, yy, 840, yy + 115], radius=58, fill=col + (255,))
        fo = F(FB, 54); w = d.textlength(lab, font=fo)
        d.text(((W - w) / 2, yy + 22), lab, font=fo, fill=WH if col == (255, 64, 64) else (30, 20, 60))
    for k, line in enumerate(cfg.get("lines", [])[:2]):
        ct(d, 1420 + k * 70, line, F(FM, 40), PU if k == 0 else WH)
    return L

def header(spec):
    L = layer(); d = ImageDraw.Draw(L)
    if spec.get("series"): ct(d, 150, spec["series"], F(FM, 40), GR)
    ct(d, 215, spec["title"], F(FB, 74))
    if spec.get("question"): ct(d, 310, spec["question"], F(FB, 58), Y)
    return L

def footer(spec):
    L = layer(); d = ImageDraw.Draw(L)
    for k, line in enumerate(spec.get("source", [])[:2]):
        ct(d, 1690 + k * 60, line, F(FM, 34 if k == 0 else 30), PU if k == 0 else GR)
    return L

def build_rank(spec):
    """순위표: 1위부터 차례로 왼쪽에서 들어오고, 마지막에 주인공 상자가 올라오며 숫자가 올라간다."""
    tl = []  # (시작, 레이어, 효과)
    rows = spec["rows"]; gap = spec.get("row_gap", 1.4)
    for i, (r, g, a, n) in enumerate(rows):
        L = layer(); d = ImageDraw.Draw(L); y = 450 + 150 * i
        d.rounded_rectangle([70, y, 1010, y + 130], radius=26, fill=(255, 255, 255, 34))
        d.text((105, y + 28), str(r), font=F(FB, 64), fill=Y)
        d.text((190, y + 20), g, font=F(FB, 46), fill=WH)
        if a: d.text((190, y + 78), "「" + a + "」", font=F(FM, 32), fill=GR)
        nf = F(FB, 46); unit = spec.get("unit", "")
        txt = (man(n) if isinstance(n, (int, float)) else str(n)) + unit
        w = d.textlength(txt, font=nf); d.text((975 - w, y + 40), txt, font=nf, fill=WH)
        tl.append((1.6 + i * gap, L, "left"))
    t_hi = 1.6 + len(rows) * gap + 0.8
    hi = spec.get("highlight")
    extra = []
    if hi:
        yb = 1310
        dots = layer(); ct(ImageDraw.Draw(dots), 1205, "· · ·", F(FB, 50), GR); tl.append((t_hi - 0.6, dots, "fade"))
        box = layer(); d = ImageDraw.Draw(box)
        d.rounded_rectangle([60, yb, 1020, yb + 330], radius=34, fill=PB + (235,), outline=Y, width=5)
        d.text((105, yb + 30), hi["name"], font=F(FB, 52), fill=WH)
        if hi.get("sub"): d.text((105, yb + 100), hi["sub"], font=F(FM, 34), fill=(240, 225, 255))
        tl.append((t_hi, box, "up"))
        if hi.get("note"):
            nt = layer(); ct(ImageDraw.Draw(nt), yb + 270, hi["note"], F(FM, 34)); tl.append((t_hi + 3.2, nt, "fade"))
        extra.append(("count", t_hi, hi["value"], yb + 150, spec.get("unit", "")))
    t_src = (t_hi + 3.8) if hi else (1.6 + len(rows) * gap + 0.5)
    return tl, extra, t_src

def build_cards(spec):
    """문장 카드: 카드마다 큰 글씨 한 줄 + 작은 설명이 아래에서 올라오고, 다음 카드로 바뀐다."""
    tl = []; t = 1.2; per = spec.get("card_sec", 3.0)
    for c in spec["cards"]:
        L = background(c["photo"]) if c.get("photo") else layer()  # 카드마다 다른 사진(덕심 편지 12장용)
        d = ImageDraw.Draw(L)
        d.rounded_rectangle([70, 560, 1010, 1380], radius=40, fill=(255, 255, 255, 30))
        y = 640
        if c.get("label"): ct(d, y, c["label"], F(FM, 40), Y); y += 80
        for line in wrap(d, c["big"], F(FB, 70), 860): ct(d, y, line, F(FB, 70)); y += 92
        y += 30
        for line in wrap(d, c.get("small", ""), F(FM, 40), 860): ct(d, y, line, F(FM, 40), GR); y += 58
        tl.append((t, L, ("card", t + per)))
        t += per
    return tl, [], t

def render(spec, outdir):
    bg = background(spec["bg"])
    brand = layer(); ct(ImageDraw.Draw(brand), 1800, spec.get("channel", "덕심저장소"), F(FB, 40), GR)
    head = header(spec)
    if spec["template"] == "rank": tl, extra, t_src = build_rank(spec)
    else: tl, extra, t_src = build_cards(spec)
    foot = footer(spec)
    t_end = max(t_src + 3.5, spec.get("min_body_sec", 0))
    dur = spec.get("dur") or (t_end + 3.8)
    t_end = min(t_end, dur - 3.0)  # 끝 화면은 최소 3초
    endL = end_card(spec.get("end", {}))
    NF = F(FB, 92)
    out = os.path.join(outdir, spec["out"] + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-stream_loop", "-1", "-i", spec["bgm"], "-t", f"{dur:.2f}",
           "-af", f"afade=t=out:st={dur-1.5:.2f}:d=1.5", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-b:a", "160k",
           "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(int(dur * FPS)):
        t = k / FPS; fr = put(bg, brand, 1)
        e = ease(t / 0.6); fr = put(fr, head, e, 0, (1 - e) * -40)
        for s, L, fx in tl:
            e = ease((t - s) / 0.5)
            if fx == "left": fr = put(fr, L, e, (1 - e) * -160, 0)
            elif fx == "up": fr = put(fr, L, e, 0, (1 - e) * 120)
            elif fx == "fade": fr = put(fr, L, e)
            elif isinstance(fx, tuple):  # 카드: 들어오고 다음 카드 시작 때 사라짐
                out_e = ease((t - (fx[1] - 0.3)) / 0.3) if fx[1] < t_src else 0
                fr = put(fr, L, e * (1 - out_e), 0, (1 - e) * 100)
        for kind, s, val, y, unit in extra:
            e = ease((t - s) / 0.5)
            if e > 0:
                c = ease((t - (s + 0.4)) / 2.0)
                L = layer(); d = ImageDraw.Draw(L); txt = man(val * c) + unit
                w = d.textlength(txt, font=NF); d.text(((W - w) / 2, y + (1 - e) * 120), txt, font=NF, fill=Y); fr = put(fr, L, e)
        fr = put(fr, foot, ease((t - t_src) / 0.5))
        e = ease((t - t_end) / 0.5); fr = put(fr, endL, e, 0, (1 - e) * 80)
        p.stdin.write(fr.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    return out, dur, t_end

def thumbnail(spec, outdir):
    """11/10 대표 확정 썸네일 표준: 빨간 띠 / 흰 제목 / 노란 질문 / 밝은 사진 / 큰 노란 숫자 / 보라 띠. 글 덩어리 5개, 색 4개."""
    th = spec["thumb"]
    img = ImageOps.fit(Image.open(th.get("photo", spec["bg"])).convert("RGB"), (W, H), Image.LANCZOS, centering=(0.5, 0.62))
    img = ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(1.05)).enhance(1.1).convert("RGBA")
    ov = layer(); o = ImageDraw.Draw(ov)
    for y in range(H):
        a = int(235 * (1 - y / 720) ** 0.8) if y < 720 else (int(245 * ((y - 1300) / 620) ** 0.9) if y > 1300 else 0)
        o.line([(0, y), (W, y)], fill=(16, 10, 40, a))
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
    def pill(y, text, size, col):
        fo = F(FK, size); w = d.textlength(text, font=fo); pad = 50
        d.rounded_rectangle([(W - w) / 2 - pad, y, (W + w) / 2 + pad, y + size + 32], radius=(size + 32) // 2, fill=col)
        ct(d, y + 8, text, fo, WH)
    pill(90, th["tag"], 48, RD)
    def fit(t, size, maxw=1000):
        while d.textlength(t, font=F(FK, size)) > maxw and size > 40: size -= 4
        return F(FK, size)
    ct(d, 200, th["title"], fit(th["title"], 104), WH, 8)
    ct(d, 345, th["question"], fit(th["question"], 92), Y, 8)
    if th.get("small"): ct(d, 1360, th["small"], F(FK, 70), WH, 8)
    ct(d, 1440, th["big"], fit(th["big"], 210), Y, 12)
    pill(1700, th["summary"], 62, PB)
    out = os.path.join(outdir, spec["out"] + "_thumb.png"); img.convert("RGB").save(out)
    return out

def post_text(spec, outdir):
    po = spec["post"]; tags = " ".join("#" + t.lstrip("#") for t in po.get("tags", []))
    txt = f"""[유튜브 쇼츠]
제목: {po['title']}
설명:
{po['desc']}

{tags}
첫 댓글(고정): {po.get('first_comment','')}

[인스타그램·페이스북 릴스 (비즈니스 스위트 예약)]
{po['desc']}
.
{tags}

[틱톡]
{po['title']} {tags}

[X]
{po.get('x', po['title'])}
{tags}
"""
    out = os.path.join(outdir, spec["out"] + "_게시문구.txt")
    open(out, "w", encoding="utf-8").write(txt)
    return out

def checklist(spec, video, dur, t_end):
    """5줄 점검표(실수 기록장). 하나라도 빠지면 '빠짐'으로 표시."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", video], capture_output=True, text=True).stdout
    po = spec.get("post", {})
    items = [
        ("끝 화면(구독·좋아요·알림) 3초 이상", dur - t_end >= 3.0),
        ("배경음악 들어감", "audio" in r),
        ("출처·기준 표시", bool(spec.get("source"))),
        ("숫자 확인 기록(확인한 곳·시각)", bool(spec.get("checked"))),
        ("썸네일·제목·소개글·첫 댓글", all([spec.get("thumb"), po.get("title"), po.get("desc"), po.get("first_comment")])),
    ]
    lines = [("✅ " if ok else "❌ 빠짐: ") + name for name, ok in items]
    return lines, all(ok for _, ok in items)

if __name__ == "__main__":
    path = sys.argv[1]; spec = json.load(open(path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(path))
    for k in ("bg", "bgm"): spec[k] = os.path.join(base, spec[k]) if not os.path.isabs(spec[k]) else spec[k]
    if spec.get("thumb", {}).get("photo"): spec["thumb"]["photo"] = os.path.join(base, spec["thumb"]["photo"])
    for c in spec.get("cards", []):
        if c.get("photo"): c["photo"] = os.path.join(base, c["photo"])
    outdir = os.path.join(base, "out"); os.makedirs(outdir, exist_ok=True)
    v, dur, t_end = render(spec, outdir)
    th = thumbnail(spec, outdir) if spec.get("thumb") else None
    pt = post_text(spec, outdir) if spec.get("post") else None
    lines, ok = checklist(spec, v, dur, t_end)
    print(f"영상: {v} ({dur:.1f}초)\n썸네일: {th}\n게시 문구: {pt}")
    print("\n".join(lines)); print("→ 올려도 됨" if ok else "→ 빠진 것부터 채우기")
