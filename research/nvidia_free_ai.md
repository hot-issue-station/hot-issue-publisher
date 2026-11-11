# 엔비디아 무료 AI + 무료 GPU 시간 조사 (2026-11-11)

- 작성: Claude (리서치 하위 작업) / 확인일: 모든 출처 **2026-11-11** 직접 열어 봄
- 원칙: 공식 페이지(엔비디아·허깅페이스 공식 계정·각 서비스 공식 문서)만 근거로 씀. 열어 봤는데 해당 내용이 없거나 페이지가 안 열린 것은 **'확인 못 함'**.
- 엔비디아 포럼 글은 공식 문서가 아니라서 '참고(비공식)'로만 표시.
- 코드 수정 없음. `factory/ai_router.py`, `router_config.json` 둘 다 그대로 두고 **제안만** 적음.

---

## 0. 한눈에 결론

1. **build.nvidia.com(NIM 체험 API)은 무료로 쓸 수 있지만, 공식 FAQ가 "앱 시제품 만들기(prototyping)용 체험 크레딧"이라고 적어 둠** → 상시 운영(발행 자동화)의 주력으로 삼기엔 약관상 애매. 보조(예비) 단계로만 권장.
2. **우리 라우터에 코드 수정 없이 들어감**: 주소가 `https://integrate.api.nvidia.com/v1/chat/completions`(POST, Bearer 인증)라서 지금의 `kind: "openrouter"` 호출기를 그대로 재사용 가능.
3. **한국어가 공식으로 확인된 엔비디아 모델은 3개**: 음성 인식 `Nemotron 3.5 ASR Streaming 0.6B`(한국어 '전사 가능' 최상위 등급, CER 약 7%), 음성 합성 `Magpie TTS Multilingual`(한국어 CER 2.57%), 번역 `Riva Translate 4B`(한국어 포함 36개 언어). 셋 다 상업 이용 가능 표시.
4. **Nemotron 3 / 3.5 대화 모델은 공식 지원 언어에 한국어가 없음** → 카드뉴스 문구·요약용으로는 기대 낮음.
5. **Cosmos(영상 생성)는 H100급 80GB가 필요** → 게이밍 노트북으론 불가, 우리 일과도 거리 멂.
6. **머리 모양 바꾸기**에는 엔비디아 자체 모델보다 build.nvidia.com에 올라온 `FLUX.2 Klein 4B`(생성+편집, '상업/비상업 사용 가능' 표시)가 후보. `FLUX.1 Kontext dev`는 **비상업 전용**이라 미용실 앱에는 못 씀.
7. **무료 GPU 시간은 Kaggle이 우리에게 가장 맞음**(자막 음성 인식 일괄 처리용). 단 Kaggle 공식 문서가 이번에 열리지 않아 주간 시간은 '확인 못 함' — 대표가 직접 확인 필요(질문 목록 참고).

---

## 1. 엔비디아 무료 AI 항목별 표

