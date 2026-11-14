#!/usr/bin/env python3
"""덕심저장소 간단 편집 쇼츠 제작기 (쇼츠 화면 표준 v1 자동화)

사용법
  python3 shorts_maker.py init  specs/새이름.json        # 빈 설정 파일 틀 만들기
  python3 shorts_maker.py check specs/파일.json          # 렌더 없이 규칙 점검(길이·자막·글자 폭·원본 파일)
  python3 shorts_maker.py build specs/파일.json [id ...] # 영상·썸네일·문구·첫 댓글 묶음 만들기
  python3 shorts_maker.py copy  specs/파일.json          # 영상 없이 제목·설명·댓글 문서만 다시 만들기
  python3 shorts_maker.py sheet specs/파일.json id       # 3초 간격 확인용 모음 이미지

결과(out_dir/<id>/): 영상_업로드본.mp4(10MB 미만), 영상_원본화질.mp4, 썸네일.jpg, 끝화면.png
공통(out_dir/): 업로드_문구.md(제목·설명·해시태그·첫 댓글·공개 시각·할 일 목록)
"""
import json, os, sys, subprocess, math, shutil
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W, H = 1080, 1920
VY, VH = 660, 608           # 영상 위치(y=660, 높이 608)
END_SEC = 3.0               # 끝 화면
MAX_SEC = 60.0              # 쇼츠 상한(끝 화면 포함 1분 안쪽 권장)
UP_LIMIT_MB = 9.5           # 크롬 확장 업로드 10MB 미만
FONT_DIR = "/usr/share/fonts/opentype/noto/"
BLACK = FONT_DIR + "NotoSansCJK-Black.ttc"
BOLD = FONT_DIR + "NotoSansCJK-Bold.ttc"
if not os.path.exists(BOLD): BOLD = BLACK
KO, JA = 1, 0               # ttc 안의 글꼴 번호(한국어, 일본어)
YEL, PINK, WH = (255, 221, 0), (255, 120, 190), (255, 255, 255)
BG_CYCLE = ["purple", "black"]  # 배경은 번갈아
DEFAULT_LOGO = "/home/claude/hot-issue-publisher/assets/brand/duksim/profile_800.png"
BAD_WORDS = ["뭐하노"]       # 제목·썸네일·큰 글씨 금지어(논란 단어). 필요하면 추가
EMOJI_BAD = ["💜", "🫂", "🙂"]  # 영상 안 글자에서 깨지는 이모지(댓글·설명에는 사용 가능)

def F(p, s, i): return ImageFont.truetype(p, s, index=i)

# ---------------------------------------------------------------- 그리기
def bg(kind):
    if kind == "black": return Image.new("RGBA", (W, H), (0, 0, 0, 255))
    a = np.zeros((H, W, 3), np.uint8)
    for y in range(H):
        t = y / H; a[y] = [int(40 + 30 * t), int(16 + 10 * t), int(70 + 40 * t)]
    return Image.fromarray(a).convert("RGBA")

def fit_font(d, s, f, maxw=1010):
    w = d.textlength(s, font=f)
    while w > maxw and f.size > 30:
        f = ImageFont.truetype(f.path, f.size - 4, index=f.index); w = d.textlength(s, font=f)
    return f, w

def ctext(d, y, s, f, fill, sw):
    f, w = fit_font(d, s, f)
    d.text(((W - w) / 2, y), s, font=f, fill=fill, stroke_width=sw, stroke_fill=(10, 6, 30))

_logo = {}
def logo(path, h):
    if path not in _logo:
        a = np.array(Image.open(path).convert("RGBA")); c = a[2, 2, :3].astype(int)
        m = np.abs(a[:, :, :3].astype(int) - c).sum(2) < 40; a[m, 3] = 0
        _logo[path] = Image.fromarray(a)
    return _logo[path].resize((h, h))

def header(im, d, y, lp):
    tw = d.textlength("덕심저장소", font=F(BLACK, 48, KO)); x0 = int((W - (90 + 16 + tw)) / 2)
    im.alpha_composite(logo(lp, 90), (x0, y - 25)); d.text((x0 + 106, y - 13), "덕심저장소", font=F(BLACK, 48, KO), fill=WH)

