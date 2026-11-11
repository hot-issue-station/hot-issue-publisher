"""게시 꾸러미 만들기 — make_today 결과 폴더 → 플랫폼 5곳 꾸러미 + 업로더 계획 파일
사용법:
  python3 package.py out/20261111_수_저녁                    # 꾸러미 만들기(유튜브만 업로더 계획)
  python3 package.py out/20261111_수_저녁 --date 2026-11-18  # 예약 날짜 직접 지정
  python3 package.py --replan outbox/20261111_수저녁_PULSE    # 대표가 txt 를 고친 뒤 계획·점검만 다시
  python3 package.py --check outbox/20261111_수저녁_PULSE/upload_plan.json   # 계획 파일 점검만
  (선택) --sites youtube,tiktok,meta,x  --outbox 다른폴더  --ai(한도 넘는 글을 AI 교환대로 줄인 초안 사용)
만드는 것: outbox/<날짜>_<요일><시간대>_<곡>/
  video.mp4 · thumb.jpg · youtube.txt · instagram.txt · tiktok.txt · x.txt · threads.txt · sources.md · checklist.txt
  upload_plan.json (uploader/run.py --plan 으로 읽는 형식, 기본 확인 모드·유튜브만)
글자 한도를 넘으면 해시태그부터 빼고, 그래도 넘으면 본문 끝을 「…」로 자르고 경고한다.
이 도구는 인터넷에 접속하지 않는다(--ai 를 켠 경우만 ai_router 사용). 아무 데도 올리지 않는다.
"""
import argparse, datetime as dt, glob, json, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "uploader"))
import upload_plan as up  # noqa: E402  (X 글자 수·해시태그·예약 시각·계획 형식을 업로더와 똑같이)

DAYS = ["월", "화", "수", "목", "금", "토", "일"]
SLOT_TIME = {"아침": "07:30", "점심": "12:00", "저녁": "18:30"}
SLOT_UP = {"아침": "출근", "점심": "점심", "저녁": "퇴근"}   # 업로더 시간대 이름
V2 = ("expose", "pulse58")   # 제작 표준 v2 쇼츠(standard_v2.json): 모든 칸 같은 파일 하나, 템플릿 길이(58.0/40.0) 넘으면 멈춤
STD2 = json.load(open(os.path.join(HERE, "standard_v2.json"), encoding="utf-8"))
def slot_time(spec, slot): return spec.get("_time") or SLOT_TIME[slot]          # v2 틀은 spec 에 19:00
def slot_up(spec, slot): return spec.get("_slot_up") or SLOT_UP[slot]          # v2 틀은 업로더 '저녁7시'
LIM = {"yt_title": 100, "yt_desc": 5000, "yt_tags": 500, "ig": 2200, "ig_tags": 30, "tt": 2200, "x": 280, "th": 500}
FILES = ["video.mp4", "thumb.jpg", "youtube.txt", "instagram.txt", "tiktok.txt", "x.txt", "threads.txt",
         "sources.md", "checklist.txt", "upload_plan.json"]


# ---------- 글자 수 맞추기 ----------
def tag_str(tags): return " ".join("#" + t.lstrip("#") for t in tags)


def cut(text, limit, measure=len):
    """measure 기준 limit 안으로 끝을 「…」로 자른다."""
    if measure(text) <= limit: return text
    out = ""
    for ch in text:
        if measure(out + ch + "…") > limit: break
        out += ch
    return out.rstrip() + "…"


def fit(body, tags, limit, measure=len, sep="\n\n", warns=None, where=""):
    """본문 + 해시태그를 limit 안에. 넘으면 ① 태그를 뒤에서부터 빼고 ② 본문을 자른다."""
    tags = list(tags)
    join = lambda b, t: b + (sep + tag_str(t) if t else "")
    full = measure(join(body, tags))
    while tags and measure(join(body, tags)) > limit: tags.pop()
    txt = join(body, tags)
    if measure(txt) > limit:
        room = limit - (measure(sep + tag_str(tags)) if tags else 0)
        txt = join(cut(body, room, measure), tags)
    if full > limit and warns is not None:
        warns.append(f"[{where}] {full}자 → {measure(txt)}자로 줄임(한도 {limit}) — 빠진 태그·잘린 끝을 확인하세요")
    return txt


