"""표준 v2 자동 점검기 — 기획 JSON + 렌더 결과(mp4)를 standard_v2.json 기준으로 점검해 통과/위반 목록을 낸다.
사용법:
  python3 check_standard.py 기획.json 결과.mp4 [--json]
종류(template): expose(쇼츠 A) · pulse58(쇼츠 B) · molabogi(롱폼 몰아보기). 그 밖의 롱폼 spec 은 기준서 v1 항목만.
점검: 쇼츠 템플릿별 길이(58-N·58-M 58.0 / 40-N·40-M 40.0, ±0.05, 모든 플랫폼 같은 파일) · 해상도 · 구간 순서·시간 · 금지어(제목·썸네일·큰 자막·우리 자막·게시 문구) · 출처 표시 ·
      정지 화면(8초 초과) · 기준서 v1 필수 요소(롱폼: 하이라이트 3초·질문 25초 무렵·출처·엔딩) · 금지·광고 구간 · 따옴표 대사 · 술·담배·도박·성인 광고 단어.
돌려주는 값(코드에서): run(spec, videos) → (lines, ok)
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STD = json.load(open(os.path.join(HERE, "standard_v2.json"), encoding="utf-8"))

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,duration,width,height,sample_rate", "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}"); st = j.get("streams", [])
    v = next((s for s in st if s.get("codec_type") == "video"), {}); a = next((s for s in st if s.get("codec_type") == "audio"), None)
    return {"dur": float(j.get("format", {}).get("duration", 0) or 0), "vdur": float(v.get("duration", 0) or 0), "w": v.get("width"), "h": v.get("height"),
            "audio": bool(a), "adur": float((a or {}).get("duration", 0) or 0), "sr": int((a or {}).get("sample_rate", 0) or 0)}

def freezes(path, limit):
    """ffmpeg freezedetect 로 limit 초 넘게 멈춘 화면 찾기."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf", f"freezedetect=n=0.003:d={limit}", "-an", "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]; en = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r.stderr)]
    return [(a, en[i] if i < len(en) else None) for i, a in enumerate(st)]

def tkey(spec):
    """쇼츠 템플릿 이름(58-N·58-M·40-N·40-M). spec "shorts_template" 이 없으면 엔진 기본값."""
    return spec.get("shorts_template") or STD["shorts_templates_default"].get(spec.get("template"), "58-N")

def tconf(spec): return STD["shorts_templates"][tkey(spec)]

def stretched_sections(sections, roles, total):
    """플랫폼 길이에 맞게 늘릴 구간(roles)만 비례로 늘린 구간표."""
    base = sections[-1][2]; extra = total - base
    if abs(extra) < 1e-6: return [tuple(s) for s in sections]
    grow = sum(b - a for n, a, b in sections if n in roles); out = []; t = 0.0
    for n, a, b in sections:
        d = (b - a) * (1 + extra / grow) if n in roles else (b - a); out.append((n, round(t, 3), round(t + d, 3))); t += d
    return out

def texts_of(spec):
    """금지어 검사 대상 글: (어디, 글, 큰 글씨 여부)."""
    T = [("제목", spec.get("title", "")), ("시리즈", spec.get("series_name", spec.get("series", "")))]
    for k, v in (spec.get("thumb") or {}).items():
        if isinstance(v, str): T.append((f"썸네일 {k}", v))
    for k, v in (spec.get("post") or {}).items():
        if isinstance(v, str): T.append((f"게시 {k}", v))
    for i, c in enumerate(spec.get("clips", []) if isinstance(spec.get("clips"), list) else []):
        for cap in c.get("captions", []): T.append((f"{i + 1}번 클립 자막({cap.get('style', 'bracket')})", cap.get("text", "")))
    for k in ("ask", "next"): T.append((f"아웃트로 {k}", (spec.get("outro") or {}).get(k, "")))
    op = spec.get("opening") or {}
    if op.get("highlight"): T.append(("오프닝 대사", op["highlight"].get("line", "")))
    if op.get("question"): T.append(("오프닝 질문", op["question"]))
    for ch in spec.get("chapters", []):
        T.append(("챕터 제목", ch.get("title", "")))
        for sc in ch.get("scenes", []):
            for s in sc.get("subs", []): T.append(("자막", s[2] if len(s) > 2 else ""))
            for r in sc.get("reacts", []): T.append(("반응 말풍선", r.get("text", "")))
    for k, v in (spec.get("ending") or {}).items():
        if isinstance(v, str): T.append((f"엔딩 {k}", v))
    return T

def check_words(spec):
    words = STD["banned_words"] + list(spec.get("banned_words", []))
    hits = [f"{w}「{x}」" for w_, t in texts_of(spec) for x in words if x in str(t) for w in [w_]]
    return hits

