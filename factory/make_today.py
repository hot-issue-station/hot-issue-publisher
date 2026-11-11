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
- 제작 표준 v2(11/11): --templates-dir templates_v2 → 월·수·금·일 19:00 쇼츠(expose=스타일 A / pulse58=스타일 B), 화·토 19:00 몰아보기(molabogi).
  v2 틀은 옛 점검표(숫자 확인·5줄)를 쓰지 않고, 렌더 뒤 check_standard.py(standard_v2.json 기준)를 자동으로 돌린다. docs/표준v2_사용법.md
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
SLOTS = {"아침": "07:30", "점심": "12:00", "저녁": "18:30"}
PH = re.compile(r"\{([^{}]+)\}")
TEMPLATES = os.path.join(HERE, "templates")   # --templates-dir 로 바꿀 수 있음(기본은 그대로)
LABEL = {"가수": "가수 이름", "곡": "곡 이름", "숫자": "주인공 숫자(예: 555104)", "순위": "순위(예: 3)",
         "순위표": "순위표 [[순위, 이름, 곡, 숫자], ...]", "카드": "카드 문장 [{\"big\":..., \"small\":...}, ...]",
         "배경": "배경 사진 파일", "출처": "출처·기준 줄(1~2줄)", "확인": "숫자·사실 확인 기록(확인한 곳·시각)",
         "클립": "무대 클립 {\"A\": [파일, 노래와 맞는 시각], ...}", "음원": "노래 파일", "bpm": "노래 빠르기(bpm)",
         "저작권확인": "저작권·팬캠 양해 확인(true)", "롱폼": "롱폼 예고 문구", "단위": "숫자 단위",
         "제목": "화면 위 제목(괄호 드립 가능)", "소스": "무대 소스 [{\"file\",\"sync\",\"label\"}, ...] 8개 이상", "노래": "노래 {\"file\",\"start\"}",
         "썸네일": "썸네일 {\"quote\"(실제 대사),\"hook\",\"frame\":{file,t}}", "기획": "몰아보기 롱폼 기획 파일(.json)",
         "길이": "쇼츠 길이 58 또는 40(40이면 40-N/40-M)", "내레이션": "Veda 내레이션 [{\"at\",\"file\"?,\"text\"}]"}

def stop(lines):
    print("❌ 아직 만들 수 없어요. 아래를 채워 주세요:")
    for l in lines: print("  - " + l)
    sys.exit(2)

def load_preset(day, slot):
    p = os.path.join(TEMPLATES, f"{day}_{slot}.json")
    if not os.path.exists(p): stop([f"틀 파일이 없어요: {os.path.relpath(p, HERE)}"])
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

V2_KINDS = ("expose", "pulse58", "molabogi")

