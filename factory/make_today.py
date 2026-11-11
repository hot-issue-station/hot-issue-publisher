"""요일·시간대 템플릿으로 오늘 쇼츠 만들기
사용법:
  python3 make_today.py --day 수 --slot 저녁 --fill fill.json          # spec 만들고 바로 렌더
  python3 make_today.py --day 수 --slot 저녁 --fill fill.json --dry    # spec 만 만들고 점검(렌더 안 함)
  python3 make_today.py --day 수 --slot 저녁 --fill fill.json --package # 렌더 뒤 게시 꾸러미까지(outbox/)
  python3 make_today.py --list                                          # 편성표 보기
- 틀: templates/<요일>_<시간대>.json (요일 월~일, 시간대 아침·점심·저녁)
- 대표가 정하는 빈칸만 fill.json 에 쓴다(가수·곡·숫자·순위표·카드·클립·출처·확인 등). docs/templates.md 참고.
- 빈칸이 빠지면 무엇이 빠졌는지 알려 주고 멈춘다.
- rank·cards 는 shorts_factory.py, stagemix 는 stagemix_factory.py 로 렌더하고 기존 점검표를 그대로 돌린다.
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
SLOTS = {"아침": "07:30", "점심": "12:00", "저녁": "18:30"}
PH = re.compile(r"\{([^{}]+)\}")
LABEL = {"가수": "가수 이름", "곡": "곡 이름", "숫자": "주인공 숫자(예: 555104)", "순위": "순위(예: 3)",
         "순위표": "순위표 [[순위, 이름, 곡, 숫자], ...]", "카드": "카드 문장 [{\"big\":..., \"small\":...}, ...]",
         "배경": "배경 사진 파일", "출처": "출처·기준 줄(1~2줄)", "확인": "숫자·사실 확인 기록(확인한 곳·시각)",
         "클립": "무대 클립 {\"A\": [파일, 노래와 맞는 시각], ...}", "음원": "노래 파일", "bpm": "노래 빠르기(bpm)",
         "저작권확인": "저작권·팬캠 양해 확인(true)", "롱폼": "롱폼 예고 문구", "단위": "숫자 단위"}

def stop(lines):
    print("❌ 아직 만들 수 없어요. 아래를 채워 주세요:")
    for l in lines: print("  - " + l)
    sys.exit(2)

def load_preset(day, slot):
    p = os.path.join(HERE, "templates", f"{day}_{slot}.json")
    if not os.path.exists(p): stop([f"틀 파일이 없어요: templates/{day}_{slot}.json"])
    return json.load(open(p, encoding="utf-8"))

def man(n):
    m, r = divmod(int(n), 10000)
    return f"{m}만 {r:,}" if m and r else (f"{m}만" if m else f"{r:,}")

def show(v):
    """빈칸에 들어갈 글자. 숫자는 '55만 5,104'처럼."""
    if isinstance(v, bool): return str(v)
    if isinstance(v, (int, float)): return man(v) if v >= 10000 else (f"{v:g}")
    return str(v)

def fill_text(t, vals, missing, where):
    if isinstance(t, list): return [fill_text(x, vals, missing, where) for x in t]
    if isinstance(t, dict): return {k: (v if k.startswith("_") else fill_text(v, vals, missing, f"{where}.{k}")) for k, v in t.items()}
    if not isinstance(t, str): return t
    def rep(m):
        k = m.group(1)
        if k not in vals or vals[k] in ("", None):
            missing.setdefault(k, set()).add(where); return m.group(0)
        return show(vals[k])
    return PH.sub(rep, t)

def resolve(path, fill_dir):
    if os.path.isabs(path): return path
    for b in (fill_dir, HERE):
        q = os.path.join(b, path)
        if os.path.exists(q): return os.path.abspath(q)
    return None

def rng(a, b): return f"{a}" if a == b else f"{a}~{b}"

def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def build(preset, fill, fill_dir, name):
    vals = dict(preset.get("defaults", {})); vals.update({k: v for k, v in fill.items() if v not in ("", None)})
    kind = preset["template"]; problems = []
    if kind == "stagemix" and "숫자" not in fill and isinstance(vals.get("클립"), dict):
        vals["숫자"] = len({v[0] for v in vals["클립"].values()})   # 무대 개수 = 클립 파일 수
    # 1) 필수 재료
    for k in preset["need"]:
        if k not in vals or vals[k] in ("", None, [], {}, False):
            problems.append(f"{k}: {LABEL.get(k, k)}")
    # 2) 파일 존재
    files = {}
    for k in ("배경", "음악", "음원", "썸네일사진"):
        if vals.get(k):
            p = resolve(vals[k], fill_dir)
            if not p: problems.append(f"{k}: 파일을 찾을 수 없어요 → {vals[k]}")
            files[k] = p
    # 3) 글 틀 채우기
    missing = {}
    hook = fill_text(preset["hook"], vals, missing, "첫 3초")
    thumb = fill_text(preset["thumb"], vals, missing, "썸네일")
    end = fill_text(preset["end"], vals, missing, "끝 화면")
    tags = [t.replace(" ", "") for t in fill_text(preset["hashtags"], vals, missing, "해시태그")]
    post = fill_text(preset["post"], vals, missing, "게시 문구")
    series = fill_text(preset["series"], vals, missing, "시리즈")
    for k, ws in missing.items():
        if not any(p.startswith(k + ":") for p in problems):
            problems.append(f"{k}: {LABEL.get(k, k)} (쓰이는 곳: {', '.join(sorted(ws))})")
    src = vals.get("출처", []); src = [src] if isinstance(src, str) else src
    spec = {"out": name, "channel": "덕심저장소", "series": series, "title": hook["title"], "question": hook["question"],
            "source": src, "checked": vals.get("확인", ""), "end": end, "thumb": thumb,
            "post": dict(post, tags=tags), "bg": files.get("배경"), "bgm": files.get("음악"),
            "_preset": f"{preset['day']}_{preset['slot']}", "_colors": preset.get("colors", {}),
            "_vals": {"가수": vals.get("가수", ""), "곡": vals.get("곡", "")}}   # 꾸러미 폴더 이름용(package.py)
    if files.get("썸네일사진"): spec["thumb"]["photo"] = files["썸네일사진"]
    L = preset["length"]
    # 4) 종류별 재료
    if kind == "rank":
        R = preset["rank"]; rows = vals.get("순위표") or []
        if rows and not (R["rows_min"] <= len(rows) <= R["rows_max"]):
            problems.append(f"순위표: 이 시간대는 {rng(R['rows_min'], R['rows_max'])}줄이에요 (지금 {len(rows)}줄)")
        for i, r in enumerate(rows):
            if not (isinstance(r, list) and len(r) == 4): problems.append(f"순위표 {i+1}번째 줄: [순위, 이름, 곡, 숫자] 4칸이어야 해요")
        num = vals.get("숫자")
        if num is not None and not isinstance(num, (int, float)): problems.append("숫자: 숫자만 써 주세요(예: 555104)")
        spec.update(template="rank", rows=[[str(r[0]), r[1], r[2], r[3]] for r in rows if isinstance(r, list) and len(r) == 4],
                    unit=vals.get("단위", ""), row_gap=R["row_gap"], min_body_sec=L["target_sec"] - 3.8,
                    highlight={"name": vals.get("주인공", f"{vals.get('가수','')}"), "sub": vals.get("부제", f"「{vals.get('곡','')}」"),
                               "value": num if isinstance(num, (int, float)) else 0, "note": vals.get("메모", "")})
        n = len(spec["rows"]); t_src = 1.6 + n * R["row_gap"] + 0.8 + 3.8
        est = max(t_src + 3.5, spec["min_body_sec"]) + 3.8
    elif kind == "cards":
        C = preset["cards"]; cards = vals.get("카드") or []
        if cards and not (C["min"] <= len(cards) <= C["max"]):
            problems.append(f"카드: 이 시간대는 {rng(C['min'], C['max'])}장이에요 (지금 {len(cards)}장)")
        for i, c in enumerate(cards):
            if not (isinstance(c, dict) and c.get("big")): problems.append(f"카드 {i+1}번째: \"big\"(큰 글씨 한 줄)이 없어요")
            elif c.get("photo"):
                p = resolve(c["photo"], fill_dir)
                if not p: problems.append(f"카드 {i+1}번째 사진을 찾을 수 없어요 → {c['photo']}")
                c["photo"] = p
        spec.update(template="cards", cards=cards, card_sec=C["card_sec"], min_body_sec=L["target_sec"] - 3.8)
        est = max(1.2 + len(cards) * C["card_sec"] + 3.5, spec["min_body_sec"]) + 3.8
    else:
        S = preset["stagemix"]; clips = vals.get("클립") or {}
        cl = {}
        for k, v in clips.items():
            p = resolve(v[0], fill_dir) if isinstance(v, list) and v else None
            if not p: problems.append(f"클립 {k}: 파일을 찾을 수 없어요 → {v}")
            else: cl[k] = [p, float(v[1]) if len(v) > 1 else 0.0]
        bpm = vals.get("bpm") or 120
        plan = vals.get("편집") or auto_plan(list(cl), S["plan_pattern"], bpm, S["body_sec"])
        body = sum(b for _, _, b in plan) * 60 / bpm
        est = body + 4.0
        spec.update(template="stagemix", song=files.get("음원"), song_start=float(vals.get("노래시작", 0.0)), bpm=bpm,
                    clips=cl, plan=plan, sub=hook["question"], sources=src,
                    copyright_checked=bool(vals.get("저작권확인")))
        # 클립 길이 확인(잘린 장면 방지)
        for k, (p, sync) in cl.items():
            d = probe_dur(p)
            need = sync + body
            if d and need > d + 0.05: problems.append(f"클립 {k}: 영상이 {d:.1f}초인데 {need:.1f}초까지 필요해요(편집을 줄이거나 시각 확인)")
        if files.get("음원"):
            d = probe_dur(files["음원"]); need = spec["song_start"] + body
            if d and need > d + 0.05: problems.append(f"음원: {d:.1f}초인데 {need:.1f}초까지 필요해요")
    spec["_est_sec"] = round(est, 1)
    if est > L["max_sec"]: problems.append(f"길이: 예상 {est:.1f}초 — 이 시간대 최대 {L['max_sec']}초를 넘어요(줄·장 수를 줄여 주세요)")
    return spec, problems

def auto_plan(names, pattern, bpm, body_sec):
    """클립을 돌아가며 시간대별 효과 순서(plan_pattern)를 반복해 목표 길이를 채운다."""
    if not names: return []
    plan, t, i, beat = [], 0.0, 0, 60 / bpm
    while t + 1e-6 < body_sec:
        fx, beats = pattern[i % len(pattern)]
        beats = min(beats, max(1, round((body_sec - t) / beat)))
        a = names[i % len(names)]
        nm = f"{a}+{names[(i + 1) % len(names)]}" if fx == "split" else a
        plan.append([nm, fx, beats]); t += beats * beat; i += 1
    return plan

def probe_dur(p):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return None

def precheck(spec):
    """렌더 전 점검(기존 5줄 점검표 중 파일 없이 볼 수 있는 것)."""
    po = spec.get("post", {})
    items = [("끝 화면 문구", bool(spec["end"].get("lines"))),
             ("출처·기준 표시", bool(spec.get("source"))),
             ("숫자 확인 기록(확인한 곳·시각)", bool(spec.get("checked"))),
             ("썸네일·제목·소개글·첫 댓글", all([spec.get("thumb"), po.get("title"), po.get("desc"), po.get("first_comment")]))]
    if spec["template"] == "stagemix": items.append(("저작권·팬캠 양해 확인", spec.get("copyright_checked")))
    return [("✅ " if ok else "❌ 빠짐: ") + n for n, ok in items], all(ok for _, ok in items)

def render(spec, outdir):
    import shorts_factory as sf
    c = spec.get("_colors", {})
    if c.get("tag"): sf.RD = hexrgb(c["tag"])
    if c.get("summary"): sf.PB = hexrgb(c["summary"])
    if c.get("number"): sf.Y = hexrgb(c["number"])
    if spec["template"] in ("rank", "cards"):
        v, dur, t_end = sf.render(spec, outdir)
        th = sf.thumbnail(spec, outdir); pt = sf.post_text(spec, outdir)
        lines, ok = sf.checklist(spec, v, dur, t_end)
        print(f"영상: {v} ({dur:.1f}초)\n썸네일: {th}\n게시 문구: {pt}")
        print("\n".join(lines)); print("→ 올려도 됨" if ok else "→ 빠진 것부터 채우기")
        return ok
    import stagemix_factory as sm
    sp = os.path.join(outdir, spec["out"] + "_spec.json")   # stagemix 는 spec 옆 out/ 에 만든다
    sm.main(sp)
    mixdir = os.path.join(outdir, "out"); v = os.path.join(mixdir, spec["out"] + ".mp4")
    shutil.move(v, os.path.join(outdir, spec["out"] + ".mp4")); v = os.path.join(outdir, spec["out"] + ".mp4")
    shutil.rmtree(os.path.join(outdir, "_tmp_mix"), ignore_errors=True)
    if not os.listdir(mixdir): os.rmdir(mixdir)
    if not spec.get("bg"):   # 썸네일 사진: 첫 클립 가운데 장면
        first = next(iter(spec["clips"].values()))
        fr = os.path.join(outdir, spec["out"] + "_frame.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{first[1] + 2:.2f}", "-i", first[0], "-frames:v", "1", fr])
        spec["bg"] = fr
    th = sf.thumbnail(spec, outdir); pt = sf.post_text(spec, outdir)
    lines, ok = precheck(spec)
    n_src = len({p[0] for p in spec["clips"].values()})   # stagemix_factory 점검표와 같은 기준
    lines.append(("✅ " if n_src >= 8 else "❌ 확인: ") + f"무대 소스 {n_src}개 (8개 이상 권장)"); ok = ok and n_src >= 8
    print(f"썸네일: {th}\n게시 문구: {pt}")
    print("\n".join(lines)); print("→ 올려도 됨" if ok else "→ 빠진 것부터 채우기")
    return ok

def print_table():
    print("요일 | 아침 07:30 | 점심 12:00 | 저녁 18:30")
    for d in DAYS:
        row = []
        for s in SLOTS:
            p = load_preset(d, s); row.append(f"{p['series'].split(' · ')[0]}({p['template']}, ~{p['length']['target_sec']}초)")
        print(f"{d} | " + " | ".join(row))

def main():
    ap = argparse.ArgumentParser(description="요일·시간대 템플릿 쇼츠 만들기")
    ap.add_argument("--day", choices=DAYS); ap.add_argument("--slot", choices=list(SLOTS))
    ap.add_argument("--fill"); ap.add_argument("--dry", action="store_true", help="spec 만 만들고 렌더하지 않음")
    ap.add_argument("--out-dir", help="결과 폴더(기본: factory/out/<날짜>_<요일>_<시간대>)")
    ap.add_argument("--list", action="store_true", help="편성표 보기")
    ap.add_argument("--package", action="store_true", help="렌더 뒤 게시 꾸러미(outbox/)·업로더 계획까지 만들기")
    ap.add_argument("--outbox", help="꾸러미 폴더(기본: factory/outbox)")
    ap.add_argument("--date", help="꾸러미 예약 날짜 YYYY-MM-DD(기본: 틀 요일의 다음 날짜)")
    ap.add_argument("--sites", help="업로더 계획에 넣을 곳(기본 youtube)")
    ap.add_argument("--ai", action="store_true", help="꾸러미 글이 한도를 넘으면 AI 교환대로 줄인 초안 사용")
    a = ap.parse_args()
    if a.list: return print_table()
    miss = [n for n, v in (("--day(요일: 월~일)", a.day), ("--slot(시간대: 아침·점심·저녁)", a.slot), ("--fill(빈칸 파일)", a.fill)) if not v]
    if miss: stop(miss)
    if not os.path.exists(a.fill): stop([f"빈칸 파일이 없어요: {a.fill}"])
    try: fill = json.load(open(a.fill, encoding="utf-8"))
    except json.JSONDecodeError as e: stop([f"빈칸 파일 형식이 틀렸어요({e.lineno}번째 줄): {a.fill}"])
    preset = load_preset(a.day, a.slot)
    name = fill.get("이름") or f"{datetime.date.today():%Y%m%d}_{a.day}_{a.slot}"
    spec, problems = build(preset, fill, os.path.dirname(os.path.abspath(a.fill)), name)
    if problems: stop(problems)
    outdir = os.path.abspath(a.out_dir or os.path.join(HERE, "out", name)); os.makedirs(outdir, exist_ok=True)
    sp = os.path.join(outdir, name + "_spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"틀: {a.day}요일 {a.slot}({SLOTS[a.slot]}) · {preset['series']} · {spec['template']} · 예상 {spec['_est_sec']}초")
    print(f"첫 3초: {spec['title']} / {spec['question']}")
    print(f"썸네일: {spec['thumb']['tag']} | {spec['thumb']['title']} | {spec['thumb']['question']} | {spec['thumb']['big']} | {spec['thumb']['summary']}")
    print(f"spec: {sp}")
    lines, ok = precheck(spec); print("\n".join(lines))
    if a.dry:
        print("(--dry: 렌더하지 않음)"); return
    if not ok: stop(["점검표에 빠진 것이 있어 렌더하지 않았어요(위 ❌ 참고)"])
    ok = render(spec, outdir)
    if a.package:
        import package
        if not ok: print("⚠️ 점검표에 ❌가 있어요. 꾸러미는 만들지만 업로더 계획은 통과하지 못합니다.")
        sites = [s.strip() for s in a.sites.split(",")] if a.sites else None
        _, _, probs = package.make_package(outdir, a.outbox, a.date, sites, a.ai)
        if probs: sys.exit(1)

if __name__ == "__main__":
    main()
