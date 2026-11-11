# GitHub 오픈소스 조사 — 우리 시스템 효율화·Claude 사용량 줄이기 (2026-11-11)

## 0. 조사 방법과 한계
- 별 수·마지막 커밋(push) 날짜·라이선스: **GitHub 공식 API(저장소 검색)로 2026-11-11에 직접 조회**한 값이다. 이 환경에서는 github.com 페이지를 curl로 열 수 없어 API로 저장소 정보를 받았다.
- 기능·라이선스 세부 조건·윈도우 지원: 아래 「README 확인」 표시가 있는 저장소만 **저장소 페이지를 직접 열어** 확인했다. 표시가 없는 칸은 API 값만 확인한 것이다.
- 설치·실행은 하지 않았다(조사만). 설치 난이도는 README 기준 추정이다.
- 라이선스 "NOASSERTION" = GitHub가 표준 라이선스로 판별하지 못함(자체 라이선스·혼합). 반드시 원문 확인이 필요하다.
- 우리 시스템 확인 결과(파일 직접 읽음): `ai_router.py`(표준 라이브러리 285줄, 제미나이 → Ollama → OpenRouter :free → Claude Haiku 순서, 429 시 쉬는 시각 기록, 개인정보 일감은 외부 무료 단계 건너뜀, budget.json 월 한도). `router_config.json`의 Ollama 모델은 **`exaone3.5:7.8b`**. 롱폼 자막(.srt)은 기획 JSON의 자막 시각을 그대로 쓰는 방식(음성 인식 없음). 업로더는 Playwright로 크롬을 조작하고 최종 예약 단추 앞에서 멈춘다.

> **바로 알릴 위험 1건**: 지금 Ollama 단계 모델인 EXAONE은 저장소에 「EXAONE AI Model License Agreement 1.2 - NC」로 적혀 있다(README 확인). NC는 보통 비상업이라는 뜻이다. 수익화 채널 작업에 쓰면 라이선스 위반 소지가 있으므로 Apache-2.0 모델(Qwen3·Gemma 등)로 바꾸기를 권한다.

---

## 1) 무료 AI 자동 전환 라우터/프록시