def overlay(cl, S, ph):
    t0, t1, ko1, ko2, ja1, ja2, punch = ph
    im = bg(cl["bg"]); d = ImageDraw.Draw(im); header(im, d, 95, S["logo"])
    if punch:
        ctext(d, 240, ko1, F(BLACK, 92, KO), WH, 9); ctext(d, 370, ko2, F(BLACK, 116, KO), PINK, 11)
    else:
        ctext(d, 250, ko1, F(BLACK, 84, KO), WH, 8); ctext(d, 380, ko2, F(BLACK, 104, KO), YEL, 10)
    d.rectangle([0, VY, W - 1, VY + VH - 1], fill=(0, 0, 0, 0))
    ctext(d, 1300, "출처 · " + S["source"]["channel"], F(BOLD, 34, KO), (220, 200, 255), 0)
    ctext(d, 1346, S["source"]["title"], F(BOLD, 30, KO), (200, 185, 240), 0)
    ctext(d, 1460, ja1, F(BLACK, 54, JA), WH, 6)
    ctext(d, 1540, ja2, F(BLACK, 62, JA), PINK if punch else YEL, 6)
    return im

def end_card(cl, S):
    e = cl["end"]; im = bg(cl["bg"]); d = ImageDraw.Draw(im)
    im.alpha_composite(logo(S["logo"], 260), ((W - 260) // 2, 470))
    ctext(d, 790, e["ko"], F(BLACK, 66, KO), YEL, 8)
    ctext(d, 890, e["ko2"], F(BLACK, 58, KO), PINK, 7)
    ctext(d, 1000, "원본 전체는 " + S["source"]["channel"] + " 공식 채널에서", F(BOLD, 38, KO), WH, 0)
    ctext(d, 1070, "덕심저장소", F(BLACK, 56, KO), WH, 6)
    ctext(d, 1150, "3D 덕심 갤러리 · " + S["gallery_text"], F(BLACK, 46, KO), PINK, 6)
    ctext(d, 1260, e["ja"], F(BLACK, 48, JA), WH, 6)
    return im

def make_thumb(cl, S, src, out):
    th = cl["thumb"]; fr = out + "/_tf.png"
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(th["t"] + cl["in"] if th.get("abs") is False else th["t"]), "-i", src, "-frames:v", "1", fr])
    f = Image.open(fr).convert("RGB"); x = th.get("x", 420)
    face = f.crop((x, 0, x + 1080, 1080)).resize((1080, 1080))
    im = bg(cl["bg"]); im.paste(face, (0, 560)); d = ImageDraw.Draw(im); header(im, d, 60, S["logo"])
    ctext(d, 150, th["ko"][0], F(BLACK, 96, KO), WH, 10)
    ctext(d, 290, th["ko"][1], F(BLACK, 128, KO), PINK, 12)
    ctext(d, 1700, th["sub"], F(BLACK, 60, KO), YEL, 8)
    im.convert("RGB").save(out + "/썸네일.jpg", quality=92); os.remove(fr)

# ---------------------------------------------------------------- 도구
def run(cmd): subprocess.run(cmd, check=True)

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}"); types = [s["codec_type"] for s in j.get("streams", [])]
    return float(j.get("format", {}).get("duration", 0) or 0), types

def load(path):
    S = json.load(open(path, encoding="utf-8"))
    S.setdefault("logo", DEFAULT_LOGO); S.setdefault("gallery_text", "duksim.com"); S.setdefault("gallery_url", "https://duksim.com")
    S.setdefault("out_dir", "/home/claude/shorts_maker/out/" + os.path.splitext(os.path.basename(path))[0])
    base = S.get("source_dir", "")
    for i, c in enumerate(S["clips"]):
        c.setdefault("bg", BG_CYCLE[i % 2]); c["src"] = c["src"] if os.path.isabs(c["src"]) else os.path.join(base, c["src"])
        c["dur"] = round(c["out"] - c["in"], 3)
    return S

