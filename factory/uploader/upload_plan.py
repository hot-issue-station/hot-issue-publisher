"""업로드 계획 점검 도구 (덕심저장소 쇼츠 → 유튜브·틱톡·인스타·페이스북·X)

사용법:
  python upload_plan.py 기획.json                 # 시간대를 물어봄(창에서 실행할 때) / 아니면 가장 가까운 다음 시간대
  python upload_plan.py 기획.json --slot 점심      # 출근(07:30) / 점심(12:00) / 퇴근(18:30)
  python upload_plan.py 기획.json --slot 퇴근 --date 2026-11-12
  python upload_plan.py 기획.json --sites youtube,x

하는 일:
  1) 기획 JSON + out 폴더(영상·썸네일·게시문구)를 읽는다. 게시문구.txt를 대표가 고쳤으면 고친 글이 우선.
  2) 사이트별로 올릴 내용(제목·설명·태그·예약 시각·파일)을 표로 보여 준다.
  3) 빠진 것·길이 초과·5줄 점검표(shorts_factory.checklist와 같은 항목)를 잡아낸다.
  4) out/<이름>_업로드계획.json 을 만든다(run.py와 사이트별 모듈이 이 파일을 쓴다).
끝 코드: 0 = 올려도 됨, 1 = 빠진 것 있음(올리지 않음).
이 도구는 인터넷에 접속하지 않고, 아무 사이트에도 올리지 않는다.
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, tempfile, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY = os.path.dirname(HERE)
sys.path.insert(0, FACTORY)
import shorts_factory as sf  # noqa: E402  (5줄 점검표·게시문구 형식을 공장과 똑같이 쓰기 위해)

try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except Exception:  # 윈도우에 tzdata가 없을 때(pip install tzdata 권장) — 한국은 서머타임이 없어 +9 고정과 같다
    KST = dt.timezone(dt.timedelta(hours=9), "KST")

SLOTS = {"출근": "07:30", "점심": "12:00", "퇴근": "18:30"}
SLOT_ALIAS = {"1": "출근", "2": "점심", "3": "퇴근", "0730": "출근", "07:30": "출근", "1200": "점심", "12:00": "점심",
              "1830": "퇴근", "18:30": "퇴근", "출근길": "출근", "아침": "출근", "저녁": "퇴근", "퇴근길": "퇴근"}
ALL_SITES = ["youtube", "tiktok", "meta", "x"]
SITE_KO = {"youtube": "유튜브", "tiktok": "틱톡", "meta": "인스타·페이스북", "x": "X"}
MIN_LEAD_MIN = 20  # 예약은 지금부터 최소 20분 뒤(틱톡은 15분 이상 뒤만 예약 가능 — 여유를 둠)

# 사이트 제한(2026-11 기준으로 알려진 값. 사이트가 바꿀 수 있으니 화면에서 다시 확인)
LIMITS = {
    "yt_title": 100, "yt_desc": 5000, "yt_tags_total": 500, "yt_thumb_bytes": 2 * 1024 * 1024, "yt_shorts_sec": 180,
    "tt_caption": 2200, "tt_max_days": 10,
    "ig_caption": 2200, "ig_hashtags": 30, "ig_reel_sec": 180, "meta_max_days": 29,
    "x_weighted": 280, "x_video_sec": 140,
}


# ---------- 읽기 ----------
def load_spec(path):
    spec = json.load(open(path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(path))
    for k in ("bg", "bgm"):
        if spec.get(k) and not os.path.isabs(spec[k]): spec[k] = os.path.join(base, spec[k])
    if spec.get("thumb", {}).get("photo") and not os.path.isabs(spec["thumb"]["photo"]):
        spec["thumb"]["photo"] = os.path.join(base, spec["thumb"]["photo"])
    for c in spec.get("cards", []):
        if c.get("photo") and not os.path.isabs(c["photo"]): c["photo"] = os.path.join(base, c["photo"])
    return spec, base


def probe(video):
    """영상 길이·크기·소리 유무. ffprobe가 없거나 파일이 없으면 None."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
                            "-of", "json", video], capture_output=True, text=True, timeout=60)
        j = json.loads(r.stdout or "{}")
    except Exception:
        return None
    st = j.get("streams", [])
    v = next((s for s in st if s.get("codec_type") == "video"), {})
    return {"dur": float(j.get("format", {}).get("duration", 0) or 0), "w": v.get("width"), "h": v.get("height"),
            "audio": any(s.get("codec_type") == "audio" for s in st)}


