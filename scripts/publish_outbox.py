"""보내기함(outbox) 자동 게시 (대표 결정 2026-10-31).

outbox/<ID>/ 폴더에 reel.mp4 와 post.json 을 넣어 올리면 GitHub Actions가 돌며
  - Threads: 노래 없이 바로 공개 게시 (비밀값 THREADS_TOKEN 이 있을 때)
  - 유튜브: 제목·설명·태그를 넣어 '비공개'로 올림 (유튜브 심사 통과 뒤, 저장소 변수 YT_UPLOAD=on 일 때만)
결과는 outbox/<ID>/done.json 에 남긴다(이미 올린 곳은 다시 올리지 않음).

post.json 예시
{"id": "20261031_RS",
 "threads": {"text": "…450자 이내, 태그 1개…", "replies": ["답글 1 (태그 1개)", "답글 2 (태그 1개)"]},
 "youtube": {"title": "… #Shorts", "description": "…", "tags": "리센느,RESCENE"}}

비밀값(토큰)은 대표가 GitHub 설정에 직접 넣는다. 이 스크립트는 토큰을 화면이나 파일에 남기지 않는다.
"""
import json, os, pathlib, sys, time, urllib.parse, urllib.request, datetime

REPO = os.environ.get("GITHUB_REPOSITORY", "hot-issue-station/hot-issue-publisher")
SHA = os.environ.get("GITHUB_SHA", "main")
KST = datetime.timezone(datetime.timedelta(hours=9))
TH = "https://graph.threads.net/v1.0"


def now():
    return datetime.datetime.now(KST).isoformat(timespec="minutes")


def http(method, url, data=None, headers=None, raw=None):
    body = raw if raw is not None else (urllib.parse.urlencode(data).encode() if data else None)
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(txt) if txt.strip().startswith(("{", "[")) else txt), dict(r.headers)
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(txt), dict(e.headers)
        except Exception:
            return e.code, txt[:500], dict(e.headers)


def video_urls(folder):
    rel = f"{folder.as_posix()}/reel.mp4"
    return [f"https://cdn.jsdelivr.net/gh/{REPO}@{SHA}/{rel}",           # video/mp4 로 내려줌
            f"https://raw.githubusercontent.com/{REPO}/{SHA}/{rel}"]


# ---------- Threads ----------
def post_replies(tok, parent_id, texts):
    """대표 결정 10/31: Threads는 글 하나에 주제 태그 1개만 인정 → 내 글에 답글을 달아 답글마다 태그 1개씩 더 붙인다."""
    out = []
    for t in (texts or [])[:2]:
        time.sleep(5)
        st, res, _ = http("POST", f"{TH}/me/threads", {"media_type": "TEXT", "text": t[:500], "reply_to_id": parent_id, "access_token": tok})
        if st != 200 or "id" not in res:
            out.append({"error": str(res)[:200]}); continue
        time.sleep(3)
        st, pub, _ = http("POST", f"{TH}/me/threads_publish", {"creation_id": res["id"], "access_token": tok})
        out.append({"ok": True, "id": pub.get("id")} if st == 200 and isinstance(pub, dict) and "id" in pub else {"error": str(pub)[:200]})
    return out


