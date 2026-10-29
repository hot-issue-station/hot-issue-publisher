# 릴스 재료 올리기 (자동 제작 공통 마지막 단계)

대표 결정(2026-10-28 21:04): 캐러셀은 조회가 0이라 자동 제작 묶음은 게시하지 않는다(config/auto_publish.txt=off).
Claude는 카드와 음악 없는 릴스 영상을 "릴스 재료함"에 올리고, 대표가 인스타그램 앱에서 음악을 골라 릴스로 올린다.

재료함 주소(url): https://claude.ai/artifact/Xxp8hf3gz6aWW5uemGphWS
(스튜디오와 다른 페이지다. 아래 업로드·기록은 모두 이 주소로.)

1. 영상: `python3 scripts/make_reel_silent.py <folder> /home/claude/reels/<문서ID>.mp4 (mkdir -p /home/claude/reels; 업로드는 작업 폴더 안 파일만 가능)` (약 1분, ffmpeg).
2. 업로드: Artifact 도구 action "publish", url = 재료함 주소, asset: true,
   file_paths = ["/home/claude/reels/<문서ID>.mp4", <folder>/01.jpg … 07.jpg, <folder>/r01.jpg … 절대 경로] (한 번에, 25개 이내).
   결과에서 영상의 id = reel, 01~07 의 id = cards, r01~ 의 id = readCards (각각 순서대로).
   (round JSON에 스타일 가이드 9장의 "read"를 꼭 넣어 읽는 카드도 함께 만든다)
