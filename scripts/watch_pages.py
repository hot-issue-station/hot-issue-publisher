"""유튜브 채널 페이지에서 조회수 자동 수집 (대표 결정 2026-11-01, 분석팀).

RSS(feeds/videos.xml)가 10/31 밤부터 GitHub 서버에서 404라서, 공개 채널 페이지(/shorts, /videos)를 읽는다.
- 우리 채널(@hot.issue.station) → data/stats/youtube/<날짜>.json 에 하루 여러 번 스냅샷을 쌓는다.
- 리센느·안원잘부·벤치마킹 채널(config/benchmark.json) → data/benchmark/pages/<키>.json (최근 영상 제목·조회수, 지난 확인 대비 증가).
API 키·비용 없음. 페이지 형식이 바뀌어 0개가 나오면 data/stats/_page_error.json 에 남긴다.
"""
import json, pathlib, re, urllib.request, datetime

KST = datetime.timezone(datetime.timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "ko-KR,ko;q=0.9", "Cookie": "CONSENT=YES+1"}
OURS = {"issuebrief": ("이슈브리프 (우리 채널)", "https://www.youtube.com/@hot.issue.station")}
WATCH = {"rescene": ("RESCENE 공식", "https://www.youtube.com/@RESCENE_official"),
         "wonyi": ("안원잘부", "https://www.youtube.com/@helloiamwoninicetomeetyou")}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")


def initial_data(html):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S) or re.search(r'ytInitialData"\] = (\{.*?\});', html, re.S)
    return json.loads(m.group(1)) if m else {}


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def txt(x):
    if not x:
        return ""
    if isinstance(x, str):
        return x
    if "simpleText" in x:
        return x["simpleText"]
    if "runs" in x:
        return "".join(r.get("text", "") for r in x["runs"])
    if "content" in x:
        return x["content"]
    return ""


def num(s):
    """'조회수 1.5천회' / '1.2만회' / '1,234회' / '1.5K views' → 정수"""
    m = re.search(r"([\d.,]+)\s*(천|만|억|K|M|B)?", s.replace(" ", " ").replace("조회수", ""))
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return int(round(v * {None: 1, "천": 1e3, "만": 1e4, "억": 1e8, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)]))


def parse(data, kind, seen):
    out = []
    for d in walk(data):
        if "shortsLockupViewModel" in d:
            s = d["shortsLockupViewModel"]
            vid = (s.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}).get("videoId")
                   or s.get("entityId", "").replace("shorts-shelf-item-", ""))
            om = s.get("overlayMetadata", {})
            title, views = txt(om.get("primaryText")), txt(om.get("secondaryText"))
        elif "reelItemRenderer" in d:
            s = d["reelItemRenderer"]
            vid, title, views = s.get("videoId"), txt(s.get("headline")), txt(s.get("viewCountText"))
        elif "videoRenderer" in d:
            s = d["videoRenderer"]
            vid, title, views = s.get("videoId"), txt(s.get("title")), txt(s.get("viewCountText"))
            views += " | " + txt(s.get("publishedTimeText"))
        elif "lockupViewModel" in d and d["lockupViewModel"].get("contentType", "").endswith("VIDEO"):
            s = d["lockupViewModel"]; vid = s.get("contentId")
            md = s.get("metadata", {}).get("lockupMetadataViewModel", {})
            title = md.get("title", {}).get("content", "")
            parts = [t.get("text", {}).get("content", "") for r in md.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", []) for t in r.get("metadataParts", [])]
            vtxt = next((x for x in parts if "조회수" in x or "views" in x), "")
            ptxt = next((x for x in parts if "전" in x or "ago" in x), "")
            views = vtxt + " | " + ptxt
        else:
            continue
        if not vid or vid in seen:
            continue
        seen.add(vid)
        part = views.split(" | ")
        out.append({"id": vid, "title": title, "views": num(part[0]) if part[0] else None, "viewsText": part[0],
                    "published": part[1] if len(part) > 1 else "", "kind": kind})
    return out


def channel(url):
    vids, subs, seen = [], None, set()
    for tab, kind in (("shorts", "short"), ("videos", "video")):
        try:
            html = get(f"{url}/{tab}?hl=ko&gl=KR")
        except Exception as e:  # noqa
            continue
        data = initial_data(html)
        vids += parse(data, kind, seen)
        if subs is None:
            m = re.search(r'구독자 ([\d.,]+[천만억]?)명', html) or re.search(r'"([\d.,]+[KMB]?) subscribers"', html)
            subs = m.group(1) if m else None
    return subs, vids


def main():
    now = datetime.datetime.now(KST)
    at = now.isoformat(timespec="minutes")
    errors = []
    bench = json.loads(pathlib.Path("config/benchmark.json").read_text(encoding="utf-8")).get("youtube", {})
    targets = dict(OURS, **WATCH, **{k: (v["name"], v["url"]) for k, v in bench.items()})
    for key, (name, url) in targets.items():
        try:
            subs, vids = channel(url)
        except Exception as e:  # noqa
            errors.append(f"{key}: {type(e).__name__}: {e}")
            continue
        if not vids:
            errors.append(f"{key}: 영상 0개 (페이지 형식 변경 가능성)")
            continue
        if key in OURS:
            p = pathlib.Path(f"data/stats/youtube/{now:%Y-%m-%d}.json")
            p.parent.mkdir(parents=True, exist_ok=True)
            day = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"channel": url, "snapshots": []}
            day["snapshots"].append({"at": at, "subscribers": subs, "total": sum(v["views"] or 0 for v in vids), "videos": vids})
            p.write_text(json.dumps(day, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            p = pathlib.Path(f"data/benchmark/pages/{key}.json")
            p.parent.mkdir(parents=True, exist_ok=True)
            old = {v["id"]: v.get("views") for v in json.loads(p.read_text(encoding="utf-8"))["videos"]} if p.exists() else {}
            for v in vids:
                if old.get(v["id"]) is not None and v["views"] is not None:
                    v["gain"] = v["views"] - old[v["id"]]
            p.write_text(json.dumps({"name": name, "channel": url, "checkedAt": at, "subscribers": subs, "videos": vids[:40]},
                                    ensure_ascii=False, indent=1), encoding="utf-8")
        print(key, subs, len(vids))
    e = pathlib.Path("data/stats/_page_error.json")
    if errors:
        e.parent.mkdir(parents=True, exist_ok=True)
        e.write_text(json.dumps({"at": at, "errors": errors}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("\n".join(errors))
    elif e.exists():
        e.unlink()


if __name__ == "__main__":
    main()
