# 리센느관 큐레이션 (검증된 인기 영상)

- 확인 시각: 2026-11-11 15:30~16:00 (KST)
- 대표 기준(11/11): "검증이 된 영상이어야 한다. 조회수가 높고 좋아요 수·댓글 수 등이 많은 걸 테마로 묶어서 배치."
- 방 순서(대표 지시 15:31, 15:4x 수정): 무대 영상 → 안원잘부 → TV 예능 → 유튜브 출연 → 멤버들의 일상 → 생일 이벤트

## 숫자를 어디서 확인했나

- **유튜브 시청 페이지**(youtube.com/watch)는 열어도 조회수·좋아요·댓글이 표시되지 않았다. 일부 페이지는 제목·채널·게시일만 확인됨.
- **조회수·좋아요**: Return YouTube Dislike 공개 API(`returnyoutubedislikeapi.com/votes?videoId=…`)를 영상마다 직접 열어 확인. 캐시 값이라 실제 화면 숫자와 차이가 날 수 있다.
- **제목·채널 이름**: noembed(유튜브 oEmbed 중계) 또는 유튜브 시청 페이지에서 확인.
- **댓글 수**: 열어 본 어떤 페이지에서도 확인 못 함 → 전부 null("확인 필요").
- **게시일**: 시청 페이지가 열린 4편만 확인. 나머지는 null. 제목 속 6자리 숫자(예: 260808)는 방송일이지 게시일이 아니다.
- 팬 채널 영상은 넣지 않았다(조회수가 낮거나 원작자 불분명).
- TV 예능 방: 지상파(MBC)와 케이블(JTBC 아는형님·tvN 놀토) 방송사 공식 채널 영상. `start`(초)는 지금 모두 null — 숙소 합본(KZKQS4hjIYs)만 리센느 장면 시각을 확인해 넣어야 함.

## 점수 매기는 법

```
조회수점수 = log10(조회수)를 전체 27편 안에서 0~1로 맞춘 값
반응률     = (좋아요 + 댓글) / 조회수   ← 지금은 댓글이 없어 좋아요/조회수만
반응률점수 = 반응률을 전체 27편 안에서 0~1로 맞춘 값
점수       = 0.6 × 조회수점수 + 0.4 × 반응률점수
```

조회수는 로그로 줄여서 1,000만 영상이 100만 영상을 완전히 눌러 버리지 않게 했고, 반응률로 "본 사람이 얼마나 좋아했나"를 함께 본다. 댓글 수가 확인되면 다시 계산한다.

## 전체 순위 (27편)

