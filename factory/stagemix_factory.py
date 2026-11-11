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

if __name__ == "__main__":
    main(sys.argv[1])
