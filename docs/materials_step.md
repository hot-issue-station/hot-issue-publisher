# 릴스 재료 올리기 (자동 제작 공통 마지막 단계)

대표 결정(2026-10-28 21:04): 캐러셀은 조회가 0이라 자동 제작 묶음은 게시하지 않는다(config/auto_publish.txt=off).
Claude는 카드와 음악 없는 릴스 영상을 "릴스 재료함"에 올리고, 대표가 인스타그램 앱에서 음악을 골라 릴스로 올린다.

재료함 주소(url): https://claude.ai/artifact/Xxp8hf3gz6aWW5uemGphWS
(스튜디오와 다른 페이지다. 아래 업로드·기록은 모두 이 주소로.)

1. 영상: `python3 scripts/make_reel_silent.py <folder> /tmp/<문서ID>.mp4` (약 1분, ffmpeg).
2. 업로드: Artifact 도구 action "publish", url = 재료함 주소, asset: true,
   file_paths = ["/tmp/<문서ID>.mp4", <folder>/01.jpg … 07.jpg 절대 경로] (8개 한 번에).
   결과에서 영상의 id = reel, 카드 7장의 id = cards(순서대로).
3. 캡션: <folder>/caption.txt 를 읽고, config/contact.txt 의 연락처 줄('#'로 시작하지 않는 줄)이 없으면 해시태그 바로 위에 빈 줄과 함께 넣는다.
4. 기록: ArtifactData action "set", url = 재료함 주소, collection "materials", doc_id = 문서ID,
   data = {date, slot, slotName(출근길/점심/퇴근길/리센느 응원 특집 #n/자랑스러운 한국인 #n), topic, reel, cards, caption, posted:false, createdAt:<ISO>}.
5. 스튜디오 기록(브리핑용): ArtifactData update(if_version) url = 스튜디오(https://claude.ai/artifact/H9d1SRr3uSYZEX6pYDNswV), autoq/문서ID
   {status:"ready", topic, folder, message:"릴스 재료 준비 완료 (자동 게시 안 함)", readyAt:<ISO>}. previews·vetoUntil은 넣지 않는다.
6. 마지막 답변(대표 휴대폰 알림)은 한국어 두 줄만:
   "<회차 이름> 릴스 재료 준비: <topic>"
   "재료함에서 영상 저장 → 인스타 앱에서 음악 골라 올리기: https://claude.ai/artifact/Xxp8hf3gz6aWW5uemGphWS"
