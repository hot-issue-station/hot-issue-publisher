"""덕심저장소 쇼츠 공장 v1
사용법: python factory.py 기획.json
기획 파일(JSON) 하나만 쓰면 아래가 자동으로 나온다.
  - 쇼츠 영상(유튜브·인스타·틱톡·X·페이스북 공용, 1080x1920, 48kHz)
  - 썸네일(11/10 대표 확정 표준)
  - 다섯 곳 게시 문구 파일
  - 5줄 점검표 자동 확인 결과
틀(template): "rank"(순위표가 하나씩 등장) / "cards"(문장 카드가 차례로 등장)
             / "clips"(원본 영상 하이라이트: 원본 구간 + 원본 소리, layout fit|crop. 11/11 추가, docs/shorts_options.md)
python shorts_factory.py 기획.json [결과폴더]   (결과폴더 생략 시 기획 파일 옆 out/)
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

ORIG_SUB_NOTE = "화면 속 자막은 원본 영상 편집 자막입니다"
CLIP_MIN, CLIP_MAX = 8.0, 16.0   # 원본 클립 한 개 길이 권장(점검표)

def _ff(cmd): subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *cmd], check=True)

def _clip_geom(c, spec, sw, sh):
    """클립 배치: fit(원본 가로를 가운데 통째로 + 흐린 배경) / crop(세로로 잘라 꽉 차게, x_center 0~1 또는 원본 픽셀)."""
    lay = c.get("layout", spec.get("layout", "fit"))
    fh = round(W * sh / sw / 2) * 2
    if lay != "crop": return lay, fh, None
    xc = c.get("x_center", spec.get("x_center", 0.5)); xc = xc / sw if xc > 1 else xc
    sw2 = round(sw * H / sh); x = int(max(0, min(sw2 - W, xc * sw2 - W / 2)))
    return lay, fh, (sw2, x)

def _clip_frame(c, spec, t, path):
    """클립과 같은 배치로 한 장(끝 화면 배경·썸네일 사진용)."""
    raw = path + "_raw.jpg"; _ff(["-ss", f"{t:.3f}", "-i", c["file"], "-frames:v", "1", "-q:v", "2", raw])
    im = Image.open(raw).convert("RGB"); lay, fh, cr = _clip_geom(c, spec, *im.size)
    if lay == "crop":
        out = im.resize((cr[0], H), Image.LANCZOS).crop((cr[1], 0, cr[1] + W, H))
    else:
        out = ImageOps.fit(im, (W, H)).filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.72))
        out.paste(im.resize((W, fh), Image.LANCZOS), (0, (H - fh) // 2))
    out.save(path); return out

def render_clips(spec, outdir):
    """원본 영상 하이라이트 틀: 원본 구간 여러 개(원본 소리) + 위 채널·제목 + 첫 3초 질문 + 아래 출처·원본 자막 안내 → 끝 화면.
    끝 화면·썸네일·게시 문구·점검표는 rank·cards 와 같은 함수를 쓴다."""
    clips = spec["clips"]; tmp = os.path.join(outdir, "_tmp_" + spec["out"]); os.makedirs(tmp, exist_ok=True)
    END = float(spec.get("end_sec", 3.5)); crop = spec.get("layout", "fit") == "crop"
    T = sum(c["out"] - c["in"] for c in clips); dur = T + END
    tb = spec.get("top_bar") or {"channel": spec.get("series", ""), "title": spec.get("title", "")}
    hook = spec.get("hook") or spec.get("question", "")
    src_line = spec.get("source_line") or (spec.get("source") or [""])[0] or ("출처: " + clips[0].get("credit", "") if clips[0].get("credit") else "")
    note = ORIG_SUB_NOTE if spec.get("original_sub_note") is True else (spec.get("original_sub_note") or "")
    spec.setdefault("source", [s for s in (src_line, note) if s])          # 점검표·끝 화면용
    def png(L, name): p = os.path.join(tmp, name); L.save(p); return p
    # 위: 채널 + 제목(내내). crop 은 영상 위에 바로 얹으니 위·아래를 어둡게
    top = layer(); d = ImageDraw.Draw(top)
    if crop:
        for y in range(560): d.line([(0, y), (W, y)], fill=(10, 8, 30, int(200 * (1 - y / 560) ** 1.2)))
        for y in range(1300, H): d.line([(0, y), (W, y)], fill=(10, 8, 30, int(150 * ((y - 1300) / 620) ** 1.5)))
    if tb.get("channel"): ct(d, 150, tb["channel"], F(FM, 42), GR, 3)
    if tb.get("title"):
        fo = F(FB, 70)
        while d.textlength(tb["title"], font=fo) > 1000 and fo.size > 44: fo = F(FB, fo.size - 4)
        ct(d, 215, tb["title"], fo, WH, 4)
    q = layer(); d = ImageDraw.Draw(q)
    if hook:
        fo = F(FB, 64)
        while d.textlength(hook, font=fo) > 940 and fo.size > 40: fo = F(FB, fo.size - 4)
        w = d.textlength(hook, font=fo); qy = 440 if crop else 400
        d.rounded_rectangle([(W - w) / 2 - 36, qy, (W + w) / 2 + 36, qy + fo.size + 36], radius=50, fill=NAVY + (210,))
        ct(d, qy + 10, hook, fo, Y)
    p_top, p_q = png(top, "top.png"), png(q, "q.png")
    # 클립마다: 배치 + 아래 출처(클립 credit 이 다르면 그 클립 출처) + 메모 한 줄
    inp, fl = [], []; dims = {}
    for i, c in enumerate(clips):
        if c["file"] not in dims:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", c["file"]], capture_output=True, text=True).stdout
            dims[c["file"]] = tuple(int(x) for x in r.strip().split(",")[:2])
        lay, fh, cr = _clip_geom(c, spec, *dims[c["file"]])
        foot = layer(); d = ImageDraw.Draw(foot); fy = 310 if lay == "crop" else 1400   # crop: 원본 자막(아래쪽)을 가리지 않게 제목 밑으로
        line1 = ("출처: " + c["credit"]) if c.get("credit") and len({x.get("credit") for x in clips}) > 1 else src_line
        for k, line in enumerate([s for s in (line1, note) if s][:2]):
            fo = F(FM, 34 if k == 0 else 28)
            while d.textlength(line, font=fo) > 1010 and fo.size > 22: fo = F(FM, fo.size - 2)
            ct(d, fy + k * 58, line, fo, PU if k == 0 else GR, 3)
        if c.get("note"): ct(d, 1180 if lay == "crop" else fy - 80, c["note"], F(FB, 40), WH, 4)
        pf = png(foot, f"foot{i}.png"); d_ = c["out"] - c["in"]
        inp += ["-ss", f"{c['in']:.3f}", "-t", f"{d_:.3f}", "-i", c["file"]]
        inp += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d_:.3f}", "-i", pf]
        vi, fi = 2 * i, 2 * i + 1
        if lay == "crop":
            fl.append(f"[{vi}:v]fps={FPS},setpts=PTS-STARTPTS,scale={cr[0]}:{H},crop={W}:{H}:{cr[1]}:0,setsar=1[b{i}]")
        else:
            fl += [f"[{vi}:v]fps={FPS},setpts=PTS-STARTPTS,split[a{i}][x{i}]",
                   f"[a{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=20:2,eq=brightness=-0.15[g{i}]",
                   f"[x{i}]scale={W}:{fh}[f{i}]", f"[g{i}][f{i}]overlay=0:{(H - fh) // 2},setsar=1[b{i}]"]
        fl += [f"[b{i}][{fi}:v]overlay=0:0:shortest=1,format=yuv420p,setsar=1[v{i}]",
               f"[{vi}:a]aresample=48000,aformat=channel_layouts=stereo,volume={c.get('volume', 1.0)},afade=t=in:d=0.08,afade=t=out:st={d_ - 0.12:.3f}:d=0.12[s{i}]"]
    # 끝 화면 배경: 마지막 클립 끝 1초 전 장면(같은 배치) + 공장 끝 화면
    lc = clips[-1]; ef = spec.get("end_frame", lc["out"] - 1.0)
    endbg = _clip_frame(lc, spec, ef, os.path.join(tmp, "end_bg.jpg")).convert("RGBA")
    p_end = png(Image.alpha_composite(endbg, end_card(spec.get("end", {}))).convert("RGB"), "end.png")
    fc = clips[0]; tf = spec.get("thumb_frame", fc["in"] + 2.0)
    tp = os.path.join(tmp, "thumb_photo.jpg"); _clip_frame(fc, spec, tf, tp)
    if spec.get("thumb") is not None and not spec["thumb"].get("photo"): spec["thumb"]["photo"] = tp
    if not spec.get("bg"): spec["bg"] = tp
    n = len(clips); k = 2 * n
    inp += ["-loop", "1", "-framerate", str(FPS), "-t", f"{T:.3f}", "-i", p_top, "-loop", "1", "-framerate", str(FPS), "-t", "3", "-i", p_q,
            "-loop", "1", "-framerate", str(FPS), "-t", f"{END + 0.3:.3f}", "-i", p_end, "-stream_loop", "-1", "-i", spec["bgm"]]
    qf = spec.get("hook_sec", 3.0)
    fl += ["".join(f"[v{i}][s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca0]",
           f"[cv][{k}:v]overlay=0:0:shortest=1[c1]",
           f"[{k+1}:v]format=rgba,trim=0:{qf:.2f},fade=t=out:st={max(0.1, qf - 0.4):.2f}:d=0.4:alpha=1[qq]", "[c1][qq]overlay=0:0:eof_action=pass,format=yuv420p,setsar=1[body]",
           f"[{k+2}:v]fps={FPS},format=yuv420p,setsar=1[ev]",   # 끝 화면은 0.3초 디졸브(검은 프레임 없이)
           f"[{k+3}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{T + END:.3f},asetpts=PTS-STARTPTS,asplit[bg1][bg2]",
           f"[bg2]atrim=0:{END:.3f},asetpts=PTS-STARTPTS,volume={spec.get('bgm_volume', 0.5)},afade=t=in:d=0.3,afade=t=out:st={max(0, END - 1.2):.3f}:d=1.2[ea]"]
    under = float(spec.get("bgm_under", 0))   # 클립 밑에 배경음악 깔기(기본 0 = 끝 화면에만)
    if under > 0:
        fl += [f"[bg1]atrim=0:{T:.3f},asetpts=PTS-STARTPTS,volume={under}[ub]", "[ca0][ub]amix=inputs=2:normalize=0:duration=first[ca]"]
    else: fl += ["[bg1]anullsink", "[ca0]anull[ca]"]
    fl += [f"[body]settb=AVTB,fps={FPS}[bd];[ev]settb=AVTB,fps={FPS}[ev2];[bd][ev2]xfade=transition=fade:duration=0.3:offset={T - 0.3:.3f},format=yuv420p[vo]",
           "[ca][ea]concat=n=2:v=0:a=1[ao]"]
    out = os.path.join(outdir, spec["out"] + ".mp4")
    _ff([*inp, "-filter_complex", ";".join(fl), "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", out])
    return out, dur, T

def render(spec, outdir):
    if spec.get("template") == "clips": return render_clips(spec, outdir)
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
    if spec.get("template") == "clips":   # 원본 영상 하이라이트 틀 추가 확인
        lens = [c["out"] - c["in"] for c in spec.get("clips", [])]
        bad = [f"{i + 1}번 {l:.1f}초" for i, l in enumerate(lens) if not (CLIP_MIN <= l <= CLIP_MAX)]
        items.append((f"원본 클립 각 {CLIP_MIN:.0f}~{CLIP_MAX:.0f}초 (" + (", ".join(bad) if bad else " · ".join(f"{l:.1f}" for l in lens) + "초") + ")", not bad))
        has_src = bool(spec.get("source_line") or (spec.get("source") or [""])[0]) or all(c.get("credit") for c in spec.get("clips", []))
        items.append(("출처 표시(화면 아래 출처 줄" + (" + 원본 자막 안내" if spec.get("original_sub_note") else "") + ")", has_src))
    lines = [("✅ " if ok else "❌ 빠짐: ") + name for name, ok in items]
    return lines, all(ok for _, ok in items)

if __name__ == "__main__":
    path = sys.argv[1]; spec = json.load(open(path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(path))
    for k in ("bg", "bgm"):
        if spec.get(k): spec[k] = os.path.join(base, spec[k]) if not os.path.isabs(spec[k]) else spec[k]
    if spec.get("thumb", {}).get("photo"): spec["thumb"]["photo"] = os.path.join(base, spec["thumb"]["photo"])
    for c in spec.get("cards", []):
        if c.get("photo"): c["photo"] = os.path.join(base, c["photo"])
    for c in spec.get("clips", []) if spec.get("template") == "clips" else []:
        if not os.path.isabs(c["file"]): c["file"] = os.path.join(base, c["file"])
    outdir = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(base, "out"); os.makedirs(outdir, exist_ok=True)
    v, dur, t_end = render(spec, outdir)
    th = thumbnail(spec, outdir) if spec.get("thumb") else None
    pt = post_text(spec, outdir) if spec.get("post") else None
    lines, ok = checklist(spec, v, dur, t_end)
    print(f"영상: {v} ({dur:.1f}초)\n썸네일: {th}\n게시 문구: {pt}")
    print("\n".join(lines)); print("→ 올려도 됨" if ok else "→ 빠진 것부터 채우기")
