"""덕심저장소 갤러리 30초 홍보 쇼츠 (대표 11/12 04:00~04:34 요청) — 휴대폰 화면 녹화 2개(A 43초, B 162초) 편집."""
import subprocess, os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
W, H, FPS = 1080, 1920, 30
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
MUSIC = "/home/claude/hot-issue-publisher/music/suno/7_rescene_sparkling_dance.mp3"; MUSIC_SS = 132  # 대표 11/12 04:42 "쇼츠 때 쓰는 신나는 음악"
VT, VH = 250, 1500          # 영상 칸: y=250부터 1500 높이(720x1000 자른 것을 1.5배)
CROP = "crop=720:1000:0:440,scale=1080:1500"

# (파일, 시작, 길이, 천천히 확대?)
# 대표 11/12 04:42 "장면 전환이 정신없는 것보다 쭉 보여주는 게 좋겠다" → 긴 장면 3개를 부드럽게 이어 붙임
SEG = [("B.mp4",145.5,10.0,False), ("B.mp4",0.5,8.0,False), ("B.mp4",16.0,7.5,False)]
XF = 0.6
CAPT = [(0,0.2,5.0),(1,5.0,9.7),(2,9.7,13.6),(3,13.6,17.4),(4,17.4,21.0),(5,21.0,24.3)]  # (자막 번호, 시작, 끝)
CAP = [  # 각 장면 자막(한국어, 일본어, 강조색)
 ("리센느를 걸어서 만나는 곳", "RESCENEに歩いて会える場所", "#FFD640"),
 ("덕심저장소 갤러리 OPEN", "ドクシム・ギャラリー オープン", "#FF7000"),
 ("무대·예능·일상, 방마다 모아 뒀어요", "ステージ・バラエティ・日常を部屋ごとに", "#FFD640"),
 ("액자 앞에 서면 장면이 움직여요", "額縁の前に立つとシーンが動く", "#FFD640"),
 ("누르면 공식 영상이 바로", "タップで公式映像がすぐ再生", "#FF7000"),
 ("리마인끼리 좋아요·댓글로 함께", "REMINE同士でいいね・コメント", "#FFD640"),
 ("굿즈 샵까지 둘러보고", "グッズショップも", "#FFD640"),
 ("다음 관은... 아직 잠겨 있어요", "次の館は…まだ秘密", "#C9A8FF"),
]
END = 4.6

def font(p, s): return ImageFont.truetype(p, s, index=1)   # 1 = KR face
def text_center(d, y, t, f, fill, stroke=6, sc="#1e143c"):
    w = d.textlength(t, font=f); d.text(((W - w) / 2, y), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=sc)

def frame_png():   # 위·아래 고정 띠(배경 + 시리즈 이름)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, VT], fill=(30, 20, 60, 255)); d.rectangle([0, VT + VH, W, H], fill=(30, 20, 60, 255))
    f = font(FB, 30); t = "덕심저장소 · 리센느 응원 특집"; w = d.textlength(t, font=f)
    d.rounded_rectangle([(W - w) / 2 - 22, 36, (W + w) / 2 + 22, 86], 14, fill=(150, 80, 230)); d.text(((W - w) / 2, 40), t, font=f, fill="white")
    f2 = font(FM, 34); text_center(d, VT + VH + 40, "duksim-gallery.pages.dev", f2, "#FFD640", 0)
    f3 = font(FM, 24); text_center(d, VT + VH + 96, "영상·사진은 유튜브·인스타 공식 원본 그대로", f3, "#cfc6ea", 0)
    # 대표 11/12 04:47: 오른쪽 아래 「갤러리 놀러가기 → 프로필 링크」 표시(영상 속 버튼은 눌리지 않으므로 프로필 링크로 안내)
    fb = font(FB, 34); fs = font(FM, 24); t1 = "💜 갤러리 놀러가기"; t1 = "갤러리 놀러가기"; t2 = "프로필 링크에서 바로 →"
    bw = max(d.textlength(t1, font=fb), d.textlength(t2, font=fs)) + 70; bh = 104; x1 = W - 28; x0 = x1 - bw; y1 = VT + VH - 24; y0 = y1 - bh
    d.rounded_rectangle([x0 + 4, y0 + 6, x1 + 4, y1 + 6], 26, fill=(0, 0, 0, 90))
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(150, 80, 230, 245), outline=(255, 214, 64, 255), width=4)
    hx = x0 + 30; hy = y0 + 30; d.ellipse([hx - 11, hy - 8, hx + 1, hy + 4], fill="#FFD640"); d.ellipse([hx - 1, hy - 8, hx + 11, hy + 4], fill="#FFD640"); d.polygon([(hx - 11, hy), (hx + 11, hy), (hx, hy + 13)], fill="#FFD640")
    d.text((x0 + 50, y0 + 10), t1, font=fb, fill="white"); d.text((x0 + 50, y0 + 60), t2, font=fs, fill="#FFE9A0")
    im.save("frame.png")

