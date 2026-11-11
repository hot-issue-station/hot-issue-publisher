# 덕심저장소 공장 (쇼츠·롱폼)
반복 작업은 프로그램이 하고, Claude는 **기획 파일(JSON) 하나만** 쓴다 → 대화·사용량이 크게 준다.

| 프로그램 | 넣는 것 | 나오는 것 |
|---|---|---|
| `shorts_factory.py 기획.json` | 틀(rank 순위표 / cards 문장 카드), 배경 사진, 내용 | 쇼츠 영상(5곳 공용) · 썸네일(11/10 표준) · 게시 문구 · 5줄 점검표 |
| `longform_factory.py 롱폼.json` | 챕터·장면(파일·시작·끝)·자막·댓글 | 롱폼 영상 · 썸네일 · 자막(.srt) · 점검표 |

자동으로 항상 들어가는 것: 끝 화면(구독·좋아요·알림), 배경음악, 출처 줄, 썸네일 표준.
점검표에 ❌가 하나라도 있으면 올리지 않는다.

예시: `samples/` 폴더. 배경 사진은 저작권 문제로 저장소에 올리지 않음(대표 사진을 `assets/`에 넣어 쓰기).
윈도우에서 쓰려면 `fonts/` 폴더에 Noto Sans CJK(Bold·Medium·Black .ttc)를 넣는다.

## AI 일꾼 두 가지 (Claude 사용량 아끼기)
| 프로그램 | 언제 | 쓰는 AI |
|---|---|---|
| `api_worker.py 일감.json` | **대량 일괄** (수십~수백 건, 1시간 안에 받아도 될 때, 50% 할인) | Claude Haiku Batch |
| `ai_router.py "프롬프트"` / `ai_router.py 일감.json` | **한 건씩·자동 전환** (무료부터 차례로) | 제미나이 무료 → Ollama(노트북) → OpenRouter `:free` → Claude Haiku |

- 순서·모델 이름은 `router_config.json` 에서 바꾼다. 한도(429)·서버 오류·시간 초과가 나면 다음 AI로 넘어가고, 그 AI는 `state.json` 에 적힌 시각까지 쉰다(제미나이는 하루 한도가 풀리는 태평양 자정 = 한국 오후 4~5시).
- 개인정보가 든 일(미용실 고객 메모 등)은 `--private` 또는 일감에 `"private": true` → 외부 무료 AI(학습에 쓰일 수 있음)는 건너뛰고 노트북 Ollama → Claude 만 쓴다.
- 답에는 `answered_by`(누가 답했는지)와 "초안" 표시가 붙는다. 사실 확인·최종 문구·게시는 Claude가 따로 한다.
- Claude 단계는 `budget.json` 월 한도를 api_worker와 함께 쓴다.
- 시험: `python test_router.py` (인터넷·키 없이 가짜 서버로 확인).

### 대표님이 할 일 — 키 발급 (직접, 무료)
키는 Claude가 대신 넣지 않는다. 발급한 키는 **윈도우 검색 → "시스템 환경 변수 편집" → 환경 변수 → 새로 만들기** 에 이름과 값을 넣는다(채팅창에 붙여 넣지 않기).
1. **제미나이**: Google AI Studio(aistudio.google.com) 로그인 → 왼쪽 **Get API key** → **Create API key** → 이름 `GEMINI_API_KEY` 로 저장. 결제 등록은 하지 않는다(무료 등급 유지).
2. **OpenRouter**: openrouter.ai 가입 → 오른쪽 위 메뉴 **Keys** → **Create Key** → 이름 `OPENROUTER_API_KEY`. 크레딧 구매 없이 `:free` 모델만 쓴다(하루 50회 한도).
3. Claude 키 `ANTHROPIC_API_KEY` 는 api_worker 때 넣은 것을 그대로 쓴다.
※ 무료 계정 여러 개를 돌려쓰는 방식은 약관 위반이라 넣지 않았다. 출처 모를 깃허브 "라우터"도 설치하지 않는다(키 유출 위험).

### 대표님이 할 일 — Ollama 설치 (퇴근 후 게이밍 노트북, 클릭 위주)
1. ollama.com 접속 → **Download** → **Windows** → 받은 `OllamaSetup.exe` 더블클릭 → **Install**. 끝나면 오른쪽 아래 알림 영역에 라마 아이콘이 뜬다(켜져 있어야 교환대가 씀).
2. Ollama 앱 창의 모델 고르는 칸에 `exaone3.5:7.8b` 를 넣고 아무 말이나 한 번 보내면 자동으로 받는다(4.8GB, 한 번만).
3. 권장 모델(그래픽 메모리 8GB 기준)
   - `exaone3.5:7.8b` (4.8GB) — LG AI연구원, 영어·한국어 2개 언어 모델로 소개됨. **기본값**
   - `qwen3.5:4b` (3.3~4.0GB) — 201개 언어 지원, 더 가볍고 빠름. 바꾸려면 `router_config.json` 의 ollama `model` 만 고친다.
4. 상업용으로 쓰기 전 각 모델 라이선스는 모델 페이지의 링크에서 한 번 확인.
