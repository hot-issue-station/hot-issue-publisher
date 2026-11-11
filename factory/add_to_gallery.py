"""갤러리에 영상 한 편 추가 (공장으로 만든 영상을 올린 뒤 실행)
사용법: python add_to_gallery.py <유튜브ID> short|long "그룹" "꼬리표" "제목" "한 줄 설명"
"""
import json, os, re, sys
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gallery", "index.html")
vid, kind, group, tag, title, desc = sys.argv[1:7]
html = open(P, encoding="utf-8").read()
if f'id:"{vid}"' in html: sys.exit("이미 들어 있는 영상입니다")
row = "  " + json.dumps({"id": vid, "kind": kind, "group": group, "tag": tag, "title": title, "desc": desc, "picks": []}, ensure_ascii=False)
row = re.sub(r'"(\w+)":', r'\1:', row) + ",\n"
html = html.replace("const VIDEOS = [\n", "const VIDEOS = [\n" + row, 1)  # 최신 영상이 맨 위
open(P, "w", encoding="utf-8").write(html); print("갤러리에 추가:", title)