def cap_png(i, ko, ja, col):
    im = Image.new("RGBA", (W, VT), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(FB, 58 if len(ko) < 14 else 50); text_center(d, 100, ko, f, col, 5)
    fj = ImageFont.truetype(FM, 30, index=0); text_center(d, 182, ja, fj, "#ffffff", 3)
    im.save(f"cap{i}.png")

def end_png():
    src = "endbg.png"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "9.5", "-i", "A.mp4", "-frames:v", "1", "-vf", "crop=720:1000:0:440,scale=1080:1500", src], check=True)
    bg = Image.open(src).convert("RGB").filter(ImageFilter.GaussianBlur(14)); base = Image.new("RGB", (W, H), (30, 20, 60)); base.paste(bg, (0, VT))
    ov = Image.new("RGBA", (W, H), (20, 12, 45, 150)); base = Image.alpha_composite(base.convert("RGBA"), ov); d = ImageDraw.Draw(base)
    # 물음표 실루엣 3개(실제 인물 아님)
    for k, x in enumerate((270, 540, 810)):
        cx, cy = x, 820; d.ellipse([cx - 70, cy - 170, cx + 70, cy - 30], fill=(95, 75, 150)); d.rounded_rectangle([cx - 115, cy - 20, cx + 115, cy + 210], 60, fill=(95, 75, 150))
        fq = font(FB, 110); d.text((cx - 32, cy - 175), "?", font=fq, fill="#FFD640")
        fl = font(FB, 34); lab = f"{k + 2}관"; w = d.textlength(lab, font=fl); d.text((cx - w / 2, cy + 230), lab, font=fl, fill="#e8ddff")
    text_center(d, 330, "NEXT WHO?", font(FB, 150), "#FFD640", 8)
    text_center(d, 1180, "다음 관의 주인공은?", font(FB, 70), "#ffffff", 6)
    text_center(d, 1280, "댓글로 그룹 이름을 남겨 주세요", font(FB, 52), "#FF9A3D", 5)
    text_center(d, 1360, "次の館の主役は?コメントで教えてね", ImageFont.truetype(FM, 36, index=0), "#ffffff", 3)
    f2 = font(FB, 30); t = "덕심저장소 · 리센느 응원 특집"; w = d.textlength(t, font=f2)
    d.rounded_rectangle([(W - w) / 2 - 22, 36, (W + w) / 2 + 22, 86], 14, fill=(150, 80, 230)); d.text(((W - w) / 2, 40), t, font=f2, fill="white")
    text_center(d, 1500, "duksim-gallery.pages.dev", font(FB, 56), "#FFD640", 5)
    text_center(d, 1590, "무료로 열려 있어요 · 日本語OK", font(FM, 36), "#ffffff", 3)
    base.convert("RGB").save("end.png")

