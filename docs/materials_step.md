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
   - AM(출근) 회차만: data/comments/ 의 오늘 파일로 오늘의 댓글을 뽑아(11장) 소개글 맨 위에 "어제의 베스트 댓글: '…'" 한 줄과 빈 줄을 넣는다. 뽑을 게 없으면 넣지 않는다.
   - 빈 줄, 이미지 출처 줄(사진을 쓴 회차만), config/contact.txt 의 연락처 줄('#'로 시작하지 않는 줄)
   - 빈 줄, 해시태그 6~8개(주제 3~4개 + 분야 1~2개 + #이슈브리프 #오늘의이슈). 300자 안팎.
4. 기록: ArtifactData action "set", url = 재료함 주소, collection "materials", doc_id = 문서ID,
   data = {date, slot, slotName(출근길/점심/퇴근길/리센느 응원 특집 #n/자랑스러운 한국인 #n), topic, reel, cards, readCards, caption(=3단계 릴스 소개글), readCaption(=caption.txt 캡션에 연락처 줄을 넣은 것, 캐러셀용), posted:false, createdAt:<ISO>}.
5. 스튜디오 기록(브리핑용): ArtifactData update(if_version) url = 스튜디오(https://claude.ai/artifact/H9d1SRr3uSYZEX6pYDNswV), autoq/문서ID
   {status:"ready", topic, folder, message:"릴스 재료 준비 완료 (자동 게시 안 함)", readyAt:<ISO>}. previews·vetoUntil은 넣지 않는다.
6. 마지막 답변(대표 휴대폰 알림)은 한국어 두 줄만:
   "<회차 이름> 릴스 재료 준비: <topic>"
   "재료함에서 영상 저장 → 인스타 앱에서 음악 골라 올리기: https://claude.ai/artifact/Xxp8hf3gz6aWW5uemGphWS"

## 헤드라인 릴스(HL)일 때 바뀌는 점
- 1단계 영상은 만들지 않는다(make_headline.py가 이미 headline.mp4를 만듦).
- 2단계 업로드: file_paths = [<folder>/headline.mp4, <folder>/cover.jpg]. reel = headline.mp4 id, cards = [cover.jpg id], readCards 없음.
- 3단계 소개글은 새로 쓰지 않고 caption = <folder>/caption.txt 그대로(긴 기사형 캡션, 연락처 줄이 없으면 넣는다).
- slotName "헤드라인 · 야근 퇴근길 21:50". 알림 첫 줄 "헤드라인 릴스(21:50) 재료 준비: <topic>".