def check_ad_words(spec):
    """광고 구간 표시(클립·장면의 ad·note·_장면, 상품 카드 이름)에 술·담배·도박·성인 단어."""
    bad = []; ws = STD["ad_exclude_words"]
    def look(where, d):
        for key in ("ad", "note", "_장면", "name"):
            v = d.get(key)
            if isinstance(v, str) and any(w in v for w in ws): bad.append(f"{where} {key}: {v}")
    for i, c in enumerate(spec.get("clips", []) if isinstance(spec.get("clips"), list) else []): look(f"{i + 1}번 클립", c)
    for ch in spec.get("chapters", []):
        for sc in ch.get("scenes", []): look("장면", sc)
    for p in spec.get("product_cards", []): look("상품 카드", p)
    return bad

def check_ranges(spec):
    bad = []; clips = spec.get("clips") if isinstance(spec.get("clips"), list) else []
    scenes = [sc for ch in spec.get("chapters", []) for sc in ch.get("scenes", []) if "in" in sc]
    lead = STD["style_A"]["audio_lead_sec"]
    for i, c in enumerate(clips + scenes):
        if "in" not in c: continue
        L = c.get("audio_lead", c.get("lead", (0.0 if i == 0 else lead) if c in clips else 0.0)); a, b = c["in"] - L, c["out"]
        for x, y in spec.get("forbidden_ranges", []):
            if max(a, x) < min(b, y): bad.append(f"{i + 1}번 구간({a:.1f}~{b:.1f})이 금지 구간 {x}~{y}와 겹침")
        if spec.get("clean_ranges") and not any(x - 1e-6 <= a and b <= y + 1e-6 for x, y in spec["clean_ranges"]):
            bad.append(f"{i + 1}번 구간({a:.1f}~{b:.1f})이 본편 구간 밖(광고 의심)")
    return bad

def check_quotes(spec):
    q = [t for w, t in texts_of(spec) if ("자막" in w or "말풍선" in w) and any(ch in str(t) for ch in "\"“”")]
    return q

def shorts_sections(spec, total=None):
    T = tconf(spec); S = T["sections"]
    roles = STD["style_A"]["stretch_roles"] if T["engine"] == "expose" else []
    return stretched_sections(S, roles, total or T["total_sec"])

def stretch_clips(spec, total, fps=None):
    """스타일 A 플랫폼 버전: 늘릴 역할(standard_v2 style_A.stretch_roles) 클립의 out 을 비례로 늘린 클립 목록(프레임 단위, 합이 정확히 맞게).
    공장(expose_factory)과 점검기가 같은 함수를 쓴다."""
    fps = fps or STD["shorts"]["fps"]; roles = STD["style_A"]["stretch_roles"]; clips = [dict(c) for c in spec["clips"]]
    S = shorts_sections(spec, total)
    if abs(total - tconf(spec)["total_sec"]) < 1e-6: return clips
    idx = [i for i, c in enumerate(clips) if c.get("role") in roles]
    base = sum(clips[i]["out"] - clips[i]["in"] for i in idx); target = sum(b - a for n, a, b in S if n in roles)
    if not idx or abs(target - base) < 1e-6: return clips
    f = target / base; tf = round(target * fps); acc = 0
    for k, i in enumerate(idx):
        c = clips[i]; n = round((c["out"] - c["in"]) * f * fps) if k < len(idx) - 1 else tf - acc
        acc += n; c["out"] = c["in"] + n / fps
    return clips

def actual_A(spec, total=None):
    """스타일 A 계열(58-N·40-N): 클립 역할별 실제 시각."""
    total = total or tconf(spec)["total_sec"]; S = shorts_sections(spec, total); t = 0.0; got = {}
    for c in stretch_clips(spec, total):
        d = round((c["out"] - c["in"]) * 30) / 30
        r = c.get("role", ""); a, b = got.get(r, (t, t)); got[r] = (min(a, t), t + d); t += d
    return S, got, t