| 항목 | 무엇을 하나 | 무료 범위 (가입·카드·크레딧·속도) | 상업 이용 (라이선스 원문) | 한국어 공식 언급 | 로컬 실행 GPU 메모리 | 우리 일 어디에 |
|---|---|---|---|---|---|---|
| **build.nvidia.com / NIM 체험 API** | 수십 개 모델(LLM·이미지·음성)을 엔비디아 서버에서 API로 호출 | 가입 필요(가입하면 'Developer Program' 회원이 됨). FAQ: "앱 시제품용 **무료 크레딧**", 호출은 "체험 API 크레딧에서 차감", **브라우저 화면에서 쓰는 건 차감 안 됨**. 모델 페이지: "요청이 속도 제한될 수 있고 다른 사용자 트래픽 때문에 느려질 수 있음". 카드 필요 여부·크레딧 수량·분당 횟수: **확인 못 함** (포럼 사용자들은 '1,000 크레딧', '분당 40회'라고 적지만 비공식) | API 자체는 'NVIDIA API Trial Terms of Service' 적용 — **원문 못 열어 봄 → 운영(production) 사용 가능 여부 확인 못 함**. FAQ 표현은 "prototyping" | 모델마다 다름(아래) | 해당 없음(클라우드) | ai_router 예비 단계: 번역·요약·썸네일 문구 초안 |
| **Nemotron 3 Super 120B-A12B** (대화 LLM) | 고성능 추론·대화 | NIM 체험 API로 호출 가능 | 'NVIDIA Nemotron Open Model License' — 원문: "Works are commercially usable", 출력물 소유권 주장 안 함, 재배포 시 고지문 필요 | **지원 언어: 영·프·독·이·일·스·중 — 한국어 없음** | 120B라 노트북 불가 (서버 예시만 있음) | 영문 기사 요약 정도. 한국어 문구엔 비추천 |
| **Nemotron 3.5 Lightning 30B-A3B** (대화 LLM, 2026-08-11 공개) | 경량 MoE 대화 모델, 최대 100만 토큰 문맥 | NIM API 목록에 `nvidia/nemotron-3.5-lightning-30b-a3b` 있음 | OpenMDW 1.1, "ready for commercial use" | **지원 언어에 한국어 없음**(사전학습 데이터 목록에만 있음) | 공식: H100/A100 80GB 1장, 또는 **RTX 5090 1장(GGUF Q4_K_M, llama.cpp)**. 노트북 GPU 가능 여부 확인 못 함 | 긴 영문 자료 요약. 한국어엔 비추천 |
| **Riva Translate 4B Instruct v2** (번역) | 문장 번역 전용 | NIM 체험 API (`nvidia/riva-translate-4b-instruct-v2`) | 페이지: 상업·비상업 사용 가능, 'NVIDIA Open Model License' | **한국어(ko) 포함 36개 언어 + 영어** | 확인 못 함 (4B라 작은 편이지만 공식 수치 없음) | **아침 해외 이슈 기사 한국어 초벌 번역**, 해외 쇼츠(채널2) 자막 번역 |
| **Nemotron 3.5 ASR Streaming 0.6B** (음성 인식) | 40개 언어 실시간/일괄 받아쓰기 | 허깅페이스 공개 가중치(무료 다운로드). 엔비디아 Speech NIM으로도 제공 | OpenMDW 1.1, "ready for commercial use" | **한국어 = 'Transcription-ready'(최상위 등급)**. FLEURS CER 7.12~8.31% | 허깅페이스 카드: 수치 없음. Speech NIM 표: 스트리밍 batch 32일 때 **6GB**, batch 64일 때 14.6GB (컨테이너 기준) | **덕심저장소 쇼츠·롱폼 자막 초안**(가장 쓸모 큼). 단 타임스탬프 출력 여부는 확인 못 함 |
| Parakeet TDT 0.6B v3 / Canary 1B v2 | 음성 인식(25개 언어) | 공개 가중치 | 확인 못 함 (해당 문서에 라이선스 없음) | NeMo 문서: "25개 **유럽** 언어" — 한국어 언급 없음 | 확인 못 함 | 한국어 자막엔 못 씀 |
| Parakeet 1.1B RNNT Multilingual (Riva ASR NIM) | 음성 인식 | NIM 컨테이너 | 확인 못 함 | **한국어 지원 표시** | 오프라인 25.6GB, 스트리밍 12.8GB → 노트북 불가 가능성 큼 | 위 0.6B 모델이 더 가벼움 |
| **Magpie TTS Multilingual 357M** (음성 합성) | 글 → 사람 목소리 | build.nvidia.com 호스팅 API 있음 + 공개 가중치(569MB) | 'NVIDIA Open Model License', "ready for commercial use" | **한국어 포함 12개 언어**(v2607에 추가), 한국어 CER 2.57% | 공식 VRAM 수치 없음. 지원 GPU 목록은 데이터센터용(L4·A10 등)만 적힘 | **쇼츠·롱폼 내레이션 TTS**. 음성 복제(목소리 따라 하기)는 보안상 **제거됨** |
| Cosmos Predict 2.5 / Transfer 2.5 / Cosmos3 | 문장·사진·영상 → 5초 영상(물리 세계 시뮬레이션용) | 공개 가중치 | 'NVIDIA Open Model License', 상업 가능. 배포 시 "Built on NVIDIA Cosmos" 표시 필요, 안전장치 우회 시 권리 자동 종료 | 없음 | **80GB급(H100)**, 소비자 RTX 카드 목록에 없음 | **우리 일엔 부적합** |
| FLUX.2 Klein 4B (BFL, build.nvidia.com 호스팅) | 이미지 생성 + 참조 이미지 여러 장 편집 | NIM 체험 API | 모델 카드: "commercial/non-commercial use" 가능 표시. 정확한 라이선스명은 허깅페이스 카드 확인 필요(이번에 안 열어 봄) | 확인 못 함 | 확인 못 함 (테스트 장비 H100) | **미용실 앱 머리 모양·색 바꾸기 시험**, 카드 배경 그림 |
| FLUX.1 Kontext dev | 문장 지시로 사진 편집 | NIM 체험 API | **"non-commercial use"만** — 상업은 BFL 별도 계약 | 확인 못 함 | 확인 못 함 | **미용실 앱(유료)엔 사용 불가.** 내부 시험만 |
| SANA (NVlabs, 이미지 생성) | 빠른 이미지 생성 | 허깅페이스 공개 | 라이선스 표기 Apache 2.0이지만 같은 카드에 "research purposes only" → **상업 가능 여부 애매** | 프롬프트 언어: 영어·중국어 | 공식 수치 없음("노트북 GPU에 배포 가능"이라고만) | 보류 |
| NVIDIA Broadcast (RTX 로컬 앱) | 잡음·메아리 제거, Studio Voice, 가상 배경, 시선 맞추기, 자동 구도, 파일 일괄 처리(File Processor) | 다운로드 버튼 있음. 가격 표시는 페이지에 **없음**(확인 못 함) | 확인 못 함 | 확인 못 함 | **최소 GeForce RTX 2060** 이상 | **OBS 녹화 음성 잡음 제거**, 내레이션 녹음 정리 |
| ChatRTX | (내 파일을 읽는 로컬 챗봇) | 공식 URL이 일반 'RTX AI PC' 소개 페이지로 넘어감 → **현재 상태·요구 사양 확인 못 함** | 확인 못 함 | 확인 못 함 | 확인 못 함 | 보류 |
| NVIDIA Open Model License (공통 라이선스) | — | — | 원문(2025-10-24 개정): "Models are commercially usable", **출력물 소유권 주장 안 함**, 모델을 **재배포할 때만** 고지문("Licensed by NVIDIA Corporation under the NVIDIA Open Model License") 필요, 안전장치를 비슷한 대체 없이 우회하면 권리 자동 종료, 특허·저작권 소송 제기 시 종료 | — | — | 우리가 만든 **결과물(자막·음성·이미지)**을 상업적으로 쓰는 데는 문제 없음. 미용실 앱에 모델 파일을 **넣어서 배포**하면 고지문 필요 |

