"""Threads 통계 자동 수집 (대표 결정 2026-10-31, 통계 캡처 대신).

data/stats/threads/<날짜>.json 에 스냅샷을 쌓는다:
{at, profile:{followers, views, likes, replies, reposts, quotes}, posts:[{id, text, timestamp, permalink, views, likes, replies, reposts, quotes, shares}]}
비밀값 THREADS_TOKEN 이 없으면 아무것도 하지 않는다.
"""
import json, os, pathlib, sys, urllib.request, urllib.parse, datetime

TH = "https://graph.threads.net/v1.0"
KST = datetime.timezone(datetime.timedelta(hours=9))
OUT = pathlib.Path("data/stats/threads")


def get(path, **q):
    q["access_token"] = os.environ["THREADS_TOKEN"].strip()
    url = f"{TH}/{path}?{urllib.parse.urlencode(q)}"
    try:
        return json.loads(urllib.request.urlopen(url, timeout=30).read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8", "replace")[:300]}


def metrics(res):
    out = {}
    for m in res.get("data", []):
        v = m.get("total_value", {}).get("value")
        if v is None and m.get("values"):
            v = sum(x.get("value", 0) for x in m["values"])
        out[m["name"]] = v
    return out


def main():
    if not os.environ.get("THREADS_TOKEN", "").strip():
        print("THREADS_TOKEN 없음, 건너뜀"); return 0
    now = datetime.datetime.now(KST)
    prof = metrics(get("me/threads_insights", metric="views,likes,replies,reposts,quotes,followers_count"))
    posts = []
    for p in get("me/threads", fields="id,text,timestamp,permalink,media_type", limit=25).get("data", []):
        m = metrics(get(f"{p['id']}/insights", metric="views,likes,replies,reposts,quotes,shares"))
        posts.append({"id": p["id"], "text": (p.get("text") or "")[:60], "timestamp": p.get("timestamp"),
                      "permalink": p.get("permalink"), **m})
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{now:%Y%m%d}.json"
    snaps = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    snaps.append({"at": now.isoformat(timespec="minutes"), "profile": prof, "posts": posts})
    f.write_text(json.dumps(snaps, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Threads 통계: 팔로워 {prof.get('followers_count')}, 게시물 {len(posts)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