def end_timing(spec):
    """shorts_factory.render와 같은 계산으로 (전체 길이, 끝 화면 시작)을 구한다. 영상을 다시 만들지는 않는다."""
    if spec.get("template") == "rank": _, _, t_src = sf.build_rank(spec)
    else: _, _, t_src = sf.build_cards(spec)
    t_end = max(t_src + 3.5, spec.get("min_body_sec", 0))
    dur = spec.get("dur") or (t_end + 3.8)
    return dur, min(t_end, dur - 3.0)


def parse_post_txt(txt):
    """게시문구.txt를 [제목] 칸별로 나눈다."""
    sec, cur = {}, None
    for line in txt.splitlines():
        m = re.match(r"^\[(.+)\]\s*$", line)
        if m: cur = m.group(1); sec[cur] = []; continue
        if cur is not None: sec[cur].append(line)
    out = {}
    for k, lines in sec.items():
        body = "\n".join(lines).strip("\n")
        if k.startswith("유튜브"):
            yt = {"title": "", "desc": "", "first_comment": ""}
            m = re.search(r"^제목:\s*(.*)$", body, re.M); yt["title"] = m.group(1).strip() if m else ""
            m = re.search(r"^설명:\s*\n(.*?)(?=^첫 댓글|\Z)", body, re.M | re.S); yt["desc"] = m.group(1).strip() if m else ""
            m = re.search(r"^첫 댓글\(고정\):\s*(.*)$", body, re.M); yt["first_comment"] = m.group(1).strip() if m else ""
            out["youtube"] = yt
        elif k.startswith("인스타"): out["meta"] = body.strip()
        elif k.startswith("틱톡"): out["tiktok"] = body.strip()
        elif k.upper().startswith("X"): out["x"] = body.strip()
    return out


def post_txt_from_spec(spec):
    """게시문구.txt가 없을 때 공장과 같은 형식으로 만들어 본다(파일은 남기지 않음)."""
    with tempfile.TemporaryDirectory() as d:
        return open(sf.post_text(spec, d), encoding="utf-8").read()


# ---------- 계산 ----------
def x_length(text):
    """X(트위터) 글자 수: 한글·한자·이모지는 2, 영문·숫자는 1, 링크는 23."""
    text = re.sub(r"https?://\S+", "x" * 23, text)
    n = 0
    for ch in unicodedata.normalize("NFC", text):
        o = ord(ch)
        n += 1 if (o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247) else 2
    return n


def strip_shorts_tag(text):
    """#shorts는 유튜브 전용. 다른 곳에서는 뺀다."""
    t = re.sub(r"\s*#shorts\b", "", text, flags=re.I)
    return re.sub(r"[ \t]+\n", "\n", t).strip()


def hashtags(text): return re.findall(r"#[^\s#]+", text)


def pick_schedule(slot=None, date=None, now=None, ask=False):
    now = now or dt.datetime.now(KST)
    if slot: slot = SLOT_ALIAS.get(str(slot).strip(), str(slot).strip())
    if slot and slot not in SLOTS: raise SystemExit(f"시간대는 출근(07:30)·점심(12:00)·퇴근(18:30) 중에서 골라 주세요: {slot}")
    if not slot and ask:
        print("예약 시간대를 골라 주세요:  1) 출근 07:30   2) 점심 12:00   3) 퇴근 18:30")
        slot = SLOT_ALIAS.get(input("번호: ").strip(), None) or "점심"
    def at(day, s):
        h, m = map(int, SLOTS[s].split(":")); return dt.datetime(day.year, day.month, day.day, h, m, tzinfo=KST)
    lead = now + dt.timedelta(minutes=MIN_LEAD_MIN)
    if date:
        d = dt.date.fromisoformat(date)
        s = slot or "점심"
        return s, at(d, s)
    if slot:
        t = at(now.date(), slot)
        return slot, (t if t >= lead else at(now.date() + dt.timedelta(days=1), slot))
    # 시간대를 안 고르면 가장 가까운 다음 시간대
    for add in (0, 1):
        for s in ("출근", "점심", "퇴근"):
            t = at(now.date() + dt.timedelta(days=add), s)
            if t >= lead: return s, t


