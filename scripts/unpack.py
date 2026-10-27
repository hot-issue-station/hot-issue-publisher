"""inbox/ 에 올린 카드 묶음(zip)을 posts/<날짜_회차>/ 으로 풀어 둔다.

스튜디오 zip 안의 YYYYMMDD_SLOT_주제_01.jpg, _caption.txt, _post.json을 읽어
posts/YYYYMMDD_SLOT/01.jpg … , caption.txt, post.json 으로 정리한다.
Instagram이 사진을 가져갈 공개 주소에 한글이 들어가지 않도록 이름을 영문·숫자로 바꾼다.
다 풀면 zip은 지운다.
"""
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
INBOX, POSTS = ROOT / "inbox", ROOT / "posts"


def target_dir(stem):
    m = re.match(r"(\d{8})_(AM|PM|NT)", stem)
    base = f"{m.group(1)}_{m.group(2)}" if m else "post"
    d, n = POSTS / base, 2
    while d.exists():  # 같은 회차를 다시 올리면 _2, _3 …
        d, n = POSTS / f"{base}_{n}", n + 1
    return d


def main():
    POSTS.mkdir(exist_ok=True)
    done = 0
    for z in sorted(INBOX.glob("*.zip")):
        with zipfile.ZipFile(z) as zf:
            files = {pathlib.PurePath(i.filename).name: i for i in zf.infolist() if not i.is_dir()}
            post_name = next((n for n in files if n.endswith("_post.json") or n == "post.json"), None)
            if not post_name:
                print(f"{z.name}: post.json이 없어 게시 대상이 아닙니다. 스튜디오에서 다시 저장해 주세요.")
                z.unlink(); continue
            meta = json.loads(zf.read(files[post_name]).decode("utf-8"))
            jpgs = sorted(n for n in files if n.lower().endswith((".jpg", ".jpeg")))
            order = [n for n in meta.get("images", []) if n in files] or jpgs
            target = target_dir(z.stem); target.mkdir(parents=True)
            new_names = []
            for i, n in enumerate(order, 1):
                new = f"{i:02d}.jpg"
                (target / new).write_bytes(zf.read(files[n])); new_names.append(new)
            cap = next((n for n in files if n.endswith("_caption.txt") or n == "caption.txt"), None)
            if cap:
                (target / "caption.txt").write_bytes(zf.read(files[cap]))
        meta["images"] = new_names
        meta["sourceZip"] = z.name
        (target / "post.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{z.name}: 풀기 완료 → posts/{target.name} (이미지 {len(new_names)}장, 예약 {meta.get('publishAt')})")
        z.unlink()
        done += 1
    print(f"묶음 {done}개 처리")
    return 0


if __name__ == "__main__":
    sys.exit(main())
