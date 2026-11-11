"""덕심저장소 롱폼 공장 v2.1
사용법: python longform_factory.py 롱폼기획.json
        python longform_factory.py --test-media 폴더   (시험용 가짜 영상·소리 만들기)
v1(대표 11/8 결정) 위에 벤치마킹(언더독스토리) 두 가지를 기본 기능으로 넣었다.
 ① 가로(16:9) ↔ 세로(9:16) 전환
   - 장면 "layout":"vertical" → 가운데 세로 영상(높이 1080, 둥근 모서리·그림자) + 뒤 배경은 같은 영상 흐리게·어둡게
   - 양옆 정보 패널 "side_left" / "side_right" (글만 주면 공장이 그림. 목록이면 댓글 말풍선)
   - 가로→세로 0.5초 '접힘', 세로→가로 0.5초 '펼침' 자동
   - "layout":"split" → 가로 영상 왼쪽 + 세로 영상("file2") 오른쪽 나란히
 ② 지루할 틈 없이 이어지기
   - 장면 사이 검은 화면·무음 0초: 기본 0.3초 교차 디졸브, 챕터 카드는 영상 위 반투명 오버레이(2초)
     (전체 화면 카드는 "card_style":"full" 일 때만, 되감기는 "rewind": true 인 챕터로 들어갈 때만)
   - J컷 "audio_lead"(다음 소리 먼저) / L컷 "audio_tail"(앞 소리 이어서)
   - 내레이션 "narration" → 나오는 동안 원본·배경음악 자동 덕킹(-14dB)
   - 8초 넘는 한 장면은 점검표에 "긴 정지 장면" 경고, 화면 위 챕터 진행 막대("progress": true)
   - 사진 장면 "image": 파일 (SNS 캡처 등) → 가운데 사진 + 같은 사진 흐린 배경, 길이 "sec"
 ③ 기준서 v1(11/11) 기능
   - "opening": {"highlight":{file,in,out,line,credit}, "question":"…", "question_at":25} → 0~3초 하이라이트(대사 크게 가운데) + 25초 근처 노란 질문
   - "ending": {"line","ask","next","next_date"} → 끝 화면 앞 주제 한 줄 → 질문 자막 → 끝 화면
   - 장면 "credit" → 오른쪽 아래 구석 출처 + 마지막 '영상 출처' 화면 4초 자동
   - 자막은 흰 굵은 고딕, *별표* 단어는 노란색. 자막 4번째 칸에 모양("big"/"ask"/"question")
   - 설명란 out/<이름>_설명란.txt : summary → 챕터 타임스탬프(실제 시각) → 감사한 출처 → hashtags → summary_i18n(en/ja/zh-TW)
 ④ 기준서 v1 추가 4개(11/11)
   - 감정 자막: subs 4번째 칸 "emotion" (5번째 칸 "left"/"right", 기본 오른쪽) → 작게·화면 옆쪽·기울임·연분홍, 0.35초 페이드
   - 효과음 자막: subs 4번째 칸 "sfx" (5번째 칸 [x,y] 화면 비율, 기본 [0.5,0.3]) → 짧은 의성어, 0.3초 팝 애니메이션
     장면 "sfx":[{"at":초,"file":"효과음","volume":1.0}] → 같은 시각 효과음 믹스(배경음악 덕킹 없음)
   - 음악 끊기: "music_cut":[{"at":초,"sec":길이}] → 그 구간 배경음악만 0으로(0.12초 내려가고 0.6초 복귀)
     영상 전체 기준(맨 위) 또는 장면 안 기준(장면 안에 넣으면 장면 시작부터 셈)
   - 결심 한 줄: "ending":{"resolve":"…"} → 검은 화면 위 한 줄 2초 페이드인(resolve_sec 기본 3.5초) → 끝 화면
 ⑤ 상품 카드(제휴 광고 QR, 언더독스토리 벤치마킹 11/11)
   - "product_cards":[{"at":초,"sec":6,"name":"상품명","price":"12,900원","url":"https://…","label":"안내 한 줄"}]
     (맨 위 = 영상 전체 기준, 장면 안 = 장면 시작부터) → 왼쪽 아래 흰 둥근 카드(QR + 「광고 · 제휴 링크」 + 상품명·가격), 0.3초 슬라이드 인
   - 그 시간에 떠 있는 자막·출처·말풍선·옆 패널과 겹치지 않게 자리 위로 올림(안 되면 오른쪽 아래). QR은 qr.py(순수 파이썬)
   - 설명란 맨 위에 상품 링크 목록, url에 coupang 있으면 쿠팡 파트너스 고지 문구. 주류·담배·도박·성인 단어는 점검표 ❌
 ⑦ v2.2 몰아보기(제작 표준 v2, 11/11) — "template":"molabogi" 또는 아무 롱폼 장면에서 쓸 수 있음. 기존 v2.1 기능은 그대로
   - 자막 모양 추가: "bracket"(괄호 드립, 괄호 부분 노랑) · "situation"([대괄호] 상황 자막, 왼쪽 위 상자) · "narr"(내레이션 자막)
     subs 5번째 칸 [x,y] 화면 비율로 자리 지정 가능(얼굴 옆 등)
   - 장면 "reacts":[{"at","sec","text","name"}] → 오른쪽 아래 「동네 형」 일러스트 원형 아이콘 + 말풍선(실존 인물 얼굴 없음)
   - 장면 "zooms":[{"at","x","y","scale","hold"}] → 크래시 줌(0.15초 급확대 후 hold초 유지, x·y 화면 비율)
   - 장면 "bleeps":[{"at","dur"}] → 그 구간 원음 줄이고 1kHz 삐-
   - "sfx":[{"at","name":"crow"}] → 공장이 합성한 까마귀 효과음(assets/sfx_crow.wav). file 대신 name 가능
   - 내레이션 파일이 없으면(narration 의 file 없음/파일 없음) "text"(또는 "_text")를 "narr" 자막으로 대신 보여 줌(워크맨식 빠른 내레이션 자리)
   - 렌더 뒤 check_standard.py(표준 v2 점검) 자동 실행
 ⑥ v2.1 (11/11)
   - 장면 "rewind": true (또는 "rewind":"날짜") → 그 장면에 들어갈 때 0.5초 역재생 + 날짜 도장(챕터 카드 없이, 챕터 중간 어디서나)
     날짜 글은 "date"(또는 rewind 문자열), 자리 "stamp_pos":[x,y] 비율(기본 [0.8,0.2]), 보이는 길이 "stamp_sec"(기본 1.8)
   - 챕터 "card": false → 챕터 카드(오버레이·전체 화면) 생략하고 바로 장면. 챕터 "rewind": true 는 예전 그대로
결과: 롱폼 영상(1920x1080, 30fps) + 썸네일(1280x720) + 자막(.srt) + 설명란(.txt) + 점검표
"""
import json, os, sys, subprocess, shutil, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 같은 폴더의 qr.py

W, H, FPS = 1920, 1080, 30
VW = 608; VX = (W - VW) // 2                      # 세로 틀(높이 1080 맞춤) 폭·위치
SPL_H = (40, 205, 1192, 670); SPL_V = (1272, 0)   # split: 가로(x,y,w,h) · 세로(x,y)
FD = "/usr/share/fonts/opentype/noto/"
if os.name == "nt": FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + os.sep
FB, FM = FD + "NotoSansCJK-Bold.ttc", FD + "NotoSansCJK-Medium.ttc"
def F(p, s): return ImageFont.truetype(p, s, index=1)
Y = (255, 214, 64); WH = (255, 255, 255); GR = (185, 190, 215); PU = (206, 160, 255); NAVY = (14, 12, 40); PB = (150, 80, 230); RD = (255, 70, 90)
VENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]
VTMP = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS)]  # 중간 파일(화질 손실 줄이기)
AENC = ["-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k"]
BATCH = 12   # xfade 체인 한 번에 묶는 장면 수(30개+ 일 때 묶음으로 나눠 처리)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("ffmpeg 오류:\n" + r.stderr[-2000:])
    return r.stderr

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration", "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    return any(s.get("codec_type") == "audio" for s in j.get("streams", [])), float(j.get("format", {}).get("duration", 0) or 0)

def fr(x): return max(1, round(x * FPS)) / FPS   # 프레임 단위로 맞춤

# ---------------- 그림(PNG) ----------------
def ct(d, y, t, fo, fill=WH, stroke=0):
    w = d.textlength(t, font=fo); d.text(((W - w) / 2, y), t, font=fo, fill=fill, stroke_width=stroke, stroke_fill=(10, 6, 30))

def wrap(d, text, fo, maxw):
    out = []
    for para in str(text).split("\n"):
        line = ""
        for ch in para:
            if d.textlength(line + ch, font=fo) > maxw and line: out.append(line); line = ch
            else: line += ch
        out.append(line)
    return out

SUB_STYLE = {   # 자막 모양: (글자 크기, 위치, 기본 색, 띠)
    "sub": (58, "bottom", WH, True),        # 보통 자막(화면 아래)
    "big": (96, "center", WH, False),       # 오프닝 하이라이트 대사·엔딩 주제 한 줄(크게 가운데)
    "ask": (84, "center", Y, False),        # 엔딩 질문(노란색 가운데)
    "question": (70, "top", Y, True),       # 오프닝 질문(노란색, 위쪽)
    "resolve": (72, "center", WH, False),   # 끝맺음 결심 한 줄(검은 화면 위)
}   # "emotion"(감정 자막)·"sfx"(효과음 자막)은 emotion_png / sfx_frames 가 따로 그림
SOFT = (255, 205, 228)   # 감정 자막 연분홍
def plain(t): return str(t).replace("*", "")