def ai_shorten(text, limit, measure, where, notes):
    """--ai: 한도 넘는 글을 AI 교환대로 줄인 초안. 키·연결이 없거나 답이 한도를 넘으면 None."""
    try:
        import ai_router
        r = ai_router.route(f"아래 SNS 글을 뜻은 그대로 두고 {limit}자 안(한글 1자=2로 셈하는 곳도 있으니 짧게)으로 줄여 줘. "
                            f"숫자·고유명사·해시태그는 바꾸지 마. 줄인 글만 답해.\n\n{text}", max_tokens=600)
    except Exception as e:
        notes.append(f"[{where}] AI 다듬기 건너뜀({e.__class__.__name__})"); return None
    a = (r or {}).get("answer")
    if not a: notes.append(f"[{where}] AI 다듬기 건너뜀(답한 AI 없음 — 키 없음 등)"); return None
    if measure(a) > limit: notes.append(f"[{where}] AI 초안도 한도를 넘어 쓰지 않음"); return None
    notes.append(f"[{where}] AI 초안 사용({r['answered_by']}) — 초안이니 대표 확인 필요"); return a


# ---------- 읽기 ----------
def find_result(result_dir):
    sp = sorted(glob.glob(os.path.join(result_dir, "*_spec.json")))
    if not sp: raise SystemExit(f"❌ spec 파일(*_spec.json)이 없어요: {result_dir}  → make_today.py 로 먼저 만들기")
    spec = json.load(open(sp[0], encoding="utf-8")); name = spec["out"]
    video = os.path.join(result_dir, name + ".mp4"); thumb = os.path.join(result_dir, name + "_thumb.png")
    ptxt = os.path.join(result_dir, name + "_게시문구.txt")
    miss = [p for p in (video, thumb) if not os.path.exists(p)]
    if miss: raise SystemExit("❌ 렌더 결과가 없어요(--dry 로 만든 폴더일 수 있음):\n  - " + "\n  - ".join(miss))
    return spec, sp[0], video, thumb, ptxt


def song_of(spec):
    v = spec.get("_vals") or {}
    if v.get("곡"): return v["곡"], v.get("가수", "")
    m = re.search(r"「(.+?)」", spec.get("title", "") + spec.get("post", {}).get("title", ""))
    return (m.group(1) if m else spec["out"]), ""


def pick_date(day, slot, date=None, now=None, time=None):
    """템플릿 요일·시간대의 다음 예약 시각(지금부터 20분 이후). date 를 주면 그 날. time 을 주면 그 시각(v2: 19:00)."""
    now = now or dt.datetime.now(up.KST); h, m = map(int, (time or SLOT_TIME[slot]).split(":"))
    if date: return dt.date.fromisoformat(date)
    for add in range(0, 8):
        d = now.date() + dt.timedelta(days=add)
        t = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=up.KST)
        if DAYS[d.weekday()] == day and t >= now + dt.timedelta(minutes=up.MIN_LEAD_MIN): return d
    return now.date() + dt.timedelta(days=7)


def safe(s): return re.sub(r"[\\/:*?\"<>|\s]+", "", s)[:30] or "곡"


