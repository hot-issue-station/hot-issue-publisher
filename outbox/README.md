# 보내기함 (outbox)

`outbox/<ID>/reel.mp4` + `post.json` 을 올리면 「보내기함 자동 게시」 작업이 돌아요.
- Threads: 노래 없이 바로 공개 게시 (비밀값 THREADS_TOKEN 필요)
- 유튜브: 비공개로 올림 — 유튜브 심사 통과 뒤 저장소 변수 YT_UPLOAD=on 으로 켬
- 결과: `done.json` (올린 곳은 다시 올리지 않음). 실패·건너뜀이면 작업을 다시 돌리면 재시도.