3. 릴스 소개글(대표가 릴스에 붙여 넣는 글, 대표 요청 10/28): <folder>/caption.txt 를 바탕으로 새로 씁니다.
   - 1줄: 훅(카드 1장 훅과 같은 뜻, 20자 안팎)
   - 2~3줄: 핵심 사실 1~2문장(숫자 포함, 카드에 있는 사실만)
   - 1줄: 부드러운 권유(예: "자세한 정리는 프로필 카드뉴스에서 볼 수 있어요")
   - 1줄: 댓글 유도 질문 + "좋아요를 가장 많이 받은 댓글을 내일 소개해요" (스타일 가이드 11장)
   - AM(출근) 회차만: data/comments/ 의 오늘 파일로 오늘의 댓글을 뽑아(11장) 권유 줄 바로 아래에 빈 줄과 "어제의 베스트 댓글: '…'" 한 줄을 넣는다(대표 결정 10/29: 앞 125자는 훅·사실 자리라 맨 위에 두지 않음). 뽑을 게 없으면 넣지 않는다.
   - AM(출근) 회차만: data/ranking/latest.json 에 1명 이상 있으면 베스트 댓글 줄(없으면 권유 줄) 아래에 "🏆 응원 랭킹 1위 ○○ ○점 · 2위 … · 3위 …"(최대 3명, 가린 이름 그대로) 한 줄과 "댓글 단 날마다 1점, 베스트 댓글은 +3점! 상위 분께 리센느 빵 안에 있는 2차 포카를 드려요(수량 소진 시 종료)" 한 줄을 넣는다. 아무도 없으면 넣지 않는다. 가린 이름을 풀어 쓰지 않는다.
   - 빈 줄, 이미지 출처 줄(사진을 쓴 회차만), config/contact.txt 의 연락처 줄('#'로 시작하지 않는 줄)
   - (재료함 표시용, 캡션에 넣지 않음) audio: data/audio/ 의 가장 최근 파일 규칙대로 이 소재에 맞는 추천 음원 1~2곡 "곡 - 아티스트"
   - 빈 줄, 해시태그 6~8개(주제 3~4개 + 분야 1~2개 + #이슈브리프 #오늘의이슈). 300자 안팎.
   - 앞부분 검사(대표 결정 10/29): 인스타는 앞 약 125자만 보이고 나머지는 '더 보기'로 접힌다. 첫 줄 = 훅(40자 이내), 둘째 줄 = 숫자가 든 핵심 사실. 소개글을 파일로 저장해 `python3 scripts/check_caption.py <파일> --hook "<카드 1장 훅>"` 을 돌려 "검사 통과"가 나올 때까지 고친다(최대 3번). 캐러셀 캡션(readCaption)도 같은 검사를 한다.
3-0. 훅 후보(대표 결정 10/29, 콘텐츠팀): 릴스 첫 화면·첫 줄에 쓸 문장 후보 3개를 "hooks"에 넣는다. 각 20자 안팎, 서로 다른 방식으로: ① 숫자로 시작(예: "200만 회, 하루 만에") ② 질문형(예: "삼성 그립감, 진짜였을까?") ③ 반전·대비(예: "팬이 부른 광고, 진짜가 됐다"). 모두 카드에 있는 사실만, 과장·낚시·최상급 금지. 1번은 카드 1장 훅과 같은 뜻으로 둔다. 대표가 재료함에서 골라 인스타 편집 화면의 첫 글자나 소개글 첫 줄로 쓴다.
3-1. 홍보 재료(대표 결정 10/29, 분석팀): 같은 소재로 채널별 홍보 문구를 만들어 4단계 기록의 "promo"에 넣는다. 대표가 재료함에서 채널별 [복사]를 눌러 붙여 넣는다. 자동 팔로우·좋아요·댓글·DM은 하지 않는다(인스타 규칙 위반). 모든 문장은 카드에 있는 사실만, 과장·최상급 금지, 링크는 넣지 않는다(프로필 링크로 안내).
   promo = {
     "bestTime": "<추천 올리는 시각 한 줄, 예: 오늘 21:30~22:00 (퇴근 뒤 휴대폰 보는 시간)>",
     "story": {"text": "<스토리 위에 얹을 2줄, 각 18자 안팎>", "sticker": "<질문 스티커 문구 20자 안팎>"},
     "threads": "<Threads 글 300~450자: 첫 줄 훅, 사실 2~3줄, 마지막 줄 질문. 해시태그는 끝에 1~3개>",
     "shorts": {"title": "<유튜브 쇼츠 제목 40자 안팎 + ' #Shorts'>", "description": "<설명 2~4줄 + 출처 + 연락처 줄>", "tags": "<쉼표로 구분한 태그 8개 안팎>"},
     "x": "<X 글: 한글 기준 130자 이내(영문 280자 한도, 한글은 2자로 셈), 해시태그 2~3개>",
     "community": "<팬 커뮤니티용 글(리센느 등 팬덤 소재일 때만, 아니면 빈 문자열): 정보 위주 존댓말, 우리 계정 홍보 문구는 마지막 한 줄 '정리 카드는 @hot.issue.station에 올려 두었어요' 정도로만>"
   }
   - 쇼츠·Threads·X는 우리 계정(@hot.issue.station)을 알리는 게 목적: 각 글 끝에 "매일 이슈를 짧게 정리해요 · 인스타 @hot.issue.station" 한 줄.
   - 남의 사진을 쓴 회차는 각 채널 글에도 이미지 출처 줄을 넣는다.
4. 기록: ArtifactData action "set", url = 재료함 주소, collection "materials", doc_id = 문서ID,
   data = {date, slot, slotName(출근길/점심/퇴근길/리센느 응원 특집 #n/자랑스러운 한국인 #n), topic, audio, reel, cards, readCards, caption(=3단계 릴스 소개글), readCaption(=caption.txt 캡션에 연락처 줄을 넣은 것, 캐러셀용), hooks(3-0단계, 문장 3개 배열), promo(3-1단계), posted:false, createdAt:<ISO>}.
5. 스튜디오 기록(브리핑용): ArtifactData update(if_version) url = 스튜디오(https://claude.ai/artifact/H9d1SRr3uSYZEX6pYDNswV), autoq/문서ID
   {status:"ready", topic, folder, message:"릴스 재료 준비 완료 (자동 게시 안 함)", readyAt:<ISO>}. previews·vetoUntil은 넣지 않는다.
6. 마지막 답변(대표 휴대폰 알림)은 한국어 두 줄만:
   "<회차 이름> 릴스 재료 준비: <topic>"
   "재료함에서 영상 저장 → 인스타 앱에서 음악 골라 올리기: https://claude.ai/artifact/Xxp8hf3gz6aWW5uemGphWS"

## 응원 랭킹 현황판(스토리)일 때 (대표 결정 10/29, 분석팀)
- AM(출근) 회차 재료를 다 올린 뒤 이어서 한다. data/ranking/latest.json 의 top 이 1명 이상일 때만(비었으면 건너뜀).
- `python3 scripts/make_ranking_board.py --out /home/claude/reels/<YYYYMMDD>_RANK` → board.jpg(1080×1920)·board.mp4(6초). "주의: … 넘쳤어요"가 나오면 board.jpg를 Read로 보고 알림에 적는다.
- 업로드: file_paths = [<그 폴더>/board.mp4, <그 폴더>/board.jpg]. reel = board.mp4 id, cards = [board.jpg id], readCards 없음.
- 기록: materials/<YYYYMMDD>_RANK, slot "RANK", slotName "응원 랭킹 현황판 · 스토리", topic "응원 랭킹 <M/D> 기준 TOP<n>", caption "", readCaption "", audio "".
- 대표가 스토리로 올리고 프로필 하이라이트 '응원 랭킹'에 추가한다(스토리는 24시간 뒤 사라지므로 하이라이트가 현황판 역할). 알림 둘째 줄 끝에 " · 랭킹 현황판도 준비했어요(스토리)"를 붙인다.

## 헤드라인 릴스(HL)일 때 바뀌는 점
- 1단계 영상은 만들지 않는다(make_headline.py가 이미 headline.mp4를 만듦).
- 2단계 업로드: file_paths = [<folder>/headline.mp4, <folder>/cover.jpg]. reel = headline.mp4 id, cards = [cover.jpg id], readCards 없음.
- 3단계 소개글은 새로 쓰지 않고 caption = <folder>/caption.txt 그대로(긴 기사형 캡션, 연락처 줄이 없으면 넣는다).
- slotName "헤드라인 · 야근 퇴근길 21:50". 알림 첫 줄 "헤드라인 릴스(21:50) 재료 준비: <topic>".
