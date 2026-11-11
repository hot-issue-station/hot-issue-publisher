"""AI 교환대 v1 — 단순 대량 작업(번역·요약·댓글 분류·자막 초안)을 무료 AI부터 차례로 맡긴다
사용법:
  python ai_router.py "프롬프트"              # 한 건, 답과 '누가 답했는지'를 화면에 출력
  python ai_router.py "프롬프트" --private    # 개인정보 포함 → 외부 무료 AI(제미나이·OpenRouter) 건너뜀
  python ai_router.py 일감.json               # 여러 건 → results/router_날짜시각.json
  (선택) --config 다른설정.json
일감.json 예: {"system":"한국어로 짧게.","private":false,
              "jobs":[{"id":"c1","prompt":"이 댓글 분류: ...","private":true,"max_tokens":300}]}
순서(router_config.json 에서 바꿈): 1) 제미나이 무료 → 2) Ollama(노트북) → 3) OpenRouter :free → 4) Claude Haiku
규칙
  - 키는 환경 변수에서만 읽는다(GEMINI_API_KEY / OPENROUTER_API_KEY / ANTHROPIC_API_KEY). 키가 없는 단계는 건너뜀.
    키는 화면·결과·state.json 어디에도 쓰지 않는다(오류 문장에 섞여 와도 *** 로 가림).
  - 429(한도)·5xx·시간 초과 → 다음 단계로, 그 단계는 state.json 에 '쉬는 시각'을 적어 둔다.
    제미나이 하루 한도는 태평양 시간 자정(한국 시각 오후 4~5시)에 풀리므로 그때까지 쉰다.
  - "private": true 인 일감은 외부 무료 등급(학습에 쓰일 수 있음)을 건너뛰고 로컬 Ollama → Claude 만.
  - Claude 단계는 api_worker.py 와 같은 budget.json 월 한도를 지킨다(한도 넘으면 건너뜀).
  - 모든 답은 '초안'이다. 사실 확인·최종 문구·게시는 하지 않는다(대표실 Claude가 검증).
대량 일괄(50% 할인 Batch)은 api_worker.py, 한 건씩·자동 전환은 이 파일.
표준 라이브러리만 사용(파이썬 3.10+).
"""
import json, os, re, socket, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT_NOTE = "초안 — 사실 확인은 Claude가 따로 한다"


# ───────── 설정·기록 파일 ─────────
def load_config(path=None):
    path = path or os.environ.get("AI_ROUTER_CONFIG") or os.path.join(HERE, "router_config.json")
    with open(path, encoding="utf-8") as f: cfg = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    for k in ("state_file", "budget_file", "results_dir"):
        v = cfg.get(k, {"state_file": "state.json", "budget_file": "budget.json", "results_dir": "results"}[k])
        cfg[k] = v if os.path.isabs(v) else os.path.join(base, v)
    return cfg


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError): return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def budget(path):  # api_worker.py 와 같은 규칙
    b = load_json(path, {"monthly_limit_usd": 90, "month": "", "spent_est_usd": 0})
    m = time.strftime("%Y-%m")
    if b.get("month") != m: b.update(month=m, spent_est_usd=0)
    return b


