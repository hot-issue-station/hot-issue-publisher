"""덕심저장소 롱폼 공장 v1
사용법: python longform.py 롱폼기획.json
대표 11/8 결정을 기본으로 한다:
  - 카드는 챕터가 바뀔 때만 (2.5초)
  - 그 사이에는 영상이 계속 흐르고 자막으로 잇는다
  - 챕터 사이 '되감기' 전환 (앞 장면 끝 1초를 거꾸로, 빠르게)
  - 시청자 댓글은 영상 위에 하나씩 띄운다
  - 끝 화면(구독·좋아요·알림 + 다음 편 예고) 자동
결과: 롱폼 영상(1920x1080) + 썸네일(1280x720) + 자막 파일(.srt) + 점검표
"""
import json, os, sys, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FD = "/usr/share/fonts/opentype/noto/"
if os.name == "nt": FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + os.sep
FB, FM = FD + "NotoSansCJK-Bold.ttc", FD + "NotoSansCJK-Medium.ttc"
def F(p, s): return ImageFont.truetype(p, s, index=1)
Y = (255, 214, 64); WH = (255, 255, 255); GR = (185, 190, 215); PU = (206, 160, 255); NAVY = (14, 12, 40); PB = (150, 80, 230); RD = (255, 70, 90)
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k"]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("ffmpeg 오류:\n" + r.stderr[-1500:])

def ct(d, y, t, fo, fill=WH, stroke=0):
    w = d.textlength(t, font=fo); d.text(((W - w) / 2, y), t, font=fo, fill=fill, stroke_width=stroke, stroke_fill=(10, 6, 30))

def sub_png(text, path):
    """자막: 화면 아래, 한 줄 18자 안쪽 권장, 반투명 띠 위 흰 글씨."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fo = F(FB, 54)
    lines = text.split("\n"); y0 = H - 90 - 74 * len(lines)
    for i, line in enumerate(lines):
        w = d.textlength(line, font=fo); x = (W - w) / 2; y = y0 + 74 * i
        d.rounded_rectangle([x - 26, y - 6, x + w + 26, y + 70], radius=14, fill=(0, 0, 0, 150))
        d.text((x, y), line, font=fo, fill=WH)
    im.save(path)

def comment_png(c, path, slot):
    """댓글 띄우기: 오른쪽 위에 말풍선 하나 (닉네임 + 한두 줄)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x, y = 1180, 90 + slot * 190; fo = F(FM, 36)
    d.rounded_rectangle([x, y, x + 680, y + 160], radius=26, fill=(255, 255, 255, 235))
    d.text((x + 30, y + 18), "▶ " + c.get("name", "리마인"), font=F(FB, 30), fill=PB)
    d.text((x + 30, y + 66), c["text"][:28], font=fo, fill=(30, 20, 60))
    if len(c["text"]) > 28: d.text((x + 30, y + 110), c["text"][28:56], font=F(FM, 30), fill=(30, 20, 60))
    im.save(path)

def card_png(ch, n, path, series):
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    ct(d, 330, series, F(FM, 44), GR)
    ct(d, 420, f"CHAPTER {n}", F(FB, 56), Y)
    ct(d, 520, ch["title"], F(FB, 96))
    if ch.get("sub"): ct(d, 660, ch["sub"], F(FM, 46), PU)
    im.save(path)

def end_png(cfg, path, series):
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    ct(d, 150, cfg.get("thanks", "끝까지 봐 주셔서 고마워요"), F(FM, 48), GR)
    ct(d, 230, cfg.get("channel", "덕심저장소"), F(FB, 110))
    for j, (lab, col) in enumerate([("구독", (255, 64, 64)), ("좋아요", WH), ("알림 설정", Y)]):
        x = 260 + j * 480; d.rounded_rectangle([x, 450, x + 420, 560], radius=55, fill=col)
        fo = F(FB, 56); w = d.textlength(lab, font=fo); d.text((x + (420 - w) / 2, 466), lab, font=fo, fill=WH if j == 0 else (30, 20, 60))
    if cfg.get("next"): ct(d, 680, "다음 편 · " + cfg["next"], F(FB, 60), Y)
    if cfg.get("next_date"): ct(d, 780, cfg["next_date"], F(FM, 44), WH)
    ct(d, 940, series, F(FM, 36), GR)
    im.save(path)

def thumb_png(th, photo, path):
    """롱폼 썸네일(1280x720): 쇼츠 표준과 같은 색 4개·글 덩어리 5개 규칙."""
    from PIL import ImageOps, ImageEnhance
    TW, TH = 1280, 720
    img = ImageOps.fit(Image.open(photo).convert("RGB"), (TW, TH), Image.LANCZOS)
    img = ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(1.05)).enhance(1.1).convert("RGBA")
    ov = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
    for x in range(TW):
        a = int(235 * (1 - x / 760) ** 0.9) if x < 760 else 0
        o.line([(x, 0), (x, TH)], fill=(16, 10, 40, a))
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img); K = lambda s: F(FB, s); st = dict(stroke_width=6, stroke_fill=(10, 6, 30))
    fo = K(40); w = d.textlength(th["tag"], font=fo); d.rounded_rectangle([50, 50, 50 + w + 60, 120], radius=35, fill=RD); d.text((80, 58), th["tag"], font=fo, fill=WH)
    d.text((50, 160), th["title"], font=K(88), fill=WH, **st)
    d.text((50, 280), th["question"], font=K(72), fill=Y, **st)
    d.text((50, 420), th["big"], font=K(150), fill=Y, stroke_width=10, stroke_fill=(10, 6, 30))
    fo = K(46); w = d.textlength(th["summary"], font=fo); d.rounded_rectangle([50, 620, 50 + w + 60, 690], radius=35, fill=PB); d.text((80, 626), th["summary"], font=fo, fill=WH)
    img.convert("RGB").save(path)