### 한국어 정리
- 공식 한국어 확인: Nemotron 3.5 ASR(음성 인식), Magpie TTS(음성 합성), Riva Translate(번역), Parakeet 1.1B Multilingual(음성 인식, 무거움).
- 공식 한국어 없음: Nemotron 3 Super, Nemotron 3.5 Lightning, Parakeet v3, Canary.
- NIM 목록의 다른 회사 모델(Qwen·DeepSeek·Kimi·GLM 등)의 한국어 성능: 이번에 각 회사 공식 카드를 열지 않아 **확인 못 함**.

---

## 2. ai_router에 넣기 (제안만, 코드 수정 없음)

### 2-1. 공식 문서로 확인한 것
| 항목 | 확인 내용 | 출처 |
|---|---|---|
| 주소 | `https://integrate.api.nvidia.com` + `POST /v1/chat/completions` | LLM APIs 목록, Qwen3 Next 추론 페이지 |
| 인증 | 자격 증명 종류 "Bearer" (→ `Authorization: Bearer <키>`). 정확한 머리글 한 줄 예시는 페이지에 없음 | Qwen3 Next 추론 페이지 |
| 모델 이름 형식 | `qwen/qwen3-next-80b-a3b-instruct` 처럼 `회사/모델` | 같은 페이지 ("Defaults to qwen/qwen3-next-80b-a3b-instruct") |
| OpenAI 호환 | NIM LLM 문서: "NIM LLM and VLM exposes an **OpenAI-compatible** inference API" (자체 설치 NIM 기준 문서). 호스팅 API도 같은 경로·같은 형식 | NIM LLM API Reference |
| 키 발급 | 모델 페이지 'Get API Key' → 로그인/가입 → 'Copy Key' | API Quickstart |

