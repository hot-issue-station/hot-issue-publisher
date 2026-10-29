"""릴스 소개글 앞부분 검사 (대표 결정 2026-10-29, 콘텐츠팀).

인스타는 캡션 앞 약 125자만 보여 주고 나머지는 '더 보기'로 접는다. 이 앞부분에 훅과 핵심 사실이 들어가야 한다.
사용법: python3 scripts/check_caption.py <캡션 파일 또는 -> [--hook "카드 1장 훅"]
출력: 앞 125자 미리보기 상자 + 검사 결과. 문제가 있으면 종료 코드 2(고쳐서 다시 검사).
"""
import argparse, re, sys

PREVIEW = 125


def check(text, hook=""):
    t = text.strip()
    first = t.split("\n", 1)[0].strip()
    head = t[:PREVIEW]
    probs = []
    if not first:
        probs.append("첫 줄이 비어 있어요")
    if len(first) > 40:
        probs.append(f"첫 줄(훅)이 {len(first)}자예요. 40자 안으로 줄여 주세요")
    if first.startswith("#") or first.startswith("어제의 베스트 댓글") or first.startswith("🏆") or first.startswith("광고"):
        probs.append("첫 줄은 훅이어야 해요(베스트 댓글·랭킹·해시태그·연락처는 아래로)")
    top = [l for l in t.split("\n") if l.strip()][:2]
    if any("#" in l for l in top):
        probs.append("첫 두 줄에 해시태그가 있어요. 해시태그는 맨 끝으로")
    if not re.search(r"\d", head):
        probs.append("앞 125자 안에 숫자(핵심 사실)가 없어요. 둘째 줄에 숫자가 든 사실 한 문장을 넣어 주세요")
    if hook:
        key = re.sub(r"[\s*,.!?·]", "", hook)[:6]
        if key and key not in re.sub(r"[\s*,.!?·]", "", head):
            probs.append("앞 125자에 카드 1장 훅과 같은 말이 안 보여요")
    return head, probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--hook", default="")
    a = ap.parse_args()
    text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
    head, probs = check(text, a.hook)
    print("┌─ '더 보기' 전에 보이는 부분 (" + str(len(head)) + "자) ─")
    for line in head.split("\n"):
        print("│ " + line)
    print("└─ … 더 보기")
    if probs:
        print("검사 실패:"); [print(" - " + p) for p in probs]; return 2
    print("검사 통과"); return 0


if __name__ == "__main__":
    sys.exit(main())