def build_v2(preset, fill, fill_dir, name):
    """표준 v2 틀 → 공장 spec. 대표가 정하는 칸: 쇼츠 A(클립·제목·출처·썸네일), 쇼츠 B(소스·노래·제목·출처·저작권확인), 몰아보기(기획 파일)."""
    import check_standard as cs
    STD = cs.STD; vals = dict(preset.get("defaults", {})); vals.update({k: v for k, v in fill.items() if v not in ("", None)})
    kind = preset["template"]; problems = []
    for k in preset["need"]:
        if k not in vals or vals[k] in ("", None, [], {}, False): problems.append(f"{k}: {LABEL.get(k, k)}")
    missing = {}
    post = fill_text(preset["post"], vals, missing, "게시 문구"); tags = [t.replace(" ", "") for t in fill_text(preset["hashtags"], vals, missing, "해시태그")]
    for k, ws in missing.items():
        if not any(p.startswith(k + ":") for p in problems): problems.append(f"{k}: {LABEL.get(k, k)} (쓰이는 곳: {', '.join(sorted(ws))})")
    tk = preset.get("shorts_template")
    if kind in ("expose", "pulse58"):      # fill "길이": 40 → 같은 계열 40초 판(58-N→40-N, 58-M→40-M)
        tk = tk or STD["shorts_templates_default"][kind]
        if str(vals.get("길이", "")).startswith("40"): tk = "40-" + tk.split("-")[1]
        if str(vals.get("길이", "")).startswith("58"): tk = "58-" + tk.split("-")[1]
    common = {"out": name, "template": kind, "shorts_template": tk, "_preset": f"{preset['day']}_{preset['slot']}", "_time": preset.get("time", STD["schedule"]["time"]),
              "_slot_up": STD["schedule"]["uploader_slot"], "post": dict(post, tags=tags), "checked": vals.get("확인", ""),
              "source": [vals["출처"]] if isinstance(vals.get("출처"), str) else (vals.get("출처") or []),
              "_vals": {"가수": vals.get("가수", ""), "곡": vals.get("곡", vals.get("제목", ""))}, "series": preset["series"]}
    def absf(p_):
        q = resolve(p_, fill_dir) if p_ else None
        if not q: problems.append(f"파일을 찾을 수 없어요 → {p_}")
        return q or p_
    if kind == "expose":
        clips = [dict(c) for c in (vals.get("클립") or [])]
        for i, c in enumerate(clips):
            if not all(k in c for k in ("file", "in", "out", "role")): problems.append(f"클립 {i + 1}번째: file·in·out·role 이 있어야 해요"); continue
            c["file"] = absf(c["file"])
        ft = lambda k_: fill_text(preset.get(k_, {}), vals, missing, k_)
        spec = dict(common, title=vals.get("제목", ""), series_name=vals.get("시리즈이름", preset["series"] + (" · " + vals["시리즈"] if vals.get("시리즈") else "")),
                    source_line=common["source"][0] if common["source"] else "",
                    clips=clips, brand=dict(ft("brand"), **vals.get("브랜드", {})), outro=dict(ft("outro"), **vals.get("아웃트로", {})),
                    thumb=dict(ft("thumb"), **vals.get("썸네일", {})), clean_ranges=vals.get("본편구간", []), forbidden_ranges=vals.get("금지구간", []))
        for k_ in ("outro", "thumb"):
            fr_ = spec[k_].get("frame")
            if fr_: fr_["file"] = absf(fr_["file"])
        if clips and not problems:   # 렌더 전에 구간 시간 미리 확인(점검기와 같은 계산)
            S, got, body = cs.actual_A(spec)
            for n, a, b in S[:-1]:
                g = got.get(n)
                if not g or abs(g[0] - a) > 0.05 or abs(g[1] - b) > 0.05: problems.append(f"구간 {n}: {a:g}~{b:g}초여야 해요" + (f" (지금 {g[0]:.2f}~{g[1]:.2f})" if g else " (없음)"))
        spec["_est_sec"] = STD["shorts_templates"][tk]["total_sec"]
        if vals.get("내레이션"): spec["narration"] = vals["내레이션"]
    elif kind == "pulse58":
        srcs = [dict(x) for x in (vals.get("소스") or [])]
        for x in srcs: x["file"] = absf(x.get("file", ""))
        T_ = STD["shorts_templates"][tk]
        if srcs and len(srcs) < T_["min_sources"]: problems.append(f"소스: {tk} 은 {T_['min_sources']}개 이상이어야 해요 (지금 {len(srcs)}개)")
        if srcs and T_.get("max_sources") and len(srcs) > T_["max_sources"]: problems.append(f"소스: {tk} 은 {T_['max_sources']}개 이하(지금 {len(srcs)}개)")
        song = dict(vals.get("노래") or {}); 
        if song: song["file"] = absf(song.get("file", ""))
        spec = dict(common, preset="pulse58", song=song, sources=srcs, title=vals.get("제목", ""), source_line=common["source"][0] if common["source"] else "",
                    outro=dict(fill_text(preset.get("outro", {}), vals, missing, "outro"), **vals.get("아웃트로", {})), copyright_checked=bool(vals.get("저작권확인")), _est_sec=STD["shorts_templates"][tk]["total_sec"])
        if vals.get("bpm"): spec["bpm"] = vals["bpm"]
        if vals.get("썸네일"): spec["thumb"] = dict(preset.get("thumb", {}), **vals["썸네일"])
    else:   # molabogi: 롱폼 기획 파일(longform_factory 형식 + v2.2 몰아보기 칸)
        p_ = absf(vals.get("기획", "")); lf = json.load(open(p_, encoding="utf-8")) if p_ and os.path.exists(p_) else {}
        spec = dict(lf, **{k: v for k, v in common.items() if k not in ("source",)}); spec["template"] = "molabogi"; spec["_spec_dir"] = os.path.dirname(p_) if p_ else fill_dir
        en = dict(preset.get("ending", {})); en.update(lf.get("ending", {})); spec["ending"] = en
        spec["_est_sec"] = STD["molabogi"]["target_sec"]
    return spec, problems