### 2-2. 지금 코드로 되는 이유
`call_openrouter()`는 OpenAI 형식 그대로(`model`, `max_tokens`, `messages`) 보내고 `Authorization: Bearer` 머리글을 붙인 뒤 `choices[0].message.content`를 읽음. NIM과 같은 형식이라 **`kind: "openrouter"`를 그대로 쓰면 됨**.
- 덤으로 붙는 `X-Title` 머리글은 엔비디아가 무시할 것으로 보이지만 **공식 확인 못 함** → 첫 시험 호출로 확인.
- 크레딧이 떨어지면 402가 오면 'rejected'(쉬는 시간 없음)로 처리되어 매번 한 번씩 헛걸음함 — 지금 구조상 큰 문제는 아님(다음 단계로 넘어감).

### 2-3. router_config.json에 넣을 설정 예시 (키는 환경변수, 실제 키 없음)
```json
{
  "name": "nvidia_nim",
  "kind": "openrouter",
  "enabled": false,
  "external_free": true,
  "key_env": "NVIDIA_API_KEY",
  "model": "qwen/qwen3-next-80b-a3b-instruct",
  "url": "https://integrate.api.nvidia.com/v1/chat/completions",
  "app_title": "IssueBrief AI Router",
  "cooldown_429": 300,
  "cooldown_error_sec": 1800,
  "_메모": "엔비디아 NIM 체험 API(시제품용 무료 크레딧). 한국어 품질 시험 후 enabled true로."
}
```
- `enabled: false`로 시작 → 대표가 키 발급하고 시험 호출 1번 성공하면 `true`.
- `external_free: true` → **개인정보 작업(private)은 자동으로 건너뜀** (체험 약관에서 입력 데이터를 어떻게 쓰는지 확인 못 했으므로 꼭 true 유지. 미용실 고객 정보는 절대 안 보냄).
- `cooldown_429: 300`(5분) → 엔비디아는 분당 한도 성격이라 1시간 쉬는 건 과함. 정확한 한도는 확인 못 함.
- 모델 후보(같은 주소, `model`만 바꾸면 됨):
  - 한국어 문구·요약: `qwen/qwen3-next-80b-a3b-instruct` 또는 `deepseek-ai/deepseek-v4-flash` (둘 다 NIM 목록에 있음. 한국어 성능은 확인 못 함 → 같은 질문으로 비교 시험 권장)
  - Nemotron 계열은 한국어 미지원이라 이 칸엔 비추천
- (선택) 번역 전용 칸을 따로 하나 더: `"name": "nvidia_translate"`, `"model": "nvidia/riva-translate-4b-instruct-v2"`. 단 이 모델이 같은 `/v1/chat/completions` 주소를 쓰는지 **확인 못 함**, 또 시스템 메시지에 `"en-ko"`처럼 언어쌍을 넣는 전용 형식이라 라우터의 기본 `default_system`과 맞지 않음 → 지금 구조에선 **넣지 말고 별도 스크립트로 시험**하는 게 맞음.

### 2-4. 우선순위 제안
```
gemini(무료) → nvidia_nim(무료 체험) → ollama(내 노트북) → openrouter(:free) → claude(유료, 월 한도)
```
- 이유: NIM은 큰 모델이라 노트북 Ollama(exaone 7.8B)보다 빠르고 품질이 나을 가능성이 크고, 노트북이 꺼져 있어도 됨. Gemini가 하루 한도에 걸린 날의 1차 예비로 적당.
- 단, 공식 FAQ가 "prototyping" 용도라고 한 만큼 **매일 자동 발행의 주력으로 쓰지 말 것**. 약관 원문을 대표가 확인하기 전까지는 '예비'로만.
- 개인정보 작업은 `private=True`로 부르면 gemini·nvidia_nim·openrouter를 건너뛰고 ollama → claude로만 감(지금 규칙 그대로).