# ---------- 글 만들기 ----------
def make_texts(spec, post_override, use_ai=False):
    po = spec["post"]; warns, notes = [], []
    # 대표가 _게시문구.txt 를 고쳤으면 고친 칸만 우선(공장이 만든 그대로면 무시 — 태그 겹침 방지)
    base = up.parse_post_txt(up.post_txt_from_spec(spec)).get("youtube", {})
    yo = {k: v for k, v in post_override.get("youtube", {}).items() if v and v != base.get(k)}
    if yo.get("desc"):   # 설명 끝의 해시태그 줄은 빼고 본문만(태그는 아래에서 다시 붙임)
        yo["desc"] = re.sub(r"(\n\s*(#[^\s#]+\s*)+)+\s*$", "", "\n" + yo["desc"]).strip()
    if yo: notes.append("대표가 고친 _게시문구.txt 의 유튜브 " + "·".join({"title": "제목", "desc": "설명", "first_comment": "첫 댓글"}[k] for k in yo) + " 을(를) 씀")
    title = yo.get("title") or po["title"]; desc = yo.get("desc") or po["desc"]
    first = yo.get("first_comment") or po.get("first_comment", "")
    tags = [t.lstrip("#").replace(" ", "") for t in po.get("tags", []) if t.strip("# ")]
    src = spec.get("source") or []
    src_line = "\n".join("※ " + s for s in src)
    plain_title = up.strip_shorts_tag(title)
    T = {}

    # 유튜브: 제목 100 · 설명 5000 · 태그 합계 500
    if len(title) > LIM["yt_title"]:
        warns.append(f"[유튜브 제목] {len(title)}자 → 100자로 줄임")
        title = cut(up.strip_shorts_tag(title), LIM["yt_title"] - 8) + " #shorts"
    yd = fit(desc + ("\n\n" + src_line if src_line else ""), ["shorts"] + tags, LIM["yt_desc"], warns=warns, where="유튜브 설명")
    yt_tags = list(tags)
    while yt_tags and len(",".join(yt_tags)) > LIM["yt_tags"]: yt_tags.pop()
    if len(yt_tags) < len(tags): warns.append(f"[유튜브 태그] 합계 500자 넘어 {len(tags) - len(yt_tags)}개 뺌")
    T["youtube"] = (f"제목: {title}\n설명:\n{yd}\n태그: {', '.join(yt_tags)}\n첫 댓글(고정): {first}\n")

    def platform(key, body, tg, limit, measure=len, where="", sep="\n\n"):
        full = body + (sep + tag_str(tg) if tg else "")
        if use_ai and measure(full) > limit:
            a = ai_shorten(full, limit, measure, where, notes)
            if a: return a
        return fit(body, tg, limit, measure, sep=sep, warns=warns, where=where)

    # 인스타 릴스: 2200자 · 해시태그 30개
    ig_tags = tags[:LIM["ig_tags"]]
    if len(tags) > LIM["ig_tags"]: warns.append(f"[인스타] 해시태그 {len(tags)}개 → 30개로 줄임")
    T["instagram"] = platform("ig", f"{desc}\n\n{first}" + (f"\n\n{src_line}" if src_line else "") + "\n.", ig_tags, LIM["ig"], where="인스타")
    # 틱톡: 2200자
    T["tiktok"] = platform("tt", f"{plain_title}\n{desc}", tags, LIM["tt"], where="틱톡")
    # X: 280(한글 2·영문 1)
    T["x"] = platform("x", up.strip_shorts_tag(po.get("x") or plain_title), tags, LIM["x"], up.x_length, sep="\n", where="X")
    # 스레드: 500자, 주제 태그는 1개만 붙는다
    T["threads"] = platform("th", f"{desc}\n\n{first}" + (f"\n\n{src_line}" if src_line else ""), tags[:1], LIM["th"], where="스레드")
    if len(tags) > 1: notes.append("[스레드] 주제 태그는 글 하나에 1개만 붙어 첫 태그만 씀")
    for k in ("instagram", "tiktok", "x", "threads"):
        T[k] = up.strip_shorts_tag(T[k]) + "\n"   # #shorts 는 유튜브 전용
    meta = {"title": title, "desc": yd, "tags": yt_tags, "first_comment": first}
    return T, meta, warns, notes


def counts(T):
    yt = parse_youtube(T["youtube"])
    return [("youtube.txt 제목", len(yt["title"]), LIM["yt_title"]), ("youtube.txt 설명", len(yt["desc"]), LIM["yt_desc"]),
            ("youtube.txt 태그 합계", len(",".join(yt["tags"])), LIM["yt_tags"]),
            ("instagram.txt", len(T["instagram"].strip()), LIM["ig"]),
            ("instagram.txt 해시태그(개)", len(up.hashtags(T["instagram"])), LIM["ig_tags"]),
            ("tiktok.txt", len(T["tiktok"].strip()), LIM["tt"]),
            ("x.txt (한글 2 가중)", up.x_length(T["x"].strip()), LIM["x"]),
            ("threads.txt", len(T["threads"].strip()), LIM["th"])]