def run(cmd): r = subprocess.run(cmd, capture_output=True, text=True); assert r.returncode == 0, r.stderr[-2000:]

def main():
    frame_png(); end_png()
    for i, (ko, ja, col) in enumerate(CAP): cap_png(i, ko, ja, col)
    # 장면마다 같은 크기 클립
    for i, (f, ss, du, zoom) in enumerate(SEG):
        vf = CROP + (f",zoompan=z='1+0.05*on/{int(du*FPS)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1500:fps={FPS}" if zoom else f",fps={FPS}")
        vf += f",pad={W}:{H}:0:{VT}:color=0x1e143c,format=yuv420p,setsar=1"
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(ss), "-i", f, "-t", str(du), "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", f"s{i}.mp4"])
    run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", "end.png", "-t", str(END), "-vf", f"fps={FPS},format=yuv420p,setsar=1,zoompan=z='1+0.03*on/{int(END*FPS)}':d=1:s={W}x{H}:fps={FPS}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "send.mp4"])
    clips = [f"s{i}.mp4" for i in range(len(SEG))] + ["send.mp4"]; durs = [s[2] for s in SEG] + [END]
    kinds = ["fade", "fade", "fadewhite"]
    inp = sum([["-i", c] for c in clips], []); fl = []; cur = "[0:v]"; t = durs[0]; starts = [0.0]
    for k in range(1, len(clips)):
        off = t - XF; starts.append(off); kd = kinds[(k - 1) % len(kinds)]
        fl.append(f"{cur}[{k}:v]xfade=transition={kd}:duration={XF}:offset={off:.3f}[x{k}]"); cur = f"[x{k}]"; t = off + durs[k]
    total = t
    # 고정 띠 + 장면 자막
    ni = len(clips); inp += ["-i", "frame.png"]; fl.append(f"{cur}[{ni}:v]overlay=0:0:enable='lt(t,{starts[-1]:.3f})'[f0]"); cur = "[f0]"
    for j, (i, a, b) in enumerate(CAPT):
        inp += ["-i", f"cap{i}.png"]
        fl.append(f"{cur}[{ni + 1 + j}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[c{j}]"); cur = f"[c{j}]"
    fl.append(f"{cur}format=yuv420p[vout]")
    run(["ffmpeg", "-loglevel", "error", "-y", *inp, "-filter_complex", ";".join(fl), "-map", "[vout]", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "v.mp4"])
    # 음악: bright 를 이어 붙여 total 초, 끝 1.5초 줄이기
    run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(MUSIC_SS), "-i", MUSIC, "-vn", "-t", f"{total:.3f}", "-af", f"afade=t=in:d=0.4,afade=t=out:st={total - 1.6:.3f}:d=1.6,loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "a.m4a"])
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", "v.mp4", "-i", "a.m4a", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", "덕심갤러리_홍보_30초_v2.mp4"])
    # 썸네일: 첫 장면 + 큰 글
    run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "152", "-i", "B.mp4", "-frames:v", "1", "-vf", "crop=720:1000:0:440,scale=1080:1500", "th_bg.png"])
    th = Image.new("RGB", (W, H), (30, 20, 60)); th.paste(Image.open("th_bg.png").convert("RGB"), (0, 420)); d = ImageDraw.Draw(th)
    text_center(d, 90, "리센느를", font(FB, 110), "#ffffff", 7); text_center(d, 230, "걸어서 만나는 곳", font(FB, 110), "#FFD640", 7)
    text_center(d, 1700, "NEXT WHO?", font(FB, 90), "#FFD640", 6); text_center(d, 1810, "덕심저장소 갤러리 OPEN", font(FB, 52), "#ffffff", 4)
    th.save("덕심갤러리_홍보_썸네일.png")
    print(json.dumps({"total": round(total, 2), "starts": [round(x, 2) for x in starts]}))

if __name__ == "__main__": main()
