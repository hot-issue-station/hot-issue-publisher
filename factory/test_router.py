"""ai_router.py 시험 — 인터넷·진짜 키 없이 localhost 가짜 서버로 4단계를 흉내 낸다
실행: python test_router.py
"""
import json, os, socket, subprocess, sys, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_router  # noqa: E402

FAKE = {"GEMINI_API_KEY": "fake-gemini-KEY-123456", "OPENROUTER_API_KEY": "fake-or-KEY-123456",
        "ANTHROPIC_API_KEY": "fake-claude-KEY-123456"}


class Fake(BaseHTTPRequestHandler):
    mode = {}   # 단계 이름 → "ok" | "429" | "500" | "slow" | "echo401"
    hits = []   # (단계, 경로, 머리글)

    def log_message(self, *a): pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def _common(self, stage):
        Fake.hits.append((stage, self.path, {k.lower(): v for k, v in self.headers.items()}))
        m = Fake.mode.get(stage, "ok")
        if m == "429":
            self._send(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": [{"violations": [
                {"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}}); return None
        if m == "500": self._send(500, {"error": "boom"}); return None
        if m == "slow": time.sleep(3); self._send(200, {}); return None
        if m == "echo401":  # 일부러 키를 그대로 돌려보내는 나쁜 서버
            self._send(401, {"error": "bad key " + self.headers.get("x-goog-api-key", "")}); return None
        return m

    def do_GET(self):
        if self.path.startswith("/ollama/api/tags"):
            if self._common("ollama_tags") is None: return
            self._send(200, {"models": [{"name": "exaone3.5:7.8b", "model": "exaone3.5:7.8b"}]})
        else: self._send(404, {})

    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); json.loads(self.rfile.read(n) or b"{}")
        p = self.path
        if p.startswith("/gemini/"):
            if self._common("gemini") is None: return
            self._send(200, {"candidates": [{"content": {"parts": [{"text": "제미나이 답"}]}}]})
        elif p.startswith("/ollama/api/chat"):
            if self._common("ollama") is None: return
            self._send(200, {"message": {"role": "assistant", "content": "올라마 답"}})
        elif p.startswith("/openrouter/"):
            if self._common("openrouter") is None: return
            self._send(200, {"choices": [{"message": {"content": "오픈라우터 답"}}]})
        elif p.startswith("/claude/"):
            if self._common("claude") is None: return
            self._send(200, {"content": [{"type": "text", "text": "클로드 답"}],
                             "usage": {"input_tokens": 10, "output_tokens": 5}})
        else: self._send(404, {})


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class RouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.dead = f"http://127.0.0.1:{free_port()}"   # 아무도 안 듣는 주소 = Ollama 미설치

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()

    def setUp(self):
        Fake.mode, Fake.hits = {}, []
        self.tmp = tempfile.mkdtemp()
        cfg = json.load(open(os.path.join(HERE, "router_config.json"), encoding="utf-8"))
        cfg.update(timeout_sec=1, state_file="state.json", budget_file="budget.json", results_dir="results")
        urls = {"gemini": self.base + "/gemini/v1beta/models/{model}:generateContent",
                "ollama": self.base + "/ollama", "openrouter": self.base + "/openrouter/chat/completions",
                "claude": self.base + "/claude/messages"}
        for st in cfg["stages"]: st["url"] = urls[st["name"]]
        self.cfgpath = os.path.join(self.tmp, "router_config.json")
        json.dump(cfg, open(self.cfgpath, "w", encoding="utf-8"), ensure_ascii=False)
        self.saved_env = {k: os.environ.get(k) for k in FAKE}
        os.environ.update(FAKE)

    def tearDown(self):
        for k, v in self.saved_env.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v

    def cfg(self, **stage_urls):
        c = ai_router.load_config(self.cfgpath)
        for st in c["stages"]:
            if st["name"] in stage_urls: st["url"] = stage_urls[st["name"]]
        return c

    def stages_hit(self): return [h[0] for h in Fake.hits]

    # ① 1단계 429 → 2단계로, 제미나이는 쉬는 시각 기록 → 다음 호출에선 제미나이를 아예 안 부름
    def test_1_gemini_429_falls_to_ollama(self):
        Fake.mode = {"gemini": "429"}
        c = self.cfg()
        r = ai_router.route("번역해 줘: hello", cfg=c)
        self.assertEqual(r["answered_by"], "ollama:exaone3.5:7.8b")
        self.assertEqual(r["answer"], "올라마 답")
        self.assertTrue(r["draft"]); self.assertIn("초안", r["note"])
        self.assertEqual(r["tried"][0]["outcome"], "limit")
        st = json.load(open(c["state_file"], encoding="utf-8"))
        until = ai_router.datetime.fromisoformat(st["cooldown"]["gemini"])
        self.assertEqual(until, ai_router.next_pacific_midnight())
        Fake.hits = []
        r2 = ai_router.route("또 번역", cfg=c)
        self.assertNotIn("gemini", self.stages_hit())
        self.assertEqual(r2["tried"][0]["outcome"], "resting")
        # 키는 머리글로만, 주소(URL)에는 없음
        Fake.mode, Fake.hits = {}, []
        os.remove(c["state_file"])
        r3 = ai_router.route("키 확인", cfg=c)
        self.assertEqual(r3["answered_by"], "gemini:gemini-3.1-flash-lite")
        g = [h for h in Fake.hits if h[0] == "gemini"][0]
        self.assertNotIn(FAKE["GEMINI_API_KEY"], g[1])
        self.assertEqual(g[2].get("x-goog-api-key"), FAKE["GEMINI_API_KEY"])

    # ② private → 제미나이·OpenRouter는 한 번도 안 불림
    def test_2_private_skips_external(self):
        r = ai_router.route("고객 전화번호 정리", private=True, cfg=self.cfg())
        self.assertEqual(r["answered_by"], "ollama:exaone3.5:7.8b")
        self.assertNotIn("gemini", self.stages_hit()); self.assertNotIn("openrouter", self.stages_hit())
        Fake.hits = []
        r = ai_router.route("고객 전화번호 정리", private=True, cfg=self.cfg(ollama=self.dead))  # 노트북 꺼짐
        self.assertEqual(r["answered_by"], "claude:claude-haiku-5-5")
        self.assertEqual(self.stages_hit(), ["claude"])

    # ③ 키 없음 → 그 단계 건너뜀
    def test_3_missing_keys_skipped(self):
        for k in FAKE: os.environ.pop(k)
        r = ai_router.route("요약", cfg=self.cfg(ollama=self.dead))
        self.assertIsNone(r["answer"])
        self.assertEqual(self.stages_hit(), [])
        details = {t["stage"]: t["detail"] for t in r["tried"]}
        self.assertIn("키 없음(GEMINI_API_KEY)", details["gemini"])
        self.assertIn("키 없음(OPENROUTER_API_KEY)", details["openrouter"])
        self.assertIn("키 없음(ANTHROPIC_API_KEY)", details["claude"])
        os.environ["OPENROUTER_API_KEY"] = FAKE["OPENROUTER_API_KEY"]
        r = ai_router.route("요약", cfg=self.cfg(ollama=self.dead))
        self.assertEqual(r["answered_by"], "openrouter:thinkingmachines/inkling-2-small:free")

    # ④ 전부 실패 → 한국어 안내 (5xx·꺼짐·시간 초과·429 섞어서), CLI는 종료 코드 2
    def test_4_all_fail_korean_message(self):
        Fake.mode = {"gemini": "500", "openrouter": "slow", "claude": "429"}
        c = self.cfg(ollama=self.dead)
        r = ai_router.route("자막 초안", cfg=c)
        self.assertIsNone(r["answer"])
        self.assertEqual([t["outcome"] for t in r["tried"]], ["error", "offline", "timeout", "limit"])
        self.assertIn("모든 AI가 답하지 못했습니다", r["note"])
        st = json.load(open(c["state_file"], encoding="utf-8"))
        self.assertEqual(set(st["cooldown"]), {"gemini", "openrouter", "claude"})
        # CLI 로도 확인
        os.remove(c["state_file"])
        cfg2 = json.load(open(self.cfgpath, encoding="utf-8"))
        for s in cfg2["stages"]:
            if s["name"] == "ollama": s["url"] = self.dead
        json.dump(cfg2, open(self.cfgpath, "w", encoding="utf-8"), ensure_ascii=False)
        p = subprocess.run([sys.executable, os.path.join(HERE, "ai_router.py"), "자막 초안", "--config", self.cfgpath],
                           capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(p.returncode, 2)
        self.assertIn("모든 AI가 답하지 못했습니다", p.stdout)
        self.assertIn("할 일", p.stdout)
        print("\n[④ CLI 출력]\n" + p.stdout)

    # 덤: 키가 오류 문장에 섞여 와도 결과·state.json 에 남지 않음 / 월 한도 넘으면 Claude 건너뜀 / 일감 파일
    def test_5_key_redaction_budget_jobfile(self):
        Fake.mode = {"gemini": "echo401"}
        c = self.cfg(ollama=self.dead)
        r = ai_router.route("x", cfg=c)
        dump = json.dumps(r, ensure_ascii=False) + open(c["state_file"], encoding="utf-8").read()
        for k in FAKE.values(): self.assertNotIn(k, dump)
        self.assertIn("401", r["tried"][0]["detail"])
        json.dump({"monthly_limit_usd": 20, "month": time.strftime("%Y-%m"), "spent_est_usd": 25},
                  open(c["budget_file"], "w"))
        Fake.mode, Fake.hits = {"gemini": "500", "openrouter": "500"}, []
        os.remove(c["state_file"])
        r = ai_router.route("x", cfg=c)
        self.assertNotIn("claude", self.stages_hit())
        self.assertIn("한도", r["tried"][-1]["detail"])
        # 일감 파일: 공개 1건 + private 1건
        os.remove(c["budget_file"]); os.remove(c["state_file"]); Fake.mode = {}
        job = os.path.join(self.tmp, "일감.json")
        json.dump({"jobs": [{"id": "a", "prompt": "요약"}, {"id": "b", "prompt": "고객 메모", "private": True}]},
                  open(job, "w", encoding="utf-8"), ensure_ascii=False)
        code = ai_router.run_file(job, c)
        self.assertEqual(code, 0)
        f = os.listdir(c["results_dir"])[0]
        res = json.load(open(os.path.join(c["results_dir"], f), encoding="utf-8"))
        self.assertEqual(res["a"]["answered_by"], "gemini:gemini-3.1-flash-lite")
        self.assertEqual(res["b"]["answered_by"], "claude:claude-haiku-5-5")
        b = json.load(open(c["budget_file"], encoding="utf-8"))
        self.assertEqual((b["tokens_in"], b["tokens_out"], b["router_calls"]), (10, 5, 1))


if __name__ == "__main__":
    import warnings; warnings.simplefilter("ignore", ResourceWarning)
    unittest.main(verbosity=2, warnings="ignore")
