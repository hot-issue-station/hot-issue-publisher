# 이슈브리프 게시 프로그램

이슈브리프 스튜디오에서 저장한 카드 묶음(zip)을 정해진 시각(출근 07:30 · 점심 12:00 · 퇴근 18:30)에 Instagram 캐러셀로 올립니다. GitHub의 무료 기능만 쓰며, 노트북이 꺼져 있어도 돌아갑니다. 처음에는 **시험 모드**라 실제로 게시하지 않습니다.

## 하루 사용법

1. 스튜디오 미션 7에서 **카드 저장 (JPG 7장 + 캡션)**으로 zip을 받습니다.
2. 이 저장소의 `inbox` 폴더를 열고 **Add file → Upload files**로 zip을 끌어다 놓은 뒤 **Commit changes**를 누릅니다. 이것이 **승인 3**입니다.
3. 1분쯤 뒤 `posts` 폴더에 묶음이 풀립니다. 예약 시각이 되면 자동으로 게시되고, 그 폴더에 `published.json`이 생깁니다.

게시를 취소하려면 예약 시각 전에 `posts/<묶음 이름>` 폴더를 지웁니다.

## 처음 한 번 설정

1. **저장소 만들기**: GitHub에서 새 저장소를 **Public**으로 만들고 이 파일들을 그대로 올립니다. Instagram이 사진을 가져가려면 사진 주소가 공개되어 있어야 해서 Public이어야 합니다(카드는 어차피 Instagram에 공개됩니다).
2. **비밀값 넣기**: 저장소 **Settings → Secrets and variables → Actions → New repository secret**에서 하나를 만듭니다.
   - 이름 `IG_ACCESS_TOKEN`, 값은 Meta 개발자 앱에서 발급한 액세스 토큰. Instagram 로그인 토큰(IG…)과 Facebook 로그인 토큰(EAA…) 모두 됩니다. Facebook 로그인 토큰이면 페이지에 연결된 Instagram 계정을 자동으로 찾습니다.
   - 계정 ID는 프로그램이 토큰으로 알아서 찾습니다. (`IG_USER_ID`를 따로 넣어도 됩니다.)
   - 토큰은 채팅이나 파일에 적지 말고 이 화면에만 넣습니다.
3. **시험해 보기**: **Actions → 예약 게시 → Run workflow**를 누르고, 기록에 "토큰 확인: @hot.issue.station"이 나오는지 봅니다.
4. **실제 게시 켜기**: **Settings → Secrets and variables → Actions → Variables 탭**에서 `DRY_RUN` 변수를 만들고 값을 `false`로 넣습니다. 다시 시험 모드로 돌리려면 `true`로 바꿉니다.

## 알아 둘 점

- **비용**: Public 저장소의 GitHub Actions와 Instagram API는 무료입니다.
- **시각**: GitHub 예약 실행은 붐비면 5~15분 늦게 돌 수 있습니다.
- **늦은 묶음**: 예약 시각에서 6시간이 지난 묶음은 자동으로 올리지 않습니다. 다시 올리려면 `post.json`의 `publishAt`을 고칩니다.
- **토큰 기한**: Instagram 장기 토큰은 60일마다 새로 받아 `IG_ACCESS_TOKEN`을 바꿔 줘야 합니다. 달력에 알림을 걸어 두세요.
- **한도**: Instagram은 API 게시 수를 24시간마다 제한합니다(하루 3회는 충분히 안쪽).
