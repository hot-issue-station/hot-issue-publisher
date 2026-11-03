#!/usr/bin/env python3
"""리센느 컴백 1위 축하 영상(덕심저장소) 40초 세로 영상 만들기.

화면: 위 제목 띠(한국어+일본어) / 가운데 원본 16:9 영상(연속 감상) / 아래 우리 한마디(타자) + 실제 댓글 카드(닉네임·프사 가림)가
8~10초마다 겹치며 바뀜 / 마지막 5초 마무리 문구 + 곳별 안내.
사용: python3 scripts/make_celebration.py rounds/celebration.json EP(1~6) VARIANT(yt|ig|tx) OUT.mp4
"""
import json, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 40.0
INTRO = 2.5
END_T = 35.0
B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
BD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
RG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
def F(path, size): return ImageFont.truetype(path, size, index=1)

VID_Y = 470            # 영상 위쪽
VID_H = 594            # 1080 x 594 (원본 1600x880 잘라냄: 아래 알림 띠 제외)
PINK = (255, 120, 190)
LAV = (200, 170, 255)


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if d.textlength(cur + ch, font=font) > maxw and cur:
            # 단어 중간 끊김 줄이기: 마지막 공백에서 자르기
            sp = cur.rfind(" ")
            if sp > len(cur) * 0.5:
                lines.append(cur[:sp]); cur = cur[sp + 1:] + ch
            else:
                lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines


_ST = {}
def _st_sprite(text, font, fill, sw, glow):
    key = (text, font.path, font.size, fill, sw, glow)
    if key in _ST: return _ST[key]
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    l, t_, r, b = tmp.textbbox((0, 0), text, font=font, stroke_width=sw)
    m = glow * 2 + 4
    w, h = r - l + 2 * m, b - t_ + 2 * m
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.text((m - l, m - t_), text, font=font, fill=(0, 0, 0, 200), stroke_width=sw, stroke_fill=(0, 0, 0, 200))
    lay = lay.filter(ImageFilter.GaussianBlur(glow / 2))
    ImageDraw.Draw(lay).text((m - l, m - t_), text, font=font, fill=fill, stroke_width=sw, stroke_fill=(20, 10, 30, 255))
    _ST[key] = (lay, l - m, t_ - m, r - l, b - t_)
    return _ST[key]


def shadow_text(im, xy, text, font, fill, anchor="la", sw=3, glow=10):
    if not text: return
    lay, ox, oy, tw, th = _st_sprite(text, font, tuple(fill), sw, glow)
    x, y = xy
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    l, t_, r, b = tmp.textbbox(xy, text, font=font, anchor=anchor, stroke_width=sw)
    l0, t0, _, _ = tmp.textbbox((0, 0), text, font=font, stroke_width=sw)
    dx, dy = l - l0, t_ - t0
    im.alpha_composite(lay, (int(dx + ox), int(dy + oy))) if dx + ox >= 0 and dy + oy >= 0 else im.paste(lay, (int(dx + ox), int(dy + oy)), lay)


def thumb(d, x, y, s, col):
    # 단순한 좋아요(엄지) 모양
    d.rounded_rectangle([x, y + s * 0.42, x + s * 0.24, y + s], radius=3, fill=col)
    d.polygon([(x + s * 0.30, y + s * 0.42), (x + s * 0.52, y), (x + s * 0.64, y + s * 0.06),
               (x + s * 0.58, y + s * 0.38), (x + s * 0.98, y + s * 0.38), (x + s, y + s * 0.5),
               (x + s * 0.86, y + s), (x + s * 0.30, y + s)], fill=col)