| 저장소 | 별 | 마지막 커밋 | 라이선스(상업) | 윈도우 설치 | 붙일 곳 | 사용량 절감 | 위험 |
|---|---|---|---|---|---|---|---|
| [BerriAI/litellm](https://github.com/BerriAI/litellm) (README·LICENSE 확인) | 63,089 | 2026-11-11 | MIT(단 `enterprise/` 폴더만 별도) → 상업 가능 | 중 (`uv add litellm`, 프록시는 `litellm[proxy]`) | ai_router.py 대체 후보 | 중간 | 의존성 많음, 업데이트 잦음 |
| [QuantumNous/new-api](https://github.com/QuantumNous/new-api) | 51,738 | 2026-11-11 | AGPL-3.0 (자체 사용은 가능, 고쳐서 남에게 서비스하면 소스 공개 의무) | 중~상 (서버형, 도커 권장) | 여러 키를 한곳에서 관리하는 게이트웨이 | 작다 | 서버 상시 실행 필요 |
| [Portkey-AI/gateway](https://github.com/Portkey-AI/gateway) | 13,365 | 2026-05-25 | MIT | 중 | 동일 | 작다 | 최근 커밋 6개월 직전, 활동 둔화 |
| (참고) songquanpeng/one-api | 37,402 | 2026-01-09 | MIT | 중 | — | 작다 | 10개월째 커밋 없음 → 제외 |
| (참고) katanemo/plano | 7,114 | 2026-10-24 | Apache-2.0 | 상 | — | 작다 | 에이전트 앱용, 과함 |

**판단: ai_router.py는 대체하지 않는다.** LiteLLM에도 재시도·대체(fallback) 라우터가 있고 Gemini·OpenRouter·Ollama를 모두 지원한다(README 확인). 그러나 우리 파일은 이미 (1) 429 시 태평양 자정까지 쉬기, (2) 개인정보 일감은 외부 무료 AI 건너뛰기, (3) Claude 월 한도 공유를 하고 있고 표준 라이브러리만 쓴다. LiteLLM으로 바꾸면 이 규칙을 다시 짜야 하고 설치 부담만 늘어난다. 나중에 무료 AI 제공처가 5곳 이상으로 늘면 그때 LiteLLM 파이썬 라이브러리(서버 아님)만 안쪽 호출부에 쓰는 정도를 검토한다.

## 2) 로컬 LLM 실행 + 한국어 모델

| 저장소 | 별 | 마지막 커밋 | 라이선스(상업) | 윈도우 설치 | 붙일 곳 | 절감 | 위험 |
|---|---|---|---|---|---|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) (README 확인) | 186,614 | 2026-11-11 | MIT | **하** (OllamaSetup.exe 설치 파일) | ai_router 2단계(이미 연결됨) | 크다 | 없음 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 134,020 | 2026-11-11 | MIT | 중 | Ollama 대체(필요 없음) | — | — |

한국어 모델(모델 저장소 기준):

| 저장소 | 별 | 마지막 커밋 | 라이선스(상업) | 비고 |
|---|---|---|---|---|
| [QwenLM/Qwen3](https://github.com/QwenLM/Qwen3) (README 확인) | 27,722 | 2026-01-09 | README에 "모든 공개 모델 Apache 2.0" → 상업 가능 | 0.6B~32B, 100개 이상 언어, `ollama run qwen3:8b` 안내 있음. 게이밍 노트북엔 4B·8B 권장 |
| [google-deepmind/gemma](https://github.com/google-deepmind/gemma) | 5,838 | 2026-10-28 | 저장소 코드는 Apache-2.0 (모델 가중치 조건은 미확인 → 질문 목록) | Ollama README 예시가 `gemma4` |
| [kakao/kanana](https://github.com/kakao/kanana) (README 확인) | 286 | 2025-07-23 | README에 Kanana-1.5-8B·2.1B가 Apache 2.0 표시. 나머지 미표시 | 한국어 특화(KMMLU 등 표 있음). Ollama·GGUF 언급 없음 → 직접 변환 필요, 난이도 상 |
| [LG-AI-EXAONE/EXAONE-4.0](https://github.com/LG-AI-EXAONE/EXAONE-4.0) (README 확인) | 107 | 2025-08-04 | **"License 1.2 - NC"** → 상업 위험 | llama.cpp 공식 지원. 우리 채널엔 쓰지 말 것 |

## 3) 영상 자동 편집·자막

| 저장소 | 별 | 마지막 커밋 | 라이선스 | 윈도우 설치 | 붙일 곳 | 절감 | 위험 |
|---|---|---|---|---|---|---|---|
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 26,659 | 2026-11-10 | MIT | 하~중 (pip, 노트북 GPU면 빠름) | shorts/longform 자막 시각 자동 생성 → .srt | **크다** | 없음 |
| [Softcatala/whisper-ctranslate2](https://github.com/Softcatala/whisper-ctranslate2) | 1,372 | 2026-10-05 | MIT | 하 (faster-whisper를 명령 하나로) | 위와 같음(.bat 더블클릭용으로 감싸기 쉬움) | 크다 | 없음 |
| [m-bain/whisperX](https://github.com/m-bain/whisperX) (README 확인) | 25,210 | 2026-10-22 | BSD-2 | 중 (윈도우는 CUDA 12.8 먼저, 8GB 미만 VRAM) | 단어 단위 자막(가라오케식 강조) | 중간 | 한국어 정렬 모델 기본 목록에 없음(미확인), 화자 구분은 HF 토큰 필요 |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) (README 확인) | 5,845 | 2026-11-10 | Unlicense(퍼블릭 도메인) | 하~중 | 롱폼·몰아보기 전처리: 무음 구간 자동 컷, 움직임 기준 컷, 프리미어·다빈치·샷컷 타임라인 출력 | 중간 | 없음 |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 5,429 | 2026-11-10 | BSD-3 | 하 (pip) | stagemix_factory: 무대 영상 장면 경계 자동 찾기 → 컷 후보 목록 | 크다(구간 고르기 수작업 감소) | 없음 |
| [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) (README 확인) | 5,932 | 2026-11-10 | MIT | 중 (윈도우 안내 없음, 유닉스식 명령) | 롱폼 → 쇼츠: LLM 하이라이트 점수 + OpenCV 얼굴 추적 세로 자르기 | 중간 | 기본 모드는 유료 MuAPI. 로컬 모드는 faster-whisper + OpenAI/Gemini 키 필요(Gemini 무료 등급으로 가능한지 미확인). 자막 기능 언급 없음 |
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 142,122 | 2026-11-11 | MIT | 중 | 주제 → 대본·스톡영상·자막 자동 쇼츠(참고용) | 작다 | 스톡 영상 위주라 덕심저장소 톤과 안 맞음 |
| (참고) ClipsAI/clipsai | 565 | 2024-01-17 | MIT | — | — | — | 2년 가까이 멈춤 → 제외 |
| (참고) mli/autocut | 7,846 | 2024-10-05 | Apache-2.0 | — | — | — | 1년 넘게 멈춤 → 제외 |

## 4) 한국어 TTS (무료·상업 이용)

| 저장소 | 별 | 마지막 커밋 | 라이선스(상업) | 윈도우 | 한국어 | 비고·위험 |
|---|---|---|---|---|---|---|
| [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS) (README 확인) | 7,710 | 2024-12-24 | MIT, README에 "상업·비상업 모두 무료" | 중 | **지원** | CPU 실시간 가능. 커밋 약 2년 멈춤(유지보수 끊김 위험), 기능은 완성형 |
| [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) (README 확인) | 27,757 | 2026-11-04 | MIT | 중 | **지원**(다국어 23개 중 ko) | 모든 결과물에 보이지 않는 워터마크(Perth) 삽입. 목소리 복제 기능 → 실존 인물 목소리 금지 규칙 필요 |
| [QwenAudio/CosyVoice](https://github.com/QwenAudio/CosyVoice) (README 확인) | 24,363 | 2026-05-25 | 코드 Apache-2.0, **모델 가중치 라이선스 미표시** | 상 (리눅스 기준 안내, 윈도우판은 별도 포크 v3ucn/CosyVoice_For_Windows 758별) | 지원(3.0, 9개 언어) | 엔비디아 GPU 필요 추정 |
| (주의) [rany2/edge-tts](https://github.com/rany2/edge-tts) (README 확인) | 12,514 | 2026-10-14 | 저장소 LICENSE·GPL 파일 있음(판별 불가) | 하 | 미확인(README 목록이 잘림) | 마이크로소프트 엣지 온라인 서비스를 공식 API 없이 사용 → **약관 위반 위험**. 상업 채널엔 비권장 |
| (주의) fishaudio/fish-speech | 33,672 | 2026-11-11 | NOASSERTION(자체 라이선스) | — | 미확인 | 상업 조건 확인 전 사용 금지 |
| (주의) index-tts/index-tts | 25,039 | 2026-09-29 | NOASSERTION | — | 미확인 | 동일 |
| (참고) coqui-ai/TTS | 46,213 | 2024-08-16 | 코드 MPL-2.0 | — | — | 본가 개발 중단. XTTS 가중치 조건은 미확인 |
| (참고) rhasspy/piper → OHF-Voice/piper1-gpl | 11,322 / 6,239 | 보관됨 / 2026-11-09 | MIT → **GPL-3.0**로 이전 | — | 미확인 | 원 저장소 보관(archived) |

## 5) SNS 예약 업로드 자동화

| 저장소 | 별 | 마지막 커밋 | 라이선스 | 윈도우 | 방식 | 위험 |
|---|---|---|---|---|---|---|
| [porjo/youtubeuploader](https://github.com/porjo/youtubeuploader) (README 확인) | 894 | 2026-08-07 | Apache-2.0 | **하** (윈도우 실행 파일 배포) | **유튜브 공식 Data API v3**. `publishAt` 예약·썸네일·메타 JSON 지원 | README: 기본 할당량으로 **하루 약 6개**, 2020-07-28 이후 만든 **미인증 프로젝트로 올린 영상은 비공개로 제한**(구글 심사 필요). 약관 위험은 없음 |
| [gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) (README 확인) | 41,317 | 2026-11-11 | AGPL-3.0, 자체 호스팅 무료 | 상 (도커 + Postgres + Redis) | 공식 OAuth 방식. 인스타·유튜브·틱톡·스레드·X 등 14곳 | 플랫폼별 개발자 앱 심사 수 주. 서버 상시 실행 필요 |
| [inovector/mixpost](https://github.com/inovector/mixpost) | 3,926 | 2026-03-16 | MIT | 상 (PHP 서버) | 공식 API 기반 예약 | 커밋 8개월 전 |
| (위험) [subzeroid/instagrapi](https://github.com/subzeroid/instagrapi) (README 확인) | 7,121 | 2026-11-10 | API상 NOASSERTION, README는 MIT | 하 | **인스타 비공개(private) API** — README가 "불안정, 업무용이면 공식 API 권장"이라고 직접 경고 | **약관 위반·계정 정지 위험 큼 → 쓰지 않음** |
| (위험) makiisthenes/TiktokAutoUploader | 1,225 | 2026-11-05 | AGPL-3.0 | — | 요청 위조 방식(셀레니움 아님) | **약관 위반 위험 → 쓰지 않음** |
| (위험) wkaisertexas/tiktok-uploader | 786 | 2026-02-12 | MIT | — | 브라우저 자동화 | 약관 위험, 커밋 9개월 전 |
| (참고) tokland/youtube-upload | 2,189 | 2024-04-25 | 없음 | — | — | 멈춤 → 제외 |

**판단**: 지금 크롬 업로더(확정 단추 전 멈춤)는 그대로 둔다. 유튜브만 공식 API로 옮기고 싶으면 youtubeuploader가 가장 쉽지만, 구글 프로젝트 인증 전에는 영상이 비공개로 묶이고 하루 약 6개 한도가 있어 하루 3회 발행에는 빠듯하다. 인스타·틱톡 비공식 라이브러리는 금지.

## 6) 워크플로 자동화 (셀프호스팅)

| 저장소 | 별 | 마지막 커밋 | 라이선스(상업 조건) | 윈도우 | 붙일 곳 | 절감 | 위험 |
|---|---|---|---|---|---|---|---|
| [n8n-io/n8n](https://github.com/n8n-io/n8n) (README·LICENSE 확인) | 210,090 | 2026-11-11 | Sustainable Use License: **자기 회사 내부 업무·개인 용도는 가능**, 남에게 배포는 무료·비상업일 때만 → 우리 채널 운영 자동화는 가능, 미용실 앱에 넣어 팔면 불가 | 중~상 (README는 도커만 안내) | make_today.py 앞뒤 알림·예약 실행 | 중간 | 미용실 앱(판매)에 섞지 말 것 |
| [activepieces/activepieces](https://github.com/activepieces/activepieces) (README 확인) | 25,473 | 2026-11-11 | 커뮤니티판 MIT(`packages/ee`만 상용 라이선스) → 상업 가능 | 상 (도커 compose) | 동일, MCP 서버 다수 | 중간 | 윈도우 안내 없음 |
| [node-red/node-red](https://github.com/node-red/node-red) | 23,833 | 2026-11-09 | Apache-2.0 | 하~중 (Node.js) | 가벼운 예약·알림 흐름 | 작다 | 없음 |
| (참고) huginn/huginn | 50,496 | 2026-11-09 | MIT | 상 (루비) | — | 작다 | 윈도우 부적합 |
| (참고) windmill-labs/windmill | 18,520 | 2026-11-11 | NOASSERTION | 상 | — | — | 조건 확인 필요 |

**판단**: 지금 단계에서는 붙이지 않는다. make_today.py + 윈도우 작업 스케줄러(윈도우 기본 기능, 추가 설치 없음)로 충분하고, 도커를 데스크톱에 상시 띄우는 부담이 효과보다 크다. 꼭 필요하면 Node-RED(가장 가볍고 Apache-2.0).

## 7) 헤어스타일 변경·세그멘테이션 (salon/ PWA, 게이밍 노트북)

| 저장소 | 별 | 마지막 커밋 | 라이선스 | 윈도우 | 붙일 곳 | 위험 |
|---|---|---|---|---|---|---|
| [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe) | 37,645 | 2026-11-11 | Apache-2.0 | 하 (브라우저에서 바로, 설치 없음 추정) | salon PWA: 휴대폰 카메라 사진에서 머리카락 영역 분리 → 색 바꾸기 미리보기 | 「머리카락 분리 모델」 제공 여부와 웹 사용법은 이번에 저장소 페이지로 확인 못 함 → 질문 목록 |
| [FusionBrainLab/HairFastGAN](https://github.com/FusionBrainLab/HairFastGAN) (README 확인) | 446 | 2025-03-07 | MIT | 상 (리눅스만 안내, 엔비디아 GPU+CUDA) | 노트북에서 "얼굴 + 원하는 머리 모양 + 원하는 색" 3장으로 합성(V100 기준 1초 미만). Colab·HF 데모 있음 | 커밋 8개월 전. 손님 얼굴 사진 = 개인정보 → 동의·로컬 처리 필수 |
| [Xiaojiu-z/Stable-Hair](https://github.com/Xiaojiu-z/Stable-Hair) | 538 | 2025-03-14 | Apache-2.0 | 상 (확산 모델, VRAM 많이 필요 추정) | 더 사실적인 머리 이식 | 무겁고 커밋 8개월 전 |
| [zllrunning/face-parsing.PyTorch](https://github.com/zllrunning/face-parsing.PyTorch) | 2,592 | 2023-05-21 | MIT | 중 | 얼굴·머리 영역 분리(가벼움) | 3년 멈춤. 모델 가중치 학습 데이터(CelebAMask-HQ) 상업 조건 미확인 |

**판단**: 1단계는 MediaPipe로 "머리 색 미리보기"(휴대폰 안에서 처리, 비용 0원, 사진 서버 전송 없음). 머리 모양 바꾸기는 HairFastGAN을 노트북에서 시험하는 2단계(미용실 영업 데모용).

## 8) three.js 3D 웹 갤러리 (gallery/hall.html)

| 저장소 | 별 | 마지막 커밋 | 라이선스 | 붙일 곳 | 효과 |
|---|---|---|---|---|---|
| [pmndrs/detect-gpu](https://github.com/pmndrs/detect-gpu) | 1,223 | 2026-11-08 | MIT | 접속 기기 GPU 등급 판별 → 저사양 휴대폰은 그림자·해상도 낮추기 | 모바일 끊김 감소 |
| [donmccurdy/glTF-Transform](https://github.com/donmccurdy/glTF-Transform) | 2,070 | 2026-10-20 | MIT | 3D 모델·텍스처 압축(빌드 때 한 번) | 로딩 시간 감소 |
| [gkjohnson/three-mesh-bvh](https://github.com/gkjohnson/three-mesh-bvh) | 3,565 | 2026-11-11 | MIT | 액자 클릭·벽 충돌 판정 빠르게 | 터치 반응 개선 |
| [google/draco](https://github.com/google/draco) | 7,548 | 2026-11-11 | Apache-2.0 | glTF-Transform과 함께 메시 압축 | 용량 감소 |
| (참고) mrdoob/three.js | 118,116 | 2026-11-10 | MIT | 본체 | — |
| (참고) pmndrs/drei | 10,142 | 2026-10-21 | MIT | React 전용 → 우리(순수 three.js)엔 해당 없음 | — |
| (참고) sparkjsdev/spark | 3,898 | 2026-10-20 | MIT | 실사 3D 스캔(가우시안 스플랫) 전시 | 무거움, 나중에 |

Claude 사용량 절감은 모두 "작다"(성능 개선용). 설치 난이도 하(CDN 스크립트 한 줄 또는 빌드 때 한 번).

---

## 지금 바로 붙일 것 TOP 5 (효과 큰 순 = 붙이는 순서)

| 순서 | 도구 | 붙일 곳 | 무엇이 줄어드나 | Claude 절감 | 대표가 할 일 |
|---|---|---|---|---|---|
| 1 | **faster-whisper** (+ whisper-ctranslate2) | shorts_factory·longform_factory 자막 단계 | Claude가 자막 시각·문장을 일일이 적던 일 → 음성에서 .srt 초안 자동 생성, Claude는 틀린 글자만 고침 | 크다 | 게이밍 노트북에서 Claude가 만든 설치용 .bat 파일 한 번 더블클릭(파이썬 설치는 이미 있음 가정) |
| 2 | **Ollama 모델 교체: EXAONE → Qwen3 8B(또는 4B)** | router_config.json의 ollama 단계 | 라이선스 위험(NC) 제거 + 번역·요약·댓글 분류 초안을 무료 로컬로 | 크다 | 노트북에서 .bat 더블클릭으로 모델 받기(용량 수 GB, 1회). 교체 후 test_router.py로 확인은 Claude가 |
| 3 | **PySceneDetect** | stagemix_factory.py 앞단 | 무대 영상의 장면 바뀌는 시각 목록 자동 생성 → Claude가 영상 보며 구간 고르던 수고 감소 | 크다 | 없음(공장 설치 스크립트에 함께 포함) |
| 4 | **auto-editor** | longform_factory·몰아보기 전처리 | 무음·정지 구간 자동 컷, 다빈치/프리미어 타임라인 출력 | 중간 | 결과 타임라인을 한 번 훑어보고 OK |
| 5 | **AI-Youtube-Shorts-Generator 로컬 모드 (코드 참고·일부 이식)** | 롱폼 → 쇼츠 자르기(얼굴 추적 세로 재구성) | 쇼츠용 구간 찾기·세로 크롭 좌표 계산 자동화. LLM 단계는 ai_router(제미나이 무료)로 연결 | 중간 | 없음. 유료 MuAPI 모드는 쓰지 않음 |

붙이지 않기로 한 것: ai_router 대체(LiteLLM 등 — 지금 파일이 우리 규칙에 더 맞음), n8n·Postiz(도커 서버 상시 실행 부담), instagrapi·틱톡 비공식 업로더(약관 위반), edge-tts(비공식 서비스 사용), EXAONE(비상업 라이선스).

다음 후보(TOP 5 다음): MeloTTS 한국어 내레이션(MIT, CPU), MediaPipe 머리 색 미리보기(salon), detect-gpu + glTF-Transform(갤러리 모바일 최적화), youtubeuploader(구글 앱 인증 받은 뒤).

---

## 퍼플렉시티 질문 목록 (이번에 확인 못 한 것)
1. Qwen3(또는 최신 Qwen3.x) 4B·8B 중 한국어 요약·번역 품질과 RTX 노트북(VRAM 6~8GB)에서의 속도는? Ollama 태그 이름은?
2. Gemma 3/4 모델 가중치의 「Gemma 이용 약관」이 유튜브 수익화 채널 콘텐츠 제작에 상업 이용을 허용하는가?
3. Kakao Kanana-1.5-8B / 2.1B의 Hugging Face 라이선스가 Apache 2.0이 맞는가? Ollama용 GGUF 파일이 있는가?
4. WhisperX의 한국어 단어 정렬(wav2vec2) 기본 모델이 있는가? faster-whisper large-v3 한국어 정확도는?
5. MediaPipe Tasks(웹, `@mediapipe/tasks-vision`)에 머리카락 분리(hair segmenter) 모델이 있는가? 휴대폰 브라우저에서 실시간 동작하는가? 라이선스는?
6. HairFastGAN을 윈도우 + RTX 노트북(VRAM 8GB)에서 돌린 사례가 있는가? 필요한 VRAM은?
7. CosyVoice 3.0 모델 가중치 라이선스(상업 이용 가능?)와 윈도우 설치 방법은?
8. fish-speech, index-tts 모델의 라이선스가 상업 이용을 허용하는가?
9. edge-tts의 마이크로소프트 서비스 이용이 약관상 상업 콘텐츠에 허용되는가? 한국어 음성 목록은?
10. AI-Youtube-Shorts-Generator 로컬 모드를 Gemini 무료 API 키만으로 돌릴 수 있는가? 윈도우에서 동작하는가?
11. 유튜브 Data API 프로젝트 인증(audit) 신청 절차와 기간, 개인 크리에이터도 통과 가능한가? 기본 할당량 10,000 단위로 하루 몇 개 업로드 가능한가(현재 기준)?
12. MeloTTS 한국어 음성의 자연스러움과 2024년 이후 대체 포크(유지보수 중인 것)가 있는가?
13. n8n Sustainable Use License에서 "내 유튜브 채널 운영 자동화"는 내부 업무 용도로 인정되는가?