def parse_youtube(txt):
    g = lambda pat: (re.search(pat, txt, re.M | re.S) or [None, ""])[1].strip()
    tags = [t.strip() for t in g(r"^태그:\s*(.*?)$").split(",") if t.strip()]
    return {"title": g(r"^제목:\s*(.*?)$"), "desc": g(r"^설명:\s*\n(.*?)(?=^태그:|^첫 댓글|\Z)"),
            "tags": tags, "first_comment": g(r"^첫 댓글\(고정\):\s*(.*?)$")}


def read_texts(pkg):
    return {k: open(os.path.join(pkg, k + ".txt"), encoding="utf-8").read() for k in ("youtube", "instagram", "tiktok", "x", "threads")}


# ---------- 출처·점검표 ----------
def sources_md(spec, made_at):
    src = spec.get("source") or []
    L = [f"# 출처·숫자 확인 기록 — {spec['out']}", "", f"- 만든 시각: {made_at}", f"- 틀: {spec.get('_preset', '')} · {spec.get('series', '')}", "",
         "## 출처·기준(영상·설명에 들어간 줄)"] + [f"- {s}" for s in src] + ([] if src else ["- (없음) ❌"]) + [
         "", "## 확인 기록(확인한 곳·시각)", f"- {spec.get('checked') or '(없음) ❌'}", ""]
    if spec.get("template") == "rank":
        hl = spec.get("highlight", {}); unit = spec.get("unit", "")
        L += ["## 영상 속 숫자 (원문과 하나씩 대조)", "", "| 순위 | 이름 | 곡 | 숫자 | 대조 |", "|---|---|---|---|---|"]
        L += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:,}{unit} | [ ] |" if isinstance(r[3], (int, float)) else f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | [ ] |" for r in spec.get("rows", [])]
        L += [f"| 주인공 | {hl.get('name', '')} | {hl.get('sub', '')} | {hl.get('value', 0):,}{unit} | [ ] |", ""]
        if hl.get("note"): L += [f"- 메모(비교 문장): {hl['note']}  [ ] 근거 확인", ""]
    elif spec.get("template") == "cards":
        L += ["## 카드 문장 (사실이 들어간 문장은 원문 대조)"] + [f"- [ ] {c.get('big', '')} / {c.get('small', '')}" for c in spec.get("cards", [])] + [""]
    elif spec.get("template") in V2:      # 표준 v2 쇼츠: 쓴 원본 구간 목록
        L += ["## 쓴 원본 구간(표준 v2)", f"- 출처 줄: {spec.get('source_line', '')}", f"- 저작권·팬캠 양해 확인: {'예' if spec.get('copyright_checked') else '아니요(확인 필요)'}"]
        for c in (spec.get("clips") or spec.get("sources") or []):
            L.append(f"- {os.path.basename(c['file'])} " + (f"{c['in']:.1f}~{c['out']:.1f}초 ({c.get('role', '')})" if "in" in c else f"sync {c.get('sync', 0)}초 {c.get('label', '')}"))
        L.append("")
    else:
        L += ["## 무대 클립", f"- 저작권·팬캠 양해 확인: {'예' if spec.get('copyright_checked') else '아니요 ❌'}"]
        L += [f"- {k}: {os.path.basename(v[0])}" for k, v in (spec.get("clips") or {}).items()] + [""]
    L += ["## 운영 규칙", "- 출처는 직접 열어 확인한 기사·차트만. 출처 2곳 미만·팩트 불일치·민감 이슈면 자동 게시하지 않는다.",
          "- 실존 인물 사진·뉴스 사진은 쓰지 않는다."]
    return "\n".join(L) + "\n"