def emotion_png(text, path, side="right"):
    """감정 자막: 인물 마음을 대신 말하는 한 줄. 작게, 화면 옆쪽(아래 자막 위), 기울임, 부드러운 색. *별표*는 흰색."""
    size = 42; fo = F(FM, size); dm = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = [[(p, WH if k % 2 else SOFT) for k, p in enumerate(ln.split("*")) if p] for ln in str(text).split("\n")]
    while size > 28 and max(sum(dm.textlength(s, font=fo) for s, _ in L) for L in lines) > 760: size -= 2; fo = F(FM, size)
    lh = int(size * 1.4); tw = int(max(sum(dm.textlength(s, font=fo) for s, _ in L) for L in lines)) + 60; th = lh * len(lines) + 30
    lay = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); sh = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d, ds = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    for i, L in enumerate(lines):
        w = sum(d.textlength(s, font=fo) for s, _ in L); x = (tw - w - 30) if side == "right" else 30; y = 12 + lh * i
        ds.text((x + 2, y + 3), "".join(s for s, _ in L), font=fo, fill=(0, 0, 0, 210), stroke_width=4, stroke_fill=(0, 0, 0, 210))
        for s, col in L: d.text((x, y), s, font=fo, fill=col, stroke_width=2, stroke_fill=(40, 20, 50)); x += d.textlength(s, font=fo)
    lay = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), lay)
    k = 0.2; lay = lay.transform((tw + int(k * th), th), Image.AFFINE, (1, k, -k * th, 0, 1, 0), Image.BICUBIC)   # 기울임(이탤릭)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); y0 = H - 300 - th
    im.alpha_composite(lay, (W - 70 - lay.width if side == "right" else 70, y0)); im.save(path)