def comment_card(c, seed):
    """실제 댓글 내용을 유튜브 댓글 모양으로. 닉네임·프사는 흐리게 가림."""
    cw = 860
    fnt = F(RG, 36)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = wrap(tmp, c["text"], fnt, cw - 150)[:4]
    ch = 120 + 50 * len(lines) + 56
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=28, fill=(18, 18, 22, 236), outline=(255, 255, 255, 40), width=2)
    # 가린 프사
    rng = np.random.default_rng(seed)
    av = Image.new("RGBA", (76, 76), tuple(int(x) for x in rng.integers(80, 220, 3)) + (255,))
    ad = ImageDraw.Draw(av)
    for _ in range(6):
        cx, cy = rng.integers(0, 76, 2); r = int(rng.integers(10, 30))
        ad.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(x) for x in rng.integers(60, 255, 3)) + (255,))
    av = av.filter(ImageFilter.GaussianBlur(9))
    m = Image.new("L", (76, 76), 0); ImageDraw.Draw(m).ellipse([0, 0, 75, 75], fill=255)
    card.paste(av, (32, 34), m)
    # 가린 닉네임
    nb = Image.new("RGBA", (200, 30), (150, 150, 160, 255))
    nb = nb.filter(ImageFilter.GaussianBlur(3))
    nm = Image.new("L", (200, 30), 0); ImageDraw.Draw(nm).rounded_rectangle([0, 0, 199, 29], radius=12, fill=170)
    card.paste(nb, (128, 40), nm)
    d.text((345, 40), c.get("when", "· 오늘"), font=F(RG, 26), fill=(150, 150, 160))
    y = 88
    for ln in lines:
        d.text((128, y), ln, font=fnt, fill=(240, 240, 245)); y += 50
    thumb(d, 128, y + 14, 30, (200, 200, 210))
    d.text((170, y + 10), c["likes"], font=F(BD, 28), fill=(200, 200, 210))
    return card


def typing(text, t0, t, cps=11):
    n = int(max(0, (t - t0)) * cps)
    return text[:n]