---

## 3. 일주일에 일정 시간 GPU를 무료로 주는 곳

| 서비스 | 무료 시간 | GPU 종류·메모리 | 세션 최대 길이 | 카드 등록 | 상업적 산출물 (약관) | 우리 쓰임 |
|---|---|---|---|---|---|---|
| **Kaggle Notebooks** | **확인 못 함** (공식 문서 페이지가 본문 없이 열림. 흔히 '주 30시간'이라 하지만 비공식) | 확인 못 함 (흔히 T4×2 또는 P100, 16GB라고 함 — 비공식) | 확인 못 함 | 확인 못 함 (전화번호 인증 필요하다는 말이 있음 — 비공식) | 확인 못 함 | 자막용 음성 인식 일괄 처리, 모델 시험 |
| **Google Colab 무료** | **공개 안 함**: "사용 한도는 유동적이며 공개하지 않음", GPU는 "엄격히 제한" | "시간에 따라 바뀜", 보장 안 됨 | **최대 12시간**(가용성 따라 더 짧을 수 있음), 가만히 두면 끊김 | 무료("Colab is free of charge") | 약관(2024-05-14)에 상업 사용 언급 **없음** → 확인 못 함. 금지: **딥페이크 생성**, 미디어 서빙, 여러 계정으로 한도 회피, 무료에서 SSH·원격 접속, 웹 UI 위주 사용 | 짧은 시험(음성 인식 몇 편). **머리 모양 바꾸기 시험은 '딥페이크' 금지 조항과 경계가 애매** — 손님 얼굴 사진으로는 하지 말 것 |
| **Hugging Face ZeroGPU** | **하루** 무료 계정 5분, 비로그인 2분, PRO 40분 (24시간 뒤 초기화) | RTX Pro 6000 Blackwell 절반 **48GB**(기본) / 전체 96GB(2배 차감) | 호출 1번당 기본 60초(`duration`으로 늘림, 상한 명시 없음) | 무료 계정도 Space 2개까지 만들 수 있음(이메일 인증 + 가입 30일 이상) | 확인 못 함 | **머리 모양 바꾸기 데모 화면**(Gradio 전용)을 만들어 대표·종훈이 폰으로 눌러 보기. 일괄 처리엔 하루 5분이라 부족 |
| **Lightning AI** | 가입 시 5크레딧 + **카드 등록 시 25크레딧 추가** = 최대 30크레딧 ≈ "인터럽터블(중간에 끊길 수 있는) 장비로 약 50 GPU시간". 크레딧은 12개월 뒤 소멸 (매주·매달 충전 아님) | 무료 등급 GPU 종류 표 없음. T4·L4·L40S는 세션 제한 없음, A100·H100·H200은 4시간 | 무료 Studio는 **4시간마다 재시작** | 시작엔 **카드 불필요**(카드 넣으면 크레딧 추가). 전화번호 요구 | 확인 못 함(약관 미열람) | 한 번에 몰아서 큰 작업(긴 영상 여러 편 받아쓰기) |
| Paperspace(DigitalOcean) | 공식 가격 페이지 본문이 안 열림 → **확인 못 함** | 확인 못 함 | 확인 못 함 | 확인 못 함 | 확인 못 함 | 보류 |

### 긴 영상 인코딩(내보내기)에 무료 GPU를 쓰지 않는 이유
- 영상 파일 올리고 내려받는 시간이 인코딩 시간보다 길어짐(롱폼은 수 GB).
- 세션이 12시간(Colab)·4시간(Lightning)마다 끊기고, 가만히 있으면 끊김 → 중간에 날아갈 수 있음.
- Colab 약관은 "상호작용 계산과 무관한 미디어 서빙"을 금지 → 영상 공장처럼 쓰는 건 위반 소지.
- 대표 집 게이밍 노트북의 NVENC(엔비디아 하드웨어 인코더)가 오히려 빠르고 0원. (노트북 GPU 사양은 아직 모름)
- 무료 GPU는 **음성 인식·모델 시험처럼 '계산은 무겁고 파일은 작은 일'**에만 쓰는 게 맞음(소리만 뽑아서 올리면 수십 MB).