def precheck_v2(spec):
    import check_standard as cs
    hits = cs.check_words(spec); src = bool(spec.get("source_line") or spec.get("source") or spec.get("credits") or any(sc.get("credit") for ch in spec.get("chapters", []) for sc in ch.get("scenes", [])))
    items = [("출처 표시", src), ("금지어 없음" + (" — " + ", ".join(hits) if hits else ""), not hits),
             ("게시 제목·설명", bool(spec.get("post", {}).get("title") and spec.get("post", {}).get("desc")))]
    if spec["template"] == "pulse58": items.append(("저작권·팬캠 양해 확인", spec.get("copyright_checked")))
    return [("✅ " if ok else "❌ 빠짐: ") + n for n, ok in items], all(ok for _, ok in items)

def render_v2(spec, outdir):
    """표준 v2 렌더 → check_standard 결과를 spec 파일(_v2_check)에 남김(package.py 가 읽음)."""
    import shorts_factory as sf
    sp = os.path.join(outdir, spec["out"] + "_spec.json")
    if spec["template"] == "expose":
        import expose_factory as ef
        json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        vids, th, lines, ok = ef.main(sp, outdir)
    elif spec["template"] == "pulse58":
        import stagemix_factory as sm
        _, th, lines, ok = sm.pulse58(json.loads(json.dumps(spec)), outdir, outdir)
    else:
        import longform_factory as lf, check_standard as cs
        s2 = json.loads(json.dumps(spec)); s2["_out_dir"] = outdir; s2["_tmp_dir"] = os.path.join(outdir, "_tmp_" + spec["out"])
        res = lf.build(s2, spec.get("_spec_dir", outdir)); lines, ok = cs.run(spec, [res["final"]])
        print("■ 표준 v2 점검"); print("\n".join(lines)); print("→ 통과" if ok else "→ 위반 있음(❌)")
    if spec["template"] in ("expose", "pulse58"):
        spec["post"].setdefault("first_comment", spec.get("outro", {}).get("ask", ""))
        sf.post_text(spec, outdir)
    spec["_v2_check"] = lines
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return ok

