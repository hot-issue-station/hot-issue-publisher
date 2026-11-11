# 덕심저장소 갤러리 — Netlify 공개 순서 (대표 집 컴퓨터용)

명령어 입력 없이 마우스 클릭과 끌어 놓기만으로 합니다. 비용 0원(Netlify Free, 상업 이용 가능).

## 0. 준비물
- `dist` 폴더 하나 (Claude가 만들어 압축 파일로 드림 → 집 컴퓨터에서 압축 풀기)
- 안에 `index.html`(갤러리), `about.html`·`privacy.html`·`terms.html`·`ads.html`·`takedown.html`, `assets` 폴더, `curation.json`, `endorsements.json`, `netlify.toml`, `_headers` 가 있는지 눈으로 확인

## 1. Netlify 가입 (대표가 직접)
1. 크롬에서 netlify.com 접속 → 오른쪽 위 **Sign up**
2. 원하는 방법(이메일 또는 구글 계정)으로 가입. 요금제 고르는 화면이 나오면 **Free** 선택
3. 처음 질문(팀 이름 등)은 아무 이름이나 넣고 넘어가기. 카드 정보는 넣지 않아도 됩니다

## 2. 사이트 올리기
1. 첫 화면에서 **Add new site** (화면에 따라 **Add new project**) 누르기
2. **Deploy manually** 선택
3. 회색 점선 상자에 `dist` **폴더 통째로** 끌어 놓기 (폴더 안 파일들이 아니라 폴더 자체)
4. 1분쯤 기다리면 `https://임의이름.netlify.app` 주소가 생김 → 눌러서 갤러리가 열리는지 확인

## 3. 사이트 이름 바꾸기
1. 왼쪽 메뉴 **Site configuration**(또는 **Project configuration**) → **General**
2. **Site details**(Project details) → **Change site name**(Change project name)
3. 원하는 영문 이름 입력 (예: `duksim-gallery`) → **Save**
4. 주소가 `https://duksim-gallery.netlify.app` 로 바뀜

## 4. 문의 양식 주소(FORM_URL) 넣기
문의 버튼 4곳(개인정보·광고·권리 신고)은 지금 회색 「준비 중」입니다. 양식 주소를 넣으면 눌리게 됩니다.
1. 구글 설문지 등으로 문의 양식을 만들고 **보내기 → 링크** 주소 복사 (`https://` 로 시작해야 함)
2. `dist/assets/site-config.js` 를 **메모장**으로 열기 (오른쪽 클릭 → 연결 프로그램 → 메모장)
3. `FORM_URL: "FORM_URL",` 의 **두 번째** `FORM_URL` 자리에 복사한 주소 붙여 넣기
   - 예: `FORM_URL: "https://forms.gle/abcd1234",`
   - 같은 방법으로 `EFFECTIVE_DATE`(시행일, 예: `"2026-12-01"`), `PRIVACY_OFFICER`(예: `"덕심저장소 운영자"`)도 바꾸기
   - 따옴표와 쉼표는 지우지 않기. 이메일 주소·전화번호는 넣지 않기
4. 저장 후, Netlify 왼쪽 **Deploys** 메뉴 → 아래쪽 점선 상자에 `dist` 폴더를 **다시 끌어 놓기**
5. 1시간 안에 모든 방문자 화면에 반영(바로 확인하려면 휴대폰에서 새로고침)
6. 바꾼 내용을 Claude에게 알려 주면 원본(`site/src/assets/site-config.js`)에도 똑같이 반영

## 5. 갤러리를 고친 뒤 다시 올릴 때
Claude가 새 `dist` 압축 파일을 드리면 → 압축 풀기 → **Deploys** 점선 상자에 끌어 놓기. 끝.
(4번에서 바꾼 `site-config.js` 값이 원본에 반영돼 있는지 Claude에게 한 번 확인)

## 알아 두기
- 보안 헤더·캐시 규칙은 `dist` 안의 `_headers`·`netlify.toml` 로 자동 적용됩니다
- Netlify Free 한도(월 전송량 등)를 넘기면 사이트가 잠시 멈출 수 있음 → 대시보드 **Usage** 에서 가끔 확인
- 광고 자리 판매는 개인정보 처리방침·약관 공개 후, 시행일을 넣은 다음에 시작
