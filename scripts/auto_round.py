"""자동 모드(30분 거부권) 도우미.

대표 결정(2026-10-28): 회차 카드를 Claude가 혼자 만들어 회차 시각에 게시한다. 대표는 게시 전에
스튜디오의 [올리지 않기]로 막을 수 있다(거부권). 문구 기준은 style/style_guide.md.

사용법
  python scripts/auto_round.py check 2026-10-28 NT
      → 그 날짜·회차에 이미 게시됐거나 게시 승인된 묶음이 있으면 "busy <폴더>"(종료 코드 3), 없으면 "free"
  python scripts/auto_round.py build rounds/20261028_NT_auto.json --id <autoq 문서ID>
      → 문구 검사(글자 수·사실 3개·출처 2곳·캡션) 후 카드 7장과 post.json을 만든다.
        통과하면 마지막 줄에 "folder posts/<폴더>", 검사에 걸리면 이유를 출력하고 종료 코드 2
  python scripts/auto_round.py veto posts/<폴더> --id <autoq 문서ID>
      → 아직 안 올라갔으면 승인 3을 거두고 "vetoed"(0), 이미 올라갔으면 "too_late"(4)
"""
import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
KST = dt.timezone(dt.timedelta(hours=9))
LIMITS = {"hook": 20, "sub": 40, "summary": 60, "interp": 40, "interpSub": 50}
FACT_LIMITS = {"title": 30, "desc": 80}
TAGS = ["#이슈브리프", "#오늘의이슈"]


def clen(t):
    return len(str(t or "").replace("*", "").replace("\n", ""))


def slot_posts(date, slot):
    ymd = date.replace("-", "")
    for p in sorted(POSTS.glob(f"{ymd}_{slot}*")):
        pj = p / "post.json"
        if not pj.exists():
            continue
        meta = json.loads(pj.read_text(encoding="utf-8"))
        if meta.get("slot") != slot or meta.get("date") != date:
            continue
        yield p, meta


def check(date, slot):
    for p, meta in slot_posts(date, slot):
        approved = (meta.get("approval3") or {}).get("approved") is True
        if (p / "published.json").exists() or approved:
            # 회차 시각 예약(정시 게시)만 회차를 차지한 것으로 본다. '지금 바로' 올린 수시 게시물은 회차를 막지 않는다.
            pub = meta.get("publishAt", "")
            if pub.endswith(f"T{slot_time(slot)}:00+09:00"):
                print(f"busy {p.relative_to(ROOT)}")
                return 3
    print("free")
    return 0


def slot_time(slot):
    return {"AM": "08:00", "PM": "12:00", "NT": "21:00", "RS": "18:30"}[slot]  # 10/31 대표 편성


def validate(r):
    errs = []
    for k, lim in LIMITS.items():
        if clen(r.get(k)) == 0:
            errs.append(f"{k} 비어 있음")
        elif clen(r.get(k)) > lim:
            errs.append(f"{k} {clen(r.get(k))}자 > {lim}자")
    facts = r.get("facts") or []
    if len(facts) != 3:
        errs.append(f"사실 {len(facts)}개 (3개여야 함)")
    for i, f in enumerate(facts, 1):
        for k, lim in FACT_LIMITS.items():
            if clen(f.get(k)) == 0 or clen(f.get(k)) > lim:
                errs.append(f"사실{i} {k} {clen(f.get(k))}자 (1~{lim}자)")
        if not f.get("source"):
            errs.append(f"사실{i} 출처 줄 없음")
    outlets = {s.get("outlet") for s in r.get("sources") or [] if s.get("outlet") and s.get("url")}
    if len(outlets) < 2:
        errs.append(f"서로 다른 매체 출처 {len(outlets)}곳 (2곳 이상 필요)")
    cap = r.get("caption") or ""
    if len(cap) > 2200:
        errs.append(f"캡션 {len(cap)}자 > 2200자")
    for t in TAGS:
        if t not in cap:
            errs.append(f"캡션에 {t} 없음")
    if "!" in "".join([r.get("hook", ""), r.get("sub", ""), r.get("summary", ""), r.get("interp", "")]):
        errs.append("느낌표 사용 (스타일 가이드: 감탄 대신 사실)")
    if r.get("sensitive"):
        errs.append("민감 이슈는 자동 게시하지 않음")
    if r.get("slot") not in ("AM", "PM", "NT", "RS"):
        errs.append("slot은 AM/PM/NT/RS 중 하나")
    return errs


def build(path, auto_id):
    r = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    errs = validate(r)
    if errs:
        print("검사 실패:\n- " + "\n- ".join(errs))
        return 2
    if check(r["date"], r["slot"]) == 3:
        print("검사 실패:\n- 이 회차에 이미 게시(예약)된 묶음이 있음")
        return 2
    ymd = r["date"].replace("-", "")
    base = f"{ymd}_{r['slot']}_auto"
    folder, n = POSTS / base, 2
    while (folder / "published.json").exists() or ((folder / "post.json").exists()
                                                    and json.loads((folder / "post.json").read_text(encoding="utf-8")).get("auto", {}).get("id") != auto_id):
        folder, n = POSTS / f"{base}{n}", n + 1
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_post.py"), str(path), "--out", str(folder),
                          "--approve3", "자동 모드 (대표 결정 10/28 · 30분 거부권)"], capture_output=True, text=True)
    print(res.stdout.strip())
    if "넘칩니다" in res.stdout:
        print("검사 실패:\n- 카드 글이 칸을 넘침 (문구를 줄여 다시)")
        return 2
    if res.returncode != 0 or not (folder / "07.jpg").exists():
        print("카드 생성 실패:\n" + res.stderr[-1500:])
        return 2
    meta = json.loads((folder / "post.json").read_text(encoding="utf-8"))
    meta["reel"] = False
    meta["auto"] = {"id": auto_id, "createdAt": dt.datetime.now(KST).isoformat(timespec="seconds"),
                    "vetoUntil": (dt.datetime.fromisoformat(meta["publishAt"]) - dt.timedelta(minutes=3)).isoformat()}
    (folder / "post.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"folder {folder.relative_to(ROOT)}")
    return 0


def veto(folder, auto_id):
    folder = ROOT / folder if not pathlib.Path(folder).is_absolute() else pathlib.Path(folder)
    if (folder / "published.json").exists():
        print("too_late")
        return 4
    pj = folder / "post.json"
    if not pj.exists():
        print("not_found")
        return 5
    meta = json.loads(pj.read_text(encoding="utf-8"))
    if (meta.get("auto") or {}).get("id") != auto_id:
        print("id_mismatch")
        return 5
    meta["approval3"] = {"approved": False, "vetoedAt": dt.datetime.now(KST).isoformat(timespec="seconds"),
                         "by": "대표 (스튜디오 [올리지 않기])"}
    pj.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("vetoed")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("date"); c.add_argument("slot")
    b = sub.add_parser("build"); b.add_argument("round_json"); b.add_argument("--id", required=True)
    v = sub.add_parser("veto"); v.add_argument("folder"); v.add_argument("--id", required=True)
    a = ap.parse_args()
    if a.cmd == "check":
        return check(a.date, a.slot)
    if a.cmd == "build":
        return build(a.round_json, a.id)
    return veto(a.folder, a.id)


if __name__ == "__main__":
    sys.exit(main())
