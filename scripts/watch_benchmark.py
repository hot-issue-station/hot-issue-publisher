"""벤치마킹 계정 매일 모니터링 (대표 지시 2026-10-28, 담당: 분석팀).

우리 계정 연결(IG_ACCESS_TOKEN)로 공개 비즈니스 계정의 최근 게시물(캡션 앞부분·좋아요·댓글 수·형식·시각)을 모은다. 비용 0원.
내용은 베끼지 않는다. 제목 형식·주제·반응만 참고한다. 다른 사람 아이디(댓글 작성자)는 모으지 않는다.
결과: data/benchmark/<계정>.json (최신), data/benchmark/<계정>_<날짜>.json (하루 기록)
"""
import datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import publish as pb

ACCOUNTS = ["today_issue_mag"]
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "benchmark"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(pb.KST); ok = True
    for name in ACCOUNTS:
        rec = {"account": name, "readAt": now.isoformat(timespec="minutes"), "ok": False}
        try:
            f = (f"business_discovery.username({name})"
                 "{followers_count,media_count,media.limit(25){caption,like_count,comments_count,timestamp,media_type,media_product_type,permalink}}")
            bd = pb.api("GET", pb.IG_ID, fields=f).get("business_discovery", {})
            posts = []
            for m in bd.get("media", {}).get("data", []):
                cap = (m.get("caption") or "").strip()
                posts.append({"timestamp": m.get("timestamp"), "type": m.get("media_product_type") or m.get("media_type"),
                              "likes": m.get("like_count"), "comments": m.get("comments_count"),
                              "first_line": cap.split("\n")[0][:120], "caption_len": len(cap),
                              "hashtags": [w for w in cap.split() if w.startswith("#")][:10], "url": m.get("permalink")})
            rec.update(ok=True, followers=bd.get("followers_count"), media_count=bd.get("media_count"),
                       top=sorted(posts, key=lambda p: (p["likes"] or 0), reverse=True)[:5], posts=posts)
        except Exception as e:
            ok = False
            rec["error"] = (str(e).replace(pb.TOKEN, "***") if pb.TOKEN else str(e))[:500]
        for p in (OUT / f"{name}.json", OUT / f"{name}_{now:%Y%m%d}.json"):
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(name, "ok" if rec["ok"] else rec.get("error"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
