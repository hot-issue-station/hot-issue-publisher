"""이슈브리프 게시 프로그램 — 예약 시각이 된 카드 묶음을 Instagram 캐러셀로 게시한다.

posts/<묶음 이름>/ 안의 post.json, JPG, caption 파일을 읽는다.
- DRY_RUN이 "false"가 아니면 시험 모드: 실제로 게시하지 않고 할 일만 기록한다.
  단, post.json에 "approval3": {"approved": true}(대표의 발행 직전 승인)가 있는 묶음은 실제로 게시한다.
- 게시에 성공하면 같은 폴더에 published.json을 남겨 두 번 올리지 않는다.
추가 패키지 없이 파이썬 표준 라이브러리만 쓴다.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
KST = dt.timezone(dt.timedelta(hours=9))

DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_ID = os.environ.get("IG_USER_ID", "")
VERSION = os.environ.get("GRAPH_VERSION", "v26.0")
# Instagram 로그인 토큰(IG로 시작)은 graph.instagram.com, Facebook 로그인 토큰(EAA…)은 graph.facebook.com
API = ("https://graph.instagram.com/" if TOKEN.startswith("IG") else "https://graph.facebook.com/") + VERSION
REPO = os.environ.get("GITHUB_REPOSITORY", "")       # owner/repo, Actions가 채워 줌
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
PREFLIGHT = os.environ.get("PREFLIGHT", "").strip().lower() == "true"  # 미리 점검: 사진을 Instagram이 가져가는지만 확인, 게시 안 함
LATE_LIMIT_HOURS = float(os.environ.get("LATE_LIMIT_HOURS", "6"))  # 이보다 늦은 묶음은 자동 게시하지 않음


def log(msg):
    print(f"[{dt.datetime.now(KST):%m-%d %H:%M}] {msg}", flush=True)


def api(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Instagram API 오류 {e.code}: {body[:400]}") from None


def wait_ready(container_id):
    for _ in range(10):  # 문서 권장: 1분 간격, 5분 이내 → 30초 간격 10회
        status = api("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"컨테이너 {container_id} 상태 {status}")
        time.sleep(30)
    raise RuntimeError(f"컨테이너 {container_id} 준비 시간 초과")


def public_url(folder, name):
    path = urllib.parse.quote(f"posts/{folder}/{name}")
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"


def load(folder):
    meta = json.loads((folder / "post.json").read_text(encoding="utf-8"))
    images = [n for n in meta.get("images", []) if (folder / n).exists()]
    if not images:
        images = sorted(p.name for p in folder.glob("*.jpg"))
    if not 2 <= len(images) <= 10:
        raise RuntimeError(f"캐러셀은 이미지 2~10장이 필요합니다 (지금 {len(images)}장)")
    caption = meta.get("caption", "")
    if len(caption) > 2200:
        raise RuntimeError(f"캡션이 2,200자를 넘습니다 ({len(caption)}자)")
    when = dt.datetime.fromisoformat(meta["publishAt"])
    return meta, images, caption, when


def publish(folder, images, caption):
    children = []
    for name in images:
        res = api("POST", f"{IG_ID}/media", image_url=public_url(folder.name, name), is_carousel_item="true")
        children.append(res["id"])
        log(f"  이미지 컨테이너 {name} → {res['id']}")
    for cid in children:
        wait_ready(cid)
    carousel = api("POST", f"{IG_ID}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    wait_ready(carousel)
    return api("POST", f"{IG_ID}/media_publish", creation_id=carousel)["id"]


def check_token():
    """토큰이 맞는지 확인하고 계정 ID를 알아낸다. 계정 ID 비밀값이 없어도 된다."""
    global IG_ID
    if "graph.instagram.com" in API:
        me = api("GET", "me", fields="user_id,username")
        IG_ID = IG_ID or str(me.get("user_id") or me.get("id"))
        log(f"토큰 확인(Instagram 로그인): @{me.get('username')} (계정 ID {IG_ID})")
        return
    # Facebook 로그인: 내가 관리하는 페이지에 연결된 Instagram 계정을 찾는다
    pages = api("GET", "me/accounts", fields="name,instagram_business_account{id,username}").get("data", [])
    linked = [p for p in pages if p.get("instagram_business_account")]
    if not linked:
        raise RuntimeError("이 토큰으로 볼 수 있는 Facebook 페이지에 연결된 Instagram 계정이 없습니다. 페이지와 Instagram 연결, 토큰 발급 때 페이지 선택을 확인해 주세요.")
    pick = next((p for p in linked if p["instagram_business_account"]["id"] == IG_ID), linked[0])
    IG_ID = pick["instagram_business_account"]["id"]
    log(f"토큰 확인(Facebook 로그인): 페이지 '{pick.get('name')}' → @{pick['instagram_business_account'].get('username')} (계정 ID {IG_ID})")


def main():
    now = dt.datetime.now(KST)
    log(f"{'시험 모드' if DRY_RUN else '실제 게시 모드'}로 시작")
    if TOKEN:
        try:
            check_token()
        except Exception as e:
            log(f"토큰 확인 실패 — {e}")
            log("IG_ACCESS_TOKEN 비밀값이 맞는지, 기한(60일)이 지나지 않았는지 확인해 주세요.")
            return 1
    elif not DRY_RUN:
        log("실제 게시 모드인데 IG_ACCESS_TOKEN 비밀값이 비어 있습니다. 설정을 확인해 주세요.")
        return 1
    else:
        log("토큰이 아직 없어 토큰 확인은 건너뜁니다.")
    failed = 0
    for folder in sorted(p for p in POSTS.iterdir() if p.is_dir()) if POSTS.exists() else []:
        if (folder / "published.json").exists() or not (folder / "post.json").exists():
            continue
        try:
            meta, images, caption, when = load(folder)
        except Exception as e:  # 묶음이 잘못되면 그 묶음만 건너뛴다
            log(f"{folder.name}: 건너뜀 — {e}")
            failed += 1
            continue
        if PREFLIGHT:
            try:
                res = api("POST", f"{IG_ID}/media", image_url=public_url(folder.name, images[0]), is_carousel_item="true")
                wait_ready(res["id"])
                log(f"{folder.name}: [미리 점검] Instagram이 사진을 정상으로 가져갔습니다 (게시는 하지 않음, 예약 {when:%m-%d %H:%M})")
            except Exception as e:
                log(f"{folder.name}: [미리 점검] 실패 — {e}")
                failed += 1
            continue
        if when > now:
            log(f"{folder.name}: 예약 {when:%m-%d %H:%M} 대기")
            continue
        late_h = (now - when).total_seconds() / 3600
        if late_h > LATE_LIMIT_HOURS:
            log(f"{folder.name}: 예약 시각에서 {late_h:.1f}시간 지나 자동 게시하지 않음 (post.json의 publishAt을 고치면 다시 올라감)")
            continue
        approved = (meta.get("approval3") or {}).get("approved") is True
        if DRY_RUN and not approved:
            log(f"{folder.name}: [시험] 이미지 {len(images)}장, 캡션 {len(caption)}자를 게시할 차례입니다")
            for n in images:
                log(f"  {public_url(folder.name, n)}")
            continue
        try:
            media_id = publish(folder, images, caption)
            (folder / "published.json").write_text(json.dumps({"mediaId": media_id, "publishedAt": now.isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"{folder.name}: 게시 완료 (미디어 {media_id})")
        except Exception as e:
            log(f"{folder.name}: 게시 실패 — {e}")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