### 우리에게 가장 맞는 1곳
**Kaggle Notebooks** — 매주 정해진 GPU 시간이 다시 채워지는 곳이라 덕심저장소 영상 소리만 뽑아 올려 Nemotron 3.5 ASR로 자막 초안을 일괄로 만드는 용도에 가장 맞음(단 주간 시간·GPU 종류는 공식 확인 못 했으니 대표가 첫 접속 때 화면에서 확인). 머리 모양 바꾸기 '보여 주는 데모'만은 Hugging Face ZeroGPU가 따로 맞음.

---

## 4. 출처 (모두 2026-11-11 직접 열어 봄)

공식 — 엔비디아
- NIM FAQ: https://docs.api.nvidia.com/nim/docs/faq
- API Quickstart: https://docs.api.nvidia.com/nim/docs/api-quickstart
- LLM APIs 목록: https://docs.api.nvidia.com/nim/reference/llm-apis
- Qwen3 Next 추론 API(주소·Bearer·모델 이름): https://docs.api.nvidia.com/nim/reference/qwen-qwen3-next-80b-a3b-instruct-infer
- Visual Models 목록: https://docs.api.nvidia.com/nim/reference/visual-models-apis
- Nemotron 3 Super 문서: https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-super-120b-a12b
- Riva Translate 4B 문서: https://docs.api.nvidia.com/nim/reference/nvidia-riva-translate-4b-instruct-v2
- Riva Translate 모델 페이지(속도 제한 문구): https://build.nvidia.com/nvidia/riva-translate-4b-instruct-v2
- Magpie TTS 모델 카드: https://build.nvidia.com/nvidia/magpie-tts-multilingual/modelcard
- FLUX.1 Kontext dev 모델 카드: https://build.nvidia.com/black-forest-labs/flux_1-kontext-dev/modelcard
- FLUX.2 Klein 4B 모델 카드: https://build.nvidia.com/black-forest-labs/flux_2-klein-4b/modelcard
- NIM LLM API Reference(OpenAI 호환): https://docs.nvidia.com/nim/large-language-models/latest/reference/api-reference.html
- Speech NIM ASR 지원표(한국어·메모리): https://docs.nvidia.com/nim/speech/26.05.0/reference/support-matrix/asr.html
- NeMo ASR 대표 모델: https://docs.nvidia.com/nemo/speech/latest/asr/featured_models.html
- Cosmos NIM 지원표: https://docs.nvidia.com/nim/cosmos/3.0.0/support-matrix.html
- Nemotron 3.5 Lightning(NGC): https://catalog.ngc.nvidia.com/orgs/nim/nvidia/models/nemotron-3.5-lightning
- NVIDIA Open Model License: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/
- NVIDIA Nemotron Open Model License: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license
- NVIDIA Broadcast: https://www.nvidia.com/en-us/geforce/broadcasting/broadcast-app/
- ChatRTX(일반 페이지로 넘어감): https://www.nvidia.com/en-us/ai-on-rtx/chatrtx/
- Developer Program: https://developer.nvidia.com/developer-program

공식 — 허깅페이스(엔비디아 공식 계정)
- Nemotron 3.5 ASR Streaming 0.6B: https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b
- Magpie TTS Multilingual 357M: https://huggingface.co/nvidia/magpie_tts_multilingual_357m
- Cosmos Predict 2.5 14B: https://huggingface.co/nvidia/Cosmos-Predict2.5-14B/blob/main/README.md
- SANA 1600M (NVlabs 연구팀 계정): https://huggingface.co/Efficient-Large-Model/Sana_1600M_1024px/blob/main/README.md

