"""덕심저장소 무대 교차편집 공장 v1 (제미나이 B형)
사용법: python stagemix_factory.py 무대믹스.json
기획 파일 예:
{"out":"with_stagemix","song":"song.m4a","song_start":42.0,"bpm":124,
 "title":"리센느 「With」 무대 8개 교차편집","sub":"쇼케이스 · 음방 · 직캠",
 "clips":{"A":["쇼케이스.mp4",30.0],"B":["뮤뱅.mp4",31.2]},          # 이름: [파일, 노래 시작과 맞는 시각]
 "plan":[["A","cut",4],["B","zoom",2],["A+B","split",8],["C","shake",1], ...],  # [클립, 효과, 박자 수]
 "sources":["KBS 뮤직뱅크 11/7", "..."], "end":{"lines":["다음 무대는 뭐로 할까요?"]}}
효과: cut(그냥 컷) / zoom(크래시 줌) / split(위아래 2분할, "A+B") / shake(흔들림+회전) / pump(펌핑)
- 박자(bpm)에 맞춰 컷 길이가 정해진다. 노래 시각과 클립 시각이 같이 흘러 립싱크가 맞는다.
- 처음 2초 제목, 마지막 4초 끝 화면(구독·좋아요·알림)은 항상 들어간다.
- 저작권: 방송 화면은 skill dukssim-platform-copyright-check, 팬캠은 양해(dukssim-fan-video-consent) 먼저.
"""
import json, os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shorts_factory import end_card, F, FB, FM, ct, Y, WH, GR, layer

W, H = 1080, 1920
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-an"]
FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
HALF = f"scale={W}:{H//2}:force_original_aspect_ratio=increase,crop={W}:{H//2}"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("ffmpeg 오류:\n" + r.stderr[-1500:])

def segment(spec, base, name, fx, t_song, dur, out):
    """노래의 t_song 시점에 해당하는 장면을 dur초 잘라 효과를 입힌다."""
    def src(n):
        f, sync = spec["clips"][n]; p = f if os.path.isabs(f) else os.path.join(base, f)
        return ["-ss", f"{sync + t_song - spec.get('song_start', 0):.3f}", "-t", f"{dur:.3f}", "-i", p]
    if fx == "split":
        a, b = name.split("+")
        run(["ffmpeg", "-y", *src(a), *src(b), "-filter_complex",
             f"[0:v]{HALF},setsar=1[t];[1:v]{HALF},setsar=1[u];"
             f"[t]crop={W}:{H//2}:0:0[t2];[u]crop={W}:{H//2}:0:0[u2];[t2][u2]vstack=inputs=2,setsar=1[v]", "-map", "[v]", *ENC, out])
        return
    vf = FILL
    if fx == "zoom":   # 크래시 줌: 1.35배에서 0.25초 만에 원래 크기로
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,scale=w='iw*(1+0.35*max(0,1-t/0.25))':h=-2:eval=frame,crop={W}:{H}"
    elif fx == "shake":  # 흔들림 + 약 15도 회전
        vf = f"scale={int(W*1.3)}:{int(H*1.3)}:force_original_aspect_ratio=increase,rotate='0.26*sin(t*38)*max(0,1-t/0.5)':ow=iw:oh=ih,crop={W}:{H}:(iw-{W})/2+30*sin(t*45):(ih-{H})/2"
    elif fx == "pump":   # 박자마다 살짝 커졌다 작아짐
        bt = 60 / spec["bpm"]
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,scale=w='iw*(1+0.08*abs(cos(PI*t/{bt:.4f})))':h=-2:eval=frame,crop={W}:{H}"
    run(["ffmpeg", "-y", *src(name), "-vf", vf + ",setsar=1", *ENC, out])

