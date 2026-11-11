# 쇼츠 공장(shorts_factory.py) 옵션 — `clips` 틀 (원본 영상 하이라이트, 11/11)

사용법: `python3 shorts_factory.py 기획.json [결과폴더]` (결과폴더 생략 시 기획 파일 옆 `out/`)
요일 틀에서 쓰기: 틀 json 의 `"template":"clips"` → `make_today.py` 가 fill 의 `클립`·`채널`·`출처`·`배치`·`원본자막` 으로 spec 을 만든다(아래 3번).
끝 화면·썸네일·게시 문구·점검표는 rank·cards 와 같은 공장 함수를 그대로 쓴다.

## 1. 맨 위 옵션

| 옵션 | 뜻 | 기본값 / 예 |
|---|---|---|
| `template` | `"clips"` | 필수 |
| `clips` | 원본 구간 목록 `[{file, in, out, credit, note?}]` (아래 2번) | 필수 |
| `hook` | 첫 3초 노란 질문(둥근 띠) | 없으면 `question` |
| `hook_sec` | 질문 보이는 길이(초, 끝 0.4초 페이드) | `3.0` |
| `top_bar` | 위 고정 줄 `{channel, title}` (작은 회색 채널 + 흰 제목, 내내) | `{series, title}` |
| `source_line` | 아래 출처 줄(보라) | `source[0]` → 첫 클립 `"출처: "+credit` |
| `original_sub_note` | `true` → 둘째 줄 「화면 속 자막은 원본 영상 편집 자막입니다」. 글자를 주면 그 글 | 없음 |
| `layout` | `"fit"` 원본 가로를 가운데 통째로 + 같은 영상 흐린 배경 / `"crop"` 세로로 잘라 꽉 차게 | `"fit"` |
| `x_center` | crop 기준 가로 위치: 0~1 비율(1보다 크면 원본 픽셀) | `0.5` |
| `bgm` | 배경음악 파일. **기본은 끝 화면에만** | 필수 |
| `bgm_volume` | 끝 화면 배경음악 크기 | `0.5` |
| `bgm_under` | 클립 밑에도 배경음악 깔기(크기, 0이면 안 깜) | `0` |
| `end_sec` | 끝 화면 길이(초, 0.3초 디졸브로 들어감) | `3.5` |
| `end_frame` | 끝 화면 배경 장면(마지막 클립 파일의 초) | 마지막 클립 `out - 1` |
| `thumb_frame` | 썸네일 사진 장면(첫 클립 파일의 초). `thumb.photo` 가 있으면 그것 | 첫 클립 `in + 2` |
| `end` / `thumb` / `post` / `checked` | rank·cards 와 같음 | — |

## 2. 클립 칸 (`clips` 안)

| 칸 | 뜻 | 기본값 |
|---|---|---|
| `file` | 원본 영상(상대 경로는 기획 파일 기준) | 필수 |
| `in` / `out` | 쓸 구간(초). **광고 구간은 넣지 않는다** | 필수 |
| `credit` | 출처(채널 「영상 제목」). 클립마다 다르면 그 클립 동안 아래 줄이 `출처: credit` 로 바뀜 | 없음 |
| `note` | 그 클립 동안 우리 자막 한 줄(흰 굵은, 사실만) | 없음 |
| `layout` / `x_center` | 이 클립만 배치·가운데 바꾸기 | 맨 위 설정 |
| `volume` | 원본 소리 크기 | `1.0` |

- 배치: fit = 위 채널·제목 / 질문(400) / 가운데 원본(높이 608) / 아래 출처 2줄(1400). crop = 위·아래 어둡게 깔고 제목 밑(310)에 출처 2줄, 질문은 440 — 원본 자막(화면 아래쪽)을 가리지 않게.
- crop 은 원본 가로의 약 1/3만 보이므로 두 사람 이상·옆에서 나오는 원본 자막은 잘린다. 원본 자막을 살려야 하면 fit.
- 클립 사이는 바로 컷, 소리는 0.08초/0.12초 페이드로 툭 끊기지 않게.

## 3. 점검표(5줄 + clips 2줄)

| 줄 | 통과 조건 |
|---|---|
| 끝 화면 3초 이상 · 배경음악 · 출처·기준 · 숫자 확인 기록 · 썸네일/제목/소개글/첫 댓글 | 기존과 같음 |
| **원본 클립 각 8~16초** | 모든 클립 길이가 8~16초(벗어나면 몇 번이 몇 초인지 ❌) |
| **출처 표시** | `source_line`(또는 `source`) 이 있거나 모든 클립에 `credit` |

## 4. make_today.py 에서 (`templates/<요일>_<시간대>.json` 의 `"template":"clips"`)

| fill 빈칸 | spec 으로 | 비고 |
|---|---|---|
| `클립` | `clips` `[{file, in, out, credit, …}]` | 파일·in·out 없으면 멈춤 |
| `채널` | `top_bar.channel` | 없으면 `가수` |
| 틀 `hook.title` / `hook.question` | `top_bar.title` / `hook` | |
| `출처` | `source_line`(첫 줄) | |
| `배치` | `layout` | 틀 `clips.layout` → `"fit"` |
| `원본자막` | `original_sub_note` | 틀 `clips.original_sub_note` → `true` |
| 틀 `clips.end_sec` | `end_sec` | `3.5` |