공식 — 무료 GPU
- Google Colab FAQ: https://research.google.com/colaboratory/faq.html
- Google Colab 약관: https://research.google.com/colaboratory/tos_v5.html
- Hugging Face ZeroGPU 문서: https://huggingface.co/docs/hub/spaces-zerogpu
- Lightning AI 가격: https://lightning.ai/pricing
- Kaggle Notebooks 문서(본문 안 열림): https://www.kaggle.com/docs/notebooks , https://www.kaggle.com/docs/efficient-gpu-usage
- Paperspace 가격(본문 안 열림): https://docs.digitalocean.com/products/paperspace/notebooks/details/pricing/

참고(비공식, 근거로 안 씀)
- 엔비디아 포럼 "API Rate Limit Increase is NOT granted…": https://forums.developer.nvidia.com/t/api-rate-limit-increase-is-not-granted-by-requesting-it-here/368420 — 한도는 "모델·용도·전체 트래픽에 따라 다름", 무료 등급 한도 상향 공식 방법 없음
- 엔비디아 포럼 "Is NIM free?": https://forums.developer.nvidia.com/t/is-nim-free/369368 — 사용자 답글만 있음

---

## 5. 대표가 퍼플렉시티에 물어볼 질문 (확인 못 한 것)

1. "NVIDIA API Trial Terms of Service(build.nvidia.com) 원문에서, 무료 체험 API로 만든 결과물을 **상업 서비스(인스타·유튜브 게시)에 써도 되는지**, 그리고 내가 보낸 입력·출력을 엔비디아가 **학습에 쓰는지** 원문 문장으로 알려 줘. 링크도."
2. "build.nvidia.com 무료 API는 **가입할 때 신용카드가 필요한지**, 무료 크레딧은 **몇 개**이고 **다 쓰면 어떻게 되는지**(충전되는지, 끝인지), 분당 요청 한도가 공식적으로 몇인지 엔비디아 공식 페이지 기준으로."
3. "build.nvidia.com 호스팅 API에서 `nvidia/riva-translate-4b-instruct-v2`도 `https://integrate.api.nvidia.com/v1/chat/completions`로 호출하는지, 한국어 번역 요청 예시(시스템 메시지 형식)를 공식 문서로."
4. "Kaggle Notebooks의 **주간 GPU 무료 시간**, GPU 종류와 메모리, 한 세션 최대 시간, 전화 인증 필요 여부를 kaggle.com 공식 문서 기준으로 2026년 현재 값으로."
5. "Kaggle·Lightning AI·Hugging Face 약관에서 **무료 GPU로 만든 결과물(자막 파일·이미지)을 상업적으로 써도 되는지** 원문 문장으로."
6. "Paperspace(DigitalOcean) 무료 GPU 노트북이 2026년에도 있는지, 있으면 세션 시간과 카드 등록 필요 여부."
7. "NVIDIA ChatRTX가 2026년 현재도 배포 중인지, 필요한 GPU와 VRAM(최소 몇 GB), 한국어 문서를 읽을 수 있는지."
8. "NVIDIA Broadcast 앱이 무료인지, 노트북용 RTX GPU에서도 되는지, File Processor(녹음 파일 일괄 잡음 제거)가 한국어 음성에도 잘 되는지."
9. "nvidia/nemotron-3.5-asr-streaming-0.6b로 **오프라인 일괄 받아쓰기할 때 단어·문장 타임스탬프(SRT 자막용)가 나오는지**, 8GB VRAM 노트북에서 돌아가는지."
10. "nvidia/magpie_tts_multilingual_357m을 **윈도우 게이밍 노트북(8GB VRAM 정도)**에서 돌릴 수 있는지, 필요한 VRAM 실제 수치."
11. "FLUX.2 Klein 4B의 정확한 라이선스(Apache 2.0인지)와, 사람 사진의 **머리 모양·머리색만 바꾸는 편집**에 쓸 때 상업 앱(미용실 앱)에 넣어도 되는지, 필요한 VRAM."
12. "build.nvidia.com에 있는 Qwen3 Next 80B, DeepSeek V4 Flash 중 **한국어 문장 품질**이 더 좋은 쪽은? 공식 지원 언어 목록 기준으로."