def post_threads(folder, text, replies_text=None):
    # 대표 결정(10/31 23:48): Threads는 대표가 앱에서 음악 스티커를 붙여 직접 올린다(사람이 올리는 느낌). 자동 게시는 THREADS_AUTO=on 일 때만.
    if os.environ.get("THREADS_AUTO", "") != "on":
        return {"skipped": "Threads는 대표가 직접 올림 (THREADS_AUTO 꺼짐)"}
    tok = os.environ.get("THREADS_TOKEN", "").strip()
    if not tok:
        return {"skipped": "THREADS_TOKEN 비밀값 없음"}
    if len(text) > 500:
        return {"error": f"글이 {len(text)}자라 500자를 넘어요"}
    last = None
    for vurl in video_urls(folder):
        st, res, _ = http("POST", f"{TH}/me/threads", {"media_type": "VIDEO", "video_url": vurl, "text": text, "access_token": tok})
        if st != 200 or "id" not in res:
            last = res; continue
        cid = res["id"]
        for _ in range(40):                       # 영상 처리 대기 (최대 약 6~7분)
            time.sleep(10)
            st, s, _ = http("GET", f"{TH}/{cid}?fields=status,error_message&access_token={tok}")
            if isinstance(s, dict) and s.get("status") in ("FINISHED", "ERROR", "EXPIRED"):
                break
        if not (isinstance(s, dict) and s.get("status") == "FINISHED"):
            last = s; continue
        st, pub, _ = http("POST", f"{TH}/me/threads_publish", {"creation_id": cid, "access_token": tok})
        if st == 200 and "id" in pub:
            st, info, _ = http("GET", f"{TH}/{pub['id']}?fields=permalink&access_token={tok}")
            replies = post_replies(tok, pub["id"], replies_text)
            return {"ok": True, "id": pub["id"], "permalink": (info or {}).get("permalink", "") if isinstance(info, dict) else "", "replies": replies, "at": now()}
        last = pub
    return {"error": str(last)[:400]}


# ---------- 유튜브 (심사 통과 뒤에만) ----------
def yt_token():
    st, res, _ = http("POST", "https://oauth2.googleapis.com/token", {
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    if st != 200:
        raise RuntimeError(f"유튜브 로그인 실패: {str(res)[:200]}")
    return res["access_token"]


def post_youtube(folder, meta):
    if os.environ.get("YT_UPLOAD", "") != "on":
        return {"skipped": "유튜브 심사 통과 전 (YT_UPLOAD 꺼짐)"}
    if not all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")):
        return {"skipped": "유튜브 비밀값 없음"}
    at = yt_token()
    video = (folder / "reel.mp4").read_bytes()
    tags = [t.strip() for t in str(meta.get("tags", "")).split(",") if t.strip()]
    body = {"snippet": {"title": meta["title"][:100], "description": meta.get("description", "")[:5000],
                        "tags": tags, "categoryId": "25", "defaultLanguage": "ko"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
    st, res, hd = http("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                       headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json; charset=UTF-8",
                                "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))},
                       raw=json.dumps(body).encode())
    loc = hd.get("Location") or hd.get("location")
    if st != 200 or not loc:
        return {"error": f"업로드 시작 실패 {st}: {str(res)[:300]}"}
    st, res, _ = http("PUT", loc, headers={"Content-Type": "video/mp4"}, raw=video)
    if st in (200, 201) and isinstance(res, dict) and res.get("id"):
        return {"ok": True, "id": res["id"], "studio": f"https://studio.youtube.com/video/{res['id']}/edit", "at": now()}
    return {"error": f"업로드 실패 {st}: {str(res)[:300]}"}


def main():
    root = pathlib.Path("outbox")
    if not root.exists():
        print("보내기함 비어 있음"); return 0
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        pj, dj = folder / "post.json", folder / "done.json"
        if not pj.exists() or not (folder / "reel.mp4").exists():
            continue
        post = json.loads(pj.read_text(encoding="utf-8"))
        done = json.loads(dj.read_text(encoding="utf-8")) if dj.exists() else {}
        changed = False
        if post.get("threads") and not done.get("threads", {}).get("ok"):
            done["threads"] = post_threads(folder, post["threads"]["text"], post["threads"].get("replies")); changed = True
        if post.get("youtube") and not done.get("youtube", {}).get("ok"):
            try:
                done["youtube"] = post_youtube(folder, post["youtube"])
            except Exception as e:
                done["youtube"] = {"error": str(e)[:300]}
            changed = True
        if changed:
            dj.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
            print(folder.name, {k: ("올림" if v.get("ok") else v.get("skipped") or v.get("error")) for k, v in done.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
