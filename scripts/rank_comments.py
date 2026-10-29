"""응원 랭킹 (대표 결정 10/28 23:57): 매일 댓글을 점수로 바꿔 순위를 공개하고 참여를 독려한다.

점수: 우리 게시물에 댓글을 단 날마다 1점(하루에 여러 개 달아도 1점, 도배 방지).
      그날 좋아요를 가장 많이 받은 댓글(좋아요 1개 이상)의 주인은 +3점.
      팔로우 보너스 +3점(대표 결정 10/29): 인스타 API로는 팔로워를 알 수 없어서, 마감(11/9) 뒤 대표가
      상위권(15명 안팎)의 팔로우 여부를 앱에서 직접 확인해 알려 주면 Claude가 data/ranking/follow_bonus.json
      의 "keys"(아이디 해시)에 넣는다. 점수를 더하기만 하므로 먼저 참여한 분께 불리하지 않다.
공개 저장소라서 아이디 원문은 저장하지 않는다. 아이디의 해시(구별용)와 가린 이름(예: re***n)만 남긴다.
본인 확인(포카 당첨 등)은 대표가 인스타 앱 댓글에서 가린 이름과 맞춰 본다.
결과: data/ranking/points.json(누적), data/ranking/latest.json(TOP10, 소개글에 쓰는 것)
"""
import datetime as dt, hashlib, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import publish as pb

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "ranking"


def mask(u):
    return (u[:2] + "***" + u[-1]) if len(u) > 3 else (u[:1] + "***")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pf = OUT / "points.json"
    db = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else {"users": {}, "best": {}}
    pb.check_token()
    me = (pb.api("GET", pb.IG_ID, fields="username").get("username") or "").lower()
    media = pb.api("GET", f"{pb.IG_ID}/media", fields="id,comments_count", limit="20").get("data", [])
    bydate = {}
    for m in media:
        if not m.get("comments_count"):
            continue
        for c in pb.api("GET", f"{m['id']}/comments", fields="id,username,like_count,timestamp", limit="100").get("data", []):
            u = (c.get("username") or "").lower()
            if not u or u == me:
                continue
            day = dt.datetime.strptime(c["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).astimezone(pb.KST).strftime("%Y-%m-%d")
            key = hashlib.sha256(u.encode()).hexdigest()[:16]
            rec = db["users"].setdefault(key, {"name": mask(u), "days": []})
            if day not in rec["days"]:
                rec["days"].append(day)
            top = bydate.get(day)
            if (c.get("like_count") or 0) > 0 and (not top or c["like_count"] > top[1]):
                bydate[day] = (key, c["like_count"])
    today = dt.datetime.now(pb.KST).strftime("%Y-%m-%d")
    for day, (key, _) in bydate.items():
        if day != today:            # 하루가 끝난 날만 베스트를 확정한다
            db["best"].setdefault(day, key)
    fb = OUT / "follow_bonus.json"
    follow = set(json.loads(fb.read_text(encoding="utf-8")).get("keys", [])) if fb.exists() else set()
    for key, rec in db["users"].items():
        rec["follow"] = key in follow
        rec["score"] = len(rec["days"]) + 3 * sum(1 for k in db["best"].values() if k == key) + (3 if rec["follow"] else 0)
    pf.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    ranked = sorted(db["users"].values(), key=lambda r: (-r["score"], min(r["days"])))[:10]
    latest = {"updatedAt": dt.datetime.now(pb.KST).isoformat(timespec="minutes"),
              "rule": "댓글 단 날마다 1점, 그날 베스트 댓글 +3점, 팔로우 보너스 +3점(마감 뒤 확인)",
              "top": [{"rank": i + 1, "name": r["name"], "score": r["score"]} for i, r in enumerate(ranked)]}
    (OUT / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("랭킹", len(db["users"]), "명")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = str(e).replace(pb.TOKEN, "***") if pb.TOKEN else str(e)
        print("실패:", msg[:300]); sys.exit(1)