def srt_time(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

def build(spec, base):
    tmp = os.path.join(base, "_tmp"); out = os.path.join(base, "out"); os.makedirs(tmp, exist_ok=True); os.makedirs(out, exist_ok=True)
    series = spec.get("series", "덕심저장소"); parts = []; srt = []; clock = 0.0; card_sec = spec.get("card_sec", 2.5)
    for ci, ch in enumerate(spec["chapters"], 1):
        cp = os.path.join(tmp, f"card{ci}.png"); card_png(ch, ci, cp, series); cv = os.path.join(tmp, f"card{ci}.mp4")
        run(["ffmpeg", "-y", "-loop", "1", "-t", str(card_sec), "-i", cp, "-f", "lavfi", "-t", str(card_sec), "-i", "anullsrc=r=48000:cl=stereo",
             "-vf", f"fade=in:0:12,fade=out:st={card_sec-0.4}:d=0.4", *ENC, "-shortest", cv])
        parts.append(cv); clock += card_sec
        for si, sc in enumerate(ch["scenes"]):
            src = os.path.join(base, sc["file"]) if not os.path.isabs(sc["file"]) else sc["file"]
            a, b = sc["in"], sc["out"]; dur = b - a; inputs = ["-ss", str(a), "-t", str(dur), "-i", src]; ov = []; k = 1
            for j, s in enumerate(sc.get("subs", [])):  # [시작, 끝, "문장"] (장면 안에서의 초)
                p = os.path.join(tmp, f"s{ci}_{si}_{j}.png"); sub_png(s[2], p); inputs += ["-i", p]; ov.append((k, s[0], s[1])); k += 1
                srt.append((clock + s[0], clock + s[1], s[2]))
            for j, c in enumerate(sc.get("comments", [])):  # {"at":초, "sec":4, "name":"", "text":""}
                p = os.path.join(tmp, f"c{ci}_{si}_{j}.png"); comment_png(c, p, j % 3); inputs += ["-i", p]; ov.append((k, c["at"], c["at"] + c.get("sec", 4))); k += 1
            fl = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1[v0]"; last = "v0"
            for n, (idx, s0, s1) in enumerate(ov):
                fl += f";[{last}][{idx}:v]overlay=0:0:enable='between(t,{s0},{s1})'[v{n+1}]"; last = f"v{n+1}"
            vol = sc.get("volume", 1.0)
            fl += f";[0:a]volume={vol},aresample=48000[a0]"
            sv = os.path.join(tmp, f"sc{ci}_{si}.mp4")
            run(["ffmpeg", "-y", *inputs, "-filter_complex", fl, "-map", f"[{last}]", "-map", "[a0]", *ENC, sv])
            parts.append(sv); clock += dur
        if ci < len(spec["chapters"]) and spec.get("rewind", True):  # 되감기 전환
            rv = os.path.join(tmp, f"rw{ci}.mp4")
            run(["ffmpeg", "-y", "-sseof", "-1.2", "-i", parts[-1], "-filter_complex",
                 "[0:v]reverse,setpts=0.4*PTS,eq=saturation=0.3:contrast=1.2,noise=alls=25:allf=t[v];[0:a]areverse,atempo=2.0,atempo=1.25,volume=0.4[a]",
                 "-map", "[v]", "-map", "[a]", *ENC, rv])
            parts.append(rv); clock += 0.48
    ep = os.path.join(tmp, "end.png"); end_png(spec.get("end", {}), ep, series); ev = os.path.join(tmp, "end.mp4"); es = spec.get("end_sec", 8)
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(es), "-i", ep, "-f", "lavfi", "-t", str(es), "-i", "anullsrc=r=48000:cl=stereo", "-vf", "fade=in:0:15", *ENC, "-shortest", ev])
    parts.append(ev); clock += es
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    joined = os.path.join(tmp, "joined.mp4"); run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    final = os.path.join(out, spec["out"] + ".mp4")
    if spec.get("bgm"):  # 배경음악은 원본 소리 아래로 깔기
        bgm = os.path.join(base, spec["bgm"]); bv = spec.get("bgm_volume", 0.12)
        run(["ffmpeg", "-y", "-i", joined, "-stream_loop", "-1", "-i", bgm, "-filter_complex",
             f"[1:a]volume={bv},afade=t=out:st={clock-3}:d=3[b];[0:a][b]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", final])
    else: shutil.copy(joined, final)
    sp = os.path.join(out, spec["out"] + ".srt")
    open(sp, "w", encoding="utf-8").write("".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(srt, 1)))
    tp = None
    if spec.get("thumb"): tp = os.path.join(out, spec["out"] + "_thumb.jpg"); thumb_png(spec["thumb"], os.path.join(base, spec["thumb"]["photo"]), tp)
    chk = [("챕터 카드는 전환 때만", True), ("끝 화면(구독·좋아요·알림·다음 편)", bool(spec.get("end", {}).get("next"))),
           ("배경음악", bool(spec.get("bgm"))), ("출처(쓴 영상 목록)", bool(spec.get("sources"))), ("썸네일", bool(tp)),
           ("팬 영상 양해 확인", bool(spec.get("consent_checked")))]
    print(f"영상: {final} ({clock/60:.1f}분)\n자막: {sp}\n썸네일: {tp}")
    for n, ok in chk: print(("✅ " if ok else "❌ 빠짐: ") + n)

if __name__ == "__main__":
    p = sys.argv[1]; build(json.load(open(p, encoding="utf-8")), os.path.dirname(os.path.abspath(p)))