| 순위 | 방 | 영상 | 채널 | 조회수 | 좋아요 | 반응률 | 점수 |
|---|---|---|---|---:|---:|---:|---:|
| 1 | 안원잘부 | [갸루와 거제에 왔습니다 (거제 1편)](https://www.youtube.com/watch?v=OrCOflk2QmQ) | 안녕하세요원이입니다잘부탁드립니다 | 16,401,124 | 286,253 | 1.75% | 0.760 |
| 2 | 안원잘부 | [저희도 리센느입니다...](https://www.youtube.com/watch?v=5JZ5biQ_hMI) | 안녕하세요원이입니다잘부탁드립니다 | 13,824,008 | 228,630 | 1.65% | 0.730 |
| 3 | 안원잘부 | [미나미의 갸루라이브 메들리!](https://www.youtube.com/watch?v=FcMaC8akSU8) | 안녕하세요원이입니다잘부탁드립니다 | 11,237,723 | 193,235 | 1.72% | 0.713 |
| 4 | 안원잘부 | [A day out in Seongsu before the blowout (사투리…](https://www.youtube.com/watch?v=JJBf0jCcfrQ) | 안녕하세요원이입니다잘부탁드립니다 | 10,073,505 | 170,722 | 1.69% | 0.698 |
| 5 | 안원잘부 | [I tried speaking only in dialect all day lon…](https://www.youtube.com/watch?v=NS7tSrMrWsc) | 안녕하세요원이입니다잘부탁드립니다 | 13,543,435 | 169,729 | 1.25% | 0.683 |
| 6 | 무대 영상 | ['SPECIAL STAGE' RESCENE(리센느) - LOVE ATTACK #…](https://www.youtube.com/watch?v=ajhEFz1zNMQ) | Mnet K-POP | 5,884,992 | 96,322 | 1.64% | 0.629 |
| 7 | 무대 영상 | ['COMEBACK' RESCENE (리센느) - Pretty Girl #엠카운트…](https://www.youtube.com/watch?v=Esd-KkxROxA) | Mnet K-POP | 3,603,577 | 71,644 | 1.99% | 0.611 |
| 8 | 유튜브 출연 | [[리무진서비스] EP.211 리센느 미나미 | RESCENE MINAMI | R…](https://www.youtube.com/watch?v=SW7M6MdlrlU) | KBS Kpop | 1,598,556 | 42,671 | 2.67% | 0.592 |
| 9 | 유튜브 출연 | [거제 야호가 문특에 왔습니다 (w. 리센느 원이, 미나미, 제나)](https://www.youtube.com/watch?v=17t9izNAYVE) | MMTG 문명특급 | 1,076,984 | 31,504 | 2.93% | 0.574 |
| 10 | 멤버들의 일상 | [[Re-log] 먹짱 원짱, 대만에 가다 🍴 | RESCENE (리센느) vlog](https://www.youtube.com/watch?v=xclVi9zCFdY) | RESCENE | 422,920 | 16,466 | 3.89% | 0.573 |
| 11 | 생일 이벤트 | [리뿌 생일 라이브에 오신 걸 환영합니다💝](https://www.youtube.com/watch?v=fCrQXP_2u3U) | RESCENE | 1,372,790 | 35,317 | 2.57% | 0.563 |
| 12 | 유튜브 출연 | [[리무진서비스] EP.240 리센느 리브 | RESCENE LIV | With,…](https://www.youtube.com/watch?v=a_c2mBMKuBE) | KBS Kpop | 1,057,213 | 29,591 | 2.80% | 0.558 |
| 13 | 무대 영상 | [[앵콜캠4K] 리센느 'LOVE ATTACK' 인기가요 1위 앵콜 직캠 (RES…](https://www.youtube.com/watch?v=rzfjou7vPP0) | SBSKPOP X INKIGAYO | 736,306 | 22,239 | 3.02% | 0.541 |
| 14 | 무대 영상 | [[4K] RESCENE(리센느) "LOVE ATTACK" Band LIVE Co…](https://www.youtube.com/watch?v=KRpt7OF4zso) | it's Live | 1,684,289 | 32,652 | 1.94% | 0.516 |
| 15 | 멤버들의 일상 | [[Re-log] 미나미의 휴가 브이로그 in JAPAN 🏠 | RESCENE (…](https://www.youtube.com/watch?v=97YE7zPrON8) | RESCENE | 684,300 | 19,395 | 2.83% | 0.511 |
| 16 | 멤버들의 일상 | [[Re-log] 까엉티비🐹 in LA US | RESCENE (리센느) vlog](https://www.youtube.com/watch?v=faDPwuKSOM4) | RESCENE | 1,255,421 | 27,280 | 2.17% | 0.508 |
| 17 | 멤버들의 일상 | [[Re-log] 미나미의 메이크업 교실🪞💄 with 메이 | RESCENE (리…](https://www.youtube.com/watch?v=V-Tz0gvDiG4) | RESCENE | 775,423 | 20,336 | 2.62% | 0.502 |
| 18 | TV 예능 | [[전참시] ★본방 놓친 리마인 주목★ 리센느 전참시 2시간 정주행 모음.zip …](https://www.youtube.com/watch?v=3fRTHjtYAes) | 픽잇 :Pick it | 2,795,874 | 20,354 | 0.73% | 0.440 |
| 19 | 생일 이벤트 | [HAPPY WONI DAY 🎂💚](https://www.youtube.com/watch?v=i3BCs-IcIl4) | RESCENE | 195,400 | 6,418 | 3.28% | 0.415 |
| 20 | 무대 영상 | [RESCENE(리센느) - LOVE ATTACK | M COUNTDOWN : P…](https://www.youtube.com/watch?v=QJeH6cRtdJA) | Mnet K-POP | 1,148,223 | 16,151 | 1.41% | 0.412 |
| 21 | TV 예능 | [【#TVPP】 음악방송 1위 후보 리센느의 대기실 비하인드 대방출✨| 전지적참견…](https://www.youtube.com/watch?v=v-6sJD4COF8) | TV-People | 3,082,565 | 9,505 | 0.31% | 0.405 |
| 22 | TV 예능 | [[전참시] 오늘도 밥은 줍니꺼? 먹는 것에 진심인 리센느✨ ＜With＞ 컴백 기…](https://www.youtube.com/watch?v=QI_aX8GPRvY) | 엠뚜루마뚜루 : MBC 공식 종합 채널 | 1,873,743 | 6,859 | 0.37% | 0.353 |
| 23 | TV 예능 | [[#간식게임] 눈이 부신 리센느를 숨김없이 보여줘✨ 대세 리센느와 함께한 여름 …](https://www.youtube.com/watch?v=1h4v7pLBwm0) | 놀라운 토요일 Amazing Saturday | 650,568 | 7,659 | 1.18% | 0.320 |
| 24 | 유튜브 출연 | [🎉구독자 10만 돌파!🎉(feat. 리센느RESCENE)](https://www.youtube.com/watch?v=4gqBmjnfJDc) | 김광규의 싱글이 좋아 | 307,826 | 5,955 | 1.93% | 0.318 |
| 25 | 생일 이벤트 | [메이 생일축하해줄사람!💗🥳🎉🎂](https://www.youtube.com/watch?v=zO7ndCNpJfs) | RESCENE | 95,819 | 2,997 | 3.13% | 0.315 |
| 26 | TV 예능 | [[전참시] 집에서도 에너지 넘치는 요즘 아이돌의 숙소 몰아보기 MBC260711…](https://www.youtube.com/watch?v=KZKQS4hjIYs) | 픽잇 :Pick it | 804,540 | 4,180 | 0.52% | 0.272 |
| 27 | TV 예능 | [💚안녕하세요원이입니다아형나왔습니다잘부탁드립니다💚 리센느(RESCENE) 원이 모…](https://www.youtube.com/watch?v=P0LNFoDtf74) | JTBC Voyage | 316,145 | 3,691 | 1.17% | 0.235 |

## 무대 영상 (5편)

1. **'SPECIAL STAGE' RESCENE(리센느) - LOVE ATTACK #엠카운트다운 EP.933 | Mnet 260618 방송**
   - `ajhEFz1zNMQ` · Mnet K-POP (방송사 공식) · long
   - 게시일 확인 필요 · 조회수 5,884,992 · 좋아요 96,322 · 댓글 확인 필요 · 점수 0.629
   - 고른 이유: 테마 최고 조회수, 역주행 시기 엠카 스페셜 무대
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=ajhEFz1zNMQ) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=ajhEFz1zNMQ)
2. **'COMEBACK' RESCENE (리센느) - Pretty Girl #엠카운트다운 EP.936 | Mnet 260709 방송**
   - `Esd-KkxROxA` · Mnet K-POP (방송사 공식) · long
   - 게시일 2026-07-09 · 조회수 3,603,577 · 좋아요 71,644 · 댓글 확인 필요 · 점수 0.611
   - 고른 이유: 컴백 무대, 반응률 2%로 무대 영상 중 높음
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=Esd-KkxROxA) / [제목·채널](https://www.youtube.com/watch?v=Esd-KkxROxA)
3. **[앵콜캠4K] 리센느 'LOVE ATTACK' 인기가요 1위 앵콜 직캠 (RESCENE Encore Fancam) @SBS Inkigayo 260726**
   - `rzfjou7vPP0` · SBSKPOP X INKIGAYO (방송사 공식) · long
   - 게시일 확인 필요 · 조회수 736,306 · 좋아요 22,239 · 댓글 확인 필요 · 점수 0.541
   - 고른 이유: 인기가요 1위 앵콜, 반응률 3.0%로 무대 영상 중 최고
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=rzfjou7vPP0) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=rzfjou7vPP0)
4. **[4K] RESCENE(리센느) "LOVE ATTACK" Band LIVE Concert 리센느와 잇라는 완벽하게 어울려💘 [it's KPOP LIVE 잇츠라이브]**
   - `KRpt7OF4zso` · it's Live (음악 라이브 공식 채널) · long
   - 게시일 확인 필요 · 조회수 1,684,289 · 좋아요 32,652 · 댓글 확인 필요 · 점수 0.516
   - 고른 이유: 밴드 라이브 버전, 라이브 실력을 보여 주는 대표 영상
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=KRpt7OF4zso) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=KRpt7OF4zso)
5. **RESCENE(리센느) - LOVE ATTACK | M COUNTDOWN : PLAY FESTA #엠카운트다운 EP.951 | Mnet 261028 방송**
   - `QJeH6cRtdJA` · Mnet K-POP (방송사 공식) · long
   - 게시일 확인 필요 · 조회수 1,148,223 · 좋아요 16,151 · 댓글 확인 필요 · 점수 0.412
   - 고른 이유: 최근(10/28) 무대인데 이미 100만 돌파
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=QJeH6cRtdJA) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=QJeH6cRtdJA)

## 안원잘부 (5편)

1. **갸루와 거제에 왔습니다 (거제 1편)**
   - `OrCOflk2QmQ` · 안녕하세요원이입니다잘부탁드립니다 (멤버 개인 공식) · long
   - 게시일 2026-05-22 · 조회수 16,401,124 · 좋아요 286,253 · 댓글 확인 필요 · 점수 0.760
   - 고른 이유: 채널 1위 영상, '거제 야호' 화제의 출발점
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=OrCOflk2QmQ) / [제목·채널](https://www.youtube.com/watch?v=OrCOflk2QmQ)
2. **저희도 리센느입니다...**
   - `5JZ5biQ_hMI` · 안녕하세요원이입니다잘부탁드립니다 (멤버 개인 공식) · long
   - 게시일 확인 필요 · 조회수 13,824,008 · 좋아요 228,630 · 댓글 확인 필요 · 점수 0.730
   - 고른 이유: 1,380만 조회, 반응률 1.65%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=5JZ5biQ_hMI) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=5JZ5biQ_hMI)
3. **미나미의 갸루라이브 메들리!**
   - `FcMaC8akSU8` · 안녕하세요원이입니다잘부탁드립니다 (멤버 개인 공식) · long
   - 게시일 확인 필요 · 조회수 11,237,723 · 좋아요 193,235 · 댓글 확인 필요 · 점수 0.713
   - 고른 이유: 미나미 '갸루' 캐릭터 대표 영상, 반응률 1.72%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=FcMaC8akSU8) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=FcMaC8akSU8)
4. **A day out in Seongsu before the blowout (사투리 2편, 페이지에 영어 제목으로 표시됨)**
   - `JJBf0jCcfrQ` · 안녕하세요원이입니다잘부탁드립니다 (멤버 개인 공식) · long
   - 게시일 2026-05-29 · 조회수 10,073,505 · 좋아요 170,722 · 댓글 확인 필요 · 점수 0.698
   - 고른 이유: 1,000만 돌파, 반응률 1.69%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=JJBf0jCcfrQ) / [제목·채널](https://www.youtube.com/watch?v=JJBf0jCcfrQ)
5. **I tried speaking only in dialect all day long. (사투리 1편, 페이지에 영어 제목으로 표시됨)**
   - `NS7tSrMrWsc` · 안녕하세요원이입니다잘부탁드립니다 (멤버 개인 공식) · long
   - 게시일 2026-05-01 · 조회수 13,543,435 · 좋아요 169,729 · 댓글 확인 필요 · 점수 0.683
   - 고른 이유: 사투리 시리즈 1편, 채널 초기 대표작
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=NS7tSrMrWsc) / [제목·채널](https://www.youtube.com/watch?v=NS7tSrMrWsc)

## TV 예능 (6편)

1. **[전참시] ★본방 놓친 리마인 주목★ 리센느 전참시 2시간 정주행 모음.zip MBC260808방송 #전지적참견시점 #리센느**
   - `3fRTHjtYAes` · 픽잇 :Pick it (공식 여부 확인 필요) · long
   - 게시일 확인 필요 · 조회수 2,795,874 · 좋아요 20,354 · 댓글 확인 필요 · 점수 0.440
   - 고른 이유: 전참시 리센느 특집 2시간 통합본, 좋아요가 테마 중 가장 많음
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=3fRTHjtYAes) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=3fRTHjtYAes)
2. **【#TVPP】 음악방송 1위 후보 리센느의 대기실 비하인드 대방출✨| 전지적참견시점 | MBC 260808 방송**
   - `v-6sJD4COF8` · TV-People (MBC 계열로 보임(공식 여부 확인 필요)) · long
   - 게시일 확인 필요 · 조회수 3,082,565 · 좋아요 9,505 · 댓글 확인 필요 · 점수 0.405
   - 고른 이유: 테마 최고 조회수(308만), 음방 대기실 비하인드
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=v-6sJD4COF8) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=v-6sJD4COF8)
3. **[전참시] 오늘도 밥은 줍니꺼? 먹는 것에 진심인 리센느✨ ＜With＞ 컴백 기념 회식 영상 모음집ㅣ#리센느 MBC260808방송**
   - `QI_aX8GPRvY` · 엠뚜루마뚜루 : MBC 공식 종합 채널 (방송사 공식) · long
   - 게시일 확인 필요 · 조회수 1,873,743 · 좋아요 6,859 · 댓글 확인 필요 · 점수 0.353
   - 고른 이유: MBC 공식 채널, 전참시 리센느 특집 회식 편
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=QI_aX8GPRvY) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=QI_aX8GPRvY)
4. **[#간식게임] 눈이 부신 리센느를 숨김없이 보여줘✨ 대세 리센느와 함께한 여름 방학🏖️ #highlight#놀라운토요일 | amazingsaturday EP.430**
   - `1h4v7pLBwm0` · 놀라운 토요일 Amazing Saturday (방송사 공식(tvN)) · long
   - 게시일 확인 필요 · 조회수 650,568 · 좋아요 7,659 · 댓글 확인 필요 · 점수 0.320
   - 고른 이유: tvN 놀토 리센느 편, 케이블 예능 중 최고 조회수
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=1h4v7pLBwm0) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=1h4v7pLBwm0)
5. **[전참시] 집에서도 에너지 넘치는 요즘 아이돌의 숙소 몰아보기 MBC260711방송 #전지적참견시점 #리센느 #올데이프로젝트 #아일릿**
   - `KZKQS4hjIYs` · 픽잇 :Pick it (공식 여부 확인 필요) · long
   - 게시일 확인 필요 · 조회수 804,540 · 좋아요 4,180 · 댓글 확인 필요 · 점수 0.272
   - 고른 이유: 대표 결정(15:4x)으로 포함, 여러 그룹 숙소 합본 중 리센느 장면
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=KZKQS4hjIYs) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=KZKQS4hjIYs)
6. **💚안녕하세요원이입니다아형나왔습니다잘부탁드립니다💚 리센느(RESCENE) 원이 모아보기｜아는 형님｜JTBC 260620 방송**
   - `P0LNFoDtf74` · JTBC Voyage (방송사 공식(JTBC)) · long
   - 게시일 확인 필요 · 조회수 316,145 · 좋아요 3,691 · 댓글 확인 필요 · 점수 0.235
   - 고른 이유: JTBC 아는형님 원이 모아보기, 안원잘부와 이어지는 영상
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=P0LNFoDtf74) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=P0LNFoDtf74)

## 유튜브 출연 (4편)

1. **[리무진서비스] EP.211 리센느 미나미 | RESCENE MINAMI | Runaway, 나였으면, My Gospel, Timeless**
   - `SW7M6MdlrlU` · KBS Kpop (방송사 공식(유튜브 전용 콘텐츠)) · long
   - 게시일 확인 필요 · 조회수 1,598,556 · 좋아요 42,671 · 댓글 확인 필요 · 점수 0.592
   - 고른 이유: 테마 최고 조회수·반응률 2.7%, 미나미 보컬
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=SW7M6MdlrlU) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=SW7M6MdlrlU)
2. **거제 야호가 문특에 왔습니다 (w. 리센느 원이, 미나미, 제나)**
   - `17t9izNAYVE` · MMTG 문명특급 (방송사 계열 유튜브 공식) · long
   - 게시일 확인 필요 · 조회수 1,076,984 · 좋아요 31,504 · 댓글 확인 필요 · 점수 0.574
   - 고른 이유: '거제 야호' 화제를 다룬 문명특급 출연
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=17t9izNAYVE) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=17t9izNAYVE)
3. **[리무진서비스] EP.240 리센느 리브 | RESCENE LIV | With, 그댄 달라요, 내 생에 아름다운, 왜 그래**
   - `a_c2mBMKuBE` · KBS Kpop (방송사 공식(유튜브 전용 콘텐츠)) · long
   - 게시일 확인 필요 · 조회수 1,057,213 · 좋아요 29,591 · 댓글 확인 필요 · 점수 0.558
   - 고른 이유: 리브 단독 출연, 반응률 2.8%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=a_c2mBMKuBE) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=a_c2mBMKuBE)
4. **🎉구독자 10만 돌파!🎉(feat. 리센느RESCENE)**
   - `4gqBmjnfJDc` · 김광규의 싱글이 좋아 (출연자 개인 채널(공식 여부 확인 필요)) · long
   - 게시일 확인 필요 · 조회수 307,826 · 좋아요 5,955 · 댓글 확인 필요 · 점수 0.318
   - 고른 이유: 다른 유튜버 채널 출연 사례(규모는 작음)
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=4gqBmjnfJDc) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=4gqBmjnfJDc)

## 멤버들의 일상 (4편)

1. **[Re-log] 먹짱 원짱, 대만에 가다 🍴 | RESCENE (리센느) vlog**
   - `xclVi9zCFdY` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 422,920 · 좋아요 16,466 · 댓글 확인 필요 · 점수 0.573
   - 고른 이유: 반응률 3.9%로 전체 최고 수준
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=xclVi9zCFdY) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=xclVi9zCFdY)
2. **[Re-log] 미나미의 휴가 브이로그 in JAPAN 🏠 | RESCENE (리센느) vlog**
   - `97YE7zPrON8` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 684,300 · 좋아요 19,395 · 댓글 확인 필요 · 점수 0.511
   - 고른 이유: 미나미 일본 휴가, 반응률 2.8%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=97YE7zPrON8) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=97YE7zPrON8)
