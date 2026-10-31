"""움직이는 릴스(약 30초. 표지는 0초부터 글이 다 보이게 — 쇼츠 미리보기·첫인상용, 1080x1920, 무음) — 사진은 천천히 확대·이동, 글은 카드마다 한 줄씩 나타난다. (대표 요청 10/31 샘플)

python scripts/make_reel_motion.py rounds/<파일>.json /home/claude/reels/<이름>.mp4 [both|photo|text] [패턴 A|B|C|D|auto]
- 대표 결정(10/31 20:04): 사진+글 같이(both)로 가되, 같은 움직임이 반복되면 지루하므로 패턴 4가지를 돌려 쓴다.
  auto(기본) = 릴스 ID(파일 이름) 기준으로 A→B→C→D 순환. 같은 날 연속 릴스가 같은 패턴이 되지 않게 한다.
  A 잔잔한 줌: 사진 천천히 확대/축소 교대, 글이 아래에서 떠오름, 전환 페이드
  B 슬라이드: 사진 좌→우 / 우→좌로 흐름, 글이 왼쪽에서 밀려 들어옴, 전환 옆으로 밀기
  C 팝 줌: 사진이 크게 시작해 빠지며 드러남, 글이 살짝 커지며 톡 나타남, 전환 원형 열림·줌
  D 와이프: 사진 대각선 이동, 글이 왼쪽부터 쓱 그려지듯 드러남, 전환 위로 닦기·블러 교대
- 카드 내용은 make_post.cards() 그대로(세로 전체 화면 레이아웃). 카드 HTML에 CSS 애니메이션을 넣고,
  Playwright로 프레임마다 애니메이션 시각을 정확히 맞춰 찍은 뒤 ffmpeg로 잇는다(끊김 없음).
"""
import json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_post  # noqa: E402

W, H, FPS = 1080, 1920, 30
DUR = [4.0, 4.6, 4.6, 4.6, 4.6, 4.2, 4.4]   # 장별 길이(초). 전환 0.4초 × 6 을 빼면 약 28.6초 + 끝 여유
XF = 0.4

ANIM_CSS = """
@keyframes kb-in {from{transform:scale(1.0) translate(0,0)} to{transform:scale(1.14) translate(-1.5%,-1.5%)}}
@keyframes kb-out{from{transform:scale(1.16) translate(1.5%,0)} to{transform:scale(1.02) translate(0,0)}}
@keyframes pan-r {from{transform:scale(1.15) translate(-5%,0)} to{transform:scale(1.15) translate(5%,0)}}
@keyframes pan-l {from{transform:scale(1.15) translate(5%,0)} to{transform:scale(1.15) translate(-5%,0)}}
@keyframes pop-out{from{transform:scale(1.35)} to{transform:scale(1.0)}}
@keyframes diag-a{from{transform:scale(1.18) translate(-4%,-4%)} to{transform:scale(1.18) translate(4%,4%)}}
@keyframes diag-b{from{transform:scale(1.18) translate(4%,-4%)} to{transform:scale(1.18) translate(-4%,4%)}}
@keyframes rise{from{opacity:0;transform:translateY(36px)} to{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-80px)} to{opacity:1;transform:none}}
@keyframes pop{0%{opacity:0;transform:scale(.86)} 70%{opacity:1;transform:scale(1.03)} 100%{opacity:1;transform:scale(1)}}
@keyframes wipe{from{clip-path:inset(0 100% 0 0)} to{clip-path:inset(0 0 0 0)}}
.kb{position:absolute;inset:0;z-index:-1;will-change:transform}
.rv{opacity:0;animation-duration:.55s;animation-timing-function:cubic-bezier(.2,.7,.2,1);animation-fill-mode:forwards}
.rv.wp{opacity:1;clip-path:inset(0 100% 0 0);animation-duration:.7s;animation-timing-function:ease-out}
"""

# 패턴: 사진 움직임(장마다 돌려 씀), 글 등장, 장 사이 전환(돌려 씀)
PATTERNS = {
    "A": {"photo": ["kb-in", "kb-out"], "text": "rise", "trans": ["fade"]},
    "B": {"photo": ["pan-r", "pan-l"], "text": "slidein", "trans": ["slideleft", "smoothleft"]},
    "C": {"photo": ["pop-out", "kb-in"], "text": "pop", "trans": ["circleopen", "zoomin", "fadeblack"]},
    "D": {"photo": ["diag-a", "diag-b"], "text": "wipe", "trans": ["wipeup", "hblur", "smoothup"]},
}