def checklist_txt(spec, base_lines, cnt, warns, notes, plan, plan_problems):
    sc = plan["schedule"]; src = spec.get("source") or []
    L = [f"■ 게시 꾸러미 점검표 — {spec['out']}", f"예약: {sc['date']} {sc['time']} ({sc['slot']}, 서울) · 다섯 곳 같은 시각", "",
         "■ 공장 점검표(5줄 + 틀별 항목)"] + ["  " + x for x in base_lines]
    L += ["", "■ 글자 수"] + [f"  {'✅' if n <= m else '❌'} {k}: {n} / {m}" for k, n, m in cnt]
    L += ["", "■ 운영 규칙", f"  {'✅' if len(src) >= 2 else '⚠️'} 출처·기준 {len(src)}줄 (2곳 미만이면 자동 게시 안 함 — 대표 판단)",
          "  [ ] 민감 이슈 아님(사건·사고·정치면 표시만 하고 대표가 제외 여부 결정)", "  [ ] 실존 인물·뉴스 사진 안 씀"]
    L += ["", "■ 대표 승인 3단계(승인 전 다음 단계로 안 감)", "  [ ] 1. 주제", "  [ ] 2. 최종 문구(각 txt)", "  [ ] 3. 발행 직전(업로더 최종 [예약] 단추는 대표가 직접)"]
    L += ["", "■ 올리는 곳", "  - 유튜브: uploader 확인 모드(upload_plan.json) — 최종 [예약] 직전에서 멈춤",
          "  - 인스타·틱톡·X: 지금은 손으로(각 txt 복사) — 업로더 계획에 넣으려면 --sites 로 추가",
          "  - 스레드: 업로더 미지원 → 손으로(threads.txt)", "  - 유튜브 첫 댓글: 공개 뒤 대표가 달고 고정"]
    if warns: L += ["", "■ 줄인 것(확인 필요)"] + ["  - " + w for w in warns]
    if notes: L += ["", "■ 알림"] + ["  - " + n for n in notes]
    if plan.get("warnings"): L += ["", "■ 업로더 주의"] + ["  - " + w for w in plan["warnings"]]
    if plan_problems: L += ["", "■ 업로더 계획 ❌ (이것부터)"] + ["  - " + p for p in plan_problems]
    L += ["", "→ " + ("업로더 점검 통과. 승인 3단계 뒤 진행." if not plan_problems else "업로더 점검 통과 못 함. 위 ❌부터 고치기.")]
    return "\n".join(L) + "\n"


# ---------- 업로더 계획 ----------
def uploader_post_txt(T):
    """업로더(upload_plan.parse_post_txt)가 읽는 _게시문구.txt 형식으로 꾸러미 글을 옮긴다."""
    y = parse_youtube(T["youtube"])
    return (f"[유튜브 쇼츠]\n제목: {y['title']}\n설명:\n{y['desc']}\n\n첫 댓글(고정): {y['first_comment']}\n\n"
            f"[인스타그램·페이스북 릴스 (비즈니스 스위트 예약)]\n{T['instagram'].strip()}\n\n[틱톡]\n{T['tiktok'].strip()}\n\n[X]\n{T['x'].strip()}\n")


