"""리센느 공식 유튜브 전담 모니터링 (대표 지시 2026-10-28).

GitHub Actions에서 하루 3번 돌며 공식 채널의 새 영상(쇼츠 포함)을 RSS로 읽어 저장한다. 비용 0원, 키 필요 없음.
결과: data/youtube/<채널>.json(최근 영상 15개: 제목·설명·게시 시각·조회수·좋아요·주소)
      data/youtube/new_<날짜>.json(지난번 이후 새로 올라온 영상) → 리센느 응원 특집·헤드라인 소재로 쓴다.
(10/31 대표 결정) 리센느 공식 영상의 미리보기 이미지를 assets/rescene/yt/<영상ID>.jpg 로 내려받는다(검은 띠는 잘라 냄).
      카드 표지에 쓸 때 출처 "영상 화면: RESCENE 공식 유튜브". 대표가 캡처를 보내지 않아도 된다.
(10/31 대표 결정) 우리 채널(@hot.issue.station) 영상별 조회수·좋아요를 data/stats/youtube/<날짜>.json 에 쌓는다(통계 캡처 대신).
"""
import json, pathlib, re, sys, urllib.request, datetime
import xml.etree.ElementTree as ET

CHANNELS = {"rescene": "https://www.youtube.com/@RESCENE_official",
            "wonyi": "https://www.youtube.com/@helloiamwoninicetomeetyou",   # 안원잘부(원이 채널), 10/31 대표 지시

            "issuebrief": "https://www.youtube.com/@hot.issue.station"}   # 우리 채널: 통계만 쌓고 new_ 파일·사진은 만들지 않음
THUMBS = {"rescene": pathlib.Path("assets/rescene/yt"), "wonyi": pathlib.Path("assets/rescene/yt")}
STATS = pathlib.Path("data/stats/youtube")
UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ko-KR,ko;q=0.9"}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}
OUT = pathlib.Path("data/youtube")
KST = datetime.timezone(datetime.timedelta(hours=9))


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")


def feed(cid):
    """채널 RSS. channel_id 주소가 404면 업로드 목록(playlist_id=UU…) 주소로 다시 시도."""
    try:
        return get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
    except Exception:
        return get(f"https://www.youtube.com/feeds/videos.xml?playlist_id=UU{cid[2:]}")


def get_bytes(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def save_thumb(vid, folder, shorts=False):
    """공식 영상 미리보기 이미지 저장. 쇼츠는 가로 그림 안에 세로 화면이 들어 있어 양옆 검은 띠를 잘라 낸다."""
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"{vid}.jpg"
    if out.exists():
        return False
    data = None
    for name in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            data = get_bytes(f"https://i.ytimg.com/vi/{vid}/{name}.jpg")
            if len(data) > 5000:
                break
        except Exception:
            data = None
    if not data:
        return False
    try:
        from PIL import Image, ImageOps
        import io
        im = Image.open(io.BytesIO(data)).convert("RGB")
        mask = ImageOps.grayscale(im).point(lambda v: 255 if v > 24 else 0)
        box = mask.getbbox()
        if box and (box[2] - box[0]) > im.width * 0.2:
            im = im.crop(box)
        if shorts and im.width > im.height:   # 쇼츠: 흐린 배경 가운데의 세로(9:16) 화면만 남김
            w = round(im.height * 9 / 16)
            x = (im.width - w) // 2
            im = im.crop((x, 0, x + w, im.height))
        im.save(out, "JPEG", quality=90)
    except Exception:
        out.write_bytes(data)
    return True


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
        try:
            cid = channel_id(url, old)
            root = ET.fromstring(feed(cid))
        except BaseException as e:  # 실패 이유를 파일로 남긴다(Actions 로그를 못 열 때 확인용)
            (OUT / "_error.json").write_text(json.dumps({"at": datetime.datetime.now(KST).isoformat(timespec="minutes"), "channel": key,
                                                          "error": f"{type(e).__name__}: {str(e)[:300]}"}, ensure_ascii=False), encoding="utf-8")
            print(key, "실패", e); continue
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
        now = datetime.datetime.now(KST)
        if key == "issuebrief":
            STATS.mkdir(parents=True, exist_ok=True)
            sp = STATS / f"{today}.json"
            snaps = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else []
            snaps.append({"at": now.isoformat(timespec="minutes"),
                          "videos": [{k: v[k] for k in ("id", "title", "published", "views", "likes")} for v in vids]})
            sp.write_text(json.dumps(snaps, ensure_ascii=False, indent=1), encoding="utf-8")
            (OUT / f"{key}.json").write_text(json.dumps({"channel": url, "channelId": cid, "checkedAt": now.isoformat(timespec="minutes"), "videos": vids}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{key}: 우리 채널 통계 {len(vids)}개 저장")
            continue
        if key in THUMBS:
            got = sum(save_thumb(v["id"], THUMBS[key], v["shorts"]) for v in vids)
            print(f"{key}: 미리보기 이미지 새로 {got}장")
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
