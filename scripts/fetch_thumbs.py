"""카드 사진 자동 준비 (대표 결정 2026-10-31 19:29: 앞으로 카드는 무조건 사진을 넣는다).

GitHub Actions(유튜브 접속 가능)에서 돈다. 작업 공간 셸은 유튜브 이미지 서버에 못 들어가기 때문.
입력: 환경변수 QUERIES = 줄바꿈으로 구분한 "이름|검색어" (예: "jhope_monalisa|j-hope MONA LISA Official MV")
      또는 "이름|https://www.youtube.com/watch?v=영상ID" (영상 주소를 알면 그대로)
출력: assets/thumbs/<이름>.jpg (검은 띠 잘라 냄, 쇼츠는 세로 9:16)
      data/thumbs/<이름>.json = {name, query, videoId, title, channel, url, at}
카드에 쓸 때 photoLabel 은 "영상 화면 · <channel> 공식 유튜브" — channel 이 공식 채널(가수·소속사·구단·리그·방송사)인지 만드는 쪽이 확인한다.
"""
import json, os, pathlib, re, sys, urllib.parse, urllib.request, datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from watch_youtube import save_thumb, get, UA  # noqa: E402

KST = datetime.timezone(datetime.timedelta(hours=9))
IMG = pathlib.Path("assets/thumbs")
META = pathlib.Path("data/thumbs")


def search(q):
    html = get("https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + "&hl=ko&gl=KR")
    for m in re.finditer(r'"videoRenderer":\{"videoId":"([\w-]{11})"', html):
        vid = m.group(1)
        chunk = html[m.end(): m.end() + 6000]
        title = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"\}', chunk)
        owner = re.search(r'"ownerText":\{"runs":\[\{"text":"(.*?)"', chunk)
        return vid, (title.group(1) if title else ""), (owner.group(1) if owner else ""), False
    m = re.search(r'"reelItemRenderer":\{"videoId":"([\w-]{11})"', html) or re.search(r'/shorts/([\w-]{11})', html)
    if m:
        return m.group(1), "", "", True
    raise RuntimeError("검색 결과 없음")


def video_info(vid):
    try:
        o = json.loads(get(f"https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={vid}"))
        return o.get("title", ""), o.get("author_name", "")
    except Exception:
        return "", ""


def main():
    lines = [l.strip() for l in os.environ.get("QUERIES", "").splitlines() if "|" in l]
    IMG.mkdir(parents=True, exist_ok=True); META.mkdir(parents=True, exist_ok=True)
    for line in lines:
        name, q = [x.strip() for x in line.split("|", 1)]
        name = re.sub(r"[^\w-]", "_", name)[:60]
        try:
            m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", q)
            if m:
                vid, title, channel, shorts = m.group(1), "", "", "shorts/" in q
            else:
                vid, title, channel, shorts = search(q)
            t2, c2 = video_info(vid)
            title, channel = title or t2, channel or c2
            tmp = IMG / "_tmp"; tmp.mkdir(exist_ok=True)
            (tmp / f"{vid}.jpg").unlink(missing_ok=True)
            if not save_thumb(vid, tmp, shorts):
                raise RuntimeError("미리보기 이미지를 받지 못함")
            (tmp / f"{vid}.jpg").replace(IMG / f"{name}.jpg")
            meta = {"name": name, "query": q, "videoId": vid, "title": title, "channel": channel,
                    "url": f"https://www.youtube.com/watch?v={vid}", "at": datetime.datetime.now(KST).isoformat(timespec="minutes")}
            print(name, "→", vid, channel, title[:50])
        except Exception as e:
            meta = {"name": name, "query": q, "error": f"{type(e).__name__}: {str(e)[:200]}"}
            print(name, "실패", e)
        (META / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        (IMG / "_tmp").rmdir()
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