3. **[Re-log] 까엉티비🐹 in LA US | RESCENE (리센느) vlog**
   - `faDPwuKSOM4` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 1,255,421 · 좋아요 27,280 · 댓글 확인 필요 · 점수 0.508
   - 고른 이유: 공식 브이로그 중 최고 조회수
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=faDPwuKSOM4) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=faDPwuKSOM4)
4. **[Re-log] 미나미의 메이크업 교실🪞💄 with 메이 | RESCENE (리센느) vlog**
   - `V-Tz0gvDiG4` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 775,423 · 좋아요 20,336 · 댓글 확인 필요 · 점수 0.502
   - 고른 이유: 두 멤버 일상 케미, 반응률 2.6%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=V-Tz0gvDiG4) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=V-Tz0gvDiG4)

## 생일 이벤트 (3편)

1. **리뿌 생일 라이브에 오신 걸 환영합니다💝**
   - `fCrQXP_2u3U` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 1,372,790 · 좋아요 35,317 · 댓글 확인 필요 · 점수 0.563
   - 고른 이유: 리브 생일 라이브, 생일 콘텐츠 중 압도적 조회수
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=fCrQXP_2u3U) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=fCrQXP_2u3U)
2. **HAPPY WONI DAY 🎂💚**
   - `i3BCs-IcIl4` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 195,400 · 좋아요 6,418 · 댓글 확인 필요 · 점수 0.415
   - 고른 이유: 원이 생일 공식 콘텐츠, 반응률 3.3%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=i3BCs-IcIl4) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=i3BCs-IcIl4)
