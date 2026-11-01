"""채널 한 곳 살펴보기 (대표가 링크를 주면 분석, 11/1).
입력 VIDEO_URL(영상 주소) 또는 CHANNEL_URL → data/probe/<NAME>.json
{channel, url, subscribers, videoCount, shorts:[...], videos:[...]} (조회수 순 정렬 포함)
"""
import json, os, pathlib, re, sys
sys.path.insert(0, "scripts")
import watch_pages as w

name = os.environ.get("NAME", "probe")
url = os.environ.get("CHANNEL_URL", "").strip()
if not url:
    vid = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", os.environ["VIDEO_URL"]).group(1)
    o = json.loads(w.get(f"https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={vid}"))
    url = o["author_url"]
html = w.get(url + "?hl=ko&gl=KR")
title = (re.search(r'<meta property="og:title" content="([^"]*)"', html) or [None, ""])[1]
desc = (re.search(r'<meta property="og:description" content="([^"]*)"', html) or [None, ""])[1]
vc = re.search(r'동영상 ([\d.,]+[천만]?)개', html)
subs, vids = w.channel(url)
out = {"channel": title, "url": url, "description": desc, "subscribers": subs,
       "videoCount": vc.group(1) if vc else None, "videos": vids}
p = pathlib.Path(f"data/probe/{name}.json"); p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(title, subs, len(vids))