# ---------------------------------------------------------------- 점검
def check(S, quiet=False):
    errs, warns = [], []
    meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for c in S["clips"]:
        n = c["id"]
        if not os.path.exists(c["src"]): errs.append(f"[{n}] 원본 파일 없음: {c['src']}")
        else:
            sd, types = probe(c["src"])
            if c["out"] > sd + 0.05: errs.append(f"[{n}] 끝 시각 {c['out']}초가 원본 길이 {sd:.1f}초를 넘음")
            if "audio" not in types: errs.append(f"[{n}] 원본에 소리가 없음")
            if types.count("audio") >= 2: errs.append(f"[{n}] 소리 줄이 2개 이상(자동 더빙 의심). 원본을 다시 받으세요")
        if c["dur"] + END_SEC > MAX_SEC: errs.append(f"[{n}] 본편 {c['dur']}초 + 끝 화면 {END_SEC}초 = {c['dur']+END_SEC:.1f}초로 1분 초과")
        ph = c["phases"]
        if abs(ph[0][0]) > 0.01: errs.append(f"[{n}] 첫 자막이 0초에서 시작하지 않음")
        for a, b in zip(ph, ph[1:]):
            if abs(a[1] - b[0]) > 0.01: errs.append(f"[{n}] 자막 구간이 이어지지 않음: {a[1]} → {b[0]}")
        if abs(ph[-1][1] - c["dur"]) > 0.05: errs.append(f"[{n}] 마지막 자막 끝 {ph[-1][1]}초 ≠ 본편 길이 {c['dur']}초(펀치라인이 잘릴 수 있음)")
        if not any(p[6] for p in ph): warns.append(f"[{n}] 펀치라인(분홍 큰 글씨) 구간이 없음")
        texts = [t for p in ph for t in p[2:6]] + list(c["thumb"]["ko"]) + [c["thumb"]["sub"]] + list(c["end"].values())
        for t in texts:
            for e in EMOJI_BAD:
                if e in t: errs.append(f"[{n}] 영상 글자에 깨지는 이모지 {e}: {t}")
        for t in list(c["thumb"]["ko"]) + [p[2] + p[3] for p in ph] + [c["yt_title"]]:
            for w in BAD_WORDS:
                if w in t: errs.append(f"[{n}] 금지 단어 '{w}' 포함: {t}")
        for p in ph:
            for t, fs in ((p[2], 84), (p[3], 104), (p[4], 54), (p[5], 62)):
                f, w = fit_font(meas, t, F(BLACK, fs, JA if t in (p[4], p[5]) else KO))
                if f.size < 52 and fs >= 84: warns.append(f"[{n}] 제목이 길어 글자가 {f.size}pt로 줄어듦: {t}")
        if c["bg"] == S["clips"][max(0, S["clips"].index(c) - 1)]["bg"] and S["clips"].index(c) > 0:
            warns.append(f"[{n}] 바로 앞 편과 배경색이 같음(번갈아 쓰는 규칙)")
        if "yt_title" not in c or "desc" not in c: errs.append(f"[{n}] 제목 또는 설명 없음")
        if not c.get("publish_at"): warns.append(f"[{n}] 공개 시각(publish_at) 없음")
    if not quiet:
        for e in errs: print("✗", e)
        for w in warns: print("△", w)
        print(f"점검 끝: 오류 {len(errs)}건, 주의 {len(warns)}건")
    return errs, warns