def build_plan(spec_path, slot=None, date=None, sites=None, now=None, ask=False):
    spec, base = load_spec(spec_path)
    sites = sites or ALL_SITES
    outdir = os.path.join(base, "out"); name = spec.get("out", "")
    video = os.path.join(outdir, name + ".mp4"); thumb = os.path.join(outdir, name + "_thumb.png")
    ptxt = os.path.join(outdir, name + "_게시문구.txt")
    problems, warns, notes = [], [], []
    now = now or dt.datetime.now(KST)

    # 파일
    for label, p in (("영상", video), ("썸네일", thumb), ("게시문구", ptxt)):
        if not os.path.exists(p): problems.append(f"{label} 파일 없음: {p}  → 먼저 shorts_factory.py로 만들기")
    po = spec.get("post") or {}
    if not po: problems.append("기획 JSON에 'post' 칸(title·desc·tags·first_comment)이 없음")

    # 5줄 점검표(공장과 같은 항목)
    info = probe(video) if os.path.exists(video) else None
    try:
        dur_calc, t_end = end_timing(spec)
    except Exception as e:
        dur_calc, t_end = None, None; problems.append(f"끝 화면 시간 계산 실패({e})")
    if t_end is not None:  # 영상이 없으면 '배경음악'은 ❌로 나온다(나머지 항목은 기획 JSON으로 확인)
        check_lines, check_ok = sf.checklist(spec, video, info["dur"] if info else dur_calc, t_end)
    else:
        check_lines, check_ok = ["❌ 빠짐: 5줄 점검표를 계산하지 못함"], False
    if not check_ok: problems.append("5줄 점검표에 ❌ 있음 (위 점검표 참고)")
    if info:
        if dur_calc and abs(info["dur"] - dur_calc) > 0.6:
            warns.append(f"영상 길이({info['dur']:.1f}초)가 기획 JSON 계산({dur_calc:.1f}초)과 다름 → 기획을 고친 뒤 영상을 다시 안 만든 것일 수 있음")
        if (info["w"], info["h"]) != (1080, 1920): warns.append(f"영상 크기 {info['w']}x{info['h']} (쇼츠 표준 1080x1920 아님)")
    dur = info["dur"] if info else (dur_calc or 0)

    # 게시 문구: 파일(대표가 고친 것) 우선, 없으면 기획 JSON으로 만듦
    if os.path.exists(ptxt): txt = open(ptxt, encoding="utf-8").read()
    elif po: txt = post_txt_from_spec(spec); notes.append("게시문구.txt가 없어 기획 JSON으로 만든 글을 보여 줌")
    else: txt = ""
    pt = parse_post_txt(txt)

    slot, when = pick_schedule(slot or (spec.get("upload") or {}).get("slot"),
                               date or (spec.get("upload") or {}).get("date"), now=now, ask=ask)
    if when < now + dt.timedelta(minutes=MIN_LEAD_MIN):
        problems.append(f"예약 시각 {when:%m/%d %H:%M}이 너무 가깝거나 지났음(지금부터 {MIN_LEAD_MIN}분 뒤 이후로)")
    days_ahead = (when - now).total_seconds() / 86400

    tags = [t.lstrip("#") for t in po.get("tags", [])]
    out = {}
    if "youtube" in sites:
        yt = pt.get("youtube", {})
        title, desc = yt.get("title") or po.get("title", ""), yt.get("desc") or po.get("desc", "")
        first = yt.get("first_comment") or po.get("first_comment", "")
        p = []
        if not title: p.append("제목 없음")
        if len(title) > LIMITS["yt_title"]: p.append(f"제목 {len(title)}자(최대 100자)")
        if re.search(r"[<>]", title + desc): p.append("제목·설명에 < > 기호(유튜브가 거부)")
        if not desc: p.append("설명 없음")
        if len(desc) > LIMITS["yt_desc"]: p.append(f"설명 {len(desc)}자(최대 5000자)")
        if len(",".join(tags)) > LIMITS["yt_tags_total"]: p.append("태그 합계 500자 초과")
        if not first: p.append("첫 댓글 문구 없음")
        if os.path.exists(thumb) and os.path.getsize(thumb) > LIMITS["yt_thumb_bytes"]:
            p.append(f"썸네일 {os.path.getsize(thumb)/1048576:.1f}MB(유튜브 최대 2MB) → JPG로 줄이기")
        if dur > LIMITS["yt_shorts_sec"]: p.append(f"영상 {dur:.0f}초 — 3분 넘으면 쇼츠가 아님")
        if "#shorts" not in (title + desc).lower(): warns.append("유튜브 제목·설명에 #shorts 없음(없어도 세로 3분 이하면 쇼츠로 분류됨)")
        out["youtube"] = {"title": title, "description": desc, "tags": tags, "thumb": thumb, "first_comment": first,
                          "made_for_kids": False, "problems": p}
    if "tiktok" in sites:
        raw = pt.get("tiktok") or (po.get("title", "") + " " + " ".join("#" + t for t in tags))
        cap = strip_shorts_tag(raw)
        if cap != raw.strip(): notes.append("틱톡 글에서 #shorts(유튜브 전용)를 뺌")
        p = []
        if not cap: p.append("설명 없음")
        if len(cap) > LIMITS["tt_caption"]: p.append(f"설명 {len(cap)}자(최대 2200자)")
        if days_ahead > LIMITS["tt_max_days"]: p.append("틱톡은 10일 이내만 예약 가능")
        out["tiktok"] = {"caption": cap, "problems": p}
    if "meta" in sites:
        raw = pt.get("meta") or (po.get("desc", "") + "\n.\n" + " ".join("#" + t for t in tags))
        cap = strip_shorts_tag(raw)
        p = []
        if not cap: p.append("설명 없음")
        if len(cap) > LIMITS["ig_caption"]: p.append(f"설명 {len(cap)}자(최대 2200자)")
        if len(hashtags(cap)) > LIMITS["ig_hashtags"]: p.append(f"해시태그 {len(hashtags(cap))}개(인스타 최대 30개)")
        if dur > LIMITS["ig_reel_sec"]: p.append(f"영상 {dur:.0f}초 — 릴스 최대 3분")
        if days_ahead > LIMITS["meta_max_days"]: p.append("비즈니스 스위트는 29일 이내만 예약 가능")
        out["meta"] = {"caption": cap, "targets": ["facebook", "instagram"], "thumb": thumb, "problems": p}
    if "x" in sites:
        raw = pt.get("x") or (po.get("x") or po.get("title", "")) + "\n" + " ".join("#" + t for t in tags)
        text = strip_shorts_tag(raw)
        if text != raw.strip(): notes.append("X 글에서 #shorts(유튜브 전용)를 뺌")
        p = []
        n = x_length(text)
        if not text: p.append("글 없음")
        if n > LIMITS["x_weighted"]: p.append(f"X 글자 수 {n}(한글 2·영문 1 기준, 최대 280) → 'post.x'에 짧은 글 쓰기")
        if dur > LIMITS["x_video_sec"]: p.append(f"영상 {dur:.0f}초 — 일반 계정은 2분 20초까지")
        out["x"] = {"text": text, "x_length": n, "problems": p}

    for s, it in out.items():
        for q in it["problems"]: problems.append(f"[{SITE_KO[s]}] {q}")

    plan = {
        "made_at": now.isoformat(timespec="seconds"), "spec": os.path.abspath(spec_path), "name": name,
        "video": video, "thumb": thumb, "post_txt": ptxt, "duration_sec": round(dur, 2),
        "schedule": {"slot": slot, "date": when.strftime("%Y-%m-%d"), "time": when.strftime("%H:%M"),
                     "iso": when.isoformat(), "timezone": "Asia/Seoul"},
        "sites": out, "checklist": check_lines, "problems": problems, "warnings": warns, "notes": notes,
        "ok": not problems,
    }
    return plan