def mood_uses(spec):
    """기획에 실제로 들어간 연출 요소."""
    caps = [c for cl in (spec.get("clips") if isinstance(spec.get("clips"), list) else []) for c in cl.get("captions", [])]
    subs = [x for ch in spec.get("chapters", []) for sc in ch.get("scenes", []) for x in sc.get("subs", [])]
    styles = {c.get("style", "bracket") for c in caps} | {x[3] for x in subs if len(x) > 3}
    scenes = [sc for ch in spec.get("chapters", []) for sc in ch.get("scenes", [])]
    clips = spec.get("clips") if isinstance(spec.get("clips"), list) else []
    u = set()
    if "bracket" in styles: u.add("bracket")
    if "sfx" in styles or any(c.get("sfx") for c in clips + scenes) or spec.get("sfx"): u.add("sfx")
    if any(c.get("zooms") for c in clips + scenes) or spec.get("template") == "pulse58": u.add("crash_zoom")
    if spec.get("music_cut") or any(sc.get("music_cut") for sc in scenes): u.add("music_cut")
    if "emotion" in styles: u.add("emotion")
    if spec.get("template") == "pulse58": u |= {"fast_cut", "shake"}
    if len(spec.get("chapters", [])) >= 2: u.add("chapters")
    if spec.get("template") == "expose" or any(sc.get("audio_lead") for sc in scenes): u.add("j_cut")
    if spec.get("chapters") and spec.get("xfade_sec", 0.3) > 0: u.add("dissolve")
    txt = [c.get("text", "") for c in caps] + [str(x[2]) for x in subs if len(x) > 2]
    if any(any(ch.isdigit() for ch in t) for t in txt): u.add("number_captions")
    if spec.get("template") == "rank" or spec.get("rank_cards"): u.add("rank_cards")
    return u

def mood_lines(spec):
    """주문 moods → 프리셋 요소가 기획에 들어갔는지(알림, 통과 여부에는 안 들어감)."""
    mp = spec.get("mood_preset") or {}; out = []
    if not mp: return out
    used = mood_uses(spec)
    for g, conf in mp.items():
        miss = [x for x in conf.get("use", []) if x not in used and x not in ("slow_cut",)]
        out.append(("ℹ️ " if not miss else "⚠️ ") + f"분위기 「{g}」({conf.get('note', '')})" + (f" — 기획에 없음: {', '.join(miss)}" if miss else " 반영됨"))
    return out

def long_conf(spec):
    k = spec.get("long_template")
    return (k, STD["long_templates"][k]) if k in STD.get("long_templates", {}) else (None, None)