def build_plan(pkg, spec, sites, slot, date, now=None, base_lines=()):
    """업로더의 build_plan 을 그대로 돌려 같은 형식·같은 점검을 받는다(임시 폴더에 업로더가 찾는 이름으로 연결)."""
    T = read_texts(pkg); y = parse_youtube(T["youtube"])
    s = json.loads(json.dumps(spec)); name = s["out"]
    s["post"] = dict(s["post"], title=y["title"], desc=y["desc"], first_comment=y["first_comment"], tags=y["tags"])
    if s.get("template") == "stagemix":   # 업로더 끝 화면 계산은 rank·cards 용 → 교차편집은 실제 길이·끝 화면 4초로 맞춤
        d = (up.probe(os.path.join(pkg, "video.mp4")) or {}).get("dur") or s.get("_est_sec", 30)
        s.update(template="cards", cards=[], dur=d, min_body_sec=d - 4.0)
    if s.get("template") in V2:           # v2: 아웃트로 5초. 옛 5줄 점검표(숫자 확인 등)는 v2 에서 끔 → 아래에서 표준 v2 점검으로 바꿈
        d = (up.probe(os.path.join(pkg, "video.mp4")) or {}).get("dur") or STD2["shorts"]["total_sec"]
        s.update(template="cards", cards=[], dur=d, min_body_sec=d - STD2["shorts"]["outro_sec"], checked=s.get("checked") or "표준 v2 점검기",
                 source=s.get("source") or [s.get("source_line", "")])
    s["upload"] = {"slot": slot_up(spec, slot), "date": date}
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "out"))
        sp = os.path.join(tmp, name + "_spec.json"); json.dump(s, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
        os.symlink(os.path.join(pkg, "video.mp4"), os.path.join(tmp, "out", name + ".mp4"))
        os.symlink(os.path.join(pkg, "thumb.jpg"), os.path.join(tmp, "out", name + "_thumb.png"))
        open(os.path.join(tmp, "out", name + "_게시문구.txt"), "w", encoding="utf-8").write(uploader_post_txt(T))
        plan = up.build_plan(sp, sites=sites, now=now)
    # 임시 경로 → 꾸러미 경로
    plan.update(spec=os.path.join(pkg, "spec.json"), video=os.path.join(pkg, "video.mp4"),
                thumb=os.path.join(pkg, "thumb.jpg"), post_txt=os.path.join(pkg, "youtube.txt"),
                mode="confirm", final_click=False, package=pkg)
    for it in plan["sites"].values():
        if "thumb" in it: it["thumb"] = plan["thumb"]
    bad = [x for x in base_lines if x.startswith("❌")]   # 공장 점검표 ❌ 는 계획도 통과 못 함
    if bad and not any("5줄 점검표" in q for q in plan["problems"]):
        plan["problems"].append("공장 점검표 ❌: " + " / ".join(bad)); plan["ok"] = False
    if spec.get("template") in V2:        # 옛 5줄 점검표 대신 표준 v2 점검(base_lines) 결과만
        plan["problems"] = [q for q in plan["problems"] if "5줄 점검표" not in q]
        plan["ok"] = not plan["problems"]
    if spec.get("template") in ("stagemix", "pulse58") and not spec.get("copyright_checked"):
        plan["problems"].append("저작권·팬캠 양해 확인 안 됨"); plan["ok"] = False
    if (plan["schedule"]["slot"], plan["schedule"]["time"]) != (slot_up(spec, slot), slot_time(spec, slot)):
        plan["problems"].append(f"예약 시간대가 틀({slot} {slot_time(spec, slot)})과 다름"); plan["ok"] = False
    return plan


NEED = {"youtube": ["title", "description", "tags", "thumb", "first_comment"], "tiktok": ["caption"],
        "meta": ["caption", "targets", "thumb"], "x": ["text"]}


def check_plan(path, now=None):
    """업로더 계획 파일 점검: 형식(run.py·사이트 모듈이 읽는 칸) + 파일 + 예약 시각 + 한도. → (plan, 문제 목록)"""
    now = now or dt.datetime.now(up.KST); P = []
    try: plan = json.load(open(path, encoding="utf-8"))
    except Exception as e: return None, [f"계획 파일을 읽을 수 없음: {e}"]
    for k in ("name", "video", "thumb", "schedule", "sites", "checklist", "problems", "ok"):
        if k not in plan: P.append(f"칸 없음: {k}")
    if P: return plan, P
    for k in ("slot", "date", "time", "iso"):
        if k not in plan["schedule"]: P.append(f"schedule.{k} 없음")
    for f in ("video", "thumb"):
        if not os.path.exists(plan[f]): P.append(f"{f} 파일 없음: {plan[f]}")
    if plan.get("mode", "confirm") != "confirm" or plan.get("final_click"): P.append("확인 모드가 아님(최종 단추 자동 누름)")
    try:
        when = dt.datetime.fromisoformat(plan["schedule"]["iso"])
        if when < now + dt.timedelta(minutes=up.MIN_LEAD_MIN): P.append(f"예약 시각 {when:%m/%d %H:%M}이 지났거나 20분 안")
    except Exception: P.append("schedule.iso 형식 틀림")
    for s, it in plan["sites"].items():
        if s not in NEED: P.append(f"모르는 사이트: {s}"); continue
        P += [f"[{s}] 칸 없음: {k}" for k in NEED[s] if k not in it]
        P += [f"[{s}] {q}" for q in it.get("problems", [])]
    yt = plan["sites"].get("youtube")
    if yt:
        if len(yt.get("title", "")) > up.LIMITS["yt_title"]: P.append("[youtube] 제목 100자 초과")
        if len(yt.get("description", "")) > up.LIMITS["yt_desc"]: P.append("[youtube] 설명 5000자 초과")
    if "x" in plan["sites"] and up.x_length(plan["sites"]["x"].get("text", "")) > up.LIMITS["x_weighted"]: P.append("[x] 280 초과")
    if not plan["ok"] or plan["problems"]: P += [f"계획 문제: {q}" for q in plan["problems"]] or ["ok=false"]
    return plan, P


# ---------- 본체 ----------
def thumb_jpg(src, dst):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    for q in (92, 85, 75, 65):
        im.save(dst, quality=q, optimize=True)
        if os.path.getsize(dst) <= 2 * 1024 * 1024: return q
    return q


def finish(pkg, spec, T, warns, notes, base_lines, sites, slot, date, now=None):
    plan = build_plan(pkg, spec, sites, slot, date.isoformat(), now, base_lines)
    pp = os.path.join(pkg, "upload_plan.json")
    json.dump(plan, open(pp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _, problems = check_plan(pp, now)
    cnt = counts(T)
    open(os.path.join(pkg, "checklist.txt"), "w", encoding="utf-8").write(
        checklist_txt(spec, base_lines, cnt, warns, notes, plan, problems))
    return plan, problems, cnt


def make_package(result_dir, outbox=None, date=None, sites=None, use_ai=False, now=None, quiet=False):
    spec, spec_path, video, thumb, ptxt = find_result(os.path.abspath(result_dir))
    day, slot = spec["_preset"].split("_")
    sites = sites or ["youtube"]; now = now or dt.datetime.now(up.KST)
    if spec.get("template") == "molabogi":
        raise SystemExit("❌ 롱폼 몰아보기는 쇼츠 꾸러미(package.py) 대상이 아니에요 → 롱폼 업로드 순서(dukssim-longform)로")
    info = up.probe(video) or {}
    if spec.get("template") in V2:        # 템플릿 길이(58-N·58-M 58.0 / 40-N·40-M 40.0)
        tk = spec.get("shorts_template") or STD2["shorts_templates_default"][spec["template"]]; lim = STD2["shorts_templates"][tk]["total_sec"]
    else: tk, lim = "옛 틀", STD2["shorts"]["max_sec"]
    if info.get("dur", 0) > lim + STD2["shorts"]["tolerance_sec"]:   # 대표 20:36·20:40·20:43: 길이 넘으면 어느 칸에도 넣지 않고 멈춤(1분 넘는 쇼츠 Content ID 전 세계 차단 위험)
        raise SystemExit(f"❌ 영상이 {info['dur']:.2f}초 — {tk} 템플릿은 {lim:.1f}초 이하만(꾸러미 만들지 않고 멈춤). 모든 칸 같은 파일")
    d = pick_date(day, slot, date, now, spec.get("_time"))
    if DAYS[d.weekday()] != day: notes0 = [f"예약 날짜 {d}는 {DAYS[d.weekday()]}요일인데 틀은 {day}요일이에요"]
    else: notes0 = []
    song, _ = song_of(spec)
    pkg = os.path.join(os.path.abspath(outbox or os.path.join(HERE, "outbox")), f"{d:%Y%m%d}_{day}{slot}_{safe(song)}")
    os.makedirs(pkg, exist_ok=True)
    shutil.copy2(video, os.path.join(pkg, "video.mp4")); q = thumb_jpg(thumb, os.path.join(pkg, "thumb.jpg"))
    json.dump(spec, open(os.path.join(pkg, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    override = up.parse_post_txt(open(ptxt, encoding="utf-8").read()) if os.path.exists(ptxt) else {}
    T, _, warns, notes = make_texts(spec, override, use_ai)
    notes = notes0 + notes + ([f"썸네일 JPG 품질 {q}(2MB 이하로)"] if q < 92 else [])
    for k, v in T.items(): open(os.path.join(pkg, k + ".txt"), "w", encoding="utf-8").write(v)
    open(os.path.join(pkg, "sources.md"), "w", encoding="utf-8").write(sources_md(spec, now.strftime("%Y-%m-%d %H:%M")))
    base_lines = base_check(spec, video)
    json.dump({"warns": warns, "notes": notes, "base": base_lines, "slot": slot, "sites": sites},
              open(os.path.join(pkg, ".package_state.json"), "w", encoding="utf-8"), ensure_ascii=False)
    plan, problems, cnt = finish(pkg, spec, T, warns, notes, base_lines, sites, slot, d, now)
    if not quiet: report(pkg, cnt, warns, plan, problems)
    return pkg, plan, problems


def base_check(spec, video):
    """5줄 점검표. rank·cards 는 shorts_factory.checklist, stagemix 는 make_today.precheck + 소리."""
    import shorts_factory as sf
    if spec.get("template") in ("rank", "cards"):
        dur, t_end = up.end_timing(spec); info = up.probe(video)
        return sf.checklist(spec, video, info["dur"] if info else dur, t_end)[0]
    if spec.get("template") in V2:        # 표준 v2: make_today 가 렌더 뒤 돌린 check_standard 결과(없으면 지금 돌림)
        if spec.get("_v2_check"): return spec["_v2_check"]
        import check_standard as cs; return cs.run(spec, [video])[0]
    import make_today as mt
    lines, _ = mt.precheck(spec); info = up.probe(video) or {}
    n_src = len({v[0] for v in (spec.get("clips") or {}).values()})   # make_today.render 와 같은 기준
    return lines + [("✅ " if info.get("audio") else "❌ 빠짐: ") + "배경음악(노래) 들어감",
                    ("✅ " if n_src >= 8 else "❌ 확인: ") + f"무대 소스 {n_src}개 (8개 이상 권장)"]


def replan(pkg, date=None, sites=None, now=None):
    """대표가 txt 를 고친 뒤: 글자 수·업로더 계획·점검표만 다시(영상은 그대로)."""
    pkg = os.path.abspath(pkg); spec = json.load(open(os.path.join(pkg, "spec.json"), encoding="utf-8"))
    st = json.load(open(os.path.join(pkg, ".package_state.json"), encoding="utf-8"))
    old = json.load(open(os.path.join(pkg, "upload_plan.json"), encoding="utf-8"))
    d = dt.date.fromisoformat(date or old["schedule"]["date"]); T = read_texts(pkg)
    plan, problems, cnt = finish(pkg, spec, T, [], st["notes"] + ["txt 를 다시 읽어 계획을 새로 만듦(--replan)"],
                                 st["base"], sites or st["sites"], st["slot"], d, now)
    report(pkg, cnt, [], plan, problems); return pkg, plan, problems


def report(pkg, cnt, warns, plan, problems):
    print(f"\n■ 게시 꾸러미: {pkg}")
    print("  " + " · ".join(f for f in FILES if os.path.exists(os.path.join(pkg, f))))
    print(f"  예약: {plan['schedule']['date']} {plan['schedule']['time']} ({plan['schedule']['slot']}) · 업로더: {', '.join(plan['sites'])} · 확인 모드")
    for k, n, m in cnt: print(f"  {'✅' if n <= m else '❌'} {k}: {n}/{m}")
    for w in warns: print("  ⚠️ " + w)
    print("  → " + ("업로더 계획 점검 통과" if not problems else "업로더 계획 ❌: " + " / ".join(problems)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="make_today 결과 → 플랫폼별 게시 꾸러미")
    ap.add_argument("result", nargs="?", help="make_today 결과 폴더(out/<이름>)")
    ap.add_argument("--outbox"); ap.add_argument("--date", help="예약 날짜 YYYY-MM-DD(기본: 틀 요일의 다음 날짜)")
    ap.add_argument("--sites", help="업로더 계획에 넣을 곳 youtube,tiktok,meta,x (기본 youtube)")
    ap.add_argument("--ai", action="store_true", help="한도 넘는 글을 AI 교환대로 줄인 초안 사용(키 없으면 건너뜀)")
    ap.add_argument("--replan", metavar="꾸러미폴더"); ap.add_argument("--check", metavar="upload_plan.json")
    a = ap.parse_args(argv)
    sites = [s.strip() for s in a.sites.split(",")] if a.sites else None
    if sites and set(sites) - set(up.ALL_SITES): raise SystemExit("사이트 이름은 youtube, tiktok, meta, x 중에서(스레드는 손으로)")
    if a.check:
        plan, P = check_plan(a.check)
        print("✅ 계획 파일 점검 통과" if not P else "❌ 계획 파일 문제:\n  - " + "\n  - ".join(P)); return 0 if not P else 1
    if a.replan: return 0 if not replan(a.replan, a.date, sites)[2] else 1
    if not a.result: ap.error("결과 폴더를 주세요")
    return 0 if not make_package(a.result, a.outbox, a.date, sites, a.ai)[2] else 1


if __name__ == "__main__":
    sys.exit(main())
