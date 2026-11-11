"""제작 11단계 파이프라인 (대표 11/11 20:59 확정 — docs/제작표준_v2_제미나이프로토콜.md 맨 아래)
사용법: python3 pipeline.py <단계> 주문.json [--out out폴더]
  scenario  (4) 시나리오 md+json 초안 — 실제 장면 목록 칸(파일·구간·화면 속 실제 대사·우리 자막·출처)
  plan      (5) 필요한 영상 수·컷 목록·연출 프리셋(standard_v2.json)
  draft     (6) 첫 렌더. 내레이션 파일이 있으면 입히고, 없으면 원고 txt(500자씩)를 만들고 'Veda 생성 필요' 표시
  check     (7) check_standard.py + 3초 간격 모음 이미지 → 8단계(대표 컨펌) 대기
  confirm   (8) 대표 컨펌 기록 — 주문판 「컨펌」 버튼과 같은 일. 대표가 직접 누를 때만 쓴다
  final     (9) 완성 렌더 + 언어별 자막(srt)·번역 원고, 더빙판 원고·오디오 자리(오디오가 있으면 믹스)
  verify   (10) 자막·오디오 싱크(무음 구간 vs 자막 시각), 길이, 금지어
  package  (11) 플랫폼별 묶음(제목·설명·해시태그·첫 댓글 + 파일). 업로드는 하지 않는다
  status        지금 단계·남은 문제 보기
주문 형식(주문판): {id, format: shorts|long|cardreels|cardnews, narr, area, subs[], moods[], free, len(프리셋 또는 숫자), stage,
                  langMode: ko|subs|dub, langs[](자막), narrLangs[](더빙), plats[],  — 언어 10개: en ja zh-Hans zh-Hant es pt id th vi fr
                  spec(선택: 이미 있는 공장 기획 json 경로 — 시나리오 초안을 여기서 채움), sensitive, status}
각 단계는 out/<주문id>/state.json 에 stage·issues·files 를 남기고, 다음 단계는 이전 결과를 읽어 이어간다(처음부터 다시 안 함).
카드릴스는 shorts_factory 의 cards 틀로 연결, 카드뉴스는 저장소에 카드 만들기 스크립트가 없어 TODO.
"""
import argparse, datetime as dt, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
STD = json.load(open(os.path.join(HERE, "standard_v2.json"), encoding="utf-8"))
STAGES = {"scenario": 4, "plan": 5, "draft": 6, "check": 7, "confirm": 8, "final": 9, "verify": 10, "package": 11}
CHUNK = 500   # 내레이션 원고 한 파일 글자 수(Veda 생성 단위)
LANG_KO = dict([("ko", "한국어")] + [tuple(x) for x in STD["languages"]["list"]])   # 10개 언어(standard_v2.json languages)
PLAT_LIM = {"youtube": {"title": 100, "desc": 5000}, "instagram": {"desc": 2200}, "tiktok": {"desc": 2200}, "x": {"desc": 280}, "threads": {"desc": 500}, "facebook": {"desc": 2200}}

# ---------------- 주문 → 틀 ----------------
def num(x):
    try: return float(str(x).rstrip("초분장 "))
    except (TypeError, ValueError): return None

def type_of(o):
    """주문 → 템플릿. len 은 프리셋(쇼츠 58/40/25초, 롱폼 8/4/6/20/30분, 카드 7/10/12/20장) 또는 직접 입력 숫자."""
    if o.get("type"): return o["type"]
    n = "N" if o.get("narr", True) else "M"; L = num(o.get("len"))
    if o.get("format") == "long": return ("L4-" if L and L <= 5 else "L8-") + n
    if o.get("format") == "shorts": return ("40-" if L and L <= 40 else "58-") + n
    return o.get("format")

def length_sec(o):
    """주문 길이 → 초(쇼츠 상한 58.0). 템플릿 기본 길이와 같으면 None."""
    L = num(o.get("len")); typ = type_of(o)
    if not L: return None
    if o.get("format") == "shorts":
        L = min(L, STD["length_presets"]["shorts_max_sec"]); return None if abs(L - STD["shorts_templates"][typ]["total_sec"]) < 1e-6 else L
    if o.get("format") == "long": return L * 60
    return None