def main(path):
    spec = json.load(open(path, encoding="utf-8")); base = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(base, "_tmp_mix"); out = os.path.join(base, "out"); os.makedirs(tmp, exist_ok=True); os.makedirs(out, exist_ok=True)
    beat = 60 / spec["bpm"]; t = spec.get("song_start", 0.0); parts = []
    for i, (name, fx, beats) in enumerate(spec["plan"]):
        d = beats * beat; p = os.path.join(tmp, f"seg{i:03}.mp4"); segment(spec, base, name, fx, t, d, p); parts.append(p); t += d
    body = t - spec.get("song_start", 0.0); END = 4.0
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    joined = os.path.join(tmp, "joined.mp4"); run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    # 제목 판 · 끝 화면
    tl = layer(); d = ImageDraw.Draw(tl)
    d.rectangle([0, 120, W, 400], fill=(14, 12, 40, 170))
    ct(d, 160, spec["title"], F(FB, 64), WH); ct(d, 260, spec.get("sub", ""), F(FM, 44), Y)
    tp = os.path.join(tmp, "title.png"); tl.save(tp)
    ep = os.path.join(tmp, "end.png"); end_card(spec.get("end", {})).save(ep)
    src_l = layer(); d = ImageDraw.Draw(src_l)
    for k, s in enumerate(spec.get("sources", [])[:2]): ct(d, 1760 + k * 48, s, F(FM, 30), GR)
    sp = os.path.join(tmp, "src.png"); src_l.save(sp)
    song = spec["song"] if os.path.isabs(spec["song"]) else os.path.join(base, spec["song"])
    total = body + END; final = os.path.join(out, spec["out"] + ".mp4")
    run(["ffmpeg", "-y", "-i", joined, "-loop", "1", "-i", tp, "-loop", "1", "-i", ep, "-loop", "1", "-i", sp,
         "-ss", str(spec.get("song_start", 0.0)), "-i", song, "-filter_complex",
         f"[0:v]tpad=stop_mode=clone:stop_duration={END}[b];"
         f"[1:v]format=rgba,fade=out:st=1.6:d=0.4:alpha=1[ti];[b][ti]overlay=0:0:enable='lt(t,2)'[v1];"
         f"[v1][3:v]overlay=0:0:enable='lt(t,{body:.2f})'[v2];"
         f"[2:v]format=rgba,fade=in:st={body:.2f}:d=0.5:alpha=1[en];[v2][en]overlay=0:0:enable='gte(t,{body:.2f})'[v];"
         f"[4:a]afade=t=out:st={total-1.5:.2f}:d=1.5[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", final])
    n_src = len({p[0] for p in spec["clips"].values()})
    chk = [("끝 화면 4초", True), ("노래(음원) 들어감", True), ("출처 표시", bool(spec.get("sources"))),
           ("저작권·팬캠 양해 확인", bool(spec.get("copyright_checked"))), (f"무대 소스 {n_src}개 (8개 이상 권장)", n_src >= 8)]
    print(f"영상: {final} ({total:.1f}초)")
    for nme, ok in chk: print(("✅ " if ok else "❌ 확인: ") + nme)

def _entry(path, outdir=None):
    spec = json.load(open(path, encoding="utf-8"))
    if spec.get("preset") == "pulse58": return pulse58(spec, os.path.dirname(os.path.abspath(path)), outdir)
    return main(path)