# ───────── 쉬는 시각 계산 ─────────
def next_pacific_midnight(now=None):
    now = now or datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        pt = ZoneInfo("America/Los_Angeles")
    except Exception:  # 윈도우에 시간대 자료가 없으면 겨울 기준(UTC-8)으로 — 최대 1시간 늦게 풀릴 뿐
        pt = timezone(timedelta(hours=-8))
    local = now.astimezone(pt)
    nxt = (local + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return nxt.astimezone(timezone.utc)


def cooldown_until(stage, kind, body=""):
    """kind: 'limit'(429) 또는 'error'(5xx·시간 초과). 돌려주는 값: UTC datetime"""
    now = datetime.now(timezone.utc)
    if kind == "limit":
        rule = stage.get("cooldown_429", 3600)
        if rule == "pacific_midnight":
            # 분당 한도라고 분명히 적혀 오면(retryDelay, 'PerDay' 없음) 그만큼만 쉼
            m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', body)
            if m and "PerDay" not in body:
                return now + timedelta(seconds=max(60, float(m.group(1))))
            return next_pacific_midnight(now)
        return now + timedelta(seconds=int(rule))
    return now + timedelta(seconds=int(stage.get("cooldown_error_sec", 3600)))


# ───────── 키 가리기 ─────────
def secrets(cfg):
    return [os.environ[s["key_env"]] for s in cfg["stages"] if s.get("key_env") and os.environ.get(s["key_env"])]


def redact(text, cfg):
    text = str(text)
    for k in secrets(cfg):
        if len(k) >= 6: text = text.replace(k, "***")
    return text[:300]


# ───────── HTTP ─────────
class StageFail(Exception):
    def __init__(self, outcome, detail="", body=""):
        super().__init__(detail); self.outcome, self.detail, self.body = outcome, detail, body


_LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_NET = urllib.request.build_opener()


def http_json(url, body, headers, timeout):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                               headers={"content-type": "application/json", **headers})
    host = urllib.parse.urlsplit(url).hostname or ""
    opener = _LOCAL if host in ("localhost", "127.0.0.1", "::1") else _NET  # 내 컴퓨터 주소는 프록시를 거치지 않음
    try:
        with opener.open(r, timeout=timeout) as f:
            return json.loads(f.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        if e.code == 429: raise StageFail("limit", "429 한도 초과", txt)
        if e.code >= 500: raise StageFail("error", f"{e.code} 서버 오류", txt)
        hint = {400: "요청 형식/모델 이름 확인", 401: "키 확인 필요", 402: "크레딧 부족",
                403: "권한·지역 제한", 404: "모델 이름·주소 확인"}.get(e.code, "")
        raise StageFail("rejected", f"{e.code} {hint}".strip(), txt)
    except (TimeoutError, socket.timeout):
        raise StageFail("timeout", "시간 초과")
    except urllib.error.URLError as e:
        if isinstance(e.reason, (TimeoutError, socket.timeout)): raise StageFail("timeout", "시간 초과")
        raise StageFail("offline", f"연결 안 됨({type(e.reason).__name__})")
    except ValueError:
        raise StageFail("empty", "응답이 JSON이 아님")


# ───────── 단계별 호출 ─────────
def call_gemini(st, key, system, prompt, max_tokens, timeout, cfg):
    url = st["url"].format(model=st["model"])
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {"maxOutputTokens": max_tokens}}
    res = http_json(url, body, {"x-goog-api-key": key}, timeout)  # 키는 주소가 아니라 머리글로
    parts = ((res.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def call_ollama(st, key, system, prompt, max_tokens, timeout, cfg):
    base = st["url"].rstrip("/")
    try:  # 설치·실행 여부와 모델 유무를 먼저 짧게 확인
        tags = http_json(base + "/api/tags", None, {}, 3)
    except StageFail as e:
        raise StageFail("offline" if e.outcome in ("offline", "timeout") else e.outcome,
                        "Ollama가 꺼져 있거나 설치 안 됨" if e.outcome in ("offline", "timeout") else e.detail, e.body)
    names = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
    want = st["model"]
    if want not in names and (want + ":latest") not in names:
        raise StageFail("skipped", f"모델 미설치 → 명령 창에서: ollama pull {want}")
    body = {"model": want, "stream": False, "options": {"num_predict": max_tokens},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    res = http_json(base + "/api/chat", body, {}, st.get("timeout_sec", timeout))
    return (res.get("message") or {}).get("content", "")


def call_openrouter(st, key, system, prompt, max_tokens, timeout, cfg):
    body = {"model": st["model"], "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    hdr = {"Authorization": "Bearer " + key, "X-Title": st.get("app_title", "AI Router")}
    res = http_json(st["url"], body, hdr, timeout)
    if res.get("error"):  # 200 안에 오류가 담겨 오는 경우
        code = int((res["error"] or {}).get("code") or 0)
        raise StageFail("limit" if code == 429 else "error" if code >= 500 else "rejected",
                        f"{code} {(res['error'] or {}).get('message', '')}", json.dumps(res))
    return ((res.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def call_claude(st, key, system, prompt, max_tokens, timeout, cfg):
    b = budget(cfg["budget_file"])
    if b.get("spent_est_usd", 0) >= b.get("monthly_limit_usd", 90):
        raise StageFail("skipped", f"이번 달 한도({b['monthly_limit_usd']}달러) 넘음 — budget.json")
    body = {"model": st["model"], "max_tokens": max_tokens, "system": system,
            "messages": [{"role": "user", "content": prompt}]}
    res = http_json(st["url"], body, {"x-api-key": key, "anthropic-version": "2023-06-01"}, timeout)
    u = res.get("usage") or {}
    b["tokens_in"] = b.get("tokens_in", 0) + u.get("input_tokens", 0)
    b["tokens_out"] = b.get("tokens_out", 0) + u.get("output_tokens", 0)
    b["router_calls"] = b.get("router_calls", 0) + 1
    save_json(cfg["budget_file"], b)
    return "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")


CALLERS = {"gemini": call_gemini, "ollama": call_ollama, "openrouter": call_openrouter, "claude": call_claude}


# ───────── 교환대 본체 ─────────
def route(prompt, private=False, system=None, max_tokens=None, cfg=None):
    cfg = cfg or load_config()
    system = system or cfg.get("default_system", "한국어로 짧게 답한다.")
    max_tokens = max_tokens or cfg.get("default_max_tokens", 800)
    timeout = cfg.get("timeout_sec", 60)
    state = load_json(cfg["state_file"], {"cooldown": {}})
    state.setdefault("cooldown", {})
    now = datetime.now(timezone.utc)
    tried = []
    for st in cfg["stages"]:
        name = st["name"]
        if not st.get("enabled", True):
            tried.append({"stage": name, "outcome": "skipped", "detail": "꺼 둠(enabled=false)"}); continue
        if private and st.get("external_free"):
            tried.append({"stage": name, "outcome": "skipped", "detail": "개인정보 작업 — 외부 무료 등급 건너뜀"}); continue
        until = state["cooldown"].get(name)
        if until and datetime.fromisoformat(until) > now:
            kst = datetime.fromisoformat(until).astimezone(timezone(timedelta(hours=9)))
            tried.append({"stage": name, "outcome": "resting", "detail": f"쉬는 중(한국 {kst:%m-%d %H:%M}까지)"}); continue
        key = None
        if st.get("key_env"):
            key = os.environ.get(st["key_env"])
            if not key:
                tried.append({"stage": name, "outcome": "skipped", "detail": f"키 없음({st['key_env']})"}); continue
        try:
            text = CALLERS[st["kind"]](st, key, system, prompt, max_tokens, timeout, cfg)
            if not (text or "").strip(): raise StageFail("empty", "빈 답")
        except StageFail as e:
            item = {"stage": name, "outcome": e.outcome, "detail": redact(e.detail, cfg)}
            if e.outcome in ("limit", "error", "timeout"):
                u = cooldown_until(st, "limit" if e.outcome == "limit" else "error", e.body)
                state["cooldown"][name] = u.isoformat(timespec="seconds")
                item["rest_until_utc"] = state["cooldown"][name]
            tried.append(item); continue
        except Exception as e:  # 예상 못 한 오류도 다음 단계로
            tried.append({"stage": name, "outcome": "error", "detail": redact(f"{type(e).__name__}: {e}", cfg)}); continue
        state["cooldown"].pop(name, None)
        save_json(cfg["state_file"], state)
        tried.append({"stage": name, "outcome": "ok"})
        return {"answer": text.strip(), "answered_by": f"{name}:{st['model']}", "draft": True,
                "note": DRAFT_NOTE, "private": bool(private), "tried": tried}
    save_json(cfg["state_file"], state)
    return {"answer": None, "answered_by": None, "draft": True, "private": bool(private), "tried": tried,
            "note": fail_message(tried, private)}


def fail_message(tried, private):
    lines = ["모든 AI가 답하지 못했습니다. 아래를 확인해 주세요."]
    for t in tried:
        lines.append(f" - {t['stage']}: {t['detail'] or t['outcome']}")
    lines.append("할 일: ① 키가 없으면 대표님이 발급해 환경 변수에 넣기(README 참고) "
                 "② Ollama는 노트북에서 프로그램을 켜 두기 ③ 쉬는 중이면 그 시각 뒤에 다시 실행")
    if private: lines.append("※ 개인정보 작업이라 외부 무료 AI는 일부러 쓰지 않았습니다.")
    return "\n".join(lines)


def run_file(path, cfg):
    with open(path, encoding="utf-8") as f: task = json.load(f)
    out = {}
    for j in task["jobs"]:
        r = route(j["prompt"], private=j.get("private", task.get("private", False)),
                  system=j.get("system", task.get("system")), max_tokens=j.get("max_tokens"), cfg=cfg)
        out[j["id"]] = r
        print(f"[{j['id']}] {'→ ' + r['answered_by'] if r['answered_by'] else '실패'}")
    os.makedirs(cfg["results_dir"], exist_ok=True)
    p = os.path.join(cfg["results_dir"], "router_" + time.strftime("%Y%m%d_%H%M%S") + ".json")
    save_json(p, out)
    ok = sum(1 for r in out.values() if r["answer"])
    print(f"저장: {p} · 성공 {ok}/{len(out)} (모두 '초안' — 사실 확인은 Claude가)")
    return 0 if ok == len(out) else 2


def main(argv):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    args = list(argv); cfgpath = None
    if "--config" in args:
        i = args.index("--config"); cfgpath = args[i + 1]; del args[i:i + 2]
    private = "--private" in args
    args = [a for a in args if a != "--private"]
    if not args:
        print(__doc__); return 1
    cfg = load_config(cfgpath)
    if args[0].lower().endswith(".json") and os.path.exists(args[0]):
        return run_file(args[0], cfg)
    r = route(" ".join(args), private=private, cfg=cfg)
    if r["answer"]:
        print(r["answer"]); print(f"\n— 답한 AI: {r['answered_by']} · {DRAFT_NOTE}"); return 0
    print(r["note"]); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