# ---------- 보여 주기 ----------
def _w(s):  # 화면 폭(한글은 2칸)
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _cut(s, n):
    s = s.replace("\n", " ⏎ "); out = ""
    for c in s:
        if _w(out + c) > n - 1: return out + "…"
        out += c
    return out


def _row(cells, widths):
    return "│ " + " │ ".join(c + " " * (w - _w(c)) for c, w in zip(cells, widths)) + " │"


def show(plan):
    sc = plan["schedule"]; W2 = [14, 64]
    print(f"\n■ 업로드 계획: {plan['name']}   (영상 {plan['duration_sec']}초)")
    print(f"  예약 시각: {sc['date']} {sc['time']} ({sc['slot']}, 서울 시간) — 다섯 곳 모두 같은 시각")
    print(f"  영상: {plan['video']}\n  썸네일: {plan['thumb']}\n  게시문구: {plan['post_txt']}")
    print("\n■ 5줄 점검표(공장과 같은 항목)"); print("  " + "\n  ".join(plan["checklist"]))
    for s, it in plan["sites"].items():
        rows = []
        if s == "youtube":
            rows = [("제목", it["title"]), ("설명", it["description"]), ("태그", ", ".join(it["tags"])),
                    ("썸네일", os.path.basename(it["thumb"])), ("아동용", "아니요"),
                    ("첫 댓글", it["first_comment"] + "  ← 공개 후 사람이 달고 고정")]
        elif s == "tiktok": rows = [("설명", it["caption"]), ("글자 수", f"{len(it['caption'])} / 2200")]
        elif s == "meta":
            rows = [("올릴 곳", "인스타그램 + 페이스북 (동시)"), ("설명", it["caption"]),
                    ("해시태그", f"{len(hashtags(it['caption']))}개 / 30"), ("커버", os.path.basename(it["thumb"]))]
        elif s == "x": rows = [("글", it["text"]), ("글자 수", f"{it['x_length']} / 280 (한글 2)")]
        rows += [("파일", os.path.basename(plan["video"])), ("예약", f"{sc['date']} {sc['time']}"),
                 ("점검", "✅ 통과" if not it["problems"] else "❌ " + " / ".join(it["problems"]))]
        full = sum(W2) + 7; head = f"┌ {SITE_KO[s]} "
        print("\n" + head + "─" * (full - _w(head) - 1) + "┐")
        for k, v in rows: print(_row([k, _cut(v, W2[1])], W2))
        print("└" + "─" * (full - 2) + "┘")
    if plan["notes"]: print("\n■ 알림\n  - " + "\n  - ".join(plan["notes"]))
    if plan["warnings"]: print("\n■ 주의(올릴 수는 있음)\n  - " + "\n  - ".join(plan["warnings"]))
    if plan["problems"]: print("\n■ 빠진 것·고칠 것 (이것부터 채우기)\n  - " + "\n  - ".join(plan["problems"]))
    print("\n→ " + ("올려도 됨. 업로드 프로그램은 '확인 모드'(예약 버튼 직전 정지)로 진행합니다."
                    if plan["ok"] else "올리지 않음. 위의 '빠진 것'부터 채운 뒤 다시 점검하세요."))