PREP_JS = r"""
(args) => {
  const [dur, idx, usePhoto, useText, photoAnims, textAnim] = args;
  // 1) 사진(배경 이미지) → 안쪽 층을 만들어 천천히 확대·이동
  let n = 0;
  document.querySelectorAll('div').forEach(el => {
    if (!usePhoto) return;
    const bg = getComputedStyle(el).backgroundImage || '';
    if (!bg.startsWith('url')) return;
    const cs = getComputedStyle(el);
    const kb = document.createElement('div');
    kb.className = 'kb';
    kb.style.backgroundImage = cs.backgroundImage; kb.style.backgroundPosition = cs.backgroundPosition;
    kb.style.backgroundSize = cs.backgroundSize; kb.style.backgroundRepeat = 'no-repeat';
    kb.style.animation = `${photoAnims[(idx + n) % photoAnims.length]} ${dur}s ${photoAnims[0]==='pop-out' && (idx+n)%2===0 ? 'cubic-bezier(.2,.7,.2,1)' : 'linear'} forwards`;
    el.style.backgroundImage = 'none';
    if (cs.position === 'static') el.style.position = 'relative';
    el.style.overflow = 'hidden'; el.style.isolation = 'isolate';
    el.prepend(kb); n++;
  });
  // 2) 글: 본문 칸(머리·꼬리 줄 사이)의 블록을 순서대로 하나씩 나타나게
  const wrap = document.body.firstElementChild.lastElementChild;   // padding 칸
  const kids = Array.from(wrap.children);
  const mids = kids.slice(1, -1);
  let items = [];
  const expand = (c, depth) => {
    const ch = Array.from(c.children).filter(x => !x.classList.contains('kb'));
    const isCol = getComputedStyle(c).flexDirection === 'column' || getComputedStyle(c).display === 'block';
    if (depth < 2 && ch.length > 1 && isCol) ch.forEach(x => expand(x, depth + 1)); else items.push(c);
  };
  mids.forEach(c => expand(c, 0));
  items = items.filter(x => x.offsetHeight > 0);
  const start = idx === 0 ? 0.15 : 0.35, gap = Math.min(0.55, (dur * 0.55) / Math.max(1, items.length));
  if (useText && idx > 0) items.forEach((x, k) => { x.classList.add('rv'); if (textAnim === 'wipe') x.classList.add('wp'); x.style.animationName = textAnim; x.style.animationDelay = (start + k * gap).toFixed(2) + 's'; });
  document.getAnimations().forEach(a => a.pause());
  return {photos: n, items: items.length};
}
"""


def main():
    rj, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    mode = sys.argv[3] if len(sys.argv) > 3 else "both"
    pat = sys.argv[4] if len(sys.argv) > 4 else "auto"
    if pat not in PATTERNS:   # auto: 릴스 이름 기준으로 순환
        import zlib
        pat = "ABCD"[zlib.crc32(out.stem.encode()) % 4]
    P = PATTERNS[pat]
    print("패턴", pat)
    r = json.loads(rj.read_text(encoding="utf-8"))
    make_post.LAYOUT = make_post.REEL
    pages = make_post.cards(r)
    make_post.LAYOUT = make_post.FEED
    work = pathlib.Path(tempfile.mkdtemp(prefix="motion_"))
    from playwright.sync_api import sync_playwright
    clips = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        N = len(pages)
        SEC = float(r.get("reelSeconds", 30))   # 특집은 round JSON 에 "reelSeconds": 60
        DURS = DUR if (N == 7 and SEC == 30) else [round(SEC / N + XF * (N - 1) / N, 2)] * N
        for i, html in enumerate(pages):
            dur = DURS[i]
            html = html.replace("</style>", ANIM_CSS + "</style>", 1)
            pg.set_content(html); pg.wait_for_timeout(300)
            info = pg.evaluate(PREP_JS, [dur, i, mode in ("both", "photo"), mode in ("both", "text"), P["photo"], P["text"]])
            fdir = work / f"c{i}"; fdir.mkdir()
            nfr = int(dur * FPS)
            for f in range(nfr):
                t = f / FPS * 1000
                pg.evaluate("t => document.getAnimations().forEach(a => { a.currentTime = t; })", t)
                pg.screenshot(path=str(fdir / f"{f:04d}.jpg"), type="jpeg", quality=88)
            clip = work / f"c{i}.mp4"
            subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(fdir / "%04d.jpg"), "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", str(clip)], check=True, capture_output=True)
            clips.append((clip, dur)); print(f"{i+1}장 {dur}s 사진 {info['photos']} 글 {info['items']}")
        b.close()
    # 장 사이 부드러운 전환(xfade) + 무음 오디오
    inputs, fl, last, off = [], [], "0:v", 0.0
    for k, (c, d) in enumerate(clips):
        inputs += ["-i", str(c)]
    for k in range(1, len(clips)):
        off += clips[k - 1][1] - XF
        lab = f"v{k}"
        tr = P["trans"][(k - 1) % len(P["trans"])]
        fl.append(f"[{last}][{k}:v]xfade=transition={tr}:duration={XF}:offset={off:.2f}[{lab}]")
        last = lab
    total = sum(d for _, d in clips) - XF * (len(clips) - 1)
    cmd = ["ffmpeg", "-y", *inputs, "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
           "-filter_complex", ";".join(fl), "-map", f"[{last}]", "-map", f"{len(clips)}:a", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"done {total:.1f}s -> {out}")


if __name__ == "__main__":
    main()