def sfx_frames(text, prefix, pos=(0.5, 0.3)):
    """효과음 자막(의성어): 노란 굵은 글씨 살짝 기울여, 0.3초 팝(작게→크게→제자리). 프레임 PNG 9장 → 마지막 장 유지."""
    fo = F(FB, 120); dm = ImageDraw.Draw(Image.new("RGBA", (1, 1))); t = plain(text)
    tw, th = int(dm.textlength(t, font=fo)) + 60, 190
    base = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); ImageDraw.Draw(base).text((30, 10), t, font=fo, fill=Y, stroke_width=10, stroke_fill=(10, 6, 30))
    base = base.rotate(8, resample=Image.BICUBIC, expand=True)
    n = max(2, round(0.3 * FPS)); cx, cy = int(W * pos[0]), int(H * pos[1])
    for i in range(n):
        u = (i + 1) / n; s = 0.35 + 0.95 * (u / 0.6) if u < 0.6 else 1.3 - 0.3 * ((u - 0.6) / 0.4)   # 0.35 → 1.3 → 1.0
        a = min(1.0, u / 0.3)
        fr_ = base.resize((max(1, int(base.width * s)), max(1, int(base.height * s))), Image.BICUBIC)
        if a < 1: fr_.putalpha(fr_.getchannel("A").point(lambda v: int(v * a)))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); im.alpha_composite(fr_, (max(0, min(W - fr_.width, cx - fr_.width // 2)), max(0, min(H - fr_.height, cy - fr_.height // 2))))
        im.save(f"{prefix}_{i:02d}.png")
    return f"{prefix}_%02d.png"

def stamp_frames(text, prefix, pos=(0.8, 0.2)):
    """날짜 도장: 빨간 잉크 테두리 + 날짜, 살짝 기울여 '쾅' 찍히듯(1.8배 → 1.0배, 0.25초). 프레임 PNG → 마지막 장 유지."""
    fo = F(FB, 64); dm = ImageDraw.Draw(Image.new("RGBA", (1, 1))); t = plain(text)
    tw = int(dm.textlength(t, font=fo)); bw, bh = tw + 90, 130
    base = Image.new("RGBA", (bw + 20, bh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(base); ink = RD + (235,)
    d.rounded_rectangle([10, 10, 10 + bw, 10 + bh], radius=18, outline=ink, width=8)
    d.rounded_rectangle([24, 24, bw - 4, bh - 4], radius=12, outline=RD + (150,), width=3)
    d.text((10 + (bw - tw) / 2, 10 + (bh - 64) / 2 - 12), t, font=fo, fill=ink, stroke_width=2, stroke_fill=(255, 255, 255, 200))
    base = base.rotate(-8, resample=Image.BICUBIC, expand=True)
    n = max(2, round(0.25 * FPS)); cx, cy = int(W * pos[0]), int(H * pos[1])
    for i in range(n):
        u = (i + 1) / n; s = 1.8 - 0.8 * (u ** 2) if u < 1 else 1.0; a = min(1.0, 0.25 + u)
        fr_ = base.resize((max(1, int(base.width * s)), max(1, int(base.height * s))), Image.BICUBIC)
        if a < 1: fr_.putalpha(fr_.getchannel("A").point(lambda v: int(v * a)))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); im.alpha_composite(fr_, (max(0, min(W - fr_.width, cx - fr_.width // 2)), max(0, min(H - fr_.height, cy - fr_.height // 2))))
        im.save(f"{prefix}_{i:02d}.png")
    return f"{prefix}_%02d.png", n

def sub_png(text, path, style="sub"):
    """자막: 흰 굵은 고딕 + 테두리·그림자. *별표* 로 감싼 단어는 노란색(기본색이 노랑이면 흰색)."""
    size, pos, base, band = SUB_STYLE.get(style, SUB_STYLE["sub"])
    hi = Y if base == WH else WH
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lines = []
    for ln in str(text).split("\n"):
        segs, on = [], False
        for k, part in enumerate(ln.split("*")):
            if part: segs.append((part, hi if on else base))
            on = not on
        lines.append(segs)
    while size > 30:
        fo = F(FB, size)
        if max(sum(d.textlength(s, font=fo) for s, _ in L) for L in lines) <= W - 160: break
        size -= 4
    fo = F(FB, size); lh = int(size * 1.32); sw = max(3, size // 12); th = lh * len(lines)
    y0 = {"bottom": H - 96 - th, "center": (H - th) // 2, "top": 120}[pos]
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    rows = []
    for i, L in enumerate(lines):
        w = sum(d.textlength(s, font=fo) for s, _ in L); x = (W - w) / 2; y = y0 + lh * i; rows.append((x, y, w, L))
        if band and L: d.rounded_rectangle([x - 30, y - 8, x + w + 30, y + lh - 4], radius=16, fill=(0, 0, 0, 120))
        ds.text((x + 4, y + 6), "".join(s for s, _ in L), font=fo, fill=(0, 0, 0, 200), stroke_width=sw, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8))); d = ImageDraw.Draw(im)
    for x, y, w, L in rows:
        for s, col in L:
            d.text((x, y), s, font=fo, fill=col, stroke_width=sw, stroke_fill=(10, 6, 30)); x += d.textlength(s, font=fo)
    im.save(path)

def credit_png(text, path):
    """장면 출처: 오른쪽 아래 구석에 작게."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fo = F(FM, 26); t = "출처 · " + text
    w = d.textlength(t, font=fo); x = W - 36 - w; y = H - 52
    d.rounded_rectangle([x - 16, y - 6, x + w + 16, y + 36], radius=18, fill=(0, 0, 0, 120)); d.text((x, y), t, font=fo, fill=(235, 235, 245, 230))
    im.save(path)

# ---------------- 상품 카드(제휴 광고 QR) ----------------
AD_MARK = "광고 · 제휴 링크"
COUPANG_NOTICE = "이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
CARD_M = 40                      # 화면 가장자리 여백
BAN_WORDS = ["주류", "소주", "맥주", "와인", "위스키", "보드카", "막걸리", "양주", "사케", "하이볼", "칵테일", "beer", "wine", "whisky", "whiskey", "vodka", "soju",
             "담배", "전자담배", "궐련", "니코틴", "시가렛", "cigarette", "vape", "베이프",
             "도박", "카지노", "토토", "배팅", "베팅", "바카라", "casino", "betting",
             "성인용품", "성인 전용", "성인전용", "19금", "야동", "adult"]

def product_card_png(c, path):
    """상품 카드: 흰 둥근 상자 + 왼쪽 QR + 오른쪽 '광고 · 제휴 링크' 표시·상품명·가격·안내. 카드 크기 그림(그림자 포함) 저장 → (폭, 높이)."""
    from qr import qr_image, qr_info
    n = qr_info(c["url"])[1]; sc = max(3, round(156 / n)); q = qr_image(c["url"], sc, border=1)   # 카드 흰 여백이 조용한 영역 역할
    pad, gap, tw, sh = 18, 18, 290, 14                                                       # sh = 그림자 여백
    fa, fn, fp, fl = F(FB, 22), F(FB, 30), F(FB, 32), F(FM, 22)
    dm = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    name, line = [], ""                                       # 띄어쓰기 단위로 줄바꿈(한 단어가 너무 길면 글자 단위)
    for wd in str(c["name"]).split():
        t = (line + " " + wd).strip()
        if dm.textlength(t, font=fn) <= tw: line = t
        else:
            if line: name.append(line)
            parts_ = wrap(dm, wd, fn, tw); name += parts_[:-1]; line = parts_[-1]
    name.append(line)
    if len(name) > 2: name = name[:2]; name[1] = name[1][:-1] + "…"
    rows_h = 40 + 40 * len(name) + (44 if c.get("price") else 0) + 34
    bw = pad + q.width + gap + tw + pad; bh = pad + max(q.height, rows_h) + pad
    im = Image.new("RGBA", (bw + sh * 2, bh + sh * 2), (0, 0, 0, 0))
    shd = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(shd).rounded_rectangle([sh, sh + 4, sh + bw, sh + bh + 4], radius=26, fill=(0, 0, 0, 150))
    im = Image.alpha_composite(im, shd.filter(ImageFilter.GaussianBlur(8))); d = ImageDraw.Draw(im)
    x0, y0 = sh, sh
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=24, fill=(255, 255, 255, 255))
    im.paste(q, (x0 + pad, y0 + (bh - q.height) // 2))
    tx = x0 + pad + q.width + gap; ty = y0 + (bh - rows_h) // 2
    aw = d.textlength(AD_MARK, font=fa); d.rounded_rectangle([tx, ty, tx + aw + 24, ty + 32], radius=16, fill=(235, 236, 242), outline=(150, 150, 165), width=1)
    d.text((tx + 12, ty + 2), AD_MARK, font=fa, fill=(70, 70, 85)); ty += 40
    for ln in name: d.text((tx, ty), ln, font=fn, fill=(25, 20, 45)); ty += 40
    if c.get("price"): d.text((tx, ty + 2), str(c["price"]), font=fp, fill=(230, 40, 70)); ty += 44
    d.text((tx, ty + 4), c.get("label") or "QR 찍고 상품 보기", font=fl, fill=(110, 110, 125))
    im.save(path); return im.size

def place_card(size, a, b, occ, m=CARD_M):
    """카드 자리: 왼쪽 아래에서 시작해 그 시간에 떠 있는 자막·출처·말풍선과 겹치지 않을 때까지 위로. 안 되면 오른쪽 아래. → (x, y, 쪽, 겹침 없음?)"""
    cw, chh = size; busy = [bb for s0, s1, bb in occ if s0 < b and s1 > a and bb]
    def free(x, y): return all(x + cw <= bx0 - 8 or x >= bx1 + 8 or y + chh <= by0 - 8 or y >= by1 + 8 for bx0, by0, bx1, by1 in busy)
    for side, x in (("left", m - 14), ("right", W - m + 14 - cw)):     # 그림 안 그림자 여백(14) 보정
        for y in range(H - m + 14 - chh, 110, -10):
            if free(x, y): return x, y, side, True
    return m - 14, H - m + 14 - chh, "left", False

def sources_png(items, path, series):
    """마지막 '영상 출처' 화면."""
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    ct(d, 110, "영상 출처", F(FB, 80), Y); fo = F(FM, 38); y = 250
    for it in items[:14]:
        ct(d, y, it, fo, WH); y += 52
    ct(d, max(y + 40, 900), "소중한 영상을 남겨 주신 분들께 감사드립니다 · " + series, F(FM, 34), GR)
    im.save(path)

def image_scene_png(src, path, mode):
    """SNS 캡처 등 사진 장면: 가운데 사진(둥근 모서리·그림자) + 같은 사진 크게 흐리게·어둡게. mode: narrow/wide/blur"""
    from PIL import ImageOps, ImageEnhance
    img = Image.open(src).convert("RGB")
    bg = ImageEnhance.Brightness(ImageOps.fit(img, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(36))).enhance(0.55 if mode == "blur" else 0.62).convert("RGBA")
    if mode != "blur":
        bw, bh = (680 if mode == "narrow" else 1500), 960; s = min(bw / img.width, bh / img.height)
        fw, fh = int(img.width * s), int(img.height * s); fg = img.resize((fw, fh), Image.LANCZOS)
        x, y = (W - fw) // 2, (H - fh) // 2
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x - 6, y + 6, x + fw + 6, y + fh + 18], radius=34, fill=(0, 0, 0, 190))
        bg = Image.alpha_composite(bg, sh.filter(ImageFilter.GaussianBlur(22)))
        m = Image.new("L", (fw, fh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, fw - 1, fh - 1], radius=28, fill=255); bg.paste(fg, (x, y), m)
    bg.convert("RGB").save(path)

def bubble(d, x, y, w, c, name_size=30, text_size=34):
    """말풍선 하나 그리고 높이 돌려줌."""
    fo = F(FM, text_size); lines = wrap(d, c.get("text", ""), fo, w - 60)[:3]
    h = 70 + int(text_size * 1.35) * len(lines) + 14
    d.rounded_rectangle([x, y, x + w, y + h], radius=26, fill=(255, 255, 255, 235))
    d.text((x + 30, y + 16), "▶ " + c.get("name", "리마인"), font=F(FB, name_size), fill=PB)
    for i, ln in enumerate(lines): d.text((x + 30, y + 64 + int(text_size * 1.35) * i), ln, font=fo, fill=(30, 20, 60))
    return h

def comment_png(c, path, slot, x=1180, w=680):
    """댓글 띄우기: 위쪽에 말풍선 하나 (닉네임 + 한두 줄)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bubble(ImageDraw.Draw(im), x, 90 + slot * 190, w, c, 30, 36); im.save(path)

def info_png(cfg, path, x, w):
    """옆 정보 카드(날짜·장소 등): {"title":"", "lines":[...]} 또는 글자."""
    if isinstance(cfg, str): cfg = {"lines": cfg.split("\n")}
    if isinstance(cfg, list): cfg = {"lines": cfg}
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ft, fl = F(FB, 54), F(FM, 40); rows = []
    if cfg.get("tag"): rows.append(("tag", cfg["tag"]))
    if cfg.get("title"): rows += [("t", s) for s in wrap(d, cfg["title"], ft, w - 70)]
    for ln in cfg.get("lines", []): rows += [("l", s) for s in wrap(d, ln, fl, w - 70)]
    hs = {"tag": 66, "t": 74, "l": 58}; h = 70 + sum(hs[k] for k, _ in rows); y = (H - h) // 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=30, fill=(14, 12, 40, 205), outline=PB + (255,), width=4)
    yy = y + 36
    for k, s in rows:
        if k == "tag":
            tw = d.textlength(s, font=F(FB, 32)); d.rounded_rectangle([x + 34, yy, x + 34 + tw + 40, yy + 50], radius=25, fill=RD)
            d.text((x + 54, yy + 4), s, font=F(FB, 32), fill=WH)
        else: d.text((x + 35, yy), s, font=ft if k == "t" else fl, fill=Y if k == "t" else WH)
        yy += hs[k]
    im.save(path)

def bubbles_pngs(items, x, w, prefix):
    """옆 댓글 목록: 말풍선을 위에서부터 쌓는다. 항목에 "at"(초)가 있으면 그때부터 보임."""
    out = []; y = 70; dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for j, c in enumerate(items):
        if isinstance(c, str): c = {"name": "", "text": c}
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); h = bubble(ImageDraw.Draw(im), x, y, w, c, 28, 32)
        if y + h > H - 40: break
        p = f"{prefix}_{j}.png"; im.save(p); out.append((p, c.get("at", 0))); y += h + 22
    return out

def rmask_png(w, h, r, path):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255); m.save(path)

def shadow_png(rects, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for (x, y, w, h) in rects: d.rounded_rectangle([x - 6, y + 4, x + w + 6, y + h + 16], radius=40, fill=(0, 0, 0, 190))
    im.filter(ImageFilter.GaussianBlur(22)).save(path)

def card_png(ch, n, path, series, overlay=False):
    """챕터 카드. overlay=True 면 영상 위에 얹는 반투명 띠(영상이 계속 흐름)."""
    if overlay:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(band).rectangle([0, 300, W, 780], fill=NAVY + (175,)); im = Image.alpha_composite(im, band.filter(ImageFilter.GaussianBlur(40)))
    else: im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im); s = 4 if overlay else 0
    ct(d, 330, series, F(FM, 44), GR, s)
    ct(d, 420, f"CHAPTER {n}", F(FB, 56), Y, s)
    ct(d, 520, ch["title"], F(FB, 96), WH, s)
    if ch.get("sub"): ct(d, 660, ch["sub"], F(FM, 46), PU, s)
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

def progress_pngs(bounds, total, tmp):
    """챕터 진행 막대: 바탕 막대(챕터마다 칸) + 칸 사이 눈금."""
    tr = Image.new("RGBA", (W, 8), (0, 0, 0, 0)); tk = Image.new("RGBA", (W, 8), (0, 0, 0, 0))
    dt, dk = ImageDraw.Draw(tr), ImageDraw.Draw(tk); dt.rectangle([0, 0, W, 7], fill=(255, 255, 255, 70))
    for b in bounds[1:]:
        x = int(W * b / total); dk.rectangle([x - 3, 0, x + 3, 7], fill=(14, 12, 40, 255))
    a, b = os.path.join(tmp, "pg_track.png"), os.path.join(tmp, "pg_ticks.png"); tr.save(a); tk.save(b); return a, b

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

# ---------------- 전환 ----------------
BX = VX / W
SMOOTH = "st(0,1-P);st(0,ld(0)*ld(0)*(3-2*ld(0)))"   # 0→1 부드럽게
FOLD = SMOOTH + f";st(1,ld(0)*{BX:.5f});st(2,clip((ld(0)-0.6)/0.4,0,1));if(between(X/W,ld(1),1-ld(1)),A*(1-ld(2))+B*ld(2),B)"
UNFOLD = SMOOTH + f";st(1,(1-ld(0))*{BX:.5f});st(2,clip(ld(0)/0.4,0,1));if(between(X/W,ld(1),1-ld(1)),A*(1-ld(2))+B*ld(2),A)"

def xf(kind):
    return {"fold": f"custom:expr='{FOLD}'", "unfold": f"custom:expr='{UNFOLD}'"}.get(kind, "fade")

# ---------------- v2.2 몰아보기 도구 ----------------
def _STD():
    import v2_fx; return v2_fx.STD

def mola_sub_png(text, path, style, pos=None):
    """괄호 드립(bracket) · [상황 자막](situation, 왼쪽 위 상자) · 내레이션 자막(narr, 위 가운데). 원본 자막(화면 아래)을 가리지 않는 자리."""
    import v2_fx
    im = v2_fx.caption_img(text, style, W); full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if pos: x, y = int(pos[0] * W - im.width / 2), int(pos[1] * H - im.height / 2)
    elif style == "situation": x, y = 40, 175          # 내레이션 자막(위 가운데) 아래
    elif style == "narr": x, y = (W - im.width) // 2, 28
    else: x, y = (W - im.width) // 2, int(H * 0.56)    # 원본 자막(화면 아래 0.8~0.95)을 가리지 않게
    full.alpha_composite(im, (max(0, min(W - im.width, x)), max(0, min(H - im.height, y)))); full.save(path)

def react_png(r, path):
    import v2_fx
    im = v2_fx.react_img(r.get("text", ""), r.get("name", "동네 형"), W); full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full.alpha_composite(im, (W - im.width - 40, H - im.height - 110)); full.save(path)

def zoom_filter(zooms):
    """크래시 줌(zoompan, 프레임마다): at 에서 ramp(0.15)초 급확대 → hold 초 유지 → 원래대로."""
    cz = _STD()["style_A"]["crash_zoom"]; zs, xs, ys = [], [], []
    for z in zooms:
        a = z["at"]; r = z.get("ramp", cz["ramp_sec"]); b = a + r + z.get("hold", cz["hold_sec"]); sc = z.get("scale", cz["scale"])
        cond = f"between(it,{a:.3f},{b:.3f})"
        zs.append(f"{cond}*{sc - 1:.3f}*min(1,(it-{a:.3f})/{r:.3f})")
        xs.append((cond, f"min(max({z['x']:.3f}*iw-iw/zoom/2,0),iw-iw/zoom)")); ys.append((cond, f"min(max({z['y']:.3f}*ih-ih/zoom/2,0),ih-ih/zoom)"))
    def nest(lst, dflt):
        e = dflt
        for c, v in reversed(lst): e = f"if({c},{v},{e})"
        return e
    return (f"zoompan=z='1+{'+'.join(zs)}':x='{nest(xs, '(iw-iw/zoom)/2')}':y='{nest(ys, '(ih-ih/zoom)/2')}':d=1:s={W}x{H}:fps={FPS},setsar=1")

# ---------------- 장면 1개 = ffmpeg 1회 ----------------
def src_of(sc, base, key="file"):
    return sc[key] if os.path.isabs(sc[key]) else os.path.join(base, sc[key])

def render_scene(sg, sc, base, tmp, tag, comp):
    lay = sg["layout"]; is_img = bool(sc.get("image"))
    L, D, T = sg["lead"], sg["dur"], sg["tail"]; tot = L + D + T; N = round(D * FPS)
    if is_img:
        has_a = False; ip = os.path.join(tmp, f"{tag}_img.png")
        mode = "blur" if lay == "blur" else ("narrow" if (sc.get("side_left") or sc.get("side_right")) else "wide")
        image_scene_png(src_of(sc, base, "image"), ip, mode)
        inputs = ["-loop", "1", "-framerate", str(FPS), "-t", f"{tot + 0.5:.3f}", "-i", ip]
    else:
        src = src_of(sc, base); has_a, _ = probe(src)
        inputs = ["-ss", f"{sc['in'] - L:.3f}", "-t", f"{tot + 0.5:.3f}", "-i", src]
    k = 1
    def add(args):
        nonlocal k; inputs.extend(args); k += 1; return k - 1
    def loopimg(p, t): return add(["-loop", "1", "-framerate", str(FPS), "-t", f"{t:.3f}", "-i", p])
    pre = f"fps={FPS},trim=start={L:.4f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2,setsar=1"
    blur = "scale=480:270:force_original_aspect_ratio=increase,crop=480:270,boxblur=10:2,scale=1920:1080,eq=brightness=-0.13:saturation=1.1"
    fl = []
    if is_img:
        fl.append(f"[0:v]{pre},format=yuv420p[v0]")
    elif lay == "blur":
        fl.append(f"[0:v]{pre},{blur},eq=brightness=-0.12[v0]")
    elif lay == "vertical":
        mk = loopimg(comp["mask_v"], D + 1); sh = add(["-i", comp["shadow_v"]])
        fl += [f"[0:v]{pre},split[pa][pb]", f"[pa]{blur}[bg]",
               f"[pb]scale={VW}:{H}:force_original_aspect_ratio=increase,crop={VW}:{H},format=yuva420p[fg0]",
               f"[{mk}:v]format=gray[mk]", "[fg0][mk]alphamerge[fg]", f"[bg][{sh}:v]overlay=0:0[b1]", f"[b1][fg]overlay={VX}:0:shortest=1[v0]"]
    elif lay == "split":
        src2 = sc["file2"] if os.path.isabs(sc["file2"]) else os.path.join(base, sc["file2"])
        i2 = add(["-ss", f"{sc.get('in2', sc['in']):.3f}", "-t", f"{D + 0.5:.3f}", "-i", src2])
        mh = loopimg(comp["mask_sh"], D + 1); mv = loopimg(comp["mask_v"], D + 1); sh = add(["-i", comp["shadow_s"]])
        x, y, w, h = SPL_H
        fl += [f"[0:v]{pre},split[pa][pb]", f"[pa]{blur}[bg]",
               f"[pb]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuva420p[h0]", f"[{mh}:v]format=gray[mh]", "[h0][mh]alphamerge[hf]",
               f"[{i2}:v]fps={FPS},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2,setsar=1,scale={VW}:{H}:force_original_aspect_ratio=increase,crop={VW}:{H},format=yuva420p[s0]",
               f"[{mv}:v]format=gray[mv]", "[s0][mv]alphamerge[sf]",
               f"[bg][{sh}:v]overlay=0:0[b1]", f"[b1][hf]overlay={x}:{y}:shortest=1[b2]", f"[b2][sf]overlay={SPL_V[0]}:{SPL_V[1]}:shortest=1[v0]"]
    else:
        fl.append(f"[0:v]{pre},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1[v0]")
    v0n = "v0"
    if sc.get("zooms"):                                # v2.2 크래시 줌(자막·출처는 줌 위에 얹힘)
        fl.append(f"[v0]{zoom_filter(sc['zooms'])}[v0z]"); v0n = "v0z"
    ov = []   # (입력번호, 시작, 끝)
    occ = sg.setdefault("occ", [])   # 화면에 얹힌 그림의 (시작, 끝, 그림 경로) — 상품 카드 자리 피하기용
    if lay == "vertical":
        sides = [("side_left", 48), ("side_right", VX + VW + 48)]
        for key, x in sides:
            v = sc.get(key)
            if not v: continue
            if isinstance(v, list) and v and (isinstance(v[0], dict)):
                for p, at in bubbles_pngs(v, x, 560, os.path.join(tmp, f"{tag}_{key}")): ov.append((add(["-i", p]), at, D + 1)); occ.append((at, D + 1, p))
            else:
                p = os.path.join(tmp, f"{tag}_{key}.png"); info_png(v, p, x, 560); ov.append((add(["-i", p]), 0, D + 1)); occ.append((0, D + 1, p))
    for j, s in enumerate(sc.get("subs", [])):        # [시작, 끝, "문장", (모양), (위치)] (장면 안에서의 초)
        st = s[3] if len(s) > 3 else "sub"; p = os.path.join(tmp, f"{tag}_s{j}.png")
        if st == "emotion":                            # 감정 자막: 옆쪽·기울임, 부드럽게 나타났다 사라짐
            emotion_png(s[2], p, s[4] if len(s) > 4 else "right"); i = loopimg(p, D + 1); fo_ = min(0.3, (s[1] - s[0]) / 3)
            fl.append(f"[{i}:v]format=rgba,fade=t=in:st={s[0]:.3f}:d={min(0.35, (s[1] - s[0]) / 3):.3f}:alpha=1,fade=t=out:st={s[1] - fo_:.3f}:d={fo_:.3f}:alpha=1[em{j}]")
            ov.append((f"em{j}", s[0], s[1])); occ.append((s[0], s[1], p))
        elif st == "sfx":                              # 효과음 자막: 0.3초 팝 프레임 → 마지막 장 유지
            pat = sfx_frames(s[2], os.path.join(tmp, f"{tag}_fx{j}"), tuple(s[4]) if len(s) > 4 else (0.5, 0.3))
            i = add(["-framerate", str(FPS), "-i", pat])
            fl.append(f"[{i}:v]format=rgba,tpad=stop_mode=clone:stop_duration={max(0.1, s[1] - s[0]):.3f},setpts=PTS+{s[0]:.3f}/TB[fx{j}]")
            ov.append((f"fx{j}", s[0], s[1])); occ.append((s[0], s[1], pat % (round(0.3 * FPS) - 1)))
        elif st in ("bracket", "situation", "narr"):   # v2.2 몰아보기 자막
            mola_sub_png(s[2], p, st, s[4] if len(s) > 4 else None); ov.append((add(["-i", p]), s[0], s[1])); occ.append((s[0], s[1], p))
        else: sub_png(s[2], p, st); ov.append((add(["-i", p]), s[0], s[1])); occ.append((s[0], s[1], p))
    for j, r_ in enumerate(sc.get("reacts", [])):      # v2.2 동네 형 반응 말풍선(오른쪽 아래)
        p = os.path.join(tmp, f"{tag}_r{j}.png"); react_png(r_, p); a_ = r_["at"]; b_ = a_ + r_.get("sec", 3)
        ov.append((add(["-i", p]), a_, b_)); occ.append((a_, b_, p))
    if sc.get("credit"):                               # 출처: 오른쪽 아래 구석, 장면 내내
        p = os.path.join(tmp, f"{tag}_cr.png"); credit_png(sc["credit"], p); ov.append((add(["-i", p]), 0, D + 1)); occ.append((0, D + 1, p))
    cx, cw = {"vertical": (VX + VW + 30, 586), "split": (40, 680)}.get(lay, (1180, 680))
    for j, c in enumerate(sc.get("comments", [])):    # {"at":초, "sec":4, "name":"", "text":""}
        p = os.path.join(tmp, f"{tag}_c{j}.png"); comment_png(c, p, j % 3, cx, cw); ov.append((add(["-i", p]), c["at"], c["at"] + c.get("sec", 4))); occ.append((c["at"], c["at"] + c.get("sec", 4), p))
    if sc.get("_stamp"):                                # 날짜 도장(장면 되감기 직후): 찍히고 → 머물고 → 0.4초 페이드 아웃
        ss = min(sc.get("stamp_sec", 1.8), D); pat, nfr = stamp_frames(sc["_stamp"], os.path.join(tmp, f"{tag}_stamp"), tuple(sc.get("stamp_pos", (0.8, 0.2))))
        i = add(["-framerate", str(FPS), "-i", pat])
        fl.append(f"[{i}:v]format=rgba,tpad=stop_mode=clone:stop_duration={max(0.1, ss - nfr / FPS):.3f},fade=t=out:st={max(0.1, ss - 0.4):.3f}:d=0.4:alpha=1[stp]")
        ov.append(("stp", 0, ss)); occ.append((0, ss, pat % (nfr - 1)))
    last = v0n
    for n, (idx, s0, s1) in enumerate(ov):
        src = f"[{idx}]" if isinstance(idx, str) else f"[{idx}:v]"
        fl.append(f"[{last}]{src}overlay=0:0:enable='between(t,{s0},{s1})'[o{n}]"); last = f"o{n}"
    if sg.get("card_overlay"):                         # 반투명 챕터 카드(영상은 계속 흐름)
        cs = sg["card_sec"]; ci = loopimg(sg["card_overlay"], cs)
        fl.append(f"[{ci}:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={cs - 0.35:.2f}:d=0.35:alpha=1[ck]")
        fl.append(f"[{last}][ck]overlay=0:0:eof_action=pass[oc]"); last = "oc"
    fl.append(f"[{last}]format=yuv420p,setsar=1[vout]")
    if has_a: ain = "[0:a]"
    else: ain = f"[{add(['-f', 'lavfi', '-t', f'{tot + 0.5:.3f}', '-i', 'anullsrc=r=48000:cl=stereo'])}:a]"
    fi, fo = max(0.02, L + sg["tin"]), max(0.02, T + sg["tout"])
    bl = sc.get("bleeps", [])                          # v2.2 삐-: 원음 줄이고 1kHz
    fl.append(f"{ain}aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={sc.get('volume', 1.0)},apad=whole_dur={tot:.4f},atrim=0:{tot:.4f},"
              f"afade=t=in:st=0:d={fi:.3f},afade=t=out:st={tot - fo:.4f}:d={fo:.3f}" + "".join(f",volume=0.04:enable='between(t,{L + b['at']:.3f},{L + b['at'] + b.get('dur', 0.5):.3f})'" for b in bl)
              + ("[a0]" if bl else "[aout]"))
    if bl:
        bp = []
        for j, b in enumerate(bl):
            bi = add(["-f", "lavfi", "-t", f"{b.get('dur', 0.5):.3f}", "-i", f"sine=frequency={_STD()['style_A']['bleep_hz']}:sample_rate=48000"])
            fl.append(f"[{bi}:a]aformat=sample_fmts=fltp:channel_layouts=stereo,volume=0.32,afade=t=in:d=0.01,adelay={int((L + b['at']) * 1000)}:all=1[bp{j}]"); bp.append(f"[bp{j}]")
        fl.append("[a0]" + "".join(bp) + f"amix=inputs={len(bp) + 1}:normalize=0:duration=first,atrim=0:{tot:.4f}[aout]")
    sg["v"] = os.path.join(tmp, f"{tag}.mp4"); sg["a"] = os.path.join(tmp, f"{tag}.wav")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fl), "-map", "[vout]", "-an", "-frames:v", str(N), *VTMP, sg["v"],
         "-map", "[aout]", "-vn", "-c:a", "pcm_s16le", sg["a"]])

def render_still(png, D, path, fade_in=False):
    N = round(D * FPS); vf = "format=yuv420p" + (",fade=in:0:12" if fade_in else "")
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", png, "-vf", vf, "-frames:v", str(N), *VTMP, path])

def render_resolve(text, D, fade, tmp):
    """끝맺음 결심 한 줄: 검은 화면 위에 한 줄이 fade초 동안 천천히 나타남."""
    p = os.path.join(tmp, "resolve.png"); out = os.path.join(tmp, "resolve.mp4"); sub_png(text, p, "resolve")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={D + 0.5:.3f}", "-loop", "1", "-framerate", str(FPS), "-t", f"{D + 0.5:.3f}", "-i", p,
         "-filter_complex", f"[1:v]format=rgba,fade=t=in:st=0:d={fade:.3f}:alpha=1[t];[0:v][t]overlay=0:0,format=yuv420p[v]",
         "-map", "[v]", "-frames:v", str(round(D * FPS)), *VTMP, out])
    return out

def render_rewind(prev, sg, tmp, tag):
    """되감기: 앞 장면 끝 1.2초를 거꾸로·빠르게(0.5초)."""
    sg["v"] = os.path.join(tmp, f"{tag}.mp4"); sg["a"] = os.path.join(tmp, f"{tag}.wav")
    run(["ffmpeg", "-y", "-sseof", "-1.2", "-i", prev["v"], "-vf",
         f"reverse,setpts=0.4*PTS,fps={FPS},eq=saturation=0.3:contrast=1.2,noise=alls=25:allf=t,tpad=stop_mode=clone:stop_duration=1",
         "-frames:v", str(round(sg["dur"] * FPS)), *VTMP, sg["v"]])
    st = prev["lead"] + prev["dur"] - 1.2
    run(["ffmpeg", "-y", "-ss", f"{max(0, st):.3f}", "-t", "1.2", "-i", prev["a"], "-af",
         f"areverse,atempo=2.0,atempo=1.25,volume=0.5,apad=whole_dur={sg['dur']:.3f},atrim=0:{sg['dur']:.3f},afade=t=out:st={sg['dur'] - sg['tout'] - 0.02:.3f}:d={sg['tout'] + 0.02:.3f}",
         "-c:a", "pcm_s16le", sg["a"]])

# ---------------- 잇기(xfade 체인) ----------------
def chain(files, joins, starts, out, extra_in=(), tail="", final_map=(), enc=VTMP, total=None):
    """files[i] 를 joins[i](i>=1, (종류, 초)) 로 잇는다. starts[i] = 체인 안 시작 초."""
    inp = []
    for f in files: inp += ["-i", f]
    inp += list(extra_in)
    g = [f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps={FPS},settb=1/{FPS},format=yuv420p,setsar=1[i{i}]" for i in range(len(files))]; last = "i0"
    for i in range(1, len(files)):
        kind, d = joins[i]
        if kind == "cut": g.append(f"[{last}][i{i}]concat=n=2:v=1:a=0,fps={FPS},settb=1/{FPS}[j{i}]")
        else: g.append(f"[{last}][i{i}]xfade=transition={xf(kind)}:duration={d:.4f}:offset={starts[i]:.4f}[j{i}]")
        last = f"j{i}"
    g.append(f"[{last}]{tail}" if "[vout]" in tail else f"[{last}]{tail or 'null'}[vout]")
    cmd = ["ffmpeg", "-y", *inp, "-filter_complex", ";".join(g), "-map", "[vout]", *final_map, *enc]
    if total: cmd += ["-t", f"{total:.4f}"]
    run(cmd + [out])

def layout_of(sc): return sc.get("layout", "vertical" if sc.get("image") else "horizontal")

def narration_fallback(spec, base):
    """v2.2: 내레이션 파일이 없으면 글(text/_text)을 'narr' 자막으로 대신(파일 생기면 그대로 소리로)."""
    n_sub = 0
    for ch in spec.get("chapters", []):
        for sc in ch.get("scenes", []):
            ns = sc.get("narration"); ns = [ns] if isinstance(ns, dict) else (ns or []); keep = []
            for n in ns:
                f = n.get("file"); ok = bool(f) and os.path.exists(f if os.path.isabs(f) else os.path.join(base, f))
                txt = n.get("text") or n.get("_text")
                if ok or not txt: keep.append(n); continue
                d = n.get("_예상초") or n.get("sec") or round(0.8 + len(txt) * 0.14, 2)
                sc.setdefault("subs", []).append([n.get("at", 0), n.get("at", 0) + d, txt, "narr"]); n_sub += 1
            if isinstance(sc.get("narration"), (list, dict)): sc["narration"] = keep
    return n_sub

def build(spec, base):
    tmp = spec.get("_tmp_dir") or os.path.join(base, "_tmp"); out = spec.get("_out_dir") or os.path.join(base, "out")   # v2.2: 결과 폴더 지정 가능
    os.makedirs(tmp, exist_ok=True); os.makedirs(out, exist_ok=True)
    n_narr_sub = narration_fallback(spec, base)
    if n_narr_sub: print(f"내레이션 파일 없음 → 자막으로 대신: {n_narr_sub}개")
    series = spec.get("series", "덕심저장소"); xd = spec.get("xfade_sec", 0.3); fd = spec.get("fold_sec", 0.5)
    # 1) 재료 그림
    comp = {"mask_v": os.path.join(tmp, "mask_v.png"), "mask_sh": os.path.join(tmp, "mask_sh.png"),
            "shadow_v": os.path.join(tmp, "shadow_v.png"), "shadow_s": os.path.join(tmp, "shadow_s.png")}
    rmask_png(VW, H, 36, comp["mask_v"]); rmask_png(SPL_H[2], SPL_H[3], 30, comp["mask_sh"])
    shadow_png([(VX, 0, VW, H)], comp["shadow_v"]); shadow_png([SPL_H, (SPL_V[0], 0, VW, H)], comp["shadow_s"])
    # 2) 장면 목록(시간표)
    segs = []
    def scene_seg(sc, ch, tag, label):
        if sc.get("image"): sc.setdefault("in", 0); sc.setdefault("out", sc["in"] + sc.get("sec", 4))
        return {"kind": "scene", "sc": sc, "layout": layout_of(sc), "dur": fr(sc["out"] - sc["in"]), "ch": ch, "tag": tag, "label": label}
    op = spec.get("opening") or {}
    if op.get("highlight"):                              # 0~3초 하이라이트: 대사 자막 크게 가운데
        h = dict(op["highlight"]); d = fr(h["out"] - h["in"])
        if h.get("line"): h["subs"] = [[0, d + 1, h["line"], "big"]] + h.get("subs", [])
        segs.append(scene_seg(h, 0, "hl", "오프닝 하이라이트"))
    for ci, ch in enumerate(spec["chapters"], 1):
        style = ch.get("card_style", spec.get("card_style", "overlay"))
        if ci > 1 and ch.get("rewind", spec.get("rewind", False)): segs.append({"kind": "rewind", "layout": segs[-1]["layout"], "dur": fr(0.5), "ch": ci})
        use_card = ch.get("card", True) is not False        # v2.1: "card": false → 챕터 카드 생략
        card = os.path.join(tmp, f"card{ci}.png")
        if use_card: card_png(ch, ci, card, series, overlay=(style != "full"))
        if use_card and style == "full": segs.append({"kind": "card", "layout": "horizontal", "png": card, "dur": fr(spec.get("card_sec", 2.5)), "ch": ci})
        for si, sc in enumerate(ch["scenes"]):
            rw = sc.get("rewind")                           # v2.1: 장면 되감기(0.5초 역재생 + 날짜 도장, 챕터 카드 없이)
            if rw:
                stamp = sc.get("date") or (rw if isinstance(rw, str) else None)
                if stamp: sc["_stamp"] = stamp
                else: print(f"⚠️ {ci}장 {si + 1}번 장면 rewind: 날짜(\"date\")가 없어 도장 없이 되감기만")
                if segs and segs[-1]["kind"] == "scene": segs.append({"kind": "rewind", "layout": segs[-1]["layout"], "dur": fr(0.5), "ch": ci, "scene_rw": True})
            sg = scene_seg(sc, ci, f"sc{ci}_{si}", f"{ci}장 {si + 1}번" + (" (사진)" if sc.get("image") else "") + (" (되감기)" if rw else ""))
            if si == 0 and use_card and style != "full": sg["card_overlay"] = card; sg["card_sec"] = min(spec.get("overlay_card_sec", 2.0), sg["dur"])
            segs.append(sg)
    en = spec.get("ending") or {}
    if en.get("line") or en.get("ask"):                  # 끝 화면 앞: 주제 한 줄 → 질문 자막 (마지막 장면을 흐리게 이어 깔고)
        last = [s for s in segs if s["kind"] == "scene"][-1]["sc"]
        ls = fr(en.get("line_sec", 3)) if en.get("line") else 0; as_ = fr(en.get("ask_sec", 3.5)) if en.get("ask") else 0; d = ls + as_
        o = {"layout": "blur", "volume": en.get("volume", 0.6), "subs": []}
        if last.get("image"): o.update(image=last["image"], **{"in": 0, "out": d})
        else:
            sd = probe(src_of(last, base))[1]; st = last["out"] if sd >= last["out"] + d + 0.6 else max(0.0, min(last["in"], sd - d - 0.6))
            o.update(file=last["file"], **{"in": st, "out": st + d})
        if ls: o["subs"].append([0, ls, en["line"], "big"])
        if as_: o["subs"].append([ls, d + 1, en["ask"], "ask"])
        segs.append(scene_seg(o, None, "outro", "엔딩 질문"))
    if en.get("resolve"):                                # 결심 한 줄: 검은 화면 + 2초 페이드인 → 끝 화면
        segs.append({"kind": "resolve", "layout": "horizontal", "dur": fr(max(en.get("resolve_sec", 3.5), en.get("resolve_fade", 2.0) + 0.5)), "ch": None})
    segs.append({"kind": "end", "layout": "horizontal", "dur": fr(spec.get("end_sec", 8)), "ch": None})
    credits = []
    for s in [op.get("highlight") or {}] + [sc for ch in spec["chapters"] for sc in ch["scenes"]]:
        if s.get("credit") and s["credit"] not in credits: credits.append(s["credit"])
    for s in spec.get("sources", []):
        if s not in credits: credits.append(s)
    if credits and spec.get("sources_screen", True):     # 마지막 '영상 출처' 화면 4초
        segs.append({"kind": "credits", "layout": "horizontal", "dur": fr(spec.get("sources_sec", 4)), "ch": None})
    for i, sg in enumerate(segs):     # 전환 종류·길이
        sg.setdefault("lead", 0.0); sg.setdefault("tail", 0.0)
        if i == 0: sg["join"] = ("cut", 0.0); continue
        p = segs[i - 1]; want = sg.get("sc", {}).get("transition")
        if sg["kind"] == "rewind": j = ("cut", 0.0)
        elif p["kind"] == "rewind": j = ("dissolve", 0.2)
        elif want == "cut": j = ("cut", 0.0)
        elif "resolve" in (sg["kind"], p["kind"]): j = ("dissolve", xd)
        elif p["layout"] == "horizontal" and sg["layout"] == "vertical" and want != "dissolve": j = ("fold", fd)
        elif p["layout"] == "vertical" and sg["layout"] in ("horizontal", "blur") and want != "dissolve": j = ("unfold", fd)
        else: j = ("dissolve", xd)
        if j[0] != "cut": j = (j[0], fr(min(j[1], p["dur"] / 2.2, sg["dur"] / 2.2)))
        sg["join"] = j
    for i, sg in enumerate(segs):
        sg["tin"] = sg["join"][1]; sg["tout"] = segs[i + 1]["join"][1] if i + 1 < len(segs) else 0.0
        if sg["kind"] == "scene" and not sg["sc"].get("image"):
            sc = sg["sc"]; _, sdur = probe(src_of(sc, base))
            if i > 0: sg["lead"] = max(0.0, min(sc.get("audio_lead", 0), sc["in"], segs[i - 1]["dur"] / 2))
            sg["tail"] = max(0.0, min(sc.get("audio_tail", 0), (sdur - sc["out"]) if sdur else 0, (segs[i + 1]["dur"] / 2) if i + 1 < len(segs) else 0))
    t = 0.0
    for i, sg in enumerate(segs):
        if i: t += segs[i - 1]["dur"] - sg["join"][1]
        sg["S"] = t
    total = segs[-1]["S"] + segs[-1]["dur"]
    E = next(s["S"] for s in segs if s["kind"] == "end")   # E = 끝 화면 시작
    PE = next((s["S"] for s in segs if s["kind"] == "resolve"), E)   # 진행 막대 끝(결심 화면부터 숨김)
    # 오프닝 질문: 25초 근처(노란 강조, 위쪽) — 영상 전체 위에 얹음
    gov = []
    if op.get("question"):
        h0 = segs[0]["dur"] if op.get("highlight") else 0
        qa = max(h0 + 1, min(op.get("question_at", 25), E - 5)); qd = op.get("question_sec", 4)
        qp = os.path.join(tmp, "op_question.png"); sub_png(op["question"], qp, "question"); gov.append((qp, qa, qa + qd, plain(op["question"])))
    # 3) 장면마다 ffmpeg 1회
    srt = [(a, b, t) for _, a, b, t in gov]
    endcfg = dict(spec.get("end", {}))
    for k2 in ("next", "next_date"):
        if en.get(k2): endcfg.setdefault(k2, en[k2])
    for i, sg in enumerate(segs):
        if sg["kind"] == "scene":
            render_scene(sg, sg["sc"], base, tmp, sg["tag"], comp)
            srt += [(sg["S"] + s[0], sg["S"] + min(s[1], sg["dur"]), ("[" + plain(s[2]) + "]") if len(s) > 3 and s[3] == "sfx" else plain(s[2])) for s in sg["sc"].get("subs", [])]
        elif sg["kind"] == "rewind": render_rewind(segs[i - 1], sg, tmp, f"rw{i}")
        elif sg["kind"] == "resolve":
            sg["v"] = render_resolve(en["resolve"], sg["dur"], en.get("resolve_fade", 2.0), tmp); srt.append((sg["S"], sg["S"] + sg["dur"], plain(en["resolve"])))
        elif sg["kind"] == "card": sg["v"] = os.path.join(tmp, f"card{sg['ch']}.mp4"); render_still(sg["png"], sg["dur"], sg["v"])
        elif sg["kind"] == "credits":
            cp = os.path.join(tmp, "sources.png"); sources_png(credits, cp, series); sg["v"] = os.path.join(tmp, "sources.mp4"); render_still(cp, sg["dur"], sg["v"])
        else:
            ep = os.path.join(tmp, "end.png"); end_png(endcfg, ep, series); sg["v"] = os.path.join(tmp, "end.mp4"); render_still(ep, sg["dur"], sg["v"])
    srt.sort()
    # 4) 소리: 장면 소리를 제자리(J/L컷 포함)에 놓고 섞기 + 내레이션 덕킹 + 배경음악
    nars = [dict(n) for n in (spec.get("narration") or [])] if isinstance(spec.get("narration"), list) else ([dict(spec["narration"])] if spec.get("narration") else [])
    for sg in segs:
        n = sg.get("sc", {}).get("narration")
        for x in ([n] if isinstance(n, dict) else (n or [])): x = dict(x); x["at"] = sg["S"] + x.get("at", 0); nars.append(x)
    for n in nars:
        n["path"] = n["file"] if os.path.isabs(n["file"]) else os.path.join(base, n["file"]); n["len"] = probe(n["path"])[1]
    def gather(key):   # 영상 전체 기준(맨 위) + 장면 안 기준(장면 시작 S 더함)
        out_ = [dict(x) for x in (spec.get(key) or [])]
        for sg in segs:
            for x in (sg.get("sc", {}).get(key) or []): x = dict(x); x["at"] = sg["S"] + x.get("at", 0); out_.append(x)
        return out_
    sfxs = gather("sfx")                               # 효과음 파일(같은 시각 효과음 자막과 짝)
    for x in sfxs:
        if x.get("file"): x["path"] = x["file"] if os.path.isabs(x["file"]) else os.path.join(base, x["file"])
        else: import v2_fx; x["path"] = v2_fx.sfx_path(x, base)   # v2.2 이름 효과음(crow 등)
    cuts = gather("music_cut")                         # 음악 끊기(강조용 정적): 배경음악만 0
    mc = "0"
    for c in cuts:
        a, b, f1, f2 = c["at"], c["at"] + c.get("sec", 1.0), c.get("fade_out", 0.12), c.get("fade_in", 0.6)
        mc = f"max({mc},clip(min((t-{a - f1:.3f})/{f1},({b + f2:.3f}-t)/{f2}),0,1))"
    mcut = f",volume='1-{mc}':eval=frame" if cuts else ""
    ain = []; ag = []; k = 0
    for sg in segs:
        if not sg.get("a"): continue
        ain += ["-i", sg["a"]]; ag.append(f"[{k}:a]adelay={int(round((sg['S'] - sg['lead']) * 1000))}:all=1[s{k}]"); k += 1
    ag.append("".join(f"[s{j}]" for j in range(k)) + f"amix=inputs={k}:normalize=0:duration=longest,apad=whole_dur={total:.4f},atrim=0:{total:.4f}[orig]" if k > 1
              else f"[s0]apad=whole_dur={total:.4f},atrim=0:{total:.4f}[orig]")
    G = 10 ** (spec.get("duck_db", -14) / 20); r1, r2 = 0.25, 0.4; m = "0"
    for n in nars:
        a, b = n["at"], n["at"] + n["len"]; m = f"max({m},clip(min((t-{a - r1:.3f})/{r1},({b + r2:.3f}-t)/{r2}),0,1))"
    duck = f"volume='1-{1 - G:.4f}*{m}':eval=frame" if nars else "anull"
    ag.append(f"[orig]{duck}[od]"); mix = ["[od]"]
    if spec.get("bgm"):
        ain += ["-stream_loop", "-1", "-i", os.path.join(base, spec["bgm"])]
        ag.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.4f},volume={spec.get('bgm_volume', 0.12)},{duck}{mcut},afade=t=out:st={total - 3:.3f}:d=3[bg]"); mix.append("[bg]"); k += 1
    for n in nars:
        ain += ["-i", n["path"]]
        ag.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={n.get('volume', 1.0)},adelay={int(round(n['at'] * 1000))}:all=1[n{k}]"); mix.append(f"[n{k}]"); k += 1
    for x in sfxs:
        ain += ["-i", x["path"]]
        ag.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={x.get('volume', 1.0)},adelay={int(round(x['at'] * 1000))}:all=1[x{k}]"); mix.append(f"[x{k}]"); k += 1
    ag.append("".join(mix) + (f"amix=inputs={len(mix)}:normalize=0:duration=first," if len(mix) > 1 else "") + f"alimiter=limit=0.97,atrim=0:{total:.4f}[aout]")
    fa = os.path.join(tmp, "final.wav")
    run(["ffmpeg", "-y", *ain, "-filter_complex", ";".join(ag), "-map", "[aout]", "-c:a", "pcm_s16le", fa])
    # 5) 영상 잇기 (+ 진행 막대) — 장면이 많으면 묶음으로
    tail = ""; extra = []
    if spec.get("progress"):
        bounds = []
        for sg in segs:
            if sg["ch"] and (not bounds or bounds[-1][0] != sg["ch"]): bounds.append((sg["ch"], sg["S"]))
        trk, tik = progress_pngs([b for _, b in bounds], PE, tmp)
        extra = ["-i", trk, "-i", tik]
    final = os.path.join(out, spec["out"] + ".mp4")
    groups = [list(range(i, min(i + BATCH, len(segs)))) for i in range(0, len(segs), BATCH)]
    if len(groups) == 1: files, joins, starts = [s["v"] for s in segs], [s["join"] for s in segs], [s["S"] for s in segs]
    else:
        files, joins, starts = [], [], []
        for gi, gr in enumerate(groups):
            s0 = segs[gr[0]]["S"]; bf = os.path.join(tmp, f"batch{gi}.mp4")
            chain([segs[i]["v"] for i in gr], [segs[i]["join"] for i in gr], [segs[i]["S"] - s0 for i in gr], bf, total=segs[gr[-1]]["S"] + segs[gr[-1]]["dur"] - s0)
            files.append(bf); joins.append(segs[gr[0]]["join"]); starts.append(s0)
    n = len(files); parts = ["null[g0]"]; cur = "g0"; idx = n
    if spec.get("progress"):   # 바탕 막대 → 노란 채움(시간 따라 늘어남) → 챕터 눈금, 끝 화면에선 숨김
        parts += [f"[{cur}][{idx}:v]overlay=0:0:enable='lt(t,{PE:.3f})'[p1]", f"color=c=0xFFD640:s={W}x6:r={FPS}[pf]",
                  f"[p1][pf]overlay=x='-w+w*min(t/{PE:.3f},1)':y=1:shortest=1:enable='lt(t,{PE:.3f})'[p2]", f"[p2][{idx + 1}:v]overlay=0:0:enable='lt(t,{PE:.3f})'[p3]"]
        cur = "p3"; idx += 2
    for j, (png, a, b, _) in enumerate(gov):   # 영상 전체 시각 기준 자막(오프닝 질문)
        extra += ["-i", png]; parts.append(f"[{cur}][{idx}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[q{j}]"); cur = f"q{j}"; idx += 1
    # 상품 카드(제휴 QR): 왼쪽 아래, 0.3초 슬라이드 인 · 0.3초 페이드 아웃. 그 시간의 자막·출처·말풍선을 피해 자리 잡기
    pcards = gather("product_cards"); occ_all = [(a, b, Image.open(png).getbbox()) for png, a, b, _ in gov]
    for sg in segs:
        occ_all += [(sg["S"] + s0, sg["S"] + s1, Image.open(pp).getbbox()) for s0, s1, pp in sg.get("occ", [])]
    nonscene = [(s["S"], s["S"] + s["dur"], s["kind"]) for s in segs if s["kind"] != "scene"]
    for j, c in enumerate(pcards):
        a = max(0.0, c.get("at", 0)); sec = max(1.0, c.get("sec", 6)); b = min(a + sec, total); sec = b - a
        pp = os.path.join(tmp, f"pcard{j}.png"); size = product_card_png(c, pp)
        x0, y0, side, ok = place_card(size, a, b, occ_all); c.update(_x=x0, _y=y0, _side=side, _ok=ok, _at=a, _end=b)
        c["_over"] = sorted({k for s0, s1, k in nonscene if s0 < b and s1 > a})
        occ_all.append((a, b, (x0, y0, x0 + size[0], y0 + size[1])))   # 카드끼리도 안 겹치게
        u = f"pow(1-clip((t-{a:.3f})/0.3,0,1),3)"
        xe = f"{x0}-({x0}+w)*{u}" if side == "left" else f"{x0}+(main_w-{x0})*{u}"
        extra += ["-loop", "1", "-framerate", str(FPS), "-t", f"{sec:.3f}", "-i", pp]
        parts += [f"[{idx}:v]format=rgba,fade=t=out:st={max(0.0, sec - 0.3):.3f}:d=0.3:alpha=1,setpts=PTS+{a:.3f}/TB[pc{j}]",
                  f"[{cur}][pc{j}]overlay=x='{xe}':y={y0}:eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[pq{j}]"]
        cur = f"pq{j}"; idx += 1
    parts.append(f"[{cur}]null[vout]"); tail = ";".join(parts)
    fin_in = extra + ["-i", fa]; ai = idx
    chain(files, joins, starts, final, extra_in=fin_in, tail=tail, final_map=["-map", f"{ai}:a"], enc=VENC + AENC + ["-movflags", "+faststart"], total=total)
    # 6) 자막·썸네일·점검표
    sp = os.path.join(out, spec["out"] + ".srt")
    open(sp, "w", encoding="utf-8").write("".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(srt, 1)))
    tp = None
    if spec.get("thumb"): tp = os.path.join(out, spec["out"] + "_thumb.jpg"); thumb_png(spec["thumb"], os.path.join(base, spec["thumb"]["photo"]), tp)
    # 설명란: 요약 → 챕터 타임스탬프(실제 렌더 시각) → 감사한 출처 → 해시태그 → 3개 언어 요약
    def ts(t): t = int(t + 0.5); h, r = divmod(t, 3600); return (f"{h}:{r // 60:02}:{r % 60:02}" if h else f"{r // 60}:{r % 60:02}")
    marks = []
    if segs[0]["ch"] == 0: marks.append((0.0, spec.get("opening_label", "오프닝")))
    for ci, ch in enumerate(spec["chapters"], 1):
        marks.append((next(s["S"] for s in segs if s["ch"] == ci), f"{ci}장 · {ch['title']}"))
    if any(s["tag"] == "outro" for s in segs if s["kind"] == "scene"): marks.append((next(s["S"] for s in segs if s.get("tag") == "outro"), spec.get("ending_label", "마무리")))
    marks[0] = (0.0, marks[0][1])
    short_ch = [m[1] for m, nx in zip(marks, marks[1:] + [(E, "")]) if nx[0] - m[0] < 10]
    i18n = spec.get("summary_i18n", {}); LB = {"en": "[English]", "ja": "[日本語]", "zh-TW": "[繁體中文]"}
    tags = " ".join(t if t.startswith("#") else "#" + t for t in spec.get("hashtags", []))
    desc = []
    if pcards:                                         # 상품 링크(광고) — 설명란 맨 위에 고지 + 목록
        if any("coupang" in str(c.get("url", "")).lower() for c in pcards): desc += [COUPANG_NOTICE, ""]
        desc += [f"■ 상품 링크 ({AD_MARK})"] + [f"- {c['name']}" + (f" ({c['price']})" if c.get("price") else "") + f" ({ts(c['_at'])}) : {c['url']}" for c in pcards] + [""]
    desc += [spec.get("summary", "").strip(), "", "■ 챕터"] + [f"{ts(a)} {t}" for a, t in marks] + ["", "■ 감사한 출처"] + [f"- {c}" for c in credits]
    if tags: desc += ["", tags]
    for k2 in ("en", "ja", "zh-TW"):
        if i18n.get(k2): desc += ["", LB[k2], i18n[k2].strip()]
    dp = os.path.join(out, spec["out"] + "_설명란.txt"); open(dp, "w", encoding="utf-8").write("\n".join(desc).strip() + "\n")
    lim = spec.get("max_still_sec", 8)
    longs = [f"{s['label']}({s['dur']:.1f}초)" for s in segs if s["kind"] == "scene" and s["dur"] > lim and not s["sc"].get("long_ok")]
    excl = [(s["S"], s["S"] + s["dur"]) for s in segs if s["kind"] in ("card", "end", "credits", "resolve")]
    blk = black_check(final, excl)
    hl = segs[0] if segs[0]["ch"] == 0 else None
    nocred = [s["label"] for s in segs if s["kind"] == "scene" and s["tag"] != "outro" and not s["sc"].get("credit") and not s["sc"].get("own")]
    nocard = [str(ci) for ci, ch in enumerate(spec["chapters"], 1) if ch.get("card", True) is False]
    chk = [("챕터 카드(" + ("오버레이" if spec.get("card_style", "overlay") != "full" else "전체 화면") + ")" + (f" — 생략: {','.join(nocard)}장" if nocard else ""), True),
           (f"오프닝 하이라이트(0~{hl['dur']:.1f}초)" if hl else "오프닝 하이라이트(0~3초)", bool(hl) and hl["dur"] <= 3.5),
           (f"오프닝 질문 자막({gov[0][1]:.0f}초)" if gov else "오프닝 질문 자막(25초 근처)", bool(gov)),
           ("엔딩 주제 한 줄 + 질문 자막", bool(en.get("line") and en.get("ask"))),
           ("끝맺음 결심 한 줄(검은 화면 페이드인)", bool(en.get("resolve"))),
           ("끝 화면(구독·좋아요·알림·다음 편)", bool(endcfg.get("next"))),
           ("배경음악", bool(spec.get("bgm"))), ("출처(쓴 영상 목록)", bool(credits)),
           ("장면마다 구석 출처 표기" + (" — 없음: " + ", ".join(nocred) if nocred else ""), not nocred),
           (f"영상 출처 화면({spec.get('sources_sec', 4)}초)", any(s["kind"] == "credits" for s in segs)),
           ("설명란 3개 언어 요약(en·ja·zh-TW)", all(i18n.get(k2) for k2 in ("en", "ja", "zh-TW"))),
           ("설명란 요약·해시태그", bool(spec.get("summary") and tags)), ("썸네일", bool(tp)),
           ("팬 영상 양해 확인", bool(spec.get("consent_checked"))),
           (f"장면 사이 검은 화면 0초 (검출 {blk:.2f}초, 카드·결심·끝·출처 화면 제외)", blk < 0.05)]
    bans = [w.lower() for w in BAN_WORDS + list(spec.get("product_ban_words", []))]
    banned = [f"{c['name']}({w})" for c in pcards for w in bans if w in (str(c.get("name", "")) + " " + str(c.get("label", ""))).lower()]
    pchk = []
    if pcards:
        cp_ = [c for c in pcards if "coupang" in str(c.get("url", "")).lower()]
        pchk += [(f"상품 카드: {len(pcards)}개, 광고 표시", True)]
        if cp_: pchk.append((f"쿠팡 파트너스 고지 문구(설명란 맨 위, 쿠팡 링크 {len(cp_)}개)", True))
        pchk.append(("상품 판매 제한 품목(주류·담배·도박·성인)" + (" — 걸림: " + ", ".join(banned) if banned else " 없음"), not banned))
        lifted = [f"{c['name']}({c['_side']}, y={c['_y']})" for c in pcards if not c["_ok"]]
        pchk.append(("상품 카드 자막·출처와 겹침 없음" + (" — 겹침: " + ", ".join(lifted) if lifted else ""), not lifted))
        for c in pcards:
            if c["_over"]: print(f"⚠️ 상품 카드 '{c['name']}'가 장면 아닌 화면({', '.join(c['_over'])}) 위에 걸침 — at 확인")
    allsubs = [s for sg in segs if sg["kind"] == "scene" for s in sg["sc"].get("subs", [])]
    n_em = sum(1 for s in allsubs if len(s) > 3 and s[3] == "emotion"); n_fx = sum(1 for s in allsubs if len(s) > 3 and s[3] == "sfx")
    kinds = {}
    for s in segs[1:]: kinds[s["join"][0]] = kinds.get(s["join"][0], 0) + 1
    print(f"영상: {final} ({total/60:.1f}분, {total:.2f}초)\n자막: {sp}\n썸네일: {tp}")
    print("전환: " + ", ".join(f"{ {'dissolve':'디졸브','fold':'접힘','unfold':'펼침','cut':'컷'}[k]} {v}" for k, v in kinds.items())
          + (f" · 내레이션 {len(nars)}개(덕킹 {spec.get('duck_db', -14)}dB)" if nars else ""))
    for nm, ok in chk: print(("✅ " if ok else "❌ 빠짐: ") + nm)
    for nm, ok in pchk: print(f"{nm} {'✅' if ok else '❌'}")
    if not pcards: print("상품 카드: 0개 (product_cards 없음)")
    print(("⚠️ 긴 정지 장면(" + str(lim) + "초 넘음, 컷 리듬 확인): " + ", ".join(longs)) if longs else f"✅ 긴 정지 장면 없음({lim}초 이하)")
    srw = [s for s in segs if s.get("scene_rw")]
    if srw or any(s.get("sc", {}).get("rewind") for s in segs):
        print(f"장면 되감기: {len(srw)}회 (" + ", ".join(f"{s['S']:.1f}초" for s in srw) + ") · 날짜 도장 " + str(sum(1 for s in segs if s.get("sc", {}).get("_stamp"))) + "개")
    print(f"기준서 추가: 감정 자막 {n_em}개 · 효과음 자막 {n_fx}개(효과음 소리 {len(sfxs)}개) · 음악 끊기 {len(cuts)}곳"
          + (" ⚠️ 배경음악이 없어 음악 끊기는 효과 없음" if cuts and not spec.get("bgm") else ""))
    if short_ch: print("⚠️ 유튜브 챕터는 10초 이상이어야 표시됨 — 짧은 챕터: " + ", ".join(short_ch))
    print(f"설명란: {dp}")
    return {"final": final, "total": total, "segs": segs, "product_cards": pcards, "nars": nars, "sfx": sfxs, "music_cut": cuts, "black": blk, "desc": dp, "marks": marks}

def black_check(path, excl):
    """검은 화면 검사(카드·끝 화면 구간 제외) → 남은 검은 초."""
    r = subprocess.run(["ffmpeg", "-i", path, "-vf", "scale=480:-2,blackdetect=d=0.03:pix_th=0.08", "-an", "-f", "null", "-"], capture_output=True, text=True)
    tot = 0.0
    for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr):
        a, b = float(a), float(b); cut = sum(max(0, min(b, y) - max(a, x)) for x, y in excl); tot += max(0, (b - a) - cut)
    return tot

