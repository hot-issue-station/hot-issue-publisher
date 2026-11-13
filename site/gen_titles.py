# 통계판(stats.html)용 이름표: gallery/hall.html 에 흩어진 유튜브 영상(광고관·조각상 직캠·포토 월 등)과 멤버 카드 이름을 모아 titles.json 으로 (대표 11/14 「통계에서 뭔 영상인지 모르겠다」)
import json, re, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
T = {}
def put(k, title, where):
    if k and title and k not in T: T[k] = {"title": title, "where": where}
for m in re.finditer(r'\bid:"([\w-]{11})"[^{}]*?\btitle:"([^"]*)"(?:[^{}]*?\bchannel:"([^"]*)")?', s):
    put(m.group(1), m.group(2), m.group(3) or "")
for m in re.finditer(r'\{[^{}]*?youtube\.com/watch\?v=([\w-]{11})[^{}]*\}', s):
    blk = m.group(0); g = lambda k: (re.search(k + r':"([^"]*)"', blk) or [None, ""])[1]
    title = g("caption") or g("title") or " · ".join(x for x in [g("brand"), g("member")] if x)
    put(m.group(1), title or "광고관·포토 월 영상", g("credit").replace("YouTube · ", ""))
for m in re.finditer(r'\{id:"([a-z]+)",\s*name:"([^"]+)",\s*name_en:"([^"]+)"', s):
    put("m_" + m.group(1), f"멤버 소개 카드 · {m.group(2)}", "건물 앞 조각상")
json.dump(T, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(len(T), "개 이름표")