# ---------------------------------------------------------------- 영상
def build_clip(S, c):
    out = os.path.join(S["out_dir"], c["id"]); os.makedirs(out, exist_ok=True)
    dur, a, src, phs = c["dur"], c["in"], c["src"], c["phases"]
    pngs = []
    for i, ph in enumerate(phs):
        p = f"{out}/_ov{i}.png"; overlay(c, S, ph).save(p); pngs.append(p)
    inp = ["-ss", f"{a}", "-t", f"{dur}", "-i", src]
    for p in pngs: inp += ["-loop", "1", "-t", f"{dur}", "-i", p]
    fc = [f"color=c=black:s={W}x{H}:d={dur}:r=30[base]", f"[0:v]scale={W}:{VH},setsar=1,fps=30[v0]", f"[base][v0]overlay=0:{VY}:shortest=1[b]"]
    prev = "b"
    for i, ph in enumerate(phs):
        fc.append(f"[{prev}][{i+1}:v]overlay=0:0:enable='between(t,{ph[0]},{ph[1]-0.001})'[o{i}]"); prev = f"o{i}"
    fc += [f"[{prev}]format=yuv420p[v]", f"[0:a]afade=t=out:st={max(0,dur-1.0)}:d=1.0[a]"]
    run(["ffmpeg", "-y", "-v", "error", *inp, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", f"{out}/_main.mp4"])
    end_card(c, S).convert("RGB").save(f"{out}/끝화면.png")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(END_SEC), "-i", f"{out}/끝화면.png", "-f", "lavfi", "-t", str(END_SEC),
         "-i", "anullsrc=r=44100:cl=stereo", "-vf", "fps=30,format=yuv420p,fade=t=in:d=0.4", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-c:a", "aac", "-shortest", f"{out}/_end.mp4"])
    open(f"{out}/_list.txt", "w").write(f"file '{out}/_main.mp4'\nfile '{out}/_end.mp4'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{out}/_list.txt", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", f"{out}/영상_원본화질.mp4"])
    total = dur + END_SEC
    vk = int(min(1100, UP_LIMIT_MB * 8192 / total - 128))   # 길이에 맞춰 10MB 미만이 되도록 계산
    for ps in (1, 2):
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", f"{out}/영상_원본화질.mp4", "-c:v", "libx264", "-b:v", f"{vk}k", "-pass", str(ps), "-passlogfile", f"{out}/_2p"]
        cmd += (["-an", "-f", "mp4", "/dev/null"] if ps == 1 else ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", f"{out}/영상_업로드본.mp4"])
        run(cmd)
    make_thumb(c, S, src, out)
    for f in os.listdir(out):
        if f.startswith("_"): os.remove(os.path.join(out, f))
    for f in os.listdir(S["out_dir"]):
        if f.endswith(".log") or f.endswith(".mbtree"): os.remove(os.path.join(S["out_dir"], f))
    mb = os.path.getsize(f"{out}/영상_업로드본.mp4") / 1e6
    d2, types = probe(f"{out}/영상_업로드본.mp4")
    ok = mb < 10 and "audio" in types and d2 <= MAX_SEC
    print(f"{c['id']}: {d2:.1f}초, {mb:.2f}MB, 소리 {'있음' if 'audio' in types else '없음'} → {'통과' if ok else '확인 필요'}")
    return ok

def sheet(S, cid):
    c = next(x for x in S["clips"] if x["id"] == cid); out = os.path.join(S["out_dir"], cid)
    v = f"{out}/영상_원본화질.mp4"; fr = []
    t = 0.5
    while t < c["dur"] + END_SEC:
        p = f"{out}/_s{len(fr)}.jpg"
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", v, "-frames:v", "1", "-vf", "scale=270:480", p]); fr.append(p); t += 3
    cols = min(6, len(fr)); rows = math.ceil(len(fr) / cols)
    im = Image.new("RGB", (cols * 270, rows * 480))
    for i, p in enumerate(fr): im.paste(Image.open(p), ((i % cols) * 270, (i // cols) * 480)); os.remove(p)
    im.save(f"{out}/확인모음.jpg", quality=85); print("확인모음:", f"{out}/확인모음.jpg")

# ---------------------------------------------------------------- 문구
def comments(S):
    s = S["source"]; u = s["url"]; g = S["gallery_url"]; who = S.get("cheer_name", "")
    cheer = f"{who}에게 " if who else ""
    yt = f"원본 전체는 {s['channel']} 공식 채널에서 보실 수 있어요 → {u} 🙂 {cheer}따뜻한 응원 한마디 남겨 주세요! 서로 존중하는 댓글 부탁드려요. 구독·좋아요·알림 설정하면 다음 영상도 바로 만나요 ♥ 3D 덕심 갤러리 {g}"
    ig = yt.replace("구독·좋아요·알림 설정하면", "팔로우·좋아요 해 주시면")
    th = f"원본 전체는 {s['channel']} 공식 채널에서 봐 → {u} {who+'한테 ' if who else ''}응원 한마디 남겨 줘 ♥ 3D 덕심 갤러리 {g}"
    return yt, ig, th

def write_copy(S):
    os.makedirs(S["out_dir"], exist_ok=True); s = S["source"]; yt, ig, th = comments(S)
    L = [f"# {S.get('title','쇼츠 묶음')} — 업로드 문구", f"원본: {s['channel']} 「{s['title']}」 {s['url']}",
         "다섯 곳(유튜브·인스타 릴스·틱톡·X·스레드) 같은 시각. 「올려」 전에는 올리지 않는다.", ""]
    for i, c in enumerate(S["clips"], 1):
        tags = " ".join(c.get("hashtags", []))
        L += [f"## {'①②③④⑤⑥⑦⑧⑨'[i-1]} {c.get('publish_at','(시각 미정)')} — {c['id']} ({c['dur']+END_SEC:.0f}초, {c['bg']} 배경)",
              f"- 유튜브 제목: {c['yt_title']}", f"- 설명: {c['desc']}",
              f"  원본 전체: {s['channel']} 공식 채널 {s['url']}", f"  3D 덕심 갤러리 {S['gallery_url']}", f"  {tags}",
              f"- 일본어 한 줄: {c.get('ja_line','')}", f"- 파일: {c['id']}/영상_업로드본.mp4 · {c['id']}/썸네일.jpg", ""]
    L += ["## 첫 댓글", f"- 유튜브(고정): {yt}", f"- 인스타 1개: {ig}", f"- 스레드(반말): {th}", "",
          "## 「올려」 뒤 할 일 (클릭만, 편마다 반복)",
          "1. 유튜브: 예약 공개 · 재생목록 「덕심저장소」 · 아동용 아님 · 썸네일 등록",
          "2. 인스타 릴스(Meta Business Suite)·틱톡·X·스레드: 같은 시각으로 예약 (틱톡 설명은 직접 입력)",
          "3. 공개 시각 +1분에 send_later로 첫 댓글 작업 걸기 (집 컴퓨터 켜 두기)",
          "4. 공개 후: 유튜브 첫 댓글 → 고정 / 인스타 1개 / 스레드 반말",
          "5. 「오늘 업로드 기록」 문서에 ID·공개 여부 기록, 3~24시간 뒤 조회수 기록"]
    open(os.path.join(S["out_dir"], "업로드_문구.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("문구:", os.path.join(S["out_dir"], "업로드_문구.md"))

TEMPLATE = {
 "title": "예: 11/15 여담 쇼츠 묶음", "source_dir": "/home/claude/ys",
 "source": {"channel": "채널명", "title": "원본 영상 제목", "url": "https://youtu.be/..."},
 "cheer_name": "그룹명", "gallery_url": "https://duksim.com", "gallery_text": "duksim.com",
 "clips": [{
   "id": "c1_짧은이름", "src": "원본파일.mp4", "in": 0.0, "out": 40.0, "publish_at": "2026-11-15 09:00",
   "phases": [[0, 20, "윗줄 흰 글씨", "아랫줄 노랑 글씨", "日本語 윗줄", "日本語 아랫줄", False],
              [20, 40, "「핵심 대사 윗줄", "핵심 대사 아랫줄」", "「日本語", "日本語」", True]],
   "end": {"ko": "끝 화면 한 줄", "ko2": "응원 댓글 유도 한 줄", "ja": "日本語 한 줄 ♥"},
   "thumb": {"t": 30.0, "x": 420, "ko": ["「대사 윗줄", "대사 아랫줄」"], "sub": "썸네일 아래 한 줄 설명"},
   "yt_title": "유튜브 제목 #해시태그", "desc": "설명 한두 문장 ♥", "hashtags": ["#덕심저장소"], "ja_line": "일본어 한 줄"}]}

def main():
    if len(sys.argv) < 3: print(__doc__); return
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == "init":
        json.dump(TEMPLATE, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("틀 만듦:", path); return
    S = load(path)
    if cmd == "check": sys.exit(1 if check(S)[0] else 0)
    if cmd == "copy": write_copy(S); return
    if cmd == "sheet": sheet(S, sys.argv[3]); return
    if cmd == "build":
        errs, _ = check(S)
        if errs: print("오류를 고친 뒤 다시 실행하세요."); sys.exit(1)
        ids = sys.argv[3:] or [c["id"] for c in S["clips"]]
        res = [build_clip(S, c) for c in S["clips"] if c["id"] in ids]
        write_copy(S); print("전체", "통과" if all(res) else "확인 필요")

if __name__ == "__main__": main()