def tconf(typ):
    if typ in STD["shorts_templates"]: return "shorts", STD["shorts_templates"][typ]
    if typ in STD.get("long_templates", {}): return "long", STD["long_templates"][typ]
    return "card", {"engine": "cards", "narration": False, "sections": []}

def mood_preset(o):
    mp = {}
    for m in o.get("moods", [])[:STD["order"]["max_moods"]]:
        # 주문판 말꼴(「뭉클한」「소름 돋는」)도 표준표 낱말(「뭉클」「소름」)에 맞춘다
        g = next((k for k, v in STD["mood_presets"].items() if not k.startswith("_") and (m == k or m.startswith(k) or any(m == i or m.startswith(i) for i in v.get("items", [])))), None)
        if g: mp[g] = {k: v for k, v in STD["mood_presets"][g].items() if k != "items"}
    return mp

# ---------------- 상태 ----------------
def odir(o, out=None): return os.path.abspath(os.path.join(out or os.path.join(HERE, "out"), str(o.get("id") or "주문")))
def load_state(d):
    p = os.path.join(d, "state.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"stage": 3, "issues": [], "files": {}, "history": [], "waiting": False, "confirmed": False}
def save_state(d, st, stage, name, issues=None, files=None, waiting=False):
    st["stage"] = max(st.get("stage", 0), stage); st["stage_name"] = name; st["waiting"] = waiting
    st["issues"] = issues or []; st.setdefault("files", {}).update(files or {})
    st.setdefault("history", []).append({"stage": stage, "name": name, "at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "issues": len(st["issues"])})
    json.dump(st, open(os.path.join(d, "state.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"■ {stage}단계 {name} — 문제 {len(st['issues'])}개" + (" · 대표 차례(대기)" if waiting else ""))
    for i in st["issues"]: print("  - " + i)
    for k, v in (files or {}).items(): print(f"  {k}: {v}")
def need(st, stage, d):
    if st.get("stage", 3) < stage - 1: sys.exit(f"❌ {stage - 1}단계가 아직이에요(지금 {st.get('stage')}단계). 순서대로: scenario → plan → draft → check → (대표 컨펌) → final → verify → package")

def rel(d, p): return os.path.relpath(p, d)

# ---------------- 4 시나리오 ----------------
def scenario(o, d):
    typ = type_of(o); kind, T = tconf(typ); os.makedirs(d, exist_ok=True)
    if o.get("sensitive") and o.get("status") != STD["order"]["approved_status"]:
        sys.exit("⛔ 민감 주문 — 대표 확인 전에는 시나리오를 만들지 않아요(주문 status 를 approved 로)")
    base = {}
    if o.get("spec"):
        sp = o["spec"] if os.path.isabs(o["spec"]) else os.path.join(HERE, o["spec"]); base = json.load(open(sp, encoding="utf-8")); base["_base"] = os.path.dirname(sp)
    scenes = []
    if base.get("clips") and isinstance(base["clips"], list):
        for c in base["clips"]:
            scenes.append({"section": c.get("role"), "file": c["file"], "in": c["in"], "out": c["out"], "real_line": c.get("_real", ""),
                           "our_captions": [x["text"] for x in c.get("captions", [])], "source": c.get("credit") or base.get("source_line", "")})
    elif base.get("chapters"):
        for ch in base["chapters"]:
            for sc in ch["scenes"]:
                scenes.append({"section": ch.get("title"), "file": sc.get("file"), "in": sc.get("in"), "out": sc.get("out"), "real_line": "",
                               "our_captions": [x[2] for x in sc.get("subs", [])], "source": sc.get("credit", "")})
    else:   # 빈 칸: 구간마다 한 줄
        for n, a, b in T.get("sections", []):
            if n != "outro": scenes.append({"section": n, "file": "", "in": None, "out": None, "real_line": "(화면 속 실제 대사·자막)", "our_captions": [], "source": ""})
    narr = base.get("narration", []) if T.get("narration") else []
    Ls = length_sec(o)
    if Ls and kind == "shorts":
        import check_standard as cs_; T = cs_.tconf({"template": T["engine"], "shorts_template": typ, "length_sec": Ls})
    sc = {"order": o, "type": typ, "kind": kind, "length_sec": Ls, "sections": T.get("sections"), "title": base.get("title", o.get("free", "")),
          "scenes": scenes, "narration": narr, "spec_base": base, "rules": ["실제 장면·실제 대사만(멤버가 하지 않은 말을 따옴표로 쓰지 않음, 드립은 괄호)",
          "출처 표기(장면마다)", "금지어: " + ", ".join(STD["banned_words"]), "광고·술·담배·도박·성인 구간 제외"]}
    jp = os.path.join(d, "scenario.json"); json.dump(sc, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = [f"# 시나리오 초안 — 주문 {o.get('id')} ({typ})", "", f"- 형식: {o.get('format')} · 영역: {o.get('area', '')} · 소제목: {', '.join(o.get('subs', []))} · 분위기: {', '.join(o.get('moods', []))}",
         f"- 제목: {sc['title']}", f"- 구간표: " + " / ".join(f"{n} {a}~{b}" for n, a, b in (T.get("sections") or [])), "", "| # | 구간 | 파일 | 원본 시각 | 화면 속 실제 대사 | 우리 자막(괄호) | 출처 |", "|---|---|---|---|---|---|---|"]
    for i, s in enumerate(scenes, 1):
        L.append(f"| {i} | {s['section']} | {os.path.basename(s['file'] or '') or '(빈칸)'} | {s['in']}~{s['out']} | {s['real_line']} | {' / '.join(s['our_captions'])} | {s['source']} |")
    if narr: L += ["", "## 내레이션(Veda)"] + [f"- {n['at']}초: {n.get('text', '')}" for n in narr]
    L += ["", "## 지킬 것"] + [f"- {r}" for r in sc["rules"]]
    mp = os.path.join(d, "scenario.md"); open(mp, "w", encoding="utf-8").write("\n".join(L) + "\n")
    issues = [f"{i + 1}번 장면 빈칸(파일·구간)" for i, s in enumerate(scenes) if not s["file"] or s["in"] is None]
    if kind == "card" and o.get("format") == "cardnews": issues.append("TODO 카드뉴스: 저장소에 카드 만들기 스크립트가 없음 — 카드 템플릿 아티팩트(issuebrief-card-news) 연결 필요")
    return {"scenario.md": mp, "scenario.json": jp}, issues

# ---------------- 5 설계 ----------------
def plan(o, d):
    sc = json.load(open(os.path.join(d, "scenario.json"), encoding="utf-8")); typ = sc["type"]; kind, T = tconf(typ)
    if sc.get("length_sec") and kind == "shorts":   # 주문 길이(예 34초)대로 구간표를 다시 잰다
        import check_standard as cs_; T = cs_.tconf({"template": T["engine"], "shorts_template": typ, "length_sec": sc["length_sec"]})
    if T.get("engine") == "pulse58": n_src = f"{T.get('min_sources')}~{T.get('max_sources', '')}개 무대(같은 곡)"
    elif kind == "long": n_src = f"장면 {max(6, int(T['target_sec'] / 12))}개 안팎(평균 컷 2~5초, 원본 영상 3~6개)"
    elif kind == "shorts": n_src = f"원본 구간 {len(T['sections']) - 1}~{2 * (len(T['sections']) - 1)}개(원본 영상 1~3개)"
    else: n_src = "카드 7장 또는 12장"
    cuts = [{"#": i + 1, "section": s["section"], "file": os.path.basename(s["file"] or ""), "in": s["in"], "out": s["out"],
             "sec": round((s["out"] or 0) - (s["in"] or 0), 2)} for i, s in enumerate(sc["scenes"])]
    mp = mood_preset(o)
    methods = {"오프닝": "가장 센 장면 먼저 0~3초(U 자료13·14)", "잇기": f"J컷 {STD['style_A']['audio_lead_sec']}초(U 자료05)",
               "자막": "굵은 고딕 흰색+괄호 노랑, 원본 자막 보존(U 자료06·A)", "엔딩": "댓글 질문 + 다음 편 + 구독(U 자료07)",
               "소리": "현장음 loudnorm" + (", 내레이션 덕킹 −14dB" if T.get("narration") else ", 내레이션 없음")}
    pl = {"type": typ, "engine": T.get("engine"), "sections": T.get("sections"), "sources_needed": n_src, "cuts": cuts,
          "mood_preset": mp, "methods": methods, "total_sec": T.get("total_sec") or T.get("target_sec")}
    jp = os.path.join(d, "plan.json"); json.dump(pl, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = [f"# 편집 설계 — {typ} ({pl['total_sec']}초)", f"- 필요한 재료: {n_src}", "- 우선순위: 기준서 v1(언더독) → 안원잘부 → 제미나이", "", "## 연출 프리셋(분위기)"]
    L += [f"- {g}: {c['note']}" for g, c in mp.items()] or ["- (분위기 없음)"]
    L += ["", "## 편집 방법"] + [f"- {k}: {v}" for k, v in methods.items()] + ["", "## 컷 목록", "| # | 구간 | 파일 | 구간(초) | 길이 |", "|---|---|---|---|---|"]
    L += [f"| {c['#']} | {c['section']} | {c['file']} | {c['in']}~{c['out']} | {c['sec']} |" for c in cuts]
    md = os.path.join(d, "plan.md"); open(md, "w", encoding="utf-8").write("\n".join(L) + "\n")
    issues = []
    if kind == "shorts" and T["engine"] == "expose" and all(c["in"] is not None for c in cuts):
        body = sum(c["sec"] for c in cuts); want = T["total_sec"] - T["outro_sec"]
        if abs(body - want) > 0.05: issues.append(f"컷 합계 {body:.2f}초 — 본문은 {want:g}초여야 해요")
    return {"plan.md": md, "plan.json": jp}, issues

# ---------------- 6 첫 렌더 ----------------
def build_spec(o, d, sc, pl):
    """시나리오(+원래 기획) → 공장 spec."""
    base = dict(sc.get("spec_base") or {}); base.pop("_base", None)
    spec = json.loads(json.dumps(base)); spec["out"] = "draft"; spec["mood_preset"] = pl["mood_preset"]; spec["order"] = o
    kind, T = tconf(sc["type"])
    if kind == "shorts": spec["shorts_template"] = sc["type"]
    if sc.get("length_sec"): spec["length_sec"] = sc["length_sec"]
    if kind == "long": spec["long_template"] = sc["type"]
    return spec

def narration_scripts(o, d, narr):
    """내레이션 원고를 500자씩 txt 로(Veda 생성용). 이미 파일이 있는 줄은 빼고."""
    todo = [n for n in narr if not (n.get("file") and os.path.exists(n["file"]))]
    if not todo: return [], []
    text = "\n".join(f"[{n['at']}초] {n.get('text', '')}" for n in todo); files = []; i = 0; buf = ""
    os.makedirs(os.path.join(d, "narration"), exist_ok=True)
    for ln in text.split("\n"):
        if len(buf) + len(ln) + 1 > CHUNK and buf:
            i += 1; p = os.path.join(d, "narration", f"원고_{i:02d}.txt"); open(p, "w", encoding="utf-8").write(buf); files.append(p); buf = ""
        buf += ln + "\n"
    if buf: i += 1; p = os.path.join(d, "narration", f"원고_{i:02d}.txt"); open(p, "w", encoding="utf-8").write(buf); files.append(p)
    open(os.path.join(d, "narration", "README.txt"), "w", encoding="utf-8").write(
        "Veda 생성 필요: 원고_NN.txt 를 Veda 로 읽혀 narration/NN_<초>.mp3 로 저장 → draft 를 다시 돌리면 입혀짐(파일 없으면 자막으로 대신).\n")
    return files, [f"Veda 생성 필요: 내레이션 {len(todo)}줄 → 원고 {len(files)}개({CHUNK}자씩)"]

def attach_voice(d, narr):
    """narration/ 폴더에 <초>.mp3|wav 가 있으면 그 줄에 붙임."""
    vd = os.path.join(d, "narration")
    if not os.path.isdir(vd): return narr
    have = {}
    for f in os.listdir(vd):
        m = re.match(r"(?:\d+_)?([\d.]+)\.(mp3|wav|m4a)$", f)
        if m: have[float(m.group(1))] = os.path.join(vd, f)
    for n in narr:
        if not n.get("file") and float(n["at"]) in have: n["file"] = have[float(n["at"])]
    return narr

def render(spec, d, name):
    """엔진 실행 → (영상, 썸네일, 점검 줄, 통과)."""
    spec = json.loads(json.dumps(spec)); spec["out"] = name; sp = os.path.join(d, name + "_spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    t = spec.get("template")
    if t == "expose":
        import expose_factory as ef; vids, th, lines, ok = ef.main(sp, d); return vids[0], th, lines, ok
    if t == "pulse58":
        import stagemix_factory as sm; v, th, lines, ok = sm.pulse58(spec, d, d); return v, th, lines, ok
    if t in ("molabogi",) or spec.get("chapters"):
        import longform_factory as lf, check_standard as cs
        s2 = json.loads(json.dumps(spec)); s2["_out_dir"] = d; s2["_tmp_dir"] = os.path.join(d, "_tmp_" + name)
        res = lf.build(s2, spec.get("_spec_dir", d)); lines, ok = cs.run(spec, [res["final"]]); return res["final"], None, lines, ok
    if t == "cards":   # 카드릴스 → shorts_factory cards 틀(기존 저장소 기능 재사용)
        import shorts_factory as sf
        v, dur, t_end = sf.render(spec, d); th = sf.thumbnail(spec, d) if spec.get("thumb") else None
        lines, ok = sf.checklist(spec, v, dur, t_end); return v, th, lines, ok
    sys.exit(f"❌ 엔진을 모르는 기획(template={t}) — 카드뉴스는 TODO")

def draft(o, d):
    sc = json.load(open(os.path.join(d, "scenario.json"), encoding="utf-8")); pl = json.load(open(os.path.join(d, "plan.json"), encoding="utf-8"))
    kind, T = tconf(sc["type"]); issues = []; files = {}
    if kind == "card" and o.get("format") == "cardnews": return {}, ["TODO 카드뉴스 엔진 연결 안 됨"]
    spec = build_spec(o, d, sc, pl)
    if T.get("narration"):
        spec["narration"] = attach_voice(d, sc.get("narration", []))
        nf, ni = narration_scripts(o, d, spec["narration"]); issues += ni
        for i, f in enumerate(nf): files[f"내레이션 원고 {i + 1}"] = f
    # 장면 시각·파일이 비었거나 영상 파일이 아직 없으면 렌더하지 않고 멈춘다(원고는 위에서 이미 만듦)
    clips = spec.get("clips") or []
    gaps = [f"{i}번 장면 시각 빈칸" for i, c in enumerate(clips, 1) if c.get("in") is None or c.get("out") is None]
    gaps += sorted({f"영상 파일 없음: {os.path.basename(c['file'])}" for c in clips if c.get("file") and not os.path.exists(c["file"])})
    if gaps:
        json.dump(spec, open(os.path.join(d, "draft_spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return files, issues + gaps + ["재료가 채워지면 draft 를 다시 돌리세요"]
    v, th, lines, ok = render(spec, d, "draft")
    files.update({"draft.mp4": v, "draft 썸네일": th}); json.dump(spec, open(os.path.join(d, "draft_spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    issues += [l[2:] for l in lines if l.startswith("❌")]
    return files, issues

# ---------------- 7 1차 검토 ----------------
def contact_sheet(video, out, every=3.0, cols=6):
    """3초 간격 모음 이미지."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", video], capture_output=True, text=True)
    j = json.loads(r.stdout); dur = float(j["format"]["duration"]); w, h = j["streams"][0]["width"], j["streams"][0]["height"]
    n = int(dur // every) + 1; rows = (n + cols - 1) // cols; tw = 240 if h > w else 384; th_ = int(tw * h / w)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-vf",
                    f"fps=1/{every},scale={tw}:{th_},drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='%{{pts\\:hms}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{rows}",
                    "-frames:v", "1", out], check=True)
    return out

def check(o, d):
    import check_standard as cs
    spec = json.load(open(os.path.join(d, "draft_spec.json"), encoding="utf-8")); v = os.path.join(d, "draft.mp4")
    lines, ok = cs.run(spec, [v]); rp = os.path.join(d, "check_draft.txt"); open(rp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    sheet = contact_sheet(v, os.path.join(d, "draft_3초모음.jpg"))
    issues = [l[2:] for l in lines if l.startswith("❌")] + [l for l in lines if l.startswith("⚠️")]
    issues.append("Claude 눈 확인: draft_3초모음.jpg 로 이상한 장면·자막 가림 확인")
    return {"점검 결과": rp, "3초 모음": sheet}, issues

# ---------------- 8 대표 컨펌 ----------------
def confirm(o, d, st, note=""):
    st["confirmed"] = True; st["confirm_note"] = note; return {}, []

# ---------------- 9 완성 ----------------
def srt_time(t): t = max(0, t); h, r = divmod(int(t), 3600); m, s = divmod(r, 60); return f"{h:02}:{m:02}:{s:02},{int(round((t - int(t)) * 1000)) % 1000:03}"

def cues_of(spec):
    """화면 자막·내레이션 → 자막 줄(시각은 영상 전체 기준)."""
    C = []
    if isinstance(spec.get("clips"), list):
        t = 0.0
        for c in spec["clips"]:
            for cap in c.get("captions", []): C.append((t + cap["at"], t + cap["at"] + cap.get("dur", 1.8), cap["text"], "caption"))
            t += round((c["out"] - c["in"]) * 30) / 30
    for n in spec.get("narration", []) or []:
        d_ = n.get("sec") or round(0.8 + len(n.get("text", "")) * 0.14, 2); C.append((n["at"], n["at"] + d_, n.get("text", ""), "narration"))
    return sorted(C)

def write_srt(path, cues, tr=None):
    out = []
    for i, (a, b, t, k) in enumerate(cues, 1): out.append(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{tr(t) if tr else t}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out)); return path

def final(o, d, st):
    if not st.get("confirmed"): sys.exit("⛔ 8단계 대표 컨펌 전에는 완성 제작을 하지 않아요(주문판 「컨펌」 → pipeline.py confirm)")
    spec = json.load(open(os.path.join(d, "draft_spec.json"), encoding="utf-8")); spec["test_label"] = None
    spec["narration"] = attach_voice(d, spec.get("narration", []) or [])
    v, th, lines, ok = render(spec, d, "final"); files = {"final.mp4": v, "final 썸네일": th}; issues = [l[2:] for l in lines if l.startswith("❌")]
    json.dump(spec, open(os.path.join(d, "final_spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cues = cues_of(spec); files["자막 ko.srt"] = write_srt(os.path.join(d, "final.ko.srt"), cues)
    mode = o.get("langMode", "ko"); langs = [l for l in o.get("langs", []) if l != "ko"]
    dubs = [l for l in o.get("narrLangs", []) if l != "ko"] or (langs if mode == "dub" else [])
    for lg in [l for l in langs + dubs if l not in LANG_KO]: issues.append(f"모르는 언어 코드: {lg} (standard_v2.json languages 10개)")
    for lg in sorted(set(langs + dubs), key=(langs + dubs).index):
        tp = os.path.join(d, f"번역원고_{lg}.txt")
        open(tp, "w", encoding="utf-8").write(f"# {LANG_KO.get(lg, lg)} 번역 원고 — 줄 번호를 지키고 오른쪽 칸만 채우기\n" +
                                              "".join(f"{i}\t{t}\t\n" for i, (_, _, t, _) in enumerate(cues, 1)))
        tr_p = os.path.join(d, f"번역_{lg}.txt")
        if os.path.exists(tr_p):   # 번역이 들어왔으면 srt 로
            m = {int(x.split("\t")[0]): x.split("\t")[2].strip() for x in open(tr_p, encoding="utf-8") if re.match(r"\d+\t", x) and len(x.split("\t")) > 2}
            files[f"자막 {lg}.srt"] = write_srt(os.path.join(d, f"final.{lg}.srt"), [(a, b, m.get(i, t), k) for i, (a, b, t, k) in enumerate(cues, 1)])
        else: files[f"번역 원고 {lg}"] = tp; issues.append(f"번역 필요: {LANG_KO.get(lg, lg)} — 번역원고_{lg}.txt 오른쪽 칸을 채워 번역_{lg}.txt 로 저장")
        if lg in dubs:   # 더빙(narrLangs): 언어별 TTS 원고 + 오디오 자리
            dd = os.path.join(d, "dub", lg); os.makedirs(dd, exist_ok=True)
            open(os.path.join(dd, "TTS_원고.txt"), "w", encoding="utf-8").write("".join(f"[{a:.2f}초] {t}\n" for a, b, t, k in cues if k == "narration"))
            au = next((os.path.join(dd, f) for f in sorted(os.listdir(dd)) if f.endswith((".wav", ".mp3", ".m4a"))), None)
            if au:
                outv = os.path.join(d, f"final_{lg}_dub.mp4")
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", v, "-i", au, "-filter_complex",
                                "[0:a]volume=0.35[o];[1:a]aresample=48000[n];[o][n]amix=inputs=2:normalize=0:duration=first[a]", "-map", "0:v", "-map", "[a]",
                                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", outv], check=True)
                files[f"더빙판 {lg}"] = outv
            else: issues.append(f"더빙 오디오 자리: dub/{lg}/ 에 오디오를 넣으면 믹스(무료 Gemini TTS, TTS_원고.txt)")
    return files, issues

# ---------------- 10 최종 검토 ----------------
def speech_segments(video):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-af", "silencedetect=n=-35dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True)
    s = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]; e = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(s, e + [1e9] * (len(s) - len(e))))

def verify(o, d):
    import check_standard as cs
    spec = json.load(open(os.path.join(d, "final_spec.json"), encoding="utf-8")); v = os.path.join(d, "final.mp4")
    lines, ok = cs.run(spec, [v]); issues = [l[2:] for l in lines if l.startswith("❌")]
    sil = speech_segments(v); cues = cues_of(spec)
    def silent_frac(a, b): return sum(max(0, min(b, y) - max(a, x)) for x, y in sil) / max(1e-6, b - a)
    bad = []
    for a, b, t, k in cues:
        f = silent_frac(a, b)
        if k == "narration" and any(n.get("file") for n in spec.get("narration", [])) and f > 0.6: bad.append(f"{a:.1f}초 내레이션 자막인데 소리 거의 없음({f:.0%})")
        if k == "caption" and f > 0.95: bad.append(f"{a:.1f}초 자막 「{t}」 구간이 무음({f:.0%}) — 장면·자막 어긋남 확인")
    issues += bad
    for lg in o.get("langs", []):
        p = os.path.join(d, f"final.{lg}.srt")
        if lg != "ko" and not os.path.exists(p): issues.append(f"{LANG_KO.get(lg, lg)}({lg}) 자막 없음(번역 대기)")
    for lg in o.get("narrLangs", []):
        if lg != "ko" and not os.path.exists(os.path.join(d, f"final_{lg}_dub.mp4")): issues.append(f"{LANG_KO.get(lg, lg)}({lg}) 더빙 오디오 대기(dub/{lg}/)")
    rp = os.path.join(d, "verify.txt"); open(rp, "w", encoding="utf-8").write("\n".join(lines + ["", "■ 싱크"] + (bad or ["✅ 자막·소리 어긋남 없음"])) + "\n")
    return {"최종 검토": rp}, issues

# ---------------- 11 플랫폼 묶음 ----------------
def package(o, d):
    spec = json.load(open(os.path.join(d, "final_spec.json"), encoding="utf-8")); po = spec.get("post", {})
    plats = o.get("plats") or ["youtube", "instagram", "tiktok", "x", "threads"]; files = {}; issues = []
    tags = " ".join("#" + t.lstrip("#") for t in po.get("tags", []) + [s.replace(" ", "") for s in o.get("subs", [])][:3])
    src = spec.get("source_line") or ""
    for p in plats:
        pd = os.path.join(d, "package", p); os.makedirs(pd, exist_ok=True)
        shutil.copy2(os.path.join(d, "final.mp4"), os.path.join(pd, "video.mp4"))
        for f in os.listdir(d):
            if f.startswith("final") and f.endswith(".srt"): shutil.copy2(os.path.join(d, f), os.path.join(pd, f))
        if os.path.exists(os.path.join(d, "final_thumb.png")): shutil.copy2(os.path.join(d, "final_thumb.png"), os.path.join(pd, "thumb.png"))
        L = PLAT_LIM.get(p, {"desc": 2200}); title = po.get("title", spec.get("title", "")); desc = po.get("desc", "") + ("\n\n" + src if src else "") + "\n\n" + tags
        if p == "x": desc = (title + " " + tags)[:L["desc"]]
        if len(desc) > L["desc"]: desc = desc[:L["desc"] - 1] + "…"; issues.append(f"{p}: 설명을 {L['desc']}자로 줄임")
        txt = (f"제목: {title[:L.get('title', 100)]}\n" if p == "youtube" else "") + f"설명:\n{desc}\n" + (f"첫 댓글(고정): {po.get('first_comment', (spec.get('outro') or {}).get('ask', ''))}\n" if p == "youtube" else "")
        open(os.path.join(pd, "post.txt"), "w", encoding="utf-8").write(txt); files[p] = pd
    issues.append("업로드는 하지 않았어요 — 주문판 「올려」 버튼 뒤에만(대표 승인)")
    return files, issues

# ---------------- 실행 ----------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="제작 11단계 파이프라인")
    ap.add_argument("step", choices=list(STAGES) + ["status"]); ap.add_argument("order"); ap.add_argument("--out"); ap.add_argument("--note", default="")
    a = ap.parse_args(argv); o = json.load(open(a.order, encoding="utf-8")); d = odir(o, a.out); os.makedirs(d, exist_ok=True); st = load_state(d)
    if a.step == "status":
        print(json.dumps({k: st.get(k) for k in ("stage", "stage_name", "waiting", "confirmed", "issues")}, ensure_ascii=False, indent=1)); return 0
    n = STAGES[a.step]
    if n > 4: need(st, n, d)
    if a.step == "scenario": files, issues = scenario(o, d)
    elif a.step == "plan": files, issues = plan(o, d)
    elif a.step == "draft": files, issues = draft(o, d)
    elif a.step == "check":
        files, issues = check(o, d); save_state(d, st, 7, "1차 검토", issues, files); st = load_state(d)
        save_state(d, st, 8, "대표 컨펌 대기", ["대표 컨펌 대기 — 주문판 「컨펌 / 수정 요청」"], {}, waiting=True); st["stage"] = 7; json.dump(st, open(os.path.join(d, "state.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2); return 0
    elif a.step == "confirm": files, issues = confirm(o, d, st, a.note)
    elif a.step == "final": files, issues = final(o, d, st)
    elif a.step == "verify": files, issues = verify(o, d)
    else: files, issues = package(o, d)
    save_state(d, st, n, {4: "시나리오", 5: "편집 설계", 6: "첫 렌더", 8: "대표 컨펌", 9: "완성", 10: "최종 검토", 11: "플랫폼 묶음"}[n], issues, files)
    return 0

if __name__ == "__main__":
    sys.exit(main())