def make_test_media(d):
    """시험용: 가로 2개(1920x1080) + 세로 1개(1080x1920) + 사인파 소리 + 내레이션 대용 3초 사인파."""
    os.makedirs(d, exist_ok=True); lv = lambda s: ["-f", "lavfi", "-i", s]
    for name, v, a in [("h1.mp4", "testsrc=s=1920x1080:r=30:d=12", "sine=f=440:r=48000:d=12"),
                       ("h2.mp4", "smptehdbars=s=1920x1080:r=30:d=12", "sine=f=440:r=48000:d=12"),
                       ("v1.mp4", "testsrc2=s=1080x1920:r=30:d=12", "sine=f=440:r=48000:d=12")]:
        run(["ffmpeg", "-y", *lv(v), *lv(a), "-shortest", *VTMP, *AENC, os.path.join(d, name)])
    run(["ffmpeg", "-y", *lv("sine=f=1000:r=48000:d=3"), "-c:a", "libmp3lame", "-b:a", "128k", os.path.join(d, "narration.mp3")])
    run(["ffmpeg", "-y", *lv("sine=f=1600:r=48000:d=0.3"), "-af", "afade=t=out:st=0.05:d=0.25", "-c:a", "pcm_s16le", os.path.join(d, "sfx_pop.wav")])   # 효과음 대용
    im = Image.new("RGB", (1080, 1350), (250, 250, 252)); dr = ImageDraw.Draw(im)   # SNS 캡처 대용(세로 사진)
    dr.rectangle([0, 0, 1080, 140], fill=(150, 80, 230)); dr.text((50, 40), "SNS 캡처 (시험)", font=F(FB, 56), fill=WH)
    for i in range(6):
        y = 200 + i * 185; dr.ellipse([50, y, 140, y + 90], fill=(200, 200, 215))
        dr.text((170, y), f"팬{i + 1}", font=F(FB, 40), fill=(30, 20, 60)); dr.text((170, y + 56), "응원 댓글 시험 문장입니다", font=F(FM, 38), fill=(60, 60, 80))
    im.save(os.path.join(d, "capture.png"))
    print("시험 재료:", d)