# ======================================================================
# 프리셋 "pulse58" — 쇼츠 스타일 B 「8단 교차편집」 (제작 표준 v2, 11/11)
# 사용법: python stagemix_factory.py 기획.json   (기획에 "preset":"pulse58" 이 있으면 이쪽)
# 구간(standard_v2.json style_B.sections): [0~6] 0.75초 간격 8단 체인지 + 크래시 줌 / [6~26] 상하 2분할 엇박 교차 + 수평 패닝 슬라이드
#   / [26~46] 후렴 0.3초 점프컷 + 15도 롤링 셰이크 / [46~53] 카메라 펌핑·진동 / [53~58] 엔딩 5초 고정 레이아웃
# 기획 예:
# {"preset":"pulse58","out":"with_mix","song":{"file":"song.m4a","start":42.0},"bpm":124,
#  "sources":[{"file":"쇼케이스.mp4","sync":30.0,"label":"쇼케이스"}, ... 8개 이상],   # sync = 노래 start 와 맞는 그 영상의 시각
#  "title":"…","source_line":"출처 · …","outro":{"ask":"…","next":"…","frame":{"file":…,"t":…}},"test_label":"형식 시험 · 공개용 아님"}
# bpm 이 없으면 v2_fx.estimate_beat(ffmpeg 소리 → numpy 온셋)로 추정해 컷을 박자에 맞춘다(추정값·신뢰도는 결과에 출력).
# 길이: 모든 플랫폼 58.0초 하나(대표 20:40 최종 확정).
# ======================================================================
def pulse58(spec, base, outdir=None):
    import numpy as np, math, cv2
    import v2_fx as fx, expose_factory as ef, check_standard as cs
    STD = fx.STD; SB = STD["style_B"]; W2, H2 = STD["shorts"]["size"]; FPS2 = STD["shorts"]["fps"]
    T = cs.tconf(spec); total = T["total_sec"]; suffix = spec.get("suffix", "")   # 58-M(58.0) / 40-M(40.0)
    outdir = os.path.abspath(outdir or os.path.join(base, "out")); os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(outdir, "_tmp_" + spec["out"]); os.makedirs(tmp, exist_ok=True)
    srcs = spec["sources"]
    for s in srcs:
        if not os.path.isabs(s["file"]): s["file"] = os.path.join(base, s["file"])
    song = spec["song"]; sf = song["file"] if os.path.isabs(song["file"]) else os.path.join(base, song["file"])
    if spec.get("bpm"): bpm, phase, conf = float(spec["bpm"]), float(spec.get("beat_phase", 0.0)), 1.0
    else: bpm, phase, conf = fx.estimate_beat(sf, song["start"], total)
    beat = 60 / bpm
    sec = {n: (a, b) for n, a, b in T["sections"]}
    def grid(a, b, step):
        """a~b 사이 컷 시각(박자 격자에 맞춤)."""
        pts = [a]; k = math.ceil((a - phase) / step + 1e-6); 
        while True:
            x = phase + k * step; k += 1
            if x >= b - step * 0.5: break
            if x > a + step * 0.5: pts.append(x)
        return pts + [b]
    def snap(target):   # 목표 간격에 가장 가까운 박자 배수(반 박 단위)
        return beat * max(0.25, round(target / beat * 4) / 4)
    def even_cuts(a, b, n):   # n 칸으로 고르게 나누고 각 컷을 ±0.15초 안의 반 박에 맞춤(8단 = 정확히 8컷)
        pts = [a]
        for i in range(1, n):
            x = a + (b - a) * i / n; g = phase + round((x - phase) / (beat / 2)) * (beat / 2)
            pts.append(g if abs(g - x) <= 0.15 and pts[-1] + 0.3 < g < b - 0.3 else x)
        return pts + [b]
    shots = []   # (t0, t1, kind, 소스번호들, 추가)
    n8 = 0
    if "change8" in sec:      # 58-M [0~6] 8단 체인지
        a, b = sec["change8"]; cuts = even_cuts(a, b, round((b - a) / SB["change_sec"]))
        for i in range(len(cuts) - 1): shots.append((cuts[i], cuts[i + 1], "change", [i % len(srcs)], {})); n8 += 1
    if "hook" in sec:         # 40-M [0~3] 훅: 0.75초 체인지 4컷 + 크래시 줌
        a, b = sec["hook"]; cuts = even_cuts(a, b, round((b - a) / SB["change_sec"]))
        for i in range(len(cuts) - 1): shots.append((cuts[i], cuts[i + 1], "change", [i % len(srcs)], {})); n8 += 1
    if "mix" in sec:          # 40-M [3~35] 한 곡 하이라이트: 4~6단 교차(2박마다 컷), 8컷마다 2분할 한 번, 4컷마다 크래시 줌
        a, b = sec["mix"]; cuts = grid(a, b, snap(1.0)); j = 0
        for i in range(len(cuts) - 1):
            if i % 8 == 5: shots.append((cuts[i], cuts[i + 1], "split", [], {"cuts": {"top": [cuts[i]], "bot": [cuts[i] + (cuts[i + 1] - cuts[i]) / 2]}}))
            else: shots.append((cuts[i], cuts[i + 1], "change" if i % 4 == 0 else "cut", [j % len(srcs)], {})); j += 1
    if "split" in sec:          # 58-M [6~26] 상하 2분할 엇박 + 수평 패닝 슬라이드
      a, b = sec["split"]; step = snap(1.0); cuts = grid(a, b, step)
      half_cuts = {"top": [], "bot": []}; k = 0
      for i in range(len(cuts) - 1):   # 엇박: 위는 짝수 칸, 아래는 홀수 칸에서 바뀜
          half_cuts["top" if i % 2 == 0 else "bot"].append(cuts[i])
      shots.append((a, b, "split", [], {"cuts": half_cuts}))
    if "jump" in sec:
        a, b = sec["jump"]; cuts = grid(a, b, snap(SB["jump_sec"]))
        for i in range(len(cuts) - 1): shots.append((cuts[i], cuts[i + 1], "jump", [(i * 3) % len(srcs)], {"sign": 1 if i % 2 == 0 else -1}))
    if "pump" in sec:
        a, b = sec["pump"]; cuts = grid(a, b, beat * 2)
        for i in range(len(cuts) - 1): shots.append((cuts[i], cuts[i + 1], "pump", [(i + 5) % len(srcs)], {}))
    body = sec["outro"][0]
    # 고정 얹기
    fixed = []
    if spec.get("test_label"):
        im = fx.text_img(spec["test_label"], 38, W2, base=fx.WH, stroke=0, font=fx.FB, box=(200, 0, 0, 225), shadow=False); fixed.append(ef.Ov(im, 20, 20, 0, total + 1, fade=0))
    if spec.get("title"):
        im = fx.caption_img(spec["title"], "big", W2); fixed.append(ef.Ov(im, (W2 - im.width) // 2, int(H2 * 0.40), 0.0, 2.2, pop=0.15, fade=0.3))
    if spec.get("source_line"):
        im = fx.text_img(spec["source_line"], 28, W2 - 60, base=fx.GR, hi=fx.GR, stroke=2, font=fx.FM, shadow=False); fixed.append(ef.Ov(im, W2 - im.width - 16, H2 - im.height - 150, 0, body, fade=0))
    labels = {}
    for i, s in enumerate(srcs):
        if s.get("label"): labels[i] = fx.text_img(s["label"], 30, W2, base=fx.WH, stroke=0, font=fx.FB, box=(0, 0, 0, 150), shadow=False, pad=(16, 6))
    def fill(img, w, h, xc=0.5):
        s = max(w / img.shape[1], h / img.shape[0]); r = cv2.resize(img, (int(img.shape[1] * s) + 1, int(img.shape[0] * s) + 1), interpolation=cv2.INTER_AREA)
        x0 = int(max(0, min(r.shape[1] - w, xc * r.shape[1] - w / 2))); y0 = (r.shape[0] - h) // 2; return np.ascontiguousarray(r[y0:y0 + h, x0:x0 + w])
    vpath = os.path.join(tmp, "v.mp4"); wr = ef.open_writer(vpath, W2, H2)
    def write(fr): wr.stdin.write(fr.tobytes())
    frame_i = 0; lab_ovs = []
    def emit(fr, t, si=None):
        for o in fixed: o.draw(fr, t)
        if si is not None and si in labels: ef.blend(fr, *(lambda a: (a[:, :, 2::-1].astype(np.float32), a[:, :, 3:4].astype(np.float32) / 255))(np.array(labels[si])), 20, H2 - 260)
        write(fr)
    for (t0, t1, kind, sis, ex) in shots:
        f0, f1 = round(t0 * FPS2), round(t1 * FPS2)
        if kind == "split":
            hh = H2 // 2; tops = ex["cuts"]["top"]; bots = ex["cuts"]["bot"]
            def half_seq(cs_, off): return [(c, (cs_[j + 1] if j + 1 < len(cs_) else t1), (j * 2 + off) % len(srcs)) for j, c in enumerate(cs_)]
            seqs = {"top": half_seq(tops, 1), "bot": [(t0, bots[0], 2 % len(srcs))] + half_seq(bots, 4) if bots else [(t0, t1, 2)]}
            rd = {}
            for fi in range(f0, f1):
                t = min(max(fi / FPS2, t0), t1 - 1e-4); fr = np.zeros((H2, W2, 3), np.uint8)   # 프레임 반올림으로 구간 밖에 걸치지 않게
                for hk, yy, dirn in (("top", 0, -1), ("bot", hh, 1)):
                    seg = next(sg for sg in seqs[hk] if sg[0] - 1e-6 <= t < sg[1] + 1e-6)
                    key = (hk, seg[0])
                    if key not in rd:
                        for kk in [k_ for k_ in rd if k_[0] == hk]: rd[kk].close(); del rd[kk]
                        rd[key] = ef.Reader(srcs[seg[2]]["file"], srcs[seg[2]]["sync"] + seg[0], seg[1] - seg[0] + 0.2)
                    img = rd[key].read(); part = fill(img, W2, hh, srcs[seg[2]].get("x_center", 0.5))
                    u = min(1, (t - seg[0]) / 0.25); e = 1 - (1 - u) ** 3; dx = int(dirn * W2 * (1 - e))   # 수평 패닝 슬라이드
                    if dx:
                        prev = fr[yy:yy + hh].copy(); M = np.float32([[1, 0, dx], [0, 1, 0]]); part = cv2.warpAffine(part, M, (W2, hh), borderMode=cv2.BORDER_REPLICATE)
                    fr[yy:yy + hh] = part
                fr[hh - 3:hh + 3] = 255
                emit(fr, t); frame_i += 1
            for r in rd.values(): r.close()
            continue
        si = sis[0]; S = srcs[si]; rd = ef.Reader(S["file"], S["sync"] + t0, t1 - t0 + 0.2)
        for fi in range(f0, f1):
            t = fi / FPS2; u = t - t0; img = rd.read(); fr = fill(img, W2, H2, S.get("x_center", 0.5))
            if kind == "change":     # 크래시 줌: 0.15초 급확대 후 유지
                e = 1 - (1 - min(1, u / 0.15)) ** 3; fr = ef.zoom_at(fr, 0.5, 0.38, 1 + 0.3 * e)
            elif kind == "jump":     # 15도 롤링 셰이크
                p = u / max(1e-6, t1 - t0); deg = ex["sign"] * SB["roll_deg"] * math.sin(math.pi * p)
                fr = ef.rotate_shake(fr, deg, 1.18)
            elif kind == "pump":     # 박자마다 펌핑 + 진동
                s_ = 1 + 0.08 * abs(math.cos(math.pi * (t - phase) / beat)); fr = ef.rotate_shake(fr, 0.6 * math.sin(t * 50), s_, 7 * math.sin(2 * math.pi * 23 * t), 5 * math.sin(2 * math.pi * 29 * t))
            emit(fr, t, si); frame_i += 1
        rd.close()
    # 엔딩 5초 고정 레이아웃
    oc = dict(spec.get("outro", {})); of = oc.get("frame") or {"file": srcs[0]["file"], "t": srcs[0]["sync"] + 10}
    end = total - frame_i / FPS2
    ef.outro_render(write, W2, H2, frame_i / FPS2, end, ef.grab(of["file"], of["t"]), oc, [o for o in fixed if o.t1 > total])
    wr.stdin.close(); wr.wait()
    apath = os.path.join(tmp, "a.wav")
    ef.build_audio([(sf, song["start"], total, 0.0, spec.get("song_volume", 1.0), 0.05, 1.5)], total, apath, loudnorm=T.get("loudnorm", True))   # 내레이션 없이 현장음 loudnorm
    out = os.path.join(outdir, spec["out"] + suffix + ".mp4"); ef.mux(vpath, apath, out, total)
    # 썸네일: 2분할 장면 한 장 대신 v2 썸네일(첫 소스)
    th = spec.get("thumb") or {}
    tf = th.get("frame") or {"file": srcs[0]["file"], "t": srcs[0]["sync"] + 3}
    from PIL import Image
    img = Image.fromarray(cv2.cvtColor(fill(ef.grab(tf["file"], tf["t"]), W2, H2), cv2.COLOR_BGR2RGB))
    thp = os.path.join(outdir, spec["out"] + "_thumb.png")
    fx.thumb_v2(img, dict(th, quote=th.get("quote", ""), source=spec.get("source_line", ""), test=spec.get("test_label")), (W2, H2), thp) if th.get("quote") else img.save(thp)
    spec["_beat"] = {"bpm": bpm, "phase": phase, "confidence": conf, "change8_shots": n8}
    lines, ok = cs.run(spec, [out])
    print(f"영상: {out}\n썸네일: {thp}\n박자: {bpm} bpm (첫 박 {phase}s, 신뢰도 {conf}) · 체인지(훅) {n8}컷")
    print("\n".join(lines)); print("→ 표준 v2 점검 통과" if ok else "→ ❌ 확인")
    return out, thp, lines, ok

if __name__ == "__main__":
    _entry(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