def build(preset, fill, fill_dir, name):
    if preset["template"] in V2_KINDS: return build_v2(preset, fill, fill_dir, name)
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
    spec = {"out": name, "channel": preset.get("channel", "덕심저장소"), "series": series, "title": hook["title"], "question": hook["question"],
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
    elif kind == "clips":   # 원본 영상 하이라이트(shorts_factory clips 틀). 클립 = [{"file","in","out","credit"}, ...]
        C = preset.get("clips", {}); cl = []
        for i, c in enumerate(vals.get("클립") or []):
            p = resolve(c.get("file", ""), fill_dir) if isinstance(c, dict) else None
            if not p or "in" not in c or "out" not in c: problems.append(f"클립 {i+1}번째: {{\"file\",\"in\",\"out\",\"credit\"}} 확인 → {c}"); continue
            cl.append(dict(c, file=p, **{"in": float(c["in"]), "out": float(c["out"])}))
        spec.update(template="clips", clips=cl, hook=hook["question"], top_bar={"channel": vals.get("채널", vals.get("가수", "")), "title": hook["title"]},
                    source_line=src[0] if src else "", original_sub_note=vals.get("원본자막", C.get("original_sub_note", True)),
                    layout=vals.get("배치", C.get("layout", "fit")), end_sec=C.get("end_sec", 3.5))
        if src and len(src) > 1: spec["source"] = src
        est = sum(c["out"] - c["in"] for c in cl) + spec["end_sec"]
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
    if spec["template"] in V2_KINDS: return render_v2(spec, outdir)
    import shorts_factory as sf
    c = spec.get("_colors", {})
    if c.get("tag"): sf.RD = hexrgb(c["tag"])
    if c.get("summary"): sf.PB = hexrgb(c["summary"])
    if c.get("number"): sf.Y = hexrgb(c["number"])
    if spec["template"] in ("rank", "cards", "clips"):
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
    if os.path.basename(TEMPLATES.rstrip(os.sep)) == "templates_v2":   # 표준 v2 편성(19:00 한 번)
        print("요일 | 시각 | 틀")
        for d in DAYS:
            p = os.path.join(TEMPLATES, f"{d}_저녁.json")
            if not os.path.exists(p): print(f"{d} | - | 쉼"); continue
            q = json.load(open(p, encoding="utf-8")); print(f"{d} | {q.get('time')} | {q['series']} ({q['template']})")
        return
    print("요일 | 아침 07:30 | 점심 12:00 | 저녁 18:30")
    for d in DAYS:
        row = []
        for s in SLOTS:
            if TEMPLATES != os.path.join(HERE, "templates") and not os.path.exists(os.path.join(TEMPLATES, f"{d}_{s}.json")):
                row.append("-"); continue   # 다른 틀 폴더는 빈 칸이 있어도 됨(예: 미용실 주 3회)
            p = load_preset(d, s); row.append(f"{p['series'].split(' · ')[0]}({p['template']}, ~{p['length']['target_sec']}초)")
        print(f"{d} | " + " | ".join(row))

def main():
    ap = argparse.ArgumentParser(description="요일·시간대 템플릿 쇼츠 만들기")
    ap.add_argument("--day", choices=DAYS); ap.add_argument("--slot", choices=list(SLOTS))
    ap.add_argument("--fill"); ap.add_argument("--dry", action="store_true", help="spec 만 만들고 렌더하지 않음")
    ap.add_argument("--out-dir", help="결과 폴더(기본: factory/out/<날짜>_<요일>_<시간대>)")
    ap.add_argument("--list", action="store_true", help="편성표 보기")
    ap.add_argument("--templates-dir", help="틀 폴더(기본: factory/templates). 예: templates_salon")
    ap.add_argument("--package", action="store_true", help="렌더 뒤 게시 꾸러미(outbox/)·업로더 계획까지 만들기")
    ap.add_argument("--outbox", help="꾸러미 폴더(기본: factory/outbox)")
    ap.add_argument("--date", help="꾸러미 예약 날짜 YYYY-MM-DD(기본: 틀 요일의 다음 날짜)")
    ap.add_argument("--sites", help="업로더 계획에 넣을 곳(기본 youtube)")
    ap.add_argument("--ai", action="store_true", help="꾸러미 글이 한도를 넘으면 AI 교환대로 줄인 초안 사용")
    a = ap.parse_args()
    global TEMPLATES
    if a.templates_dir: TEMPLATES = os.path.abspath(a.templates_dir if os.path.isabs(a.templates_dir) or os.path.isdir(a.templates_dir) else os.path.join(HERE, a.templates_dir))
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
    print(f"틀: {a.day}요일 {a.slot}({preset.get('time', SLOTS[a.slot])}) · {preset['series']} · {spec['template']} · 예상 {spec['_est_sec']}초")
    if spec["template"] in V2_KINDS:
        print(f"제목: {spec.get('title', '')}  · 썸네일 대사: {(spec.get('thumb') or spec.get('thumb_v2') or {}).get('quote', '')}")
        print(f"spec: {sp}"); lines, ok = precheck_v2(spec)
    else:
        print(f"첫 3초: {spec['title']} / {spec['question']}")
        print(f"썸네일: {spec['thumb']['tag']} | {spec['thumb']['title']} | {spec['thumb']['question']} | {spec['thumb']['big']} | {spec['thumb']['summary']}")
        print(f"spec: {sp}")
        lines, ok = precheck(spec)
    print("\n".join(lines))
    if a.dry:
        print("(--dry: 렌더하지 않음)"); return
    if not ok: stop(["점검표에 빠진 것이 있어 렌더하지 않았어요(위 ❌ 참고)"])
    ok = render(spec, outdir)
    if a.package and spec["template"] == "molabogi":
        print("ℹ️ 몰아보기(롱폼)는 쇼츠 꾸러미 대상이 아니에요 — 롱폼 업로드 순서로"); return
    if a.package:
        import package
        if not ok: print("⚠️ 점검표에 ❌가 있어요. 꾸러미는 만들지만 업로더 계획은 통과하지 못합니다.")
        sites = [s.strip() for s in a.sites.split(",")] if a.sites else None
        _, _, probs = package.make_package(outdir, a.outbox, a.date, sites, a.ai)
        if probs: sys.exit(1)

if __name__ == "__main__":
    main()