def save(plan):
    p = os.path.join(os.path.dirname(plan["video"]), plan["name"] + "_업로드계획.json")
    json.dump(plan, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return p


def main(argv=None):
    if os.name == "nt":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    ap = argparse.ArgumentParser(description="덕심저장소 쇼츠 업로드 계획 점검")
    ap.add_argument("spec", help="기획 JSON 파일")
    ap.add_argument("--slot", help="출근 / 점심 / 퇴근 (07:30 / 12:00 / 18:30)")
    ap.add_argument("--date", help="예약 날짜 YYYY-MM-DD (없으면 가장 가까운 날)")
    ap.add_argument("--sites", help="youtube,tiktok,meta,x 중 일부 (기본: 전부)")
    ap.add_argument("--no-save", action="store_true", help="업로드계획.json을 만들지 않음")
    a = ap.parse_args(argv)
    sites = [s.strip() for s in a.sites.split(",")] if a.sites else None
    if sites and set(sites) - set(ALL_SITES): raise SystemExit("사이트 이름은 youtube, tiktok, meta, x 중에서")
    plan = build_plan(a.spec, a.slot, a.date, sites, ask=(a.slot is None and a.date is None and sys.stdin.isatty()))
    show(plan)
    if not a.no_save and os.path.isdir(os.path.dirname(plan["video"])): print(f"\n계획 파일: {save(plan)}")
    return 0 if plan["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
