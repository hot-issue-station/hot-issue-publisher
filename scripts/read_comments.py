"""최근 게시물 댓글을 읽어 data/comments/<YYYYMMDD>.json 에 저장한다(대표 결정 10/28: 콘텐츠팀이 '오늘의 댓글'을 자동 선발).

저장소가 공개라서 아이디(username)는 저장하지 않는다. 댓글 글, 좋아요 수, 시각, 댓글 ID, 게시물 주제만 남긴다.
GitHub Actions(comments.yml)에서 IG_ACCESS_TOKEN 비밀값으로 실행한다.
"""
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import publish as pb

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    now = dt.datetime.now(pb.KST)
    out = ROOT / "data" / "comments"; out.mkdir(parents=True, exist_ok=True)
    rec = {"readAt": now.isoformat(timespec="seconds"), "ok": False, "media": []}
    try:
        pb.check_token()
        media = pb.api("GET", f"{pb.IG_ID}/media", fields="id,caption,timestamp,comments_count,media_type", limit="12").get("data", [])
        for m in media:
            item = {"mediaId": m["id"], "type": m.get("media_type"), "timestamp": m.get("timestamp"),
                    "topic": " ".join((m.get("caption") or "").split())[:40], "commentsCount": m.get("comments_count", 0), "comments": []}
            if m.get("comments_count"):
                cs = pb.api("GET", f"{m['id']}/comments", fields="id,text,timestamp,like_count", limit="50").get("data", [])
                item["comments"] = [{"id": c["id"], "text": (c.get("text") or "")[:300], "likes": c.get("like_count", 0),
                                     "timestamp": c.get("timestamp")} for c in cs]
            rec["media"].append(item)
        rec["ok"] = True
    except Exception as e:
        rec["error"] = str(e).replace(pb.TOKEN, "***")[:500] if pb.TOKEN else str(e)[:500]
    (out / f"{now:%Y%m%d}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ok" if rec["ok"] else f"실패: {rec.get('error')}")
    return 0 if rec["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