if __name__ == "__main__":
    if sys.argv[1] == "--test-media": make_test_media(sys.argv[2]); sys.exit()
    p = sys.argv[1]; sp_ = json.load(open(p, encoding="utf-8"))
    if len(sys.argv) > 2: sp_["_out_dir"] = os.path.abspath(sys.argv[2]); sp_["_tmp_dir"] = os.path.join(sp_["_out_dir"], "_tmp_" + sp_["out"])
    res = build(json.loads(json.dumps(sp_)), os.path.dirname(os.path.abspath(p)))
    if sp_.get("thumb_v2"):                           # v2.2 썸네일(standard_v2 thumbnail_v2) 1280x720
        import v2_fx, expose_factory as ef, cv2
        tv = sp_["thumb_v2"]; bgr = ef.grab(tv["frame"]["file"], tv["frame"]["t"])
        if tv.get("zoom"): bgr = ef.zoom_at(bgr, *tv["zoom"])
        tp_ = os.path.join(os.path.dirname(res["final"]), sp_["out"] + "_thumb.png")
        v2_fx.thumb_v2(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)), dict(tv, source=tv.get("source", (sp_.get("credits") or [""])[0] if sp_.get("credits") else ""), test=sp_.get("test_label")), (1280, 720), tp_)
        print("썸네일(v2):", tp_)
    import check_standard as cs                       # v2.2: 표준 v2 자동 점검
    lines, ok = cs.run(sp_, [res["final"]]); print("■ 표준 v2 점검"); print("\n".join(lines)); print("→ 통과" if ok else "→ 위반 있음(❌)")
