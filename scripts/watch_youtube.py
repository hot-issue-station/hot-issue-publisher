"""리센느 공식 유튜브 전담 모니터링 (대표 지시 2026-10-28).

GitHub Actions에서 하루 3번 돌며 공식 채널의 새 영상(쇼츠 포함)을 RSS로 읽어 저장한다. 비용 0원, 키 필요 없음.
결과: data/youtube/<채널>.json(최근 영상 15개: 제목·설명·게시 시각·조회수·좋아요·주소)
      data/youtube/new_<날짜>.json(지난번 이후 새로 올라온 영상) → 리센느 응원 특집·헤드라인 소재로 쓴다.
"""
import json, pathlib, re, sys, urllib.request, datetime
import xml.etree.ElementTree as ET

CHANNELS = {"rescene": "https://www.youtube.com/@RESCENE_official"}
UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ko-KR,ko;q=0.9"}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}
OUT = pathlib.Path("data/youtube")
KST = datetime.timezone(datetime.timedelta(hours=9))


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")


def channel_id(handle_url, cache):
    if cache.get("channelId"):
        return cache["channelId"]
    html = get(handle_url)
    m = re.search(r'"(?:externalId|channelId)":"(UC[\w-]{22})"', html) or re.search(r'channel/(UC[\w-]{22})', html)
    if not m:
        raise SystemExit("채널 번호를 찾지 못했어요")
    return m.group(1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now(KST).strftime("%Y%m%d")
    for key, url in CHANNELS.items():
        path = OUT / f"{key}.json"
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        cid = channel_id(url, old)
        root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
        vids = []
        for e in root.findall("a:entry", NS):
            vid = e.findtext("yt:videoId", "", NS)
            link = e.find("a:link", NS).get("href", "")
            g = e.find("m:group", NS)
            stats = g.find("m:community/m:statistics", NS) if g is not None else None
            rate = g.find("m:community/m:starRating", NS) if g is not None else None
            vids.append({
                "id": vid, "title": e.findtext("a:title", "", NS),
                "published": e.findtext("a:published", "", NS),
                "url": link, "shorts": "/shorts/" in link,
                "description": (g.findtext("m:description", "", NS) if g is not None else "")[:600],
                "views": int(stats.get("views", 0)) if stats is not None else None,
                "likes": int(rate.get("count", 0)) if rate is not None else None,
            })
        seen = {v["id"] for v in old.get("videos", [])}
        new = [v for v in vids if v["id"] not in seen] if seen else []
        data = {"channel": url, "channelId": cid, "checkedAt": datetime.datetime.now(KST).isoformat(timespec="minutes"), "videos": vids}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        if new:
            np = OUT / f"new_{today}.json"
            prev = json.loads(np.read_text(encoding="utf-8")) if np.exists() else []
            ids = {v["id"] for v in prev}
            np.write_text(json.dumps(prev + [dict(v, channel=key) for v in new if v["id"] not in ids], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{key}: 영상 {len(vids)}개, 새 영상 {len(new)}개")


if __name__ == "__main__":
    sys.exit(main())
