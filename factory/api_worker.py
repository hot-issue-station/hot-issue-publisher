"""API 일꾼 v1 — 100달러 크레딧을 아껴 쓰는 대량 작업용
사용법:
  python api_worker.py 일감.json            # 일괄(Batch) 제출 → 50% 할인, 보통 1시간 안에 끝남
  python api_worker.py 결과 <batch_id>       # 결과 받아서 results/ 에 저장
일감.json 예: {"model":"claude-haiku-5-5","system":"한국어로 짧게.","jobs":[{"id":"q1","prompt":"..."}]}
규칙
  - API 키는 대표가 직접 환경 변수 ANTHROPIC_API_KEY 에 넣는다(Claude는 키를 입력하지 않음).
  - 기본 모델은 가장 싼 Haiku. 문장 다듬기·번역·댓글 분류·요약 같은 단순 대량 작업만 맡긴다.
  - 같은 system 문장은 캐시(prompt caching)로 묶어 반복 비용을 줄인다.
  - budget.json 의 월 한도(기본 20달러)를 넘으면 제출하지 않는다.
  - 사실 확인·최종 문구·게시는 하지 않는다(대표실 Claude가 검증).
"""
import json, os, sys, time, urllib.request

API = "https://api.anthropic.com/v1/messages/batches"
KEY = os.environ.get("ANTHROPIC_API_KEY")
HERE = os.path.dirname(os.path.abspath(__file__))
BUDGET = os.path.join(HERE, "budget.json")

def req(url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method="POST" if body else "GET",
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(r) as f: return f.read().decode()

def budget():
    b = json.load(open(BUDGET)) if os.path.exists(BUDGET) else {"monthly_limit_usd": 20, "month": "", "spent_est_usd": 0}
    m = time.strftime("%Y-%m")
    if b["month"] != m: b.update(month=m, spent_est_usd=0)
    return b

def submit(path):
    task = json.load(open(path, encoding="utf-8")); b = budget()
    if b["spent_est_usd"] >= b["monthly_limit_usd"]: sys.exit(f"이번 달 한도({b['monthly_limit_usd']}달러)를 넘어서 멈춤")
    system = [{"type": "text", "text": task.get("system", "한국어로 짧게 답한다."), "cache_control": {"type": "ephemeral"}}]
    reqs = [{"custom_id": j["id"], "params": {"model": task.get("model", "claude-haiku-5-5"), "max_tokens": j.get("max_tokens", 800),
             "system": system, "messages": [{"role": "user", "content": j["prompt"]}]}} for j in task["jobs"]]
    res = json.loads(req(API, {"requests": reqs}))
    print("제출됨:", res["id"], "· 일감", len(reqs), "개 → 나중에: python api_worker.py 결과", res["id"])

def fetch(bid):
    st = json.loads(req(f"{API}/{bid}"))
    if st["processing_status"] != "ended": sys.exit(f"아직 처리 중: {st['request_counts']}")
    out = os.path.join(HERE, "results"); os.makedirs(out, exist_ok=True); b = budget(); tin = tout = 0
    lines = req(st["results_url"]).splitlines(); res = {}
    for ln in lines:
        r = json.loads(ln); m = r["result"].get("message")
        if m:
            res[r["custom_id"]] = "".join(c.get("text", "") for c in m["content"])
            tin += m["usage"]["input_tokens"]; tout += m["usage"]["output_tokens"]
        else: res[r["custom_id"]] = "실패: " + json.dumps(r["result"])[:200]
    p = os.path.join(out, bid + ".json"); json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    b["tokens_in"] = b.get("tokens_in", 0) + tin; b["tokens_out"] = b.get("tokens_out", 0) + tout
    json.dump(b, open(BUDGET, "w"), indent=1)
    print("저장:", p, f"· 입력 {tin:,} / 출력 {tout:,} 토큰 (콘솔의 실제 사용액으로 spent_est_usd 갱신)")

if __name__ == "__main__":
    if not KEY: sys.exit("ANTHROPIC_API_KEY 가 없습니다. 대표님이 키를 환경 변수에 넣어 주세요.")
    fetch(sys.argv[2]) if sys.argv[1] == "결과" else submit(sys.argv[1])