def run(spec, videos):
    items = []; tol = STD["shorts"]["tolerance_sec"]; kind = spec.get("template")
    for v in videos:
        if not os.path.exists(v): items.append((f"결과 파일 있음: {v}", False)); continue
        P = probe(v); tag = os.path.basename(v)
        if kind in ("expose", "pulse58"):
            T = tconf(spec); sec = T["total_sec"]   # 템플릿별 길이(58.0 / 40.0), 모든 플랫폼 같은 파일
            items.append((f"[{tag}] 쇼츠 템플릿 {tkey(spec)} ({'내레이션+자막' if T['narration'] else '무대·음악, 내레이션 없음'})", True))
            items.append((f"[{tag}] 길이 {sec:.1f}초 ±{tol} (지금 {P['dur']:.2f} · 영상 {P['vdur']:.2f} · 소리 {P['adur']:.2f})",
                          abs(P["dur"] - sec) <= tol and abs(P["vdur"] - sec) <= tol))
            items.append((f"[{tag}] 해상도 {STD['shorts']['size'][0]}x{STD['shorts']['size'][1]} (지금 {P['w']}x{P['h']})", [P["w"], P["h"]] == STD["shorts"]["size"]))
            items.append((f"[{tag}] 소리 {STD['shorts']['audio_hz']}Hz", P["audio"] and P["sr"] == STD["shorts"]["audio_hz"]))
            S = shorts_sections(spec, sec)
            if kind == "expose":
                _, got, body = actual_A(spec, sec)
                for n, a, b in S[:-1]:
                    g = got.get(n); ok = bool(g) and abs(g[0] - a) <= tol and abs(g[1] - b) <= tol
                    items.append((f"[{tag}] 구간 {n} {a:g}~{b:g}" + (f" (실제 {g[0]:.2f}~{g[1]:.2f})" if g else " (없음)"), ok))
                order = [c.get("role") for c in spec["clips"]]; want = [n for n, _, _ in S[:-1]]
                seq = [r for i, r in enumerate(order) if i == 0 or r != order[i - 1]]
                items.append((f"[{tag}] 구간 순서 {'→'.join(want)}", seq == want))
                o = S[-1]; items.append((f"[{tag}] 아웃트로 {o[2] - o[1]:g}초 ({o[1]:g}~{o[2]:g})", abs(sec - body - T["outro_sec"]) <= tol))
                if T["narration"]:
                    nn = spec.get("narration") or []
                    nf = sum(1 for n in nn if n.get("file") and os.path.exists(n["file"]))
                    items.append((f"[{tag}] 내레이션 자리 {len(nn)}개 ({T.get('narrator', '')} 파일 {nf}개, 나머지는 자막)", bool(nn)))
            else:
                items.append((f"[{tag}] 구간표 " + " / ".join(f"{n} {a:g}~{b:g}" for n, a, b in S), True))
                n_src = len(spec.get("sources", [])); lo = T.get("min_sources", 1); hi = T.get("max_sources")
                items.append((f"[{tag}] 소스 {lo}개 이상" + (f" {hi}개 이하" if hi else "") + f" (지금 {n_src})", n_src >= lo and (not hi or n_src <= hi)))
                if not T["narration"]: items.append((f"[{tag}] 내레이션 트랙 없음(현장음 loudnorm)", not spec.get("narration")))
            fz = freezes(v, STD["longform_v1"]["max_still_sec"])
            items.append((f"[{tag}] 정지 화면 {STD['longform_v1']['max_still_sec']:g}초 초과 없음" + (f" — {fz}" if fz else ""), not fz))
        else:   # 롱폼(몰아보기 포함)
            items.append((f"[{tag}] 해상도 {P['w']}x{P['h']} (롱폼 1920x1080)", (P["w"], P["h"]) == (1920, 1080)))
            items.append((f"[{tag}] 소리 있음", P["audio"]))
            fz = freezes(v, STD["longform_v1"]["max_still_sec"])
            items.append((f"[{tag}] 정지 화면 {STD['longform_v1']['max_still_sec']:g}초 초과 없음" + (f" — {fz}" if fz else ""), not fz))
            lk, LT = long_conf(spec)
            if LT and not spec.get("test_sections_check"):
                lo, hi = LT["range_sec"]; items.append((f"[{tag}] 롱폼 {lk}({LT['name']}) 길이 {lo}~{hi}초 (지금 {P['dur']:.1f})", lo <= P["dur"] <= hi))
            if LT and not LT["narration"]:
                nn = [n for ch in spec.get("chapters", []) for sc in ch.get("scenes", []) for n in (sc.get("narration") or [])]
                items.append((f"[{tag}] {lk}: 내레이션 없음(무대·음악)", not nn and not spec.get("narration")))
            if kind == "molabogi" and spec.get("test_sections_check"):
                ts = STD["molabogi"]["test_sections"]; end = ts[-1][2]
                items.append((f"[{tag}] 시험 조각 길이 {end}초 ±0.5 (지금 {P['dur']:.2f})", abs(P["dur"] - end) <= 0.5))
    # 글·출처·구간
    hits = check_words(spec)
    items.append(("금지어 없음(" + ", ".join(STD["banned_words"]) + ")" + (" — " + ", ".join(hits) if hits else ""), not hits))
    has_src = bool(spec.get("source_line")) or bool(spec.get("sources")) or (isinstance(spec.get("clips"), list) and spec["clips"] and all(c.get("credit") for c in spec["clips"])) \
        or any(sc.get("credit") for ch in spec.get("chapters", []) for sc in ch.get("scenes", []))
    items.append(("출처 표시(화면 출처 줄/credit)", has_src))
    rspecs = [spec]
    if kind == "expose": rspecs.append(dict(spec, clips=stretch_clips(spec, tconf(spec)["total_sec"])))
    bad = sorted({b for sp in rspecs for b in check_ranges(sp)}); items.append(("금지 구간·광고 구간 안 씀" + (" — " + "; ".join(bad) if bad else ""), not bad))
    ad = check_ad_words(spec); items.append(("술·담배·도박·성인 광고 구간 없음" + (" — " + "; ".join(ad) if ad else ""), not ad))
    q = check_quotes(spec); items.append(("우리 자막에 따옴표 대사 없음(드립은 괄호)" + (" — " + " / ".join(q) if q else ""), not q))
    if kind not in ("expose", "pulse58"):   # 기준서 v1 필수 요소
        op = spec.get("opening") or {}; hl = op.get("highlight") or {}
        hd = (hl.get("out", 0) - hl.get("in", 0)) if hl else 0
        items.append((f"기준서 v1: 오프닝 하이라이트 약 {STD['longform_v1']['highlight_sec']:g}초 (지금 {hd:.1f})", bool(hl) and abs(hd - STD["longform_v1"]["highlight_sec"]) <= 1.0))
        qa = op.get("question_at"); lo, hi = STD["longform_v1"]["question_window"]
        items.append((f"기준서 v1: 질문 {lo}~{hi}초 사이 (지금 {qa})", bool(op.get("question")) and qa is not None and lo <= qa <= hi))
        items.append(("기준서 v1: 엔딩(다음 편·질문)", bool(spec.get("ending"))))
    return [("✅ " if ok else "❌ ") + n for n, ok in items] + mood_lines(spec), all(ok for _, ok in items)

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="표준 v2 자동 점검"); ap.add_argument("spec"); ap.add_argument("videos", nargs="+")
    ap.add_argument("--json", action="store_true"); a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8")); lines, ok = run(spec, a.videos)
    if a.json: print(json.dumps({"ok": ok, "lines": lines}, ensure_ascii=False, indent=1))
    else: print("■ 표준 v2 점검 — " + os.path.basename(a.spec)); print("\n".join(lines)); print("→ 통과" if ok else "→ 위반 있음(❌)")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