def build_overlay_frames(ep, variant, cfg):
    e = cfg["episodes"][ep - 1]
    n = ep
    title_kr = cfg.get("title_kr", "리센느 컴백 1위 축하 영상 {n}탄").format(n=n)
    title_jp = cfg.get("title_jp", "RESCENE カムバック1位おめでとう映像 第{n}弾").format(n=n)
    cards = [comment_card(c, 100 * ep + i) for i, c in enumerate(e["comments"])]
    ftk = F(B, 54); ftj = F(BD, 32); fsub = F(B, 60); fsubj = F(BD, 34)
    fline = F(B, 44); fjp = F(RG, 30); fend = F(B, 56); fendj = F(BD, 32); fcta = F(B, 40)
    fbrand = F(BD, 28)

    # 고정 위쪽 띠(제목) 미리 그리기
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    td.rounded_rectangle([W // 2 - 230, 150, W // 2 + 230, 202], radius=26, fill=(255, 120, 190, 235))
    td.text((W // 2, 176), "덕심저장소 · 推し活アーカイブ", font=F(BD, 28), fill=(255, 255, 255), anchor="mm")
    shadow_text(top, (W // 2, 262), title_kr, ftk, (255, 255, 255), anchor="mm")
    shadow_text(top, (W // 2, 322), title_jp, ftj, (235, 220, 255), anchor="mm", sw=2)
    shadow_text(top, (W // 2, 400), f"“{e['sub_kr']}”  {e['sub_jp']}", F(B, 40), PINK, anchor="mm", sw=3)

    # 댓글 등장 시간: 4초부터 10초 간격, 각 9.2초(앞뒤 0.6초 페이드)
    slots = e.get("slots", [4.0, 13.5, 23.5])
    lines = e["lines"]   # [{t, kr, jp}]
    prev_key, prev_bytes = None, None
    for i in range(int(DUR * FPS)):
        t = i / FPS
        # 같은 모양이 이어지는 프레임은 다시 그리지 않음
        if t < INTRO:
            key = ("i", i)
        elif t < END_T:
            cur = None
            for ln in lines:
                if ln["t"] <= t < ln["t"] + ln.get("d", 7.0):
                    cur = ln
            ks = None
            if cur:
                s_ = typing(cur["kr"], cur["t"], t)
                ks = (s_, len(s_) < len(cur["kr"]) and int(t * 4) % 2, t > cur["t"] + len(cur["kr"]) / 11 + 0.2, cur["kr"])
            kc = None
            for k, st in enumerate(slots):
                if k >= len(cards): break
                en = (slots[k + 1] + 0.6) if k + 1 < len(slots) and k + 1 < len(cards) else END_T
                if st <= t < en:
                    kc = (k, round(min(1, (t - st) / 0.6) * min(1, (en - t) / 0.6), 2), int(30 * (1 - min(1, (t - st) / 0.6))))
            key = ("m", ks, kc)
        else:
            key = ("e", round(min(1, (t - END_T) / 0.6), 2), t < END_T + 0.4)
        if key == prev_key:
            yield prev_bytes; continue
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t < END_T + 0.4:
            im.alpha_composite(top)
        # 첫 2.5초: 응원법 표시
        if t < INTRO:
            a = min(1, t / 0.2) * min(1, (INTRO - t) / 0.3)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pop = 1 + 0.15 * max(0, 1 - t * 4)
            shadow_text(lay, (W // 2, VID_Y + VID_H + 90), "응원법  It's all you!", F(B, int(52 * pop)), (255, 255, 255), anchor="mm")
            shadow_text(lay, (W // 2, VID_Y + VID_H + 160), "리! 센! 느!", F(B, int(88 * pop)), PINK, anchor="mm", sw=4)
            arr = np.array(lay); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
            im.alpha_composite(Image.fromarray(arr))
        elif t < END_T:
            # 우리 한마디(타자)
            cur = None
            for ln in lines:
                if ln["t"] <= t < ln["t"] + ln.get("d", 7.0):
                    cur = ln
            if cur:
                s = typing(cur["kr"], cur["t"], t)
                if s:
                    shadow_text(im, (W // 2, VID_Y + VID_H + 58), s + ("|" if len(s) < len(cur["kr"]) and int(t * 4) % 2 else ""), fline, (255, 255, 255), anchor="mm")
                if t > cur["t"] + len(cur["kr"]) / 11 + 0.2:
                    shadow_text(im, (W // 2, VID_Y + VID_H + 112), cur["jp"], fjp, LAV, anchor="mm", sw=2)
            # 댓글 카드(겹치며 바뀜)
            for k, st in enumerate(slots):
                if k >= len(cards): break
                en = (slots[k + 1] + 0.6) if k + 1 < len(slots) and k + 1 < len(cards) else END_T
                if st <= t < en:
                    a = min(1, (t - st) / 0.6) * min(1, (en - t) / 0.6)
                    rise = int(30 * (1 - min(1, (t - st) / 0.6)))
                    cd = cards[k]
                    arr = np.array(cd); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
                    x = 44; y = VID_Y + VID_H + 160 + rise
                    im.alpha_composite(Image.fromarray(arr), (x, y))
                    c = e["comments"][k]
                    tr = c.get("jp") or c.get("kr_tr")
                    if tr and a > 0.05:
                        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                        ld = ImageDraw.Draw(lay)
                        tl = wrap(ld, ("🇯🇵 " if False else "") + tr, F(RG, 28), 860)[:2]
                        yy = y + cd.size[1] + 14
                        for ln in tl:
                            shadow_text(lay, (x + 10, yy), ln, F(RG, 28), (220, 205, 255), sw=2, glow=6); yy += 38
                        arr2 = np.array(lay); arr2[..., 3] = (arr2[..., 3] * a).astype(np.uint8)
                        im.alpha_composite(Image.fromarray(arr2))
        # 마무리 5초
        if t >= END_T:
            a = min(1, (t - END_T) / 0.6)
            lay = Image.new("RGBA", (W, H), (10, 0, 20, int(150 * a)))
            fin = cfg["ending"]
            shadow_text(lay, (W // 2, 640), fin["kr1"], fend, (255, 255, 255), anchor="mm")
            shadow_text(lay, (W // 2, 720), fin["kr2"], fend, PINK, anchor="mm")
            shadow_text(lay, (W // 2, 800), fin["jp"], fendj, LAV, anchor="mm", sw=2)
            cta = cfg["cta"][variant]
            last = len(cfg["episodes"])
            nk = cfg.get("next_kr", "▶ 다음 편 {m}탄 「{sub}」"); nj = cfg.get("next_jp", "次は第{m}弾「{sub}」")
            nxt = (nk.format(m=n + 1, sub=cfg['episodes'][n]['sub_kr']) if n < last else cfg.get("last_kr", "▶ 1~6탄 전체 이어 보기"))
            nxtj = (nj.format(m=n + 1, sub=cfg['episodes'][n]['sub_jp']) if n < last else cfg.get("last_jp", "第1〜6弾まとめて見てね"))
            shadow_text(lay, (W // 2, 930), nxt, fcta, (255, 255, 255), anchor="mm")
            shadow_text(lay, (W // 2, 990), nxtj, fendj, (235, 220, 255), anchor="mm", sw=2)
            shadow_text(lay, (W // 2, 1090), cta, F(BD, 36), (255, 235, 150), anchor="mm", sw=2)
            shadow_text(lay, (W // 2, 1160), "이슈브리프 · @hot.issue.station", fbrand, (230, 230, 240), anchor="mm", sw=2)
            arr = np.array(lay); arr[..., 3] = np.minimum(255, arr[..., 3]).astype(np.uint8)
            if a < 1:
                arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
            im.alpha_composite(Image.fromarray(arr))
        # 출처 표시(작게)
        ImageDraw.Draw(im).text((W - 190, VID_Y + VID_H - 34), e["credit"], font=F(RG, 20), fill=(255, 255, 255, 170), anchor="ra")
        prev_key, prev_bytes = key, im.tobytes()
        yield prev_bytes


def main():
    cfgp, ep, variant, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    cfg = json.load(open(cfgp))
    e = cfg["episodes"][ep - 1]
    intro = cfg["intro"]
    # 입력: 0=응원법 원본, 1..=본편 조각들
    ins = ["-ss", str(intro["ss"]), "-t", str(INTRO + 0.3), "-i", intro["file"]]
    body_parts = e["parts"]  # [{file, ss, t}]
    for p in body_parts:
        ins += ["-ss", str(p["ss"]), "-t", str(p["t"]), "-i", p["file"]]
    k = len(body_parts)
    crop = "crop=1600:880:160:153"
    fc = []
    fc.append(f"[0:v]{crop},setpts=PTS-STARTPTS,fps={FPS}[iv]")
    fc.append(f"[0:a:0]asetpts=PTS-STARTPTS,aresample=48000[ia]")
    vcat = "".join(f"[{i + 1}:v]" for i in range(k)); acat = "".join(f"[{i + 1}:a:0]" for i in range(k))
    fc.append(f"{vcat}concat=n={k}:v=1:a=0,{crop},setpts=PTS-STARTPTS,fps={FPS}[bv]")
    fc.append(f"{acat}concat=n={k}:v=0:a=1,asetpts=PTS-STARTPTS,aresample=48000[ba]")
    fc.append(f"[iv]trim=0:{INTRO},setpts=PTS-STARTPTS[iv2]")
    fc.append(f"[bv]trim=0:{DUR - INTRO},setpts=PTS-STARTPTS[bv2]")
    fc.append(f"[iv2][bv2]concat=n=2:v=1:a=0,split[mv1][mv2]")
    fc.append(f"[ia]atrim=0:{INTRO + 0.3},asetpts=PTS-STARTPTS[ia2]")
    fc.append(f"[ba]atrim=0:{DUR - INTRO + 0.3},asetpts=PTS-STARTPTS[ba2]")
    fc.append(f"[ia2][ba2]acrossfade=d=0.3,atrim=0:{DUR},afade=t=out:st={DUR - 2.5}:d=2.5,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    fc.append(f"[mv1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.18:saturation=1.2[bg]")
    fc.append(f"[mv2]scale={W}:{VID_H}[fg]")
    fc.append(f"[bg][fg]overlay=0:{VID_Y}[base]")
    fc.append(f"[{k + 1}:v]format=rgba[ov]")
    fc.append(f"[base][ov]overlay=0:0:format=auto,format=yuv420p[vout]")
    cmd = ["ffmpeg", "-v", "error", "-y"] + ins + ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]", "-t", str(DUR),
           "-c:v", "libx264", "-preset", "veryfast", "-b:v", "3800k", "-maxrate", "4500k", "-bufsize", "8000k",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in build_overlay_frames(ep, variant, cfg):
        pr.stdin.write(fr)
    pr.stdin.close(); pr.wait()
    print("done", out, pr.returncode)


if __name__ == "__main__":
    main()