3. **메이 생일축하해줄사람!💗🥳🎉🎂**
   - `zO7ndCNpJfs` · RESCENE (리센느 공식) · long
   - 게시일 확인 필요 · 조회수 95,819 · 좋아요 2,997 · 댓글 확인 필요 · 점수 0.315
   - 고른 이유: 메이 생일 공식 콘텐츠, 반응률 3.1%
   - 출처: [숫자](https://returnyoutubedislikeapi.com/votes?videoId=zO7ndCNpJfs) / [제목·채널](https://noembed.com/embed?url=https://www.youtube.com/watch?v=zO7ndCNpJfs)

## 확인 비율

- 뽑은 영상 27편 × 숫자 3개(조회수·좋아요·댓글) = 81칸 중 54칸 확인(67%). 조회수·좋아요는 27편 모두 확인, 댓글은 0편.
- 게시일은 27편 중 4편 확인.
- TV 예능 방은 대표 결정(케이블 예능 추가·숙소 합본 포함)으로 6편.
- 생일 이벤트 방은 공식 영상 3편(리브·메이·원이). 미나미·제나는 못 찾음.

## 참고: 공식 뮤직비디오 숫자 (지금 방 구성에는 없음)

| 영상 | 조회수 | 좋아요 |
|---|---:|---:|
| [RESCENE (리센느) 'LOVE ATTACK' Official MV](https://www.youtube.com/watch?v=9XttLI0oH0I) | 32,495,554 | 266,482 |
| [RESCENE (리센느) 'Bloom' Official MV](https://www.youtube.com/watch?v=MC6-82GRK5I) | 28,112,365 | 62,918 |
| [RESCENE (리센느) 'Deja Vu' Official MV](https://www.youtube.com/watch?v=ZbO9PBdFRdc) | 23,744,769 | 143,650 |
| [RESCENE (리센느) 'Runaway' Official MV](https://www.youtube.com/watch?v=rsZwrTNklos) | 21,982,329 | 82,804 |
| [RESCENE (리센느) 'Heart Drop' Official MV](https://www.youtube.com/watch?v=ByX8EZq8500) | 19,319,041 | 48,310 |
| [RESCENE (리센느) 'Glow Up' Official MV](https://www.youtube.com/watch?v=h0xUtrb_JBc) | 16,131,025 | 105,689 |
| [RESCENE (리센느) 'New World' Official MV](https://www.youtube.com/watch?v=QNXeGm-Wkms) | 992,043 | 24,213 |

※ 'Mood' MV 후보(h63TV1G2gzc)는 RYD 값이 조회수 46으로 나와 공식 영상인지 의심스러워 뺐다.

## 확인 대기 목록 (오늘 밤 데스크톱 크롬에서)

영상을 열어 설명란 위쪽(조회수·게시일), 좋아요 버튼 숫자, 댓글 제목 옆 숫자를 적으면 된다.

| # | 방 | 영상 주소 | 확인할 것 |
|---|---|---|---|
| 1 | 무대 영상 | https://www.youtube.com/watch?v=ajhEFz1zNMQ | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 2 | 무대 영상 | https://www.youtube.com/watch?v=Esd-KkxROxA | 댓글 수, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 3 | 무대 영상 | https://www.youtube.com/watch?v=KRpt7OF4zso | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 4 | 무대 영상 | https://www.youtube.com/watch?v=QJeH6cRtdJA | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 5 | 무대 영상 | https://www.youtube.com/watch?v=rzfjou7vPP0 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 6 | 안원잘부 | https://www.youtube.com/watch?v=OrCOflk2QmQ | 댓글 수, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 7 | 안원잘부 | https://www.youtube.com/watch?v=5JZ5biQ_hMI | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 8 | 안원잘부 | https://www.youtube.com/watch?v=NS7tSrMrWsc | 댓글 수, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 9 | 안원잘부 | https://www.youtube.com/watch?v=FcMaC8akSU8 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 10 | 안원잘부 | https://www.youtube.com/watch?v=JJBf0jCcfrQ | 댓글 수, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 11 | TV 예능 | https://www.youtube.com/watch?v=QI_aX8GPRvY | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 12 | TV 예능 | https://www.youtube.com/watch?v=v-6sJD4COF8 | 댓글 수, 게시일, 채널 공식 여부, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 13 | TV 예능 | https://www.youtube.com/watch?v=3fRTHjtYAes | 댓글 수, 게시일, 채널 공식 여부, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 14 | TV 예능 | https://www.youtube.com/watch?v=KZKQS4hjIYs | 댓글 수, 게시일, 채널 공식 여부, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 15 | TV 예능 | https://www.youtube.com/watch?v=1h4v7pLBwm0 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 16 | TV 예능 | https://www.youtube.com/watch?v=P0LNFoDtf74 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 17 | 유튜브 출연 | https://www.youtube.com/watch?v=SW7M6MdlrlU | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 18 | 유튜브 출연 | https://www.youtube.com/watch?v=17t9izNAYVE | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 19 | 유튜브 출연 | https://www.youtube.com/watch?v=a_c2mBMKuBE | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 20 | 유튜브 출연 | https://www.youtube.com/watch?v=4gqBmjnfJDc | 댓글 수, 게시일, 채널 공식 여부, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 21 | 멤버들의 일상 | https://www.youtube.com/watch?v=faDPwuKSOM4 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 22 | 멤버들의 일상 | https://www.youtube.com/watch?v=V-Tz0gvDiG4 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 23 | 멤버들의 일상 | https://www.youtube.com/watch?v=97YE7zPrON8 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 24 | 멤버들의 일상 | https://www.youtube.com/watch?v=xclVi9zCFdY | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 25 | 생일 이벤트 | https://www.youtube.com/watch?v=fCrQXP_2u3U | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 26 | 생일 이벤트 | https://www.youtube.com/watch?v=i3BCs-IcIl4 | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 27 | 생일 이벤트 | https://www.youtube.com/watch?v=zO7ndCNpJfs | 댓글 수, 게시일, 조회수·좋아요 화면값 대조(RYD 캐시) |
| 28 | 생일 이벤트 | https://www.youtube.com/@RESCENE_official/search?query=생일 | 미나미·제나 생일 공식 콘텐츠 찾기(검색 3번으로 못 찾음, 팬 채널 SCENEBAG 영상은 조회수가 낮아 제외), video_id·조회수·좋아요·댓글 |
| 29 | 무대 영상(후보) | https://www.youtube.com/watch?v=aDHmmrfizIE | 채널 이름·공식 여부(조회수 755,918·좋아요 16,801은 RYD로 확인) |
| 30 | 무대 영상(후보) | https://www.youtube.com/watch?v=nQSBOVxs_YY | 채널 이름·공식 여부(조회수 548,485·좋아요 16,329는 RYD로 확인) |
| 31 | TV 예능 | https://www.youtube.com/watch?v=KZKQS4hjIYs | 리센느 장면 시작 시각(start 초) |
| 32 | TV 예능(후보) | https://www.youtube.com/watch?v=EnJjpUIOWGk | 아는형님 프로미스나인X리센느 숙소 편(JTBC Voyage, 조회수 399,752·좋아요 4,368) — 방이 6편이라 뺐음, 넣을지 대표 판단 |
| 33 | TV 예능(후보) | https://www.youtube.com/watch?v=pWTBJV0OrqU | 전참시 선공개(MBCentertainment, 조회수 245,400·좋아요 7,540) — 케이블 예능에 자리를 내주고 뺐음 |
