"""벤치마킹 유튜브 채널 모니터링 (대표 지시 2026-10-29, 담당: 분석팀).

config/benchmark.json 의 youtube 채널들을 RSS로 읽는다(비용 0원, 키 없음). 하루 4번(리센느 모니터링과 같은 시각).
내용은 베끼지 않는다. 제목 형식·주제·올린 시각·반응(조회수·좋아요)만 참고한다.
결과: data/benchmark/yt_<키>.json (최근 영상 15개 + 지난 확인 대비 조회수 증가 viewsGain)
      data/benchmark/yt_log_<날짜>.json (그날 확인 기록, 보고서용)
리센느 소재용 data/youtube/new_*.json 에는 섞지 않는다.
"""
import datetime, json, pathlib, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from watch_youtube import get, channel_id, feed, NS, KST

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "benchmark"


def read_channel(url, old):
    cid = channel_id(url, old)
    root = ET.fromstring(feed(cid))
    prev = {v["id"]: v.get("views") for v in old.get("videos", [])}
    vids = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", "", NS)
        link = e.find("a:link", NS).get("href", "")
        g = e.find("m:group", NS)
        stats = g.find("m:community/m:statistics", NS) if g is not None else None
        rate = g.find("m:community/m:starRating", NS) if g is not None else None
        views = int(stats.get("views", 0)) if stats is not None else None
        vids.append({"id": vid, "title": e.findtext("a:title", "", NS), "published": e.findtext("a:published", "", NS),
                     "url": link, "shorts": "/shorts/" in link, "views": views,
                     "likes": int(rate.get("count", 0)) if rate is not None else None,
                     "viewsGain": (views - prev[vid]) if (vid in prev and views is not None and prev[vid] is not None) else None,
                     "isNew": bool(prev) and vid not in prev})
    return cid, vids


def main():
    cfg = json.loads((ROOT / "config" / "benchmark.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(KST)
    logp = OUT / f"yt_log_{now:%Y%m%d}.json"
    log = json.loads(logp.read_text(encoding="utf-8")) if logp.exists() else []
    for key, ch in cfg.get("youtube", {}).items():
        path = OUT / f"yt_{key}.json"
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        try:
            cid, vids = read_channel(ch["url"], old)
        except BaseException as e:  # 한 채널이 실패해도 나머지는 계속
            print(f"{key}: 실패 {str(e)[:200]}")
            log.append({"at": now.isoformat(timespec="minutes"), "key": key, "ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})
            continue
        data = {"key": key, "name": ch.get("name", key), "channel": ch["url"], "channelId": cid,
                "checkedAt": now.isoformat(timespec="minutes"), "videos": vids}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        log.append({"at": now.isoformat(timespec="minutes"), "key": key, "ok": True,
                    "new": [v["id"] for v in vids if v["isNew"]],
                    "top": sorted([{"id": v["id"], "title": v["title"], "views": v["views"], "gain": v["viewsGain"]} for v in vids],
                                  key=lambda x: (x["gain"] or 0, x["views"] or 0), reverse=True)[:3]})
        print(f"{key}: 영상 {len(vids)}개, 새 영상 {sum(v['isNew'] for v in vids)}개")
    logp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
