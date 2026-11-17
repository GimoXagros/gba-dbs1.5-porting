# Port recovery audit

## 2026-11-17 v78 후속 — E5 최초 생성과 화면 복귀 확인

주 빌드와 ROM은 그대로다. 수정 전8C72에서 ID14 시작 번호B054 → 명령FFFFFFFF →
실제 B 포인터A02004E3 → 실제 종류9F0000E5 → 충돌 목록00E5 쓰기를 관찰했다.
쓰기 전후 같은 행의0008→00E5 변경은 독립 검수D7663FD0으로 확인했다.
동일 입력의 현재C91은 원본 번호115와 유효한 명령을 선택했고, 실제 B 읽기가0이어서
정상적으로 빈 충돌 경로를 처리했다. v78의15명 진화 표 복원이 이 생성 원인을 교정한다.
과거 timeout의 사각형 겹침·잘못된 분기까지 같은 실행으로 재현한 것은 아니다.

종료 직후 P1 미표시는 원본과 같은 진화 종료 깜박임이었다. 뒤120프레임의 좌표와
카메라는 일정했고,58프레임부터 계속 표시됐다. 카메라나 그림을 임의 수정하지 않았다.
모든 새 실행은 창 없이 일반 입력으로 수행했다. 이미 검증된 음악·Shoot 시험과 전체
빌드는 반복하지 않았다. **최종 완성본은 아니다.** ID13 공중 재도약 구현을 이어간다.

[원인·실제 비교와 남은 범위](records/e5-first-producer-and-render-v78-20261117.md).

## 2026-11-16~17 v78 — 추가 캐릭터 진화 표와 세 곡 실전 검증

구현 후보 ROM은 16MiB이며 SHA256은
`C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1`이다.
기존 11명 기준 진화 표 세 곳을 WSC 1.5의 15명 자료로 확장하고,
현재 기본 모드의 임프몬 진화 접촉 경로를 연결했다. 음악 교체를 막는 우회 처리는 넣지 않았다.

- 6C·6D·6F 모두 실제 대전에서 정지·재개와 원래 스테이지 음악 복귀를 확인했다.
  독립 검수 `76742352` / `286E9188` / `F72A105B`.
- 수정 전 CPU 임프몬은 공중 종료 번호 `4000`, ID14는 시작 번호 `B054`를
  읽어 잘못된 명령 포인터와 음악04 요청을 만들었다. 실제 선택과 요청을 함께 기록했다.
  수정 후에는 원본 번호를 사용하며, ID14도 동일한 일반 조작으로 정지·재개·복귀를
  독립 검수 `C21553F0`로 확인했다.
- 11월17일 ID14 공중 종료도 일반 점프로 관찰했다. 수정 전 E3A0→음악04와
  수정 후 정상25→음악 복귀를 독립 검수 `7AD91F37`로 비교했다. ROM 변경은 없다.
- E5는 해결 판정하지 않는다. ID14의 잘못된 시작·공중 종료 번호 실행에서도 E5는 없었다.
  `04000020` 값은 보호된 BIOS 읽기에서도 발생하므로, 과거 ROM 주소 가설만으로
  원인을 확정할 수 없다. 최초 E5 생성자와 실제 실패 메타데이터는 계속 열린 항목이다.
- 두 독립 생성 빌드의 파일325개와 매니페스트 항목125개가 일치한다. 검수 `C59C5FA1`.
  A는 전체 종료0이며, B는 생성 후 중단되어 기존309개를 보존한 채 남은 검증만 재개했다.
  B 원래 종료 코드는 확인할 수 없고, 재개 검증은 종료0이다. 새로 파일을 복사하지 않았다.
- 모든 실행은 창을 표시하지 않았다. CPU 임프몬 대전에는 승인된 D스피릿 보조만
  사용했고, ID14 시험은 메모리 쓰기 없이 일반 조작으로 진행했다. 제공 세이브는 읽지 않았다.
- **최종 완성본이 아니다.** 전체 콘텐츠·일반 카메라·네 언어·저장/리셋·안정성 및
  음악의 완전한 청감 일치에 대한 최종 QA가 남아 있다.

[이번 통합과 실제 증거](records/evolution-runtime-integration-v78.md) ·
[전체 산출물 검수와 재개 범위](records/repro-v78-inventory-qa-20261117.md) ·
[임프몬 동작 표 실행 검수](records/evolution-music-6f-event-table-runtime-qa-20261116.md) ·
[ID14 잘못된 번호 실제 기록](records/evolution-id14-malformed-entry-actual-20261116.md).

## 2026-11-16 v77 — 원더스완 진화 BGM 통합

현재 주 빌드는 16MiB이며 ROM SHA256은
`C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278`이다.
원본의 네 진화 악보·파형과 캐릭터별 선택을 연결했고, 새 네 곡이 일시정지용
현재 음악 기록에서도 처리되도록 고쳤다. 시험용 전체 음악 정지 무효화는 포함하지 않는다.

- 두 빌드 c/d의 완료 매니페스트, 산출물 319개와 항목 123개를 대조했다.
  추가로 생긴 d의 세이브 하나는 읽거나 해시하지 않고 제외·보존했다.
  당시 프로세스 종료 코드는 남아 있지 않다. 독립 산출물 검수 `0EBBA5EF`.
- 원본·GBA 네 곡씩의 창 없는 재생 기록은 `E9864FFB`로 검수했다.
  신호 잘림이 없고 GBA 종료 시점은 예상값과 2.04ms 이내다.
  템포·음량·좌우 배분 양자화와 파형 위상 차이는 남아 있다.
- 실제 한국어 설정→일반 전투→WIN은 `19A5D7B9`/`DBD0CC1A`로 검수했다.
  화면 8장, 전체 EWRAM·화면 메모리·128줄 진행 기록이 v76과 같다.
  IWRAM의 음악 상태·복사된 코드·스택 값 차이는 전부 기록했으며 전체 RAM 동일을 주장하지 않는다.
- 실제 진화 요청 6E가 9076에 재생되고, 진화 종료 후 10365에 스테이지 10 음악으로
  복귀했다. 별도 실제 시험 `68A8960E`에서는 새 곡 6E의 9077 정지→9112 재개→
  10400 스테이지 음악 복귀를 확인했다. 감시한 RAM 복사본 진입점 두 곳은
  실행 0회다. 이 한 경로의 확인을 모든 곡·모든 간접 호출의 검증으로 넓히지 않는다.
- 앞서 v76에서 가장 이른 counter1 IRQ도 실제 검수 `9472B613`을 통과했다.
  하나의 실행 주기에서 8회 일치·최종 호출을 확인했다. 원본 저장 상태와의
  오디오 상태 6바이트 차이는 숨기지 않았으며, v77의 Shoot 재실행을 뜻하지 않는다.
- **최종 완성본은 아니다.** E5 최초 발생 원인, 일반 움직임·카메라 영역,
  전체 콘텐츠와 네 언어 최종 QA, 음악의 완전한 청감 일치는 남아 있다.

[음악 통합](records/original-evolution-bgm-integration-v77.md) ·
[빌드 검수](records/repro-v77-inventory-qa-20261116.md) ·
[실제 전투·음악](records/result-v77-capture-qa-20261116.md) ·
[실제 정지·재개](records/evolution-music-pause-capture-qa-20261116.md).

## 2026-11-10 v76 — Shoot 실제 종료·후속 모드 연결

현재 주 빌드의 ROM SHA256은
`280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7`이다.
종료 화면이 적용할 배치값을 검사하고, 실제 사용 직전에 화면 상태를 짧게
재검사하도록 고쳤다. v75 대비 84바이트 범위에서 69바이트가 바뀌며, 역변환하면
v75 전체 ROM과 일치한다. 아래 절은 각 시점의 기록이다.

- 원본부터 만든 두 전체 빌드가 모두 통과했다. 310개 파일과 120개 매니페스트
  항목이 일치한다. 기존 v75의 307개 경로를 모두 보존했다. 검수 `130361D1`.
- 창 없는 실제 Shoot에서 공격 격파→종료 장면→IRQ 8회 일치·최종 호출→
  화면 위치 쓰기→객체·컨트롤러 정리→후속 mode8까지 도달했다. 69935의 기존
  저장 상태까지 코어 전체 21개가 이전 실행과 완전히 같고, 70441의 정리 요청은
  아직 mode7, 70443에서 실제 mode8이다. 독립 검수 `9F909134`.
- 화면 위치 검증은 쓰기 전용 레지스터를 읽는 잘못된 판정을 제거했다. 실제
  STRH 명령 전후와 복귀 시점·RAM 보관값으로 70→68 쓰기를 입증했다.
  기존 실패 기록은 그대로 남겼으며 이 수정은 게임 ROM을 바꾸지 않는다.
- 한국어 설정→일반 전투→WIN 회귀 검증도 통과했다. 화면 8개, 전체 메모리·
  화면 기록과 128줄 실행 기록·시점이 v75와 같다. 검수 `2547A556`/`1E2C54B1`.
  소리는 꺼져 있었으며 저장된 출력 방식은 이번 3, 이전 1로 차이를 기록했다.
- 보스 영역의 반복 글자 무늬는 기존 원더스완 캡처와 이전 GBA 빌드에도 있다.
  해당 BG1 타일 16KiB가 원본 변환과 일치한다. 새 화면 손상으로 단정하지 않으며
  전환의 모든 시점을 원본과 같은 픽셀이라고 주장하지도 않는다.
- **최종 완성본은 아니다.** 실제 첫 IRQ 검증은 counter143이며 가장 이른
  counter1 시점은 별도 확인 중이다. 일반 움직임·카메라 영역, 기존 E5,
  전체 콘텐츠와 4개 언어 최종 QA가 남아 있다.
- 추가 요청한 원더스완 진화 BGM 네 종류는 별도 16MiB 개발본 `DD6D73B5`에
  원본 악보·파형으로 구성했고 독립 구조 검수 `B8D1D704`를 통과했다.
  아직 주 빌드에 넣지 않았으며 실제 음원 비교·곡명 식별·게임 재생 검증이 남았다.

[전체 빌드](records/repro-v76-inventory-qa-20261110.md) ·
[실제 종료](records/shoot-native-terminal-display-store-capture-qa-20261110.md) ·
[일반 전투](records/result-v76-capture-qa-20261110.md) ·
[원본 음악](records/wsc-original-evolution-bgm-20261110.md).

## 2026-11-10 v75 — 종료 호출·소속 보스 검사 수정 통합

현재 주 빌드는 v75이며 ROM SHA256은
`46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B`다.
팔레트 보조 함수를 자기 자신으로 호출하던 4곳과 보조 객체의 소속을 잘못 읽던
1곳을 고쳤다. v74 대비 20바이트를 선언하고 실제 13바이트가 달라졌으며,
역변환하면 v74 전체 ROM과 일치한다. 아래 절은 각 시점의 기록이다.

- 원본부터 만든 전체 빌드 두 개가 모두 통과했다. 307개 파일과 각 119개
  매니페스트 항목이 완전히 같다. 독립 검수 `B1A1B933`.
- 창 없는 한국어 설정→일반 전투→WIN 검증을 통과했다. 화면 8개, 전체 메모리·
  화면 레지스터와 128줄 실행 기록·시점이 v74와 같다. 검수 `49377964`/`820002D2`.
  사운드 출력 방식은 실행 전 요청 3과 종료 후 저장값 1이 달랐고 소리는 꺼져 있었다.
  이를 숨기거나 사운드 재현 검증으로 간주하지 않는다.
- Shoot는 실제 격파→종료 동작→화면 전환 대기까지 진행했다. 소속 검사 수정 전후의
  초기 상태와 저장 상태 18개는 ROM CRC 비교값 외에는 코어 전체가 같았다.
- 남은 중단 원인도 실제 두 프레임에서 확인했다. 69932에서 화면 흔들림 값이 먼저
  생기고 검사가 거부된 뒤 지워졌다. 대체 화면 함수가 배치값을 바꿔 69933의 다음
  검사도 막았다. 읽기 기록 20개를 추가해도 저장 상태 20개와 기존 실행 기록은
  완전히 같았다. 검수 `324821AF`/`F25BB784`.
- 다음 작업은 적용 예정 배치값 검사와 짧은 실행 직전 재검사다. 무거운 검사를
  IRQ 안으로 옮기면 시간 제한을 어길 수 있어 채택하지 않았다. **종료 IRQ·정리·
  mode8 도달, 기존 E5, 전체 콘텐츠와 4개 언어 최종 QA는 아직 미완료다.**

[빌드 검수](records/repro-v75-inventory-qa-20261110.md) ·
[일반 전투 검수](records/result-v75-capture-qa-20261110.md) ·
[종료 중단의 실제 순서](records/shoot-native-terminal-bg-epoch-capture-qa-20261110.md).

## 2026-11-09 v74 — 실제 진입·조작·적중 통합, 종료 중단 추적

현재 주 빌드는 v74다. ROM SHA256은
`1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC`이다.
원본 순서의 진입 연결, 대상 포인터 보존, Shoot HUD 분기·비치명타 처리와
자식 공격의 원본 상대 주소 수정을 통합했다. 아래 이전 절은 당시 기록이다.

- 원본부터 만든 두 전체 빌드의 301개 파일과 각각 117개 매니페스트 항목이 일치했다.
  19곳의 변경을 역변환하면 v73 전체 ROM으로 돌아간다. 검수 `02DAA803`.
- 창 없는 한국어 설정→일반 전투→WIN 검증을 통과했다. 화면 8개, 전체 게임·그림
  메모리와 실행 기록·시점이 v73과 같다. 이번에는 IWRAM 차이도 없다. 검수 `70D002DE`/`B2D579D9`.
- 실제 Shoot에서는 새 A 입력·점프에 이어, 69014프레임에 실제 공격으로 보스 체력
  37→36을 확인했다. 점멸 타이머 8이 자연스럽게 소진되고 69022에 끝났다. 검수 `2A94A337`.
- 승인된 보스 체력 1회 수정(37→1) 뒤 실제 공격으로 격파하고 종료 장면에 진입했다.
  팔레트 함수의 자기 자신을 호출하는 분기 4곳을 별도 수정본 `FF3A9D54…E3590A8`에서
  고쳤다. 같은 상태·입력으로 실제 종료 동작과 전환 대기까지 진행했다. 검수 `91E07B23`.
  다음 중단은 보조 객체의 상대(+18)를 소속 보스(+28)로 잘못 읽는 검사다. 한 곳을
  고친 `46B37BAA…AB3C22B`는 독립 검수·실행 전이다. 두 수정은 아직 주 빌드에
  통합하지 않았다. IRQ·정리·mode8 완료는 아직 관찰하지 못했다.
- **최종 완성본이 아니다.** 기존 E5, 종료의 나머지 경로, 움직이는/낮은 Y 계열,
  전체 콘텐츠와 4개 언어 최종 검증은 남아 있다. 저장 복원의 사운드·통신 상태 차이는
  그대로 기록하며 전체 코어 일치를 주장하지 않는다. 검증된 원본 플레이는 반복하지 않는다.

[전체 빌드 검수](records/shoot-native-v74-build-qa-20261109.md) ·
[일반 전투 검수](records/result-v74-runtime-qa-20261109.md) ·
[실제 적중 검수](records/shoot-positive-hit-aim-capture-qa-20261109.md) ·
[종료 관찰 절차](records/shoot-native-terminal-probe-20261109.md).

## 2026-11-09 첫 조작 확인·공격 판정 주소 수정 중

Shoot 조작 대기68927에서 새 A 입력이 실제 캐릭터로 전달되고,68933에 점프를
시작하는 것을 창 없이 확인했다. 체력4/37을 유지했고 독립 검수EEDA506A를 통과했다.

후속 공격 검증은69165에서 잘못된 충돌 주소를 포착해 중단했다. 원인은 자식 공격
데이터의 로컬 주소010C에 구버전 전용 주소 규칙을 적용한 것이었다. 현재 생성 항목
163개 중8개 참조가 영향받는다. 원본의 type19 판정 데이터를 복사한 별도 수정본
`1477F90E…941FAC`은 독립 검수281C43DF를 통과했다. 같은 초기 상태와 입력으로
이전 오류 지점을 지나1200프레임까지 진행했으며, 검수68786697로 확인했다.
아직 적중은 없었으므로 자동 조작의 방향·공격 간격을 고쳐 적중·점멸 종료를 검증한다.
이 실패는 체력0 패배나 원래 E5 사례와 구분한다. 주 빌드는 여전히 v73이며 완성본이 아니다.

[첫 입력 검수](records/shoot-first-native-input-qa-20261109.md) ·
[새 중단 원인](records/shoot-child-attack-pointer-cause-20261109.md).

## 2026-11-09 실제 Shoot 초기화·조작 대기 도달

별도 개발 ROM `84D6FA3F…CA43B`에서 대상 포인터를 함수 호출 뒤에도 보존하도록
5곳을 고쳤다. 실제 보스 격파 뒤 초기화67786→67788, 체력4 복원68815,
컨트롤러 복귀68926, 조작 대기68927을 창 없이 관찰했다. 새 치트 쓰기는0회다.
주 빌드는 아래 v73 그대로이며, 첫 입력·비치명타·종료는 이어서 검증한다.

저장 복원 시 CPU·게임/그림 메모리는 같지만 사운드·통신 상태12바이트가 달랐다.
수정 전 ROM의 무진행 대조에서도 동일하게 재현됐다. 코드 수정과 무관함을
확인했지만 원본 저장 전체 일치 검사는 실패로 유지한다. E5와 최종 완성은 미해결이다.

[실행 결과와 독립 검수](records/shoot-native-entry-replay-capture-qa-20261109.md).

## 2026-11-09 v73 — 종료 IRQ·보스 격파 연결 통합

정지한 기본 ID0 계열의 종료 화면 IRQ와 stage11 치명타 콜백을 주 빌드에 연결했다.
개발 ROM은 `6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7`이다.
새 RAM·태스크 없이 5곳을 변경했고, 역변환하면 v72 전체 ROM과 일치한다.

- 원본부터 만든 두 전체 빌드: 295개 파일과 각 115개 매니페스트 항목 일치.
- 창 없는 한국어 설정→일반 전투→WIN 회귀 검증 통과. 화면 8개와 게임·그림 메모리,
  실행 기록·시점이 v72와 같다. IWRAM 스택 7–8바이트 차이는 기록했다.
- 실제 화면 처리는 1번째 줄에 호출되므로 긴 검사는 앞선 화면 준비 단계에 둔다.
  실제 FFFFF000 우선순위, GBA 160줄, 모자이크, 종료 후 mode8도 검수했다.
- **완성본은 아니다.** Shoot 외부 진입·움직이는 진입 계열·비치명타 연결·E5 원인,
  전체 콘텐츠·번역과 최종 QA는 남아 있다. 원본의 건강한 진입·실제 격파·mode8 종료
  관찰은 이미 끝났으므로 반복하지 않고 별도 개발 ROM의 실제 진입 관찰로 이어간다.

[통합 기록과 고정 해시](records/shoot-terminal-integration-v73.md).


## 2026-11-09 actual preactivation failure and verified checkpoint replay

The new baseline and genuine checkpoint replay completed normally. FIRST already had HP0/event005B
at the actual boss hit/root5 (91708). The following scene saved0 at payload2334+46, temporarily set
HP1, then restored0 at93549 before input activation93570. The earlier carried-survivor-HP1 inference
is withdrawn; a fresh jump cannot repair this captured entry. No3030 damage pair occurred.

The restored complete native+managed core equals the genuine checkpoint. All2810 recorded FIRST/stage
contexts and seven shared activation RAM/SRAM/PNG outputs match. Original save and GBA v72 are unchanged.
The formerly unobserved terminal/DI chain is now observed below. Ordinary Continue now produced a genuine fresh stage7 checkpoint at
core95931: P1HP8/bossHP44/pending damage0 and released controls. Independent capture audit E56B9C19
verified the complete saved core and23files/sixpins, with no P1 HP or progression writes. Next: actual
positive-P1-HP hit/root5 and healthy stage11 entry. This subsequent observation also passed: direct
FIRST hit/root5 at97022 retained P1HP4; source saved4 at97023 into scene2114+46, and actual stage11
checkpoint97712 retains4 while temporary currentHP is1. Independent fullcapture audit691A479B
passed. The subsequent actual second-boss direct hit/root5 occurred at99458 with P1HP4, natural
terminal at99459 and consumed0DEC pair at100569. Independent9989AD1B verified the full chain.
Observed DI2214 aliases graphics RAM521E/F and consumed0, but this first read is offscreen line146
(k117). The readonly continuation now reaches mode8 at101035 after465 neutral frames. Independent
8C5480CC verifies106 paired/full-snapshot potential-visible samples and26272 zero mapcells, with
blank tile0 in all128 images. The first offscreen pre-calibration read is excluded; CPU write logging
does not observe DMA. Neither DI2214 nor0 is universal. Next is a guarded native stationary-family
transition IRQ; the valid low-Y moving caller remains separate. GBA v72 and E5 remain unchanged. Stage11 is mechanically the second boss; do not conflate this
repository's Shoot label with the separate menu mode23. E5's first invalid writer remains unknown.
See [corrected cause](records/shoot-actual-input-boundary-20261109.md) and
[completed capture/replay QA](records/wsc-shoot-boundary-checkpoint-qa-20261109.md).

## 2026-11-09 approved boss HP1 observation — actual hit and Shoot entry

The separate hidden original-reference run completed normally, including host cleanup. Exactly one
approved active-boss HP write44→1 at core87975 was followed by a direct FIRST/P1 engine hit1→0 and
native root5 victory at91708, then the original Shoot initializer at92374 and stage11 entry.
Independent audit2D862A33 verified91 capture files,14 frozen pins and9 identical pre-boss baseline files.
The hit-pair full RAM differs only in the boss HP low byte; SRAM is identical. The source save and
v72 GBA remain unchanged. This is cheat-assisted original observation, not final GBA validation.

Shoot lasted2810 frames before failure/return to stage7. Terminal hits and consumed-DI pairs are both0.
The next target is the actual input-enable boundary and first P1 damage writer; a phase-gated fresh
jump is only a source-backed proposal, not a tested fix. E5 and the complete port remain unresolved.
See [independent capture QA](records/wsc-boss1-capture-qa-20261109.md) and
[actual input boundary](records/shoot-actual-input-boundary-20261109.md).

## 2026-11-09 original-only score999 observation

The authorized copy/score-only run reached stage7 through ten ordinary battles. Lua completed120,000frames;
the final state is Continue, P1 HP0 / boss HP42, with zero Shoot/terminal/DI observations. The host launcher
exited1 during cleanup; its initial report is preserved and explicit postchecks were recovered separately.
This is not a successful whole-port run. Original save and v72 GBA remain unchanged. See
[current resume](RESUME.md), [score contract](records/shoot-source-score999-20261109.md) and
[cleanup fix](records/private-desktop-cleanup-race-20261109.md). The user subsequently approved one original-only boss HP reduction to1 after its intro, followed by an actual attack. This new observation must preserve natural victory dispatch and remain separate from the completed score-only run.

## 2026-11-09 v72 — Shoot 탄환 그림의 종료 타일 처리

- 기준 커밋: `3354a6fb4d3850d406d826e8178bda49d8cb570b`(v71).
- 개발 ROM: `025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA`.
- 종료 때 지운 타일을 고정 자원 `93E7`에도 반영한다. 기존 소유자·그림 처리 코드를
  재사용하는 76바이트 연결 코드와 포인터만 추가했다. 80바이트 선언, 실제73바이트 변경,
  새 RAM·태스크 없음. 기존 v71 코드·후크는 보존했다.
- 독립 검증: 실제 ARM 실행4,585개 사례, 실제 지워진 부분512개, 오류 삽입19개 통과.
  정상 콜백 범위의 후속 재적재 증명을 사용하며, 전체 입력 범위나 외부 진입을 허용하지 않는다.
- 원본부터 만든 두 전체 빌드의 **289개 파일 경로·해시와 각113개 매니페스트 항목이 일치**했다.
  감사: `1643B67D7179360B1DAB8E8D34E5CEA8F0556A5276E42D5DF2180A2D6178F6D1`.
  분석 자료도 각 새 출력 폴더에서 생성해 과거 작업 폴더 의존성을 제거했다.
- 정확한 새 ROM으로 한국어 설정 저장→일반 전투→WIN과300프레임 후 표시를 창 없이 확인했다.
  감사: `62FE91FAE6245EA2F28DBD419D12E0AA70ED62CA65B5EEED37C6E75A0534BDB6`.
  전체 실행 기록·시점,8개 화면, EWRAM·VRAM·팔레트·OAM은 v71과 같다.
  IWRAM 스택과 일부 표시 레지스터 차이는 기록에 남겼다. 실제 Shoot 실행 검증은 아니다.
- **Shoot 실제 진입·전체 종료, 종료 화면 갱신·IRQ와 E5 원인은 미완료다.**
  배경 재적재와 행 지우기는 이미 연결돼 있었다. 빠진 화면 줄별 갱신을 따로 추적한다.
  전체 배경이 검게 되어 차이가 사라진다는 가정은 실제 팔레트·그림 자료로 반증했다.
- 사용자가11월9일 **제공 WSC 세이브 복사본의 개발 중 원본 관찰**을 명시적으로 허용했다.
  원본을 보존하고 창 없이 관찰하는 새 범위에만 적용한다. 예전 세이브 사용 금지 문구는
  이 범위에서 대체되며, 전체 포팅·최종 QA 완료를 뜻하지 않는다. [허용 범위](records/final-qa.md).
- [v72 통합 기록](records/shoot-projectile-integration-v72.md),
  [독립 QA](records/shoot-projectile-clear-qa-20261109.md),
  [원본 진입·복사본 관찰 조건](records/shoot-normal-entry-save-copy-20261109.md)을 따른다.
- **전체1.5 콘텐츠·전체 번역·최종 QA는 미완료이며 완성본이 아니다.**

## 2026-11-09 v71 — Shoot 동료 그림의 종료 타일 처리

- 기준 커밋: `3e5d6441ceb634398a1bca84d8301c215b7fb6b1`.
- 개발 ROM: `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A`.
- 종료 시 지운 동료 그림 타일을 기존 장면 상태로 추적하고, 실제 자원 재적재 시 복원한다.
  새 RAM·태스크 없이 기존 동료 30종과 제한된 카메라 구간에 적용했다.
- 검토 중 발견한 재적재 인수 해석 오류를 수정했다. `R5`는 주소가 아니라 표 안의 위치다.
  잘못된 초안 `31790830…`은 주 빌드에 넣지 않았다.
- 독립 검증: 실제 ARM 실행 37,962개 사례와 오류 삽입 19개 통과.
  두 새 전체 빌드의 **284개 파일 경로·SHA-256이 일치**했다.
  최종 빌드 감사: `A864BD691118545B651643EA3D94422DE22ABEC57BECC052E34B46E44539F77A`.
- 정확한 새 ROM으로 한국어 설정 저장→일반 전투→WIN과 300프레임 후 표시를 창 없이 확인했다.
  실행 감사: `23F56022C242F78F6C224D8DFD08FE245829E9E7E2A94AA06A207E46DC25E5F1`.
  61개 파일·8개 캡처·WIN 그림 1,508픽셀을 검사했다. 이전 v70과 8개 화면 및
  EWRAM·VRAM·팔레트·OAM은 바이트 단위로 같다. 옵션 저장 이후 절대 시점은 1프레임 늦고,
  전투 시작부터 결과까지의 7,520프레임은 같다. 전체 실행 시간 일치로 확대하지 않는다.
- **Shoot 실제 진입·전체 종료, 다른 공유 타일·주인공 그림 뱅크, 카메라·IRQ와 E5 원인은 미완료다.**
  다음은 검증된 정상 콜백 범위에서 `93E7`의 고정 타일 처리다. 원본의 비정상 분기 범위는
  계속 외부 진입을 막는 조건이며, 아직 이 범위를 해결했다고 보지 않는다.
- [v71 통합 기록](records/shoot-static-companion-integration-v71.md),
  [독립 구성 요소 QA](records/shoot-static-companion-qa-20261109.md),
  [후속 재적재 소유권](records/shoot-p2-reload-eligibility-20261109.md)을 따른다.
- 제공 WSC 세이브는 사용하지 않았다. **전체 콘텐츠·전체 번역·최종 QA는 미완료이며 완성본이 아니다.**

## 2026-11-06 v70 — Shoot 탄환 소비자와 정상 패턴 선택 수정

- 기준 HEAD: `31153db186d7cbf9d3634cc12b6d73327e527c24`(v69).
- 개발 ROM: `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717`.
- 새 탄환1A/1B가 기존 처리표 밖의 RAM 주소로 분기하던 누락을 수정했다.
  원본의 세 피격 반응과 기존 native 체력·구슬 함수를 연결하고 기존 공격 처리를 보존했다.
- 추적 규칙8EF3에서 기존 검사가 거부하던 원본의 정상 X표 끝 분기를 연결했다.
  원본이 정상 패턴을 선택하는 모든16비트 조합을 표현한다. 원본의 비정상 분기 도달 여부는 미확정이다.
- 두 수정 합계4구간1,856바이트 선언, 실제1,402바이트 변경, 새 RAM 없음.
  탄환1,242개/패턴544개 ARM 사례와 오류 삽입22개/7개를 독립 검사했다.
- 원본부터 만든 두 전체 빌드 A/B의 **281개 파일 경로·SHA-256이 일치**했다.
  독립 최종 감사: `D87DBF8491B363F0DE75264E49F04DA750A1598B417F891A46F176129A920A7E`.
- 정확한 새 ROM의 한국어 옵션 저장→일반 전투→WIN 및300프레임 후 표시를 창 없이 검증했다.
  독립 실행 감사 `D7B85F2D0606FB4D26B499CFC1388E45D358A7B3CE908B3B8A204102218B8DC0`:
  61개 파일·8개 캡처 묶음·실제 그림1508픽셀 일치.
- **Shoot 외부 진입·종료, 카메라·IRQ·그림 지우기 수명, 과거 E5 원인은 남아 있다.**
  원본의 창 없는 캠페인 관찰은 모두 부분 기록으로 종료했다. 마지막 관찰에서는
  같은 시작 상태에서 착지 후 점프를 보내 벽에 갇히던 동작을 해소했으나 Shoot에는 도달하지 못했다.
  추가 자동 조작 변형은 중단하고 종료 타일·투사체 수명의 실제 연결을 진행한다.
  제공 WSC 세이브는 사용하지 않았다. [실제 비교 기록](records/shoot-recovery-v4-actual-20261106.md)을 따른다.
- [v70 통합 기록](records/shoot-consumer-integration-v70.md),
  [최종 독립 QA](records/shoot-attack-subset-integration-v70-qa-20261106.md),
  [새 원본 관찰 경로](records/shoot-short-hard-probe-20261106.md)를 따른다.
- **전체1.5 콘텐츠·전체 번역·최종 QA는 미완료이며 완성본이 아니다.**

## 2026-11-06 v69 — Shoot 내부 컨트롤러 연결

- 기준 HEAD: `c22eddc8522a917ae63e12506945ff96eafb825d`(v68).
- 개발 ROM: `72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC`.
- `085C0A00`의 반환 명령 한 워드(4바이트)를 기존 SELECT/APPLY 호출로 연결했다.
  전체 역복원으로 정확한 v68과 일치한다. 외부 장면 선택·진행 분기는 그대로 닫혀 있다.
- 원본부터 만든 두 전체 빌드 A/B의 **275개 파일 경로·SHA-256이 일치**했다.
  독립 최종 감사: `393C2804E1E5AED6A180B7F4E0B790AF278ACBB1322FE96FF5EA0A84120D88D8`.
- 새 ROM의 한국어 옵션 저장→타이틀→일반 전투→WIN 및300프레임 후 표시를 창 없이 검증했다.
  독립 검사에서62개 파일·8개 캡처 묶음·실제 그림1508픽셀이 일치했다.
- 전체 좌표 판단은 `OPEN_DOMAIN`이다. 새 타격이 필요한 ID14 공중 순환과 상하좌우 좌표의
  연관 조건, 종료 카메라·IRQ·화면 지우기 대상 수명이 남아 있다. 실제 Shoot 도달로 세지 않는다.
- E5 비교 실행은 과거 초기 난수 세 값과17개 레지스터를 맞췄으나,7340갱신 뒤 결과 화면으로
  넘어가 과거 실패 경로와 달랐다. E5 원인 해결 또는 오류 부재를 선언하지 않는다.
- 별도로 **Shoot 탄환1A/1B의 native 충돌 분기 누락**을 실제 새 자원과 기존 처리표에서 찾았다.
  현재 독립 구현·검증 중이며 v69에는 아직 수정되지 않았다. 과거 E5와 같은 원인으로 단정하지 않는다.
- [v69 통합 기록](records/shoot-controller-integration-v69.md),
  [독립 최종 QA](records/shoot-controller-integration-v69-qa-20261106.md),
  [E5 관찰 기록](records/id14-preseed-observer-20261106.md)을 따른다.
- 제공 WSC 세이브는 사용하지 않았다. **전체1.5 콘텐츠·번역·최종 QA는 미완료이며 완성본이 아니다.**

## 2026-11-06 v68 — Shoot 호출 코드와 종료 분기 통합

- 기준 HEAD: `9dbfab9669f673bcecad6f15c17287f951250a76`(v67).
- 개발 ROM: `9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738`.
- 원본부터 새로 만든 `build/repro-v68-20261106-e`와 `-f`의 **271개 파일 경로·SHA-256이 일치**했다.
  독립 최종 감사: `7512E3880FA0D60C2B38D8C8A8F1084966CEBE4D531C8C0139A8EDF317D82541`.
- 같은 호출 안의 컨트롤러 SELECT/APPLY와 무대11 전용 종료 분기를 상주 코드로 통합했다.
  실제 ARM 모델의8192/8960경우,35개 부정 사례와 전체 역복원 검사를 통과했다.
- 정확한 새 ROM으로 한국어 옵션 저장→일반 대전→WIN 결과를 창 없이 확인했다.
  독립 검사에서61개 파일·8개 캡처 묶음·실제 그림1508픽셀이 일치했다.
- **Shoot 외부 진입·컨트롤러 경계는 아직 연결하지 않았다.** 실제 종료 BX의 대상,
  IRQ·화면 수명과 일반 추적 중 좌표 범위가 남아 있다. `193B` 같은 차례 실행은
  기존 v54 보정에 이미 있으므로 중복 수정하지 않았다.
- E5 비교 실행은 원본과 다른 폭포 패턴0이라 재현·해결로 인정하지 않는다.
  비교 도구의 다음 단계 조건은17개 레지스터 전체 일치로 보강했다.
- 중단된11월5일 전체 빌드c와 원본 캠페인k/l은 완료로 세지 않는다. 제공 WSC 세이브는 사용하지 않았다.
- [v68 통합 기록](records/shoot-caller-integration-v68.md), [호출 코드 독립 QA](records/shoot-caller-resident-qa-20261105.md),
  [장면 연결 초안](records/shoot-route-draft-20261106.md)을 따른다.
- **전체1.5 콘텐츠·추가 메뉴·전체 번역·최종 QA는 미완료다. 최종 패치나 완성본 ROM으로 배포하지 않는다.**

## 2026-11-05 v67 — 1.5 타이틀과 네 언어 결과 그림

- 기준 HEAD: `56a888444fa384a315848bef14e455d081bc6487`(v66).
- 개발 ROM: `A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F`.
- 원본부터 만든 두 전체 빌드의 **268개 파일 경로·SHA-256이 일치**했다.
  비교 `249B3B2E997E8C2B289D53B0C7BD46A17B029AE5F020BB215BEAF96386BF5AD3`,
  최종 독립 감사 `2006A629A9F8334ADDF771ED8C104A06CFE758A12DFFCDF789C49805973BD155`.
- 1.5 원본 타이틀 배경과 기존 mode8 결과의 네 언어 자원을 통합했다.
  한국어·디지코드의 승리/무승부는 일본어판 WIN/DRAW를 사용한다.
  디지코드 마지막 기회!는 요청에 따라64×16에서 **102×16**으로 확대하고 별도 픽셀 QA를 통과했다.
- 실제 타이틀·선택 화면을 창 없이 확인했다. 최종 ROM의 네 언어 모두 정상 옵션 저장→전투→WIN 결과와300프레임 후 표시를 관찰했다. DRAW·마지막 기회!의 실제 발생은 미관찰이다.
- Shoot 외부 장면·컨트롤러는 아직 연결하지 않았다. 저장 소비자·종료 IRQ·카메라·실제 Y/플래그 소유권과 E5 원인은 남아 있다.
  원본 hard 캠페인j의900초 중단을90,000프레임 성공 또는 Shoot 관찰로 계산하지 않는다.
- [v67 구현·검증 기록](records/title-result-integration-v67.md), [결과 그림 독립 QA](records/result-language-qa-20261105.md),
  [원본 수명 조사](records/shoot-lifetime-consumers-20261105.md)를 따른다. 제공 WSC 세이브는 사용하지 않았다.
- **전체 콘텐츠·추가 메뉴·전체 번역과 최종 QA는 미완료다. 완성본 포팅으로 배포하지 않는다.**

## 2026-11-05 v66 — Shoot 상주 장면 통합과 관찰 도구 보정

- 재개 HEAD: `98e00e9111b63dfdac866b354ee1e00c732696dd`.
- 개발 ROM: `428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281`.
- 원본부터 새로 만든 `build/repro-v66-20261105-a`와 `-b`의 전체 **259개 파일 경로·SHA-256 일치**.
  비교 보고서: `A7D7DAC45B1B4636A40954C245D776FD3D6F0C2F3FBFD37606C2C12E5DDAA9A5`.
- 원본 순서의 장면 코드 22구간을 주 빌드에 넣고 실제 초기화 `08629800`을 내부 호출한다.
  기존 분기 대상과 겹치던 `12C6` 배치를 `085C9B00`으로 옮겨 네 기존 참조를 보존했다.
  648개 ARM 명령, 의미 부정 사례15개·소유권 부정 사례6개, 전체 ROM 역변환을 독립 검증했다.
- **외부 장면 진입과 컨트롤러는 아직 연결하지 않았다.** 저장 소비자·종료 IRQ의 DI·카메라 수명과
  `8EF3` 실제 입력 범위가 남았다. 범위 밖에서 원본도 별도 코드로 넘어가므로 임의 제한이나 유휴 반환으로 해결하지 않는다.
- v65와 v66에서 바꾼 일반 입력 경로18,000프레임을 창 없이 관찰했다. 각 기록 생성44,960회,
  충돌50회·분기42회이며 RAM·화면과 이벤트 순서가 일치했다. E5는 미재현이며 원인은 미해결이다.
- 관찰 기록의 마지막128행을 쓰기 전에 종료할 수 있던 완료 신호 경쟁을 수정하고 v66에서 재검증했다.
  이는 관찰 도구 수정이며 게임 E5 수정이 아니다. 상세: [v66 통합 기록](records/shoot-scene-integration-v66.md).
- 원본 WSC 관찰 알림의 실행/쓰기 역연결을 정확한 BizHawk2.11.1 소스로 확인해 보정했다.
  보정 후4,500/30,000프레임 검사는 양성 교정을 통과했으나 해당 입력은 Shoot에 도달하지 못했다.
- 사용자가 코드 기반 정밀 픽셀 제작을 승인했다. 한글 마지막 기회!와 일본어판 WIN/DRAW 재사용은
  별도 픽셀 QA를 통과했다. 디지코드 크기 확대와 타이틀 배경은 추가 작업 중이며 ROM 통합 완료가 아니다.
- 제공 WSC 세이브는 사용하지 않는다. 완성본 포팅·전체 언어·최종 QA를 완료로 표시하지 않는다.

## 2026-11-05 v65 — Shoot 저장·후속 초기화 통합

- 재개 HEAD: `af34f1ac85798e31e1552138d7d3a8017994192a`.
- 개발 ROM: `5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46`.
- 원본부터 새로 만든 `build/repro-v65-20261105-a`와 `-b`의 전체 **255개 파일 경로·SHA-256 일치**.
  비교 보고서: `B4963676C8AB8F3338E334AD0190D9B430DF9D852E8681101310B33C1498F7B7`.
- 서로 다른 원본 영속 상태 두 쓰기를 native EEPROM block25의 개별 읽기·수정·쓰기로 구현했다.
  각 쓰기는 나머지 6바이트를 보존한다. 이어서 다른 플레이어 복원 → HUD·스크롤 → 선택 팔레트 준비를
  원본 순서로 연결했다. 조건부 초기화 본문은 `7168..7534`까지 연결됐으나 외부 장면 호출은 아직 없다.
- 독립 검증: 저장 ABI·오류 조합4,096개/부정 사례186개, 후속 초기화 ABI256개/부정 사례142개 통과.
  검증에서 빠졌던 애니메이션 설정 함수 뒷부분과 동기 호출·리터럴 범위를 보강했다.
- 정확한 v65로 창 없는 30,000프레임 검사를 두 번 완료했다. 각 충돌 판정84회·분기79회,
  RAM·VRAM·OAM·팔레트·화면 등 8개 파일과 입력·이벤트 순서가 일치했다.
  첫 240초 제한 중단은 별도 보존하고 완료 수에 포함하지 않았다. 완료 두 실행은 480초 제한을 사용했다.
- 실행 검증은 ID14 일반 전투·결과·다음 전투·컨티뉴 경로다. 새 Shoot 초기화 실행 또는 E5 원인 해결이 아니다.
- 다음은 실제 저장 소비자, 앞선 팔레트 저장 시점과 장면 소유권, 외부 초기화·컨트롤러 연결,
  IRQ·카메라 수명이다. 전체 포팅·언어·최종 QA는 미완료이며 완성본 ROM으로 배포하지 않는다.
- 제공 WSC 세이브에 접근하지 않았다. 새 결과 언어 초안은 주 빌드에 포함하지 않았다.
- 상세: [v65 통합 근거](records/shoot-initializer-integration-v65.md).

## 2026-11-03 v64 — Shoot 초기화 연결과 충돌 관찰 보강

- 시작 HEAD: `485e04891fab9c540e168e95ee3ae25514f7d27d`.
- 개발 ROM SHA-256: `CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7`.
- `build/repro-v64-20261103-a`와 `-b`의 전체 **249개 파일 경로·SHA-256 일치**.
  비교 보고서: `8CB237E43BF523FAB61E18EF0F16C2B5552421B5FA99341166197750F5864B28`.
- 초기화 준비 → 플레이어 재설정 → OBJ 슬롯5 팔레트 → 소유권이 확인된 `0660` 지우기를
  원본 `7168..73E2`의 단계 순서로 연결했다. 외부 호출은 아직 연결하지 않았다.
- 독립 검증: 플레이어 연결은 ABI256경우·부정 사례126개, 후속 연결은 ABI256경우·부정 사례94개 통과.
  생성기와 별개 검증기를 전체 빌드에서도 각각 실행했다.
- 첫 미구현 구간은 `ES1000:3CD8/3CDA`의 두 저장 쓰기다. 전체 초기화·장면 진입,
  종료 IRQ·카메라 수명·나머지 콘텐츠 및 전체 언어 지원은 여전히 미완료다.
- 충돌 관찰 도구는 실제 18개 분기 표와 인덱스를 검사하고 입력·명령 시점·프레임을 구분한다.
  고정 v62/389F에서 창 없는 30,000프레임 실행을 두 번 수행해 각각 충돌 판정84회·분기79회를 관찰했다.
  두 실행의 RAM·VRAM·OAM·팔레트·화면이 바이트 단위로 같았다. E5는 재현되지 않았으나 원인은 미해결이다.
  이는 v64의 실행 또는 전체 안정성 검증이 아니다. `records/runtime-collision-observer-20261103.md` 참조.
- 제공 WSC 세이브에는 접근하지 않았다. 새 결과 언어 초안은 주 빌드에 포함하지 않았다.
- GitHub 비공개 저장소 `GimoXagros/gba-dbs1.5-porting`을 사용한다. 아래 과거의 원격 없음 기록은 역사적 상태다.


## 2026-10-26 v63 — 포트 전용 Shoot 초기화 접두부

- 기준 코드 체크포인트: `bdc4389`; 작업 기록 동기화: `bb8de98`.
- 개발 ROM SHA-256: `4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC`.
- `build/repro-v63-20261026-a`와 `-b`의 전체 243개 파일 경로·해시가 일치한다.
  비교 보고서 SHA-256: `BC0AFBC6E4515363C6AD254E8F308B153FB39BEDA61FA3595B6E6F08D378F2C1`.
- 원본 `7168..71D1`의 표시 준비 → 무대11 → 그래픽 → 타이머·상태 → 무대 관리자 순서를
  호출되지 않는 새 접두부에 구현했다. 92바이트 선언/89바이트 실제 변경이며 기존 동작 경로를 바꾸지 않았다.
- 독립 검증: 원본 37명령/ARM20명령, ABI128경우, 부정 사례179개와 전체 역복원 통과.
  보고서 SHA-256: `58B559ADDB89ED4279A000447E276FDAAE68F0C90EBB4A6D5345E3B6C7F05BEB`.
- 새 결과 언어 후보 F9E5는 이 빌드의 의존성이 아니다. 사용자 요청에 따라 1.5 포팅과 안정성을 우선한다.
  기존 검증된 옵션·타이틀 언어는 유지하고 새 언어 그래픽은 별도로 준비한다.
- ID14의 충돌 종류 E5에 의한 실행 중단은 여전히 미해결이다. 원본·변환 P1의 15,004항목에는 E5가 없다.
  추가 창 없는 두 실행에서 정상 콜백 7/8회를 관찰하고 컨티뉴 상태에 도달했지만, 실패 원인을 해결했다는 증거는 아니다.
- 픽셀 담당과 별도 QA가 일본어판 WIN/DRAW 및 사용자 디지코드를 데이터로 검증했다.
  한국어 시안은 반투명 가장자리와 픽셀 격자 문제로 게임 적용을 보류했다. `records/result-art-qa.md` 참조.
- 전체 Shoot 초기화·외부 진입, 나머지 콘텐츠·언어 및 최종 QA는 미완료다. 완성본 ROM이 아니다.

## 2026-10-23 v62 폭포 세 번째 패턴·결과 포즈·무대 판별 수정

- 재개 기준 HEAD: `5a313d4004128a99badb69536d99f39ad7b04bec`.
- 개발 ROM: `389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1`.
- 원본부터 새로 만든 `build/repro-v62-20261023-a`와 `-b`의 240개 파일은 상대 경로와 SHA-256이 모두 같다.
  비교 보고서: `build/repro-v62-20261023-comparison.json`,
  SHA-256 `0750DFCF3AFA1B35ED3880BE5A2B1364125714ABA9B6238218F96267CF2C36F0`.
- 장시간 중단의 실제 쓰기 `0836D85C`는 누락된 폭포 세 번째 설정을 읽고 있었다.
  원본의 세 번째 레코드·초기화와 후속 행 지우기를 복원했다. 독립 검증 오류 사례 522개를 통과했다.
- 창 없는 실제 실행에서 초기 패턴 2가 새 초기화 `08629668`에 도달하고,
  무대 객체에 정상 대기 주소 `08585274`, 위상 `C0`, 모드 3이 설정되는 것을 확인했다.
  별도 230초 일반 전투도 컨티뉴까지 진행했고, 예외 중단 없이 32개 화면 객체와 렌더러를 유지했다.
  실제 캡처 화면을 확인했다. 이는 한 전투 경로의 증거이며 전체 게임 안정성 판정은 아니다.
- 후속 경로 검사에서 캐릭터 충돌 처리 중 `PC=E28DD00C`, `LR=08353FF0`인 별도 실행 중단을 확인했다.
  실제 소비자를 추적 중이며, 앞선 230초 성공만으로 안정성이 확정된 것은 아니다.
- 결과 포즈의 두 표를 원본 15개 캐릭터에 맞췄다. 독립 오류 사례 304개와 실제 ID14 패배 포즈 소비자를 확인했다.
- 무대 관리자의 두 조회만 실제 Shoot 무대 11을 우선하도록 고쳤다. 65,536개 조합 중 원본과 충돌하던 세 조합만 바뀐다.
  독립 오류 사례 103개를 통과했으며, 전체 Shoot 진입을 연결한 것은 아니다.
- 상세 증거: `records/runtime-repair-20261023.md`, `records/waterfall-third-pattern.md`,
  `records/result-pose-routing.md`, `records/stage-priority-routing.md`.
- 옵션과 타이틀의 네 언어는 유지했다. 결과 문구의 네 언어는 별도 구현 중이며 이 v62에는 아직 포함하지 않았다.
  전체 Shoot 초기화·전환, 나머지 콘텐츠와 전체 언어·최종 QA는 미완료다.
- 제공 WSC 세이브에 접근하지 않았고 실행 창을 표시하지 않았다. 완성본이 아닌 재현 가능한 개발 체크포인트다.

## 2026-10-23 v61 회복·피격 경로와 타이틀 네 언어 체크포인트

- 재개 기준 HEAD: `166496fd7b5854de00ac5e40b677bf22ad028497`.
- 주 빌드 개발 ROM: `A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61`.
- 원본부터 새로 만든 `build/repro-v61-20261023-a`와 `-b`의 231개 파일은 상대 경로와 SHA-256이 모두 같다.
  비교 보고서 `build/repro-v61-20261023-comparison.json`의 SHA-256은
  `8D332AFD80265755626A245E65F2A4562157D1947488ECC73666539333D9A42B`다.
- 기존 ID14 목록·VS·폭포 수정과 입력 행동 표를 유지하고, 회복 표 및 피격·후속 표 네 개를 원본 15행에 맞췄다.
  독립 검증은 회복 오류 사례 88개와 피격 409개를 통과했다. 원본 피격 변형 8의 후속 경로도 보존했다.
- 타이틀 다섯 문구도 영어·일본어·한국어·디지코드를 지원한다. 옵션의 저장 언어를 사용한다.
  디지코드는 일본어 읽기 기준이며, 일본어 원문에 실제로 있는 알파벳만 영문 표를 사용한다.
  타이틀 독립 검증 112개 오류 사례와 전체 객체 수 검사를 통과했다.
- 정확한 A3E 통합본을 창 없이 230초 실행하여 ID14 첫 전투에서 컨티뉴까지 도달했다.
  예외 중단 없이 32개 OAM 객체와 원래 렌더러를 유지했다. 한국어 저장 및 새 실행 타이틀·메뉴도 확인했다.
  일본어·디지코드 타이틀 저장·새 실행 검사는 바로 전 타이틀 계층 143E에서 확인했다.
- 상세 증거: `records/runtime-repair-20261023.md`, `records/character-damage-routing.md`,
  `records/character-hit-routing.md`, `records/title-language.md`.
- 후속 장시간 실행에서 폭포 세 번째 설정 누락으로 무대 객체가 `FFFFFFFF`를 포인터로 읽는 중단도 확인했다.
  실제 쓰기 `0836D85C`를 관찰했으며 수정 중이다. 앞선 230초 성공은 한 경로의 결과다.
- 후속 조사에서 결과 화면 승리·패배 포즈 표의 추가 ID 범위 초과를 확인했다. 이 A3E에는 아직 미수정이다.
  결과 화면 등 전체 언어 지원, Shoot 전체 초기화·전환과 나머지 콘텐츠·최종 QA도 남아 있다.
- 제공 WSC 세이브에 접근하지 않았고 실행 창을 표시하지 않았다. v61은 개발 체크포인트이며 완성본이 아니다.

## 2026-10-23 v60 폭포·행동 표·네 언어 옵션 체크포인트

- 재개 기준 HEAD: `6682d50b776056a6c2cf32951afeaf6ce09384c5`.
- 주 빌드 개발 ROM: `F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0`.
- 원본부터 새로 만든 `build/repro-v60-20261023-c`와 `-d`의 222개 파일은 경로와 SHA-256이 모두 같다.
  비교 보고서: `build/repro-v60-20261023-comparison.json`,
  SHA-256 `256F2FF2A4DB6B4EC4B1238F01766A69026BA11B8AAB8A3E3E005A337B31E26C`.
- ID14 선택 목록 수정은 유지했다. 후속 전투 중단은 12행 행동 표의 범위 초과로 실행 주소에 0을 쓰는 별개 문제였다.
  실제 쓰기와 소비자를 추적해 15행 원본 대응 표로 연결했다. 입력 행동 표 14개도 원본 210행에 맞춰 확장했다.
- 폭포의 배경 객체·표시 비트·팔레트 상태 소유권을 수정했다. 통합본 ID14 이동·공격 99초 검사에서
  예외 중단 없이 두 캐릭터와 폭포, 42개 OAM 객체 및 렌더러 무결성을 확인했다.
- 옵션은 영어·일본어·한국어·디지코드 선택과 저장을 지원한다. 별도 후보에서 일본어·한국어·디지코드의
  새 실행 불러오기와 선택 취소를 확인했고, 정확한 F2D 통합본에서도 디지코드 저장·새 실행 불러오기를 확인했다.
  디지코드는 일본어 읽기를 기준으로 하며, 일본어 원문 속 알파벳에만 영문 표를 쓴다.
- 빌드는 Pillow가 있는 Python과 `--font`, `--font-license`가 필요하다. 이번 환경은 Python 3.12.14 / Pillow 12.3.0이다.
  기본 Python의 Pillow 누락으로 중단된 `-a`/`-b`는 완료 빌드로 세지 않는다.
- 상세 실행 증거·폰트 해시·남은 범위: `records/runtime-repair-20261023.md`.
- 별도 회복 표 A18 수정은 독립 검증을 통과했지만 이 F2D 주 빌드에는 아직 포함하지 않았다.
  타이틀 언어 확장과 추가 피해 표도 후속 작업이다. 전체 Shoot 초기화·전환, 추가 콘텐츠 및 최종 QA는 미완료다.
- 모든 실행 창을 숨겼고 제공 WSC 세이브에 접근하지 않았다. v60은 개발 체크포인트이며 완성본이 아니다.

## 2026-10-21 v59 ID14 선택·VS 화면 수정 체크포인트

- 재개 HEAD는 `aa2ef2d260ae8b0867abb9f39a61a8f5d91ce026`이다. 이전 값을 되돌리지 않고 실제 소비자를 수정했다.
- 원본부터 두 번 빌드한 `build/repro-v59-20261021-a`와 `-b`의 206개 파일은 상대 경로와 SHA-256이 모두 같다.
  최종 개발 ROM: `AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF`.
  비교 보고서 SHA-256: `2733D2C28AB4A14250B73AFB52E9088577F2DF20BBA97BBBD7732D767625524A`.
- 추가 무대 충돌·논리 무대별 시작 좌표·기차 배경·Iraira 바닥 반응을 연결했다.
  ID13 기차 첫 전투는 창 없는 실행에서 두 캐릭터와 배경을 확인했다. 기차 위험 요소와 전체 진행 규칙은 남았다.
- ID14의 목록 13번째 항목이 `03004728` 표시 객체 포인터를 덮어썼다.
  세 목록 소비자를 ROM 표로 연결하고, 색상만 전환하는 네 번째 경로도 실제 캐릭터 ID로 변환했다.
- 이후 드러난 VS 화면 중단은 이름 그림 표의 누락 때문이었다. 기존 11행에 원본 이름 두 행을 덧붙였다.
  첫 OAM 초과 쓰기에서 잘못된 개수·주소와 97회 반복을 확인했고, 수정 후 ID14 첫 폭포 전투와 색상 전환을 각각 관찰했다.
- 폭포 첫 전투는 중단 없이 진행되지만 배경 표시 비트와 팔레트 상태 소유권의 후속 오류를 조사 중이다.
  v59를 그래픽 완성본이나 최종 포팅으로 배포하지 않는다.
- 한국어 Options 시험본에서 실제 표시와 90/120/180, 쉬움/보통/어려움, 예/아니요 조작을 확인했다.
  이는 별도 시험본이며 v59 기본 언어를 바꾸지 않는다. 네 언어 선택·저장·전체 문구와 디지코드 글꼴은 구현 중이다.
- 증거: `records/roster-list-routing.md`, `records/vs-name-layout-repair.md`,
  `records/selection-palette-index-repair.md`, `records/options-korean-native-poc.md`.
- 제공 WSC 세이브에는 접근하지 않았고 실행 창도 표시하지 않았다. 전체 Shoot 초기화·전환 및 최종 플레이 검증은 여전히 미완료다.


## 2026-10-16 v57 실행 회귀 수정 체크포인트

- 재개 기준 HEAD: `d6f976c84c150b6a1fc172024b31fa887435c879`.
- 빌드: `build/repro-v57-20261016-a/current-candidate.gba`와 `-b`.
  SHA-256 `1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995`.
- 39개 ROM 계층, 전체 185개 파일의 상대 경로와 SHA-256 동일.
  비교 보고서 `build/repro-v57-20261016-comparison.json`,
  SHA-256 `3F8B89BD8A31ACBACB96252E15B310AAAFD58C3BA6379C86B75737F0426A5599`.
- 세 물리 포인터는 유지하고, 원본의 비연속 포인터 표에 맞춰 데이터 출처를 수정했다.
  도입부 중단은 별개인 11행 표시 표의 범위 초과가 원인이었으며, 확장 표로 연결했다.
- 추가 캐릭터의 P0 누락 구간, 전체 P1 544개 이벤트/2,742개 명령,
  네 그룹의 자원 표, 동료 P4와 누락 팔레트를 실제 소비자에 맞게 연결했다.
  추가 효과음 5개는 악보를 구현했으나 음색·하드웨어 변조 동등성은 미완료다.
- 선택 화면 팔레트 참조와 재배치된 생성 코드의 잘못된 주소 참조를 수정했다.
  수정 전 첫 좌표 쓰기부터 명령 바이트를 좌표로 읽었다는 실행 증거를 확보했다.
- 창 없는 실행에서 기본 캐릭터의 첫 전투와 두 캐릭터 표시를 확인했다.
  이는 제한된 경로의 검증이며 전체 게임 완료를 뜻하지 않는다.
- **추가 캐릭터 ID13 경로는 여전히 불합격**: 기차 무대의 충돌 연결 누락과
  초기화·배경 맵 계약 불일치를 확인했다. 이 원인에 대한 후속 구현을 진행 중이다.
- 네 언어 확장이 승인됐다. 디지코드는 일본어 읽기를 기준으로 하고,
  일본어 원문에 포함된 알파벳만 영문 표를 적용한다. 98개 대응 항목과
  변환 도구는 있으나 네 언어 메뉴·글꼴·저장은 아직 미완료다.
- 현재 증거: [runtime-repair](records/runtime-repair-20261016.md),
  [spawn repair](records/player-spawn-literal-repair.md),
  [language consumers](records/language-consumers.md).
- 전체 Shoot 초기화·전환, 추가 무대/모드, 언어 구현과 최종 플레이 검증이 남았다.
  v57은 개발 체크포인트이며 완성본으로 배포하지 않는다. 제공 WSC `.sav`는
  열거나 해시하지 않았으며, 모든 실행은 창을 표시하지 않는 방식으로 유지한다.

## 2026-10-16 추가 승인 범위 — 4개 언어

영어·일본어·한국어·디지코드 선택을 최종 포팅 범위에 추가했다.
디지코드는 사용자 첨부 가나표와 **일본어 원문/읽기**를 기준으로 하며,
영어 번역을 경유하지 않는다. 현재 72개 표 항목과 엄격한 읽기 변환
도구만 마련했으며, 메뉴·저장·실제 글꼴 연결은 아직 미완료다.
상세 상태: [four-language-expansion](records/four-language-expansion.md).
기존 실행 오류 수정 및 전체 콘텐츠 포팅을 계속하며, 개발 중 창 없는
검증 허용과 제공 WSC 세이브 접근 금지를 유지한다.

## 2026-10-15 v54 implementation update

The user explicitly authorized invisible development-time source/GBA runtime
verification. Earlier defer-until-integration wording below is superseded;
the supplied WSC save remains unopened and unhashed. The final requested local
deliverable is a completed GBA ROM, but this checkpoint is not complete.

v54 installs the missing Shoot collision grid in both BG resource consumers
and repairs the successful 193B-to-197A same-invocation transition. See
`records/shoot-spatial-repair.md`. Both full source-input builds passed all
checks: 30 ROM layers and 158 identical relative-path/hash pairs. Candidate:
`CAB43EA68A6620D150CA853FC51D4690AAF0889A6D7351D90F99128FE5DD2C69`.
Manifest: `B0795BA5A4AFB743A824EC43C0D411348DE752FE47528D045730A8BE72624D53`.

Original WSC cold boot, roster and first battle were observed using an isolated
Mednafen 1.32.1 source build6985841 and emucap corecd0a39b, no visible window,
no supplied save and no guest-memory writes. The logged route does not reach
Shoot and cannot close its terminal/SRAM observer or coordinate gates.
Evidence: `build/source-runtime-20261015/probe-log.json`.

The old mGBA0.10.5 private-desktop environment showed abnormal screens for both
retail USA and candidate, so those screens are not proof of a port regression.
The preserved development mGBA buildfa977ccbc815efc93aefad9acddc9af0577d7827
displayed the retail USA title normally. Runtime results must identify their
exact emulator and input timing; static reproducibility is not runtime parity.

Audit date: 2026-08-31; implementation resumed 2026-10-13 (Asia/Seoul)

The user resumed implementation from the preserved v50 checkpoint. Current v53
adds lower rules, dedicated graphics, corrected source-addressed stage assets,
stage update/normal display, and resident terminal phases to the v51 components.
The complete original-order initializer and normal-play transition remain
unconnected. SRAM observers, terminal IRQ live-ins, and spatial domains are
explicit unresolved contracts, not waived checks.
See [`RESUME.md`](RESUME.md) for the current boundary. No new runtime claim is made.

This document is the authoritative recovery baseline for the current port.
It separates committed implementation from behavior actually observed in a
GBA emulator. A runtime item is marked `PASS` only when the exact candidate
identified below has produced direct evidence for it.

## Repository state

- Branch: `codex/progress-snapshot`
- Recovery-audit base commit: `48b5d3932d92b334454dc9a9bc00ef5f6fcf6ca1`
- Available repository baseline: `ffa4ddb75cc5277d9e483e018447917480083ee3`
- Working tree at the start of the audit: clean
- Commits from baseline through recovery-audit base: 12
- Configured Git remote: none
- Tracked ROM, save, extracted binary, screenshot, or emulator state: none

There is currently no GitHub destination to which this branch can be pushed.
The local Git history is the only repository record until a remote is supplied
or configured.
On 2026-09-02, the renewed upload request was checked against both local Git
configuration and the connected GitHub repository list: the remote list is
empty and no accessible GitHub repository was returned. The upload destination
must be supplied; no remote upload is claimed.

## Exact port objective

Reproduce the additional content and behavior of *Digimon Tamers: Battle
Spirit Ver. 1.5* in the USA GBA release of *Digimon: Battle Spirit*. The final
deliverable is a reproducible BPS patch, input/output hashes, application
instructions, and verification evidence. Original or patched ROM images must
not be committed or distributed. The supplied WSC save is reserved for final
QA after all declared content is integrated.

## Architecture decision

**Current architecture: static/binary translation on the commercial GBA
engine.**

Python tools convert selected WSC data and assets, while generated ARM code and
tables hook or extend the existing USA GBA program. This repository does not
contain a WonderSwan CPU, PPU, APU, or system emulator, and it does not append
the WSC ROM as an executable compatibility payload. It is therefore neither a
native source port nor an emulator-assisted port.

## Work classification

### A. Actual GBA runtime integration

- GBA ROM expansion, table relocation, ARM hook generation, and guarded
  downstream layering.
- Added fighter/evolution resource routes, added-stage tables and callbacks,
  progression/unlock changes, and alternate final-boss data/code.
- Digimon Shoot stage routing, graphics/palette data, core-loop route, timer
  callback, normal display callback, and scanline-threshold callback.
- Digimon Shoot child P1/P0/P2 resources plus the resident
  `9229 -> 94C1 -> 9570 -> 9617` generator/callback family at guarded expansion
  offsets. The family includes the payload-proved WSC 1.5 `A7` -> WSC 1.0
  `A5` -> native GBA `0x4A` sound request and is internally connected, but has
  no external parent entry. The Ver. 1.5-only parent-start `CE` command now has
  a bounded native GBA ID `0x5B` reconstruction. The resident
  `9083 -> 90F3 -> 912A -> 91AB -> 91EF` parent chain connects that request to
  child generator `9229` internally; controller `9908/9A1B` does not yet assign
  the parent entry.
- Ver. 1.5-only upper-state sound `D2` reconstructed as native GBA ID `0x5C`
  with exact nine-note/80-tick/right-only scheduling, a commercial voice-`0x1F`
  timbre oracle, and native pitch MOD. Its three upper-state requests are now
  connected inside the resident v46 graph but are not menu-reachable. CE's
  source-proved right-only direction is corrected by a
  final one-byte M4A pan layer.
- Resident Shoot auxiliary-object constructor and idle callback. A guarded
  commercial lineage proves Ver. 1.5 `ES:071E` is WSC 1.0 `ES:06A2` and maps
  to native GBA slot `0x03004D3C`, allocation ID `0x343`, pool 5. The v45
  constructor binds installed rule resources and player slots but intentionally
  has no menu or upper-state caller yet.
- Resident v46 upper-state population covering all 26 source callbacks and
  2,320 source code bytes, including v45's idle member. It adds 25 ARM callbacks,
  the fourth P2 record, seven-row intro palette, eight movement targets, native
  helper calls, and internal transitions. The v47 player phase now assigns
  `7792` internally; the phase itself remains uncalled from normal play and
  both `9908` calls terminate at an explicit unimplemented boundary.
- v47 corrects two P1/P2 constructor argument inversions and the auxiliary
  active/other player-link inversion. It implements source `71D1..7394` as a
  resident active-player/auxiliary reconfiguration phase, including the
  fifteen-character HP table and an allocation-free auxiliary reuse entry.
  These are consumer-checked static corrections, not gameplay evidence.
- v48 repairs the child P0 and four initializer P0 resources whose tile
  descriptors were silently omitted by the legacy `0x2000`-segment-only
  parser. Five pointer corrections connect all 46 far descriptors and 393
  converted tiles while preserving all code and layouts. Their source-loader,
  commercial-oracle, pixel and frame-selection checks are static evidence only.
- v49 corrects three additional-character physics pointers that were one
  `0x78`-byte record early and installs resident other-player restoration
  `73F0..74A2`. All three source-derived records already existed; only their
  pointers change. The phase uses the native character constructor, existing
  palette mirror and a 32-bit physics pointer. It still has no caller.
- v50 adds two resident resource segments: `7394..73A9` loads OBJ palette
  slot 5; `74A2..74DA` restores the exact commercial HUD tiles at native tile
  `3FC`, loads OBJ palette slot 6, and clears the mapped scroll state. Both
  entries remain uncalled. No complete initializer or palette ownership is
  claimed; ten semantic negative checks cover their actual native consumers.
- Opening modulo-5 dispatcher plus the added state-3/state-4 case setup,
  callbacks, converted motion/event tables, four added linear callbacks,
  selector-3→13 predecessor hook, and sequential auxiliary slot-3 reuse.

These are real GBA-side code/data changes. Their presence and static structure
do not by themselves prove that the corresponding gameplay paths work.

### B. Asset and conversion tooling

- WSC-to-GBA graphics, palette, map, descriptor, object-record, and table
  conversion helpers.
- ROM survey, disassembly, probe, smoke-build, and manifest generation tools.
- Guarded builders used for every current composite layer.

### C. Emulation or compatibility layer

None. No WonderSwan execution core or compatibility runtime is present.

### D. Stubs, placeholders, and bounded fallbacks

- `UPDATE_STUB` at expansion address `0x582E80` is written as `bx lr`; the
  current stage update table points at dedicated train, waterfall, Iraira, and
  Shoot entries instead, so this is an unused residue rather than a working
  implementation.
- The Digimon Shoot spawn record is a bounded safety copy of a retail stage-7
  record, not yet a translation of the complete Ver. 1.5 rules/object system.
- Several `legacy_stage_analogs` mappings deliberately keep old GBA consumers
  in range; they are compatibility fallbacks, not proof of equivalent added
  stage behavior.
- The Shoot `0x400` transition branch falls back to a matching retail callback
  because the WSC private state used by `5EEA:0D87/0E0B` is not mapped.
- Resident v46's controller boundary at `0x085C0A00` is an explicit `BX LR`
  stub. A later layer must replace it with the real `9908` rules and connect
  the dedicated initializer/menu entry together; it is not gameplay completion.
- Probe and smoke ROMs demonstrate isolated routes only and are not release or
  full-candidate evidence.

### E. Irrelevant, superseded, or duplicate artifacts

- The ignored `build/` directory contains dozens of historical ROMs,
  manifests, binary extracts, saves, and screenshots from intermediate v2-v30
  work. They are not the current candidate.
- Earlier provisional waterfall mode-3 work was retracted after direct table
  analysis showed the assumption was incorrect.
- `local/mgba-dev/` contains an unusable zero-byte executable, while
  `local/mgba-dev-complete/` contains the usable development build.
- Numerous one-off probe/smoke scripts overlap in purpose. They are retained
  until their dependencies are audited; this correction does not delete or
  rewrite valid historical work.

## Reproducibility audit

The current static candidate is built in twenty-two guarded layers into two
ignored clean output directories:

| Layer | SHA-256 |
|---|---|
| Corrected base roster | `5FE62385736851014C62E8F68B5D8F1583230DE2A30648CE893E3A45440B4ECA` |
| Stage integration | `FA0A48EC933AB9A2BD8960A61D0BE6F07CD15E2FC0B2037917595BDE154DACED` |
| Progression integration | `6D18B67E80C85429B20468449EB4024D4A29C50FC73A133163D028B02408D623` |
| Zeed boss / runtime-evidenced composite v32 | `1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291` |
| Opening choice/resources / static composite v34 | `33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1` |
| Four linear callbacks / static intermediate v35 | `9E3D495A3E07F2A9A6ECCF3C07E446036AD027B2A32666DD5A5984879BA6AA5F` |
| Disconnected Shoot child resources / static intermediate v36 | `4028AB75706FDE162E7F247B2AD52CAB20E9B30E487C306B70EE1E1F38E2F45C` |
| Payload-corrected Shoot child sound request / static intermediate v39 | `35B2F717A96573B0823E43433A547B5398CC13129DAEECED6646153FC69F5492` |
| Ver. 1.5-only CE native sound reconstruction / static intermediate v40 | `9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B` |
| Resident Shoot parent callback chain / static intermediate v41 | `B192AC03F75FB1B55B3BCB3BA6363836EDDFCBBAC8379DAF6D9DAB08B9AD2E06` |
| Shoot initializer resource-only placement / static intermediate v42 | `AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E` |
| Ver. 1.5-only D2 native sound reconstruction / static intermediate v43 | `7BB890FEC50BBAB796B5F94FE7761EAE9C4A284BB8E3CC9FA75A12FD20FB2264` |
| CE source-stereo correction / static intermediate v44 | `000683972B02F1E58369517F6AC32B270854ED2BBA4FC292BCA54E9E9700FBEB` |
| Resident Shoot auxiliary-object binding / static intermediate v45 | `C8C3AF5DABBE7CCE9F0D124DDEEF3CD6348FCDB085416DBA5E78C65DD5BFB3B4` |
| Resident Shoot upper-state graph / static intermediate v46 | `034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC` |
| Shoot constructor correction and player binding / static intermediate v47 | `ECE3D7E6428A81C93767FC72F79BC8EA5BD7E243E814FBEDCC6FFB079CEFDFC0` |
| Shoot far-descriptor/tile repair / static intermediate v48 | `11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E` |
| Added physics pointer repair and other-player binding / static intermediate v49 | `93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E` |
| Tail HUD/OBJ resource binding / preserved static v50 | `C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1` |
| Shoot rule-selection/application components | `FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C` |
| Shoot palette operations | `2008EC0520554F09C84351220B8A30931E1E636A7CEEE9BF3CBBB12C28C1B5AE` |
| Bounded initializer and constructor resources / static v51 | `726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284` |
| CF/D1 lower audio | `0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103` |
| Lower rule population | `223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E` |
| Dedicated graphics / preserved static v52 | `6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29` |
| Source-addressed stage asset repair | `00C4A8F4710BC0E2F4A31810CDD6FE2610D9670D9A989273162ADF33167211E7` |
| Stage update/display/IRQ components | `F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF` |
| Resident terminal phases and order repairs | `39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D` |
| Normal display route / current static v53 | `455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48` |

The full candidate is 8 MiB. Its GBA header has entry word `0xEA00002E`, title
`DIGIMON BTSP`, game code `A8SE`, maker code `B2`, fixed byte `0x96`, and a
valid stored/computed complement byte of `0x6C`.

The clean-build gap is now closed for the current candidate.
`tools/build_current_candidate.py` takes the hash-identified USA GBA, retail
WSC 1.0, and WSC Ver. 1.5 originals and regenerates the P4 and opening-P1
conversion corpora, all fourteen consumed character/evolution/VS/boss blobs,
the opening P0 blob, all twelve consumed stage blobs, the three Shoot child
resources, the initializer P1/P0/P2 resource set, the source-bound far-tile
repair, corrected physics asset, other-player and tail-resource phases, the new
rule/palette/initializer components, and all twenty-two ROM layers.
Every source, intermediate, asset, and layer is checked against its expected
SHA-256.

The former VS presentation generator required two ignored 64 KiB emulator RAM
dumps. Direct attribution proved that the Patamon/Tailmon palettes and planar
tiles are exact WSC ROM ranges. Their verified sparse 28x18 runtime placement
is now encoded as a reviewable generator rule. A clean ROM-only regeneration
produces VS blob SHA-256
`2D212622DB36E3D86281768F8C3438D394451FA275D519AA32B97FEE697D2856`,
byte-identical to the prior RAM-derived blob.

The preserved earlier runs in separate empty output directories `build/repro-v50-a` and
`build/repro-v50-b` each regenerated exact v50 SHA
`C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`.
All 121 files in each output tree match by relative path and SHA-256; the
identical build-manifest SHA-256 is
`5CDD5FB7595039958DB3B5D37D22168C3216A9CD69791234219E5E33C7F90EA5`.
The preceding four layers still reproduce exact v32 SHA
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`.
This proves current-candidate reproducibility only; it does not close any
missing-content or final-QA gate. No emulator or supplied save was used for
the v50 build checks.

The preserved v51 checkpoint was built on 2026-10-13 in `build/repro-v51-20261013-a` and
`build/repro-v51-20261013-b` produced all 22 layers and 131 files each.
The complete relative-path/SHA-256 comparison has zero differences. Both final
ROMs hash to `726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284`;
the identical build manifest hashes to
`F3C2B03E5608B5D0533D05F19F82D17D55E938360040C606CFBEB26F7E5705F7`.
The comparison record `build/repro-v51-20261013-comparison.json` hashes to
`62E253640552F3E7227F25D2DA7289ED2C78E873BA602FC9C0C42A4834511841`.
There are 2,340 changed bytes relative to preserved v50, all within the three
new layers' exact Expected Write intervals. The source hashes and both old v50
ROM hashes were rechecked unchanged; the final header complement remains `6C`.
The main build now refuses a populated output directory before generating files.
No save access or emulator execution was used in these checks.

The v51 pinned independent report hashes are:

| Verification | SHA-256 |
|---|---|
| Palette source lifetime and consumer projection | `2F5FA817B464F13A7606388F9650549A41C801A8FEB439A4FE51A2430A3048ED` |
| Rule selection/application | `7F4DFF7CB239B0C90A80A2168FC1D9BF5F9F05605E7953084A8203C2C8FC7678` |
| Palette final code and finite channel semantics | `7A6A9632EEDA2A98498405A2EAD2F78A27AB4BC6CEF142CEC9CBDF1FD9B96AAB` |
| Initializer final code, consumer/ABI/resource inverse | `F2BC89B285C7051DCE8C4A1680344A426CA5201B36F15764302DEB069D184C3E` |

The new native-consumer verifier exposed a historical physics placement
defect: ID 12 reached zero padding, ID 13 reached ID 12's record, and ID 14
reached ID 13's record. Converter/manifest agreement had not proved actual
pointer-to-payload identity. v49 changes the three pointers without moving
payloads; fourteen semantic negative checks reject each reverted pointer and
wrong phase arguments/fields/palette extents. The correct standalone asset
builder now checks the pointed-to records. Its explicit legacy option exists
only to regenerate the pinned intermediates, which are not release candidates.
The final composite must equal the corrected standalone physics blob. Full
consumer evidence and the still-unproved initializer/lifetime boundaries are
in `records/digimon-shoot-runtime.md`, v49 section.

`tools/analyze_opening_linear_integration.py` independently compares v34 with
v35. It confines all 2,199 changed bytes to three predecessor hooks and eleven
declared expansion placements, disassembles the exact four ARM callback call
graphs, verifies successor selectors and native helper calls, isolates event
`0x1E` to callback 9, and checks callback 10's converted seven-entry event
table. Its deterministic report SHA-256 is
`15BA39813EE3B54BFA3181251432310E558420D2491A8FF4AAE8825D5DC6FB80`.
This is static evidence only.

The seventh layer installs the converted Shoot child P1/P0/P2 resources at
`0x5B9000`, `0x5B9200`, and `0x5B9300`. The integration builder checks exact
v35 input identity, the builder-owned 8 MiB expansion, an all-`FF` ownership
window after the last v35 placement, zero pre-existing aligned pointers into
the planned interval, and exact diff containment. The independent verifier
does not import the converter; it checks the fixed asset hashes, native
container topology, and all eleven post-insertion pointers. Every pointer is
internal to the containers, so this is disconnected storage evidence rather
than a runtime-consumption claim. The report SHA-256 is
`1047C6163FCC7C40D0F4CED65305108BFE16CD5ED2C9E3DF84ADA757AC504E3F`.

The eighth layer installs ARM7TDMI translations of WSC generator `9229` and
callbacks `94C1`, `9570`, and `9617` at four builder-owned ranges. The builder
checks exact v36 input and WSC/GBA oracle hashes, an all-`FF` ownership window,
zero pre-existing aligned pointers into that window, and four Expected Writes.
An independent verifier re-derives the exact diff, disassembles the final ROM
placement, rejects instructions outside the target ISA, checks native call
graphs, and proves the three resource literals and complete internal callback
chain. The audio-lineage analyzer pairs all eleven WSC 1.0 requests in this
commercial object cluster with the eleven GBA calls in source order, then
independently compares the underlying WSC command payloads. This corrects the
provisional equal-ID assumption: WSC 1.5 `A7` exactly matches WSC 1.0 `A5`,
which maps consistently to GBA `0x4A`; WSC 1.0 `A7` instead maps to GBA
`0x4C`. The analyzer also proves that parent/upper-state sound `CE` has a
unique 30-byte Ver. 1.5 payload with no exact match among bounded WSC 1.0
sounds `00..B8`. Its expanded target population additionally checks three
upper-state `D2` requests, request type 2. `D2` has a distinct 32-byte
Ver. 1.5 payload with no WSC 1.0 match and therefore remains a native-
reconstruction boundary. The updated report SHA-256 is
`0CD28C17EB6DC3F1FE88F0FB755910434EC0B05DD06AD2F164A078BBEE60997E`.
v39 installs the corrected `0x4A` request in generator `9229`; the independent
integration report SHA-256 is
`ACA1CE4BABEC56324AA5F06D216F462DB50FD7F3128FF7BD9C233321D8058F05`.
No external pointer reaches generator `9229`; parent `9083`/`912A`, runtime
reachability, and audible playback are explicitly outside this layer. The
following v40 layer resolves only the separate `CE` asset dependency.

The ninth layer resolves the static `CE` asset dependency without assigning a
retail sound ID that does not exist. It preserves the commercial song table
IDs `00..5A` byte-for-byte, relocates the table, appends native ID `0x5B`, and
retargets all five commercial lookup literals. The new one-track M4A asset
uses commercial square voice `0x14` and maps WSC packed note `0x10`, its
20-tick lead, and four 10-tick volume steps `9,6,3,1` to a 60-tick GBA
pitch/timing/decay schedule, held by the correct M4A N72 opcode `0xF7`. The
independent verifier confines the layer to
790 changed bytes, checks the complete table and pointer population, parses
both source and target command schedules, and reproduces report SHA-256
`98EB32D4CA01A8AF1F824D1FAB6E88E2F735CB620DE012D819182498D72EC748`.
This proves a bounded semantic reconstruction only. In v40, parent
`9083`/`912A` did not yet request ID `0x5B`; the following v41 layer connects
that internal request. Runtime playback and audible/timbre parity are not
claimed.

The tenth layer installs translations of parent callbacks `9083`, `90F3`,
`912A`, `91AB`, `91EF`, and idle `88F7`. They preserve the four cleared motion
fields, target-relative start position, presentation events 0→1→2→3,
60/38-tick oscillation phases, Shoot flag `0x40`, linked-object flag lifetime,
and final offscreen cleanup. `9083` requests native `0x5B`; `912A` requests
payload-proved `0x4A` and calls resident generator `9229`. The commercial WSC
1.0/GBA generator pair directly proves that source linked-object field `+0x1C`
maps to GBA `+0x28`.

The independent verifier confines this layer to 695 changed bytes,
disassembles all six final-placement ARM7TDMI functions, checks every native
call and five internal callback literals, and asserts the translated field,
timer, event, flag, generator, and audio argument words. Its report SHA-256 is
`3989E33CD893742F9DD116D7050D9F33071763A04D9A174321EEC0A723755D13`.
No v41 pointer outside the inserted parent window reaches `9083`; controller
`9908/9A1B`, runtime reachability, and audible playback remain excluded.

`tools/analyze_shoot_initializer_resources.py` now guards the full 1,034-byte
`4090:7168` initializer/local-table range and all nine direct resource call
signatures. It resolves two constructor triples and seven direct loads to five
unique P0, two unique P1, and four unique P2 sources. All five P0 containers
convert deterministically; the four P2 blocks convert to fixed 40-byte GBA
forms. P2 source `0x3D4B20` is byte-identical to the already generated Shoot
spawn-palette source `0x3D7AF0`, while `0x3D6B16` converts byte-for-byte to
commercial GBA data at `0x080D3078`.

The two P1 sources are explicitly not fed through an incompatible converter.
They contain 6/13 logical commands and 34/109 payload items; their largest
payload word-1 indices are 3/49. Those indices address the paired P0 layouts,
whose converted containers expose exactly 4/50 entries; they do not size P1 A
data. Each P1 source instead references one eight-byte A record, and both
records are byte-identical. Adjacent bytes are explicitly excluded from the A
record boundary. The first P1 source also requires a relocated non-null
10-byte B record. The existing generic parser rejects the sources for distinct
structural reasons, while the spawn-specific converter forces every B pointer
to zero. The commercial oracle below proves payload, A-record, and B rules.
The same report maps WSC player slots
`ES:065C/065E` to GBA pointer slots `0x0300489C/0x030048A0` and isolates the
Ver. 1.5-only auxiliary object `ES:071E`. At this analysis stage its native
counterpart remained deliberately unassigned; the later dedicated lifetime
analysis resolves it through commercial lineage. Two report runs reproduce SHA-256
`4367C6588F904C282DD857E37CC6F67AC9B8E5DAB8FA8D222239655D7522C1C5`.
This analysis writes no ROM bytes; the later v42 resource-only installation is
a separate Expected Writes layer and does not change the runtime percentage.

`tools/analyze_direct_p1_commercial_oracle.py` now guards twelve exact WSC 1.0
to USA GBA P1 container pairs comprising 92 commands and 283 payload items.
All 283 match the complete Shoot-lineage 12-to-16-byte conversion; 266 also
match the zero-tail subset, while the 17 remaining spawn items prove the
word-5 tail relocation. A commercial non-null-B pair proves six 10-byte B
records byte-for-byte, alongside 86 exact null pointers. Both Ver. 1.5
initializer sources have zero non-null word-5 items, so their 34/109 payload
populations are inside the proved conversion rule. All 92 commercial command
references, covering 14 unique source/target mappings, also prove that each A
record is exactly eight bytes and remains byte-identical; unrelated adjacent
bytes are not interpreted. Two report runs reproduce SHA-256
`21B9DF5B7248E069FF4AC750C34305D42B6974FE5141C667B31A231B2E19D82B`.
The oracle is read-only and uses neither runtime nor the supplied save.

`tools/build_shoot_initializer_p1_assets.py` now emits both native P1
containers at `0x085D0000..0x085D0A4C`. The 2,636-byte blob contains 19
commands, 143 converted payload items, two unique eight-byte A records, and
the one required non-null 10-byte B record; SHA-256 is
`778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2`.
An independent parser verifies every final-placement pointer and source-derived
payload/A/B byte; its report SHA-256 is
`A435A75BA9D68D4D937125F3B0523BE54980A21D58EBE86E137A665B1DA3CBAD`.

v42 installs that P1 blob, all five converted P0 containers, and the two P2
blocks that are not reused from existing data in the pointer-unclaimed
`0x5D0000..0x5DB768` ownership window. The Expected Writes layer changes
44,696 bytes only inside eight declared placements. Its independent verifier
checks every placed hash, all preserved gaps, and 198 internal pointers; zero
post-write pointers originate outside the ownership window. Verification
report SHA-256 is
`7114A9C7B8CA51F8C52254EB03C3771F90B0CBB63B2D19D3D9B50ABA34A3576B`.
No code or menu route points to these resources yet.

`tools/analyze_shoot_d2_sound.py` guards the WSC 1.0/1.5 command handlers and
decodes the unique Ver. 1.5 `D2` payload as setup `A1=09`, `A2=01`, `C1=00`,
`A3=20`, followed by nine packed notes lasting 40+8×5=80 ticks. Volume `0x0F`
has left nibble zero and right nibble fifteen. Commercial WSC 1.0 sound `B5`
uses the same `A2=01` wave and maps to USA GBA sound `0x56`, whose native
track selects voice `0x1F`; this bounds the timbre selection without claiming
audible identity. The report SHA-256 is
`ECB4780B4EC38D44B6F5FC0B11D7E45A7BF0D30214474D5A45778F91CC231E0B`.

v43 preserves song IDs `00..5B`, appends native ID `0x5C`, and writes only an
eight-byte table entry plus a 67-byte song. The independent verifier checks
all nine pitches, all note/wait durations, 80 total ticks, right pan, voice
`0x1F`, native pitch MOD, exact diff containment, and both new pointers. Its
report SHA-256 is
`A636C763D0AF93DA8E47D9BC67DDBD8F1895D1A4BF95C1AE0029CF2A3C79B473`.
The three source upper-state requests are connected inside resident v46,
whose graph remains externally unreachable; conditional WSC
hardware-channel-3 sweep response and audible parity remain final hidden-QA
boundaries.

The same interpreter proof corrects the CE commentary: `A1 72` is sweep
control, not note duration. The source schedule still totals 60 ticks and M4A
`FINE` ends the longer note gate at that boundary. CE's header and every `A0`
volume step have zero left nibbles, so v44 changes exactly one pan byte from
center (64) to right (127). The independent verifier also checks that v43 D2
bytes are unchanged; report SHA-256 is
`A087DCD31E27A17615AEB897BD037F090F69C699D1EB2C6384674D4B2F0A0ABA`.
No emulator or supplied save is used by either layer.

`tools/analyze_shoot_aux_object_lifetime.py` closes the former `ES:071E`
allocation gate through exhaustive source references and commercial lineage.
Ver. 1.5 `ES:071E` and WSC 1.0 `ES:06A2` both use allocation ID `0x343`, pool
5, equivalent screen-effect consumers, and matching object roles. The exact
USA GBA counterpart uses native slot `0x03004D3C`, allocator `0x08352374`,
callback `0x083703EC`, the same ID/pool, and matching field offsets. Its timing
oracle converts 225/400/420 source ticks to 180/320/336 native ticks at 75→60
Hz. Two report runs reproduce SHA-256
`8F7E38A3C835503B5F1598CD9CD2468A7E229A1B483307F8A918D5ED10097F50`.

v45 installs a 436-byte resident ARM constructor at `0x085BC200` and the
four-byte native `BX LR` form of source idle callback `88F6` at `0x085BC600`.
It allocates through the proved commercial ABI, populates the native fields,
binds player slots and installed Shoot rule resources, and links the object
back to the active player. Exact diff containment covers 434 changed bytes.
The independent verifier checks final-placement calls, literals, field stores,
resource preservation, lineage signatures, and that no caller reaches the
constructor. Its report SHA-256 is
`BC3B8E04C681C6DB7EF3A3A9A1BDF02B320E7478590877E0C5513C3327610228`.
No emulator, supplied save, or runtime claim is involved.

v46 installs the remaining 25 upper-state callbacks after v45's `88F6` idle
member. Three code ranges plus that idle byte cover 2,320 reachable source
bytes. The 29 declared placements include the fourth P2 record, seven-row
intro palette, eight movement targets, and native presentation/trigonometry/
RNG/P2-loader/sound calls. Exact diff containment covers 4,144 changed bytes.
The independent verifier checks fixed placement hashes, all native call
targets, internal callback pointers, source-derived palette/target data, and
the three `0x5C` requests. It separately guards central X/Y dead-band paths,
the retained completion-count field, and address-based palette table indexing.
Both calls corresponding to `8057/80AF` stop at the `0x085C0A00` boundary stub,
and no aligned pointer outside the owned window reaches the resident graph.
Verification report SHA-256 is
`504A375A5A4F98A6F92975D06044FC46791481915E3A7FF528FA21ECF38353EE`.
This is resident-code/static evidence only; initializer/menu reachability,
controller rules, runtime behavior, audible parity, and save QA remain open.

v47 corrects three faults that the earlier constructor verifiers missed:
P1/P2 arguments were reversed in both the child and auxiliary constructors,
and the auxiliary primary/secondary player identities were reversed. The
native constructor consumer at `0x080127E4` proves entry-SP `+48/+36/+24`
correspond to P1/P0/P2. The source `71D1..7394` and commercial player setup
prove active slot `0x030048A0` and other slot `0x0300489C`. The six dependent
word changes preserve all historical build layers and leave shared palette
literals intact. This supersedes the earlier claim that v45's link/argument
semantics had been verified; hashes and literal lists did not establish them.

The resident v47 phase at `0x085C1000` supplies active flags, HP/difficulty,
thresholds, motion reset, bounds, presentation/P2, callback `7792`, auxiliary
reconfiguration and active links. The eight-byte entry `0x085C1300` bypasses
the existing constructor's allocator and reuses its body at `0x085BC244`.
It requires valid existing active/other/auxiliary objects; upstream lifetime
and the outer initializer remain open. The source `36C0` setup does not itself
allocate fighters, correcting an earlier working hypothesis.

`tools/verify_shoot_player_binding.py` checks the native consumer and actual
stack argument order, reproduces the three old defects, rejects all six
individual reversions, checks the HP/table/field and stack contracts, and
confines 459 changed bytes to nine writes. All 98 newly generated instructions
round-trip at their final addresses with literals excluded from code. Report
SHA-256 is
`8427FBAD3FDD00EB15CCDF69D55BD39E0341E21629B86CD2B143AFFCC07F9930`.
No runtime evidence is added. Detailed source boundaries and remaining
contracts are in `records/digimon-shoot-runtime.md` under the v47 heading.

The commercial-lineage analyzer's earlier function-address mapping was
correct, but its report accidentally hashed `0x371xx` slices while labeling
the callbacks at `0x372xxx`. The ranges are corrected without changing the
mapped callback addresses. Corrected report SHA-256 is
`7F705C9F2623C93E0C90682DB9C90990188789A0ED6BCD8B633FB7C8040B7602`.

## Boot regression and correction

The exact v31 composite was rechecked with mGBA on a private Windows desktop,
with no emulator window visible on the user's monitor. At 45 seconds it had
returned to the initial white/blue frame instead of reaching the title. The
base, stage, progression, and full v31 layers shared this failure, while the
unaltered USA ROM reached the title under the same harness.

Binary ablation isolated the failure to the relocated roster literal at ROM
offset `0x83CF8`. The builder treated `0x0D3FC0` as the start of each 0x20-byte
record, but the engine consumer at `0x08088250` reads fields at offsets 0, 4,
and 8 from the canonical record base `0x0D3FB8`. The relocated table therefore
lost its first eight bytes and supplied `0xFFFFFFFF` fields during the opening
sequence. The minimal correction relocates from `0x0D3FB8` to `0x4A80F8`,
preserving all existing pointer values while copying complete records. Builder
assertions now require unchanged retail records to remain byte-identical.

## Runtime status for exact v32 candidate

The exact full v32 SHA-256 is
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`.
It was run for 45 seconds with development mGBA SHA-256
`0D9A2779ADD78D41A093C3AF8CEC7D72CC07A5451C8A1E1B167B48CD54950288`
on a private, non-interactive Windows desktop. The captured 240x160 title
frame SHA-256 is
`644C6C5269FB847FF90BB9ADDFECC11462830A96CFCC47D9D33A2620455F387B`,
byte-identical to the historical known-good title capture. The evidence and
memory hashes are recorded under ignored directory
`evidence/full-fixed-gdb-title-20260831-r2/`; its manifest records
`monitor_visible: false`.

The next controlled run pressed the default mGBA Start key at 45.0 seconds,
held it for 0.25 seconds, and captured at 52.0 seconds. Exact v32 produced
menu-frame SHA-256
`CFDA553C0C6B14BB65E8A34543E3A657B92338751B207644A9D42D2786C24BF2`,
byte-identical to the unmodified USA ROM under the same timings. Palette,
VRAM, and OAM hashes also match the USA control. Manifests are under ignored
directories `evidence/usa-gdb-menu-20260831/` and
`evidence/full-fixed-gdb-menu-20260831/`, both with `monitor_visible: false`.

A second scheduled input pressed the default mGBA A key at 53.0 seconds and
captured at 60.0 seconds. Exact v32 and the USA control both entered display
state `DISPCNT=0x6B40`; palette, VRAM, and EWRAM were byte-identical. Their
frames differed by 635 of 38,400 pixels and OAM differed from offset `0x210`,
consistent with a different sprite-animation phase at a wall-clock capture;
the shared selection background and game state are direct evidence for the
transition, not for roster correctness. Manifests are under ignored
directories `evidence/usa-gdb-character-select-20260831/` and
`evidence/full-fixed-gdb-character-select-20260831/`.

A third A press at 61.0 seconds and capture at 75.0 seconds entered the first
retail battle in both ROMs. `DISPCNT=0x3F40`, the full palette, battle state
`0x03002310..0x0300231F`, stage byte 1, and player pointers
`0x0300489C/A0` match. Exact v32 differs as intended in the selection list
(`0x03004710`) and maximum cursor (12 instead of 6); dynamic battle VRAM and
the frame are not byte-identical because the independently timed battles had
already advanced to different animation/camera phases. This proves baseline
battle entry only. Manifests are under ignored directories
`evidence/usa-gdb-first-battle-20260831/` and
`evidence/full-fixed-gdb-first-battle-20260831/`.

The first directional-input experiment compared player coordinates at two
wall-clock times. The USA control moved right, but v32 had already entered a
different combat/animation phase and its object was repositioned; that result
is `INCONCLUSIVE`, not evidence of either success or failure. Static analysis
then identified the common retail input consumer: `0x083750FC` loads the frame
input at `0x03001302`, and `0x08375138/3C` stores the translated halfwords to
the current player object's `+0x2C/+0x2E`. A corrected run delivered Right
while stopped and broke at `0x08375140`, immediately after those stores.

Both the USA control and exact v32 produced GBA `KEYINPUT=0x03EF` (Right
active-low), frame input `0x0002`, registers `r0=r1=0x0002`, and player-1
fields `+0x2C/+0x2E=0x0002`. This directly proves the same bounded Right-input
consumer path. Evidence is under ignored directories
`evidence/usa-gdb-first-battle-right-consumer-20260831-r2/` and
`evidence/full-fixed-gdb-first-battle-right-consumer-20260831-r2/`; both
manifests record `monitor_visible: false`.

| Runtime area | Status | Evidence or limitation |
|---|---|---|
| ROM build and header | PASS | Four corrected layers rebuilt; header validated |
| GBA boot / first rendered frame | PASS | Exact v32 rendered through the opening sequence |
| Initialization beyond first frame | PASS | Exact v32 reached the stable title frame at 45 s |
| Title/logo | PASS | Exact title PNG matches known-good capture byte-for-byte |
| Main menu | PASS | Post-Start frame is byte-identical to the USA control |
| Input response | PASS | Start/A transitions and battle Right consumer observed |
| Character select entry | PASS | A input reached matching display/background/game state |
| First gameplay entry | PASS | ID-0 selection reached matching retail battle state |
| Background/map display | PASS | First retail arena rendered; stage ID matches control |
| Sprites, animation, palettes, scrolling | PARTIAL | Rendered in baseline battle; behavior not exercised |
| Collision, events, battle logic | UNKNOWN | Not exercised on exact v32 |
| Added fighters/evolutions | UNKNOWN | Static routes exist; no exact-v32 runtime proof |
| Added stage mechanics | UNKNOWN | Static code exists; no exact-v32 runtime proof |
| Digimon Shoot complete rules and transitions | PARTIAL STATIC ONLY | Current v53 includes lower rules, dedicated graphics/HUD, corrected twelve-map resources, connected normal stage/display updates, and resident terminal phases. Complete original-order initialization and normal-play scene entry remain absent; both `9908` calls still stop at a boundary stub. Bank-sensitive SRAM stores, terminal IRQ live-ins, spatial domains, full lifetime/callback routing, audible parity, and end-to-end win/loss/menu/exit remain gates. Uninstalled scene/controller drafts are not counted as integrated content |
| Tag/rating/opening additions | PARTIAL STATIC ONLY | The complete 19-linear + 5-choice opening graph is preserved in untested v47 through its v35 intermediate; tag/rating producers, persistence/UI, and all opening runtime behavior remain unverified |
| Alternate final boss route | UNKNOWN | Static integration exists; no exact-v32 runtime proof |
| BGM | UNKNOWN | Not verified on exact v32 |
| SFX | UNKNOWN | Not verified on exact v32 |
| Save/load | UNKNOWN | Deferred save has not been used |
| Soft reset / restart | UNKNOWN | Not exercised on exact v32 |
| Extended stability | UNKNOWN | No exact-v32 soak or regression run |

### Opening/presentation evidence correction (2026-09-01)

The 18-to-24 initializer increase is now connected to the registered cold-boot
roots rather than inferred from call counts. Static callback recovery proves
that the commercial GBA and WSC 1.0 openings each contain a 15-callback linear
path and three choice callbacks. WSC 1.5 contains 19 linear callbacks and five
choices. Every population member is graph-reachable from its version's
registered root.

Monotonic instruction-shape alignment identifies four WSC 1.5-only linear
callbacks at `7077`, `7407`, `7698`, and `7992`, plus choice callbacks at
`9C17` and `9E40`. Object-selector extraction also confirms the expanded
roster/evolution inputs. The split state is a high-nibble cycle: GBA/WSC 1.0
advance modulo 3, while WSC 1.5 advances modulo 5. New state 3 selects callback
`9E40` with pair `[13,14]`; state 4 selects `9C17` with `[12,11]`.

Internal v34 now translates those two added case setup blocks, both callbacks,
their motion/event tables, and the five-state dispatcher into GBA ARM code.
States 0..2 branch to the unchanged commercial GBA cases. The builder hashes
the exact WSC source ranges and reused GBA ranges, refuses nonblank expansion
targets, and is part of the clean main build. A dedicated 15-record resource
view preserves commercial selectors 0..10 and adds Ver. 1.5 selectors 11..14.
All four P1/P2 resources and selector 11/13 P0 resources reuse byte-identical
commercial assets. Only selector 12/14 P0 containers are newly converted and
inserted.

The four added linear callbacks at `7077`, `7407`, `7698`, and `7992` are
inserted at the chain edge from GBA `0x08085118` to `0x08085454`; the exact
assignment and selector instructions are ROM offsets `0x08516C` and
`0x0851CC`. The selector changes from 3 to 13 and the successor now runs four
new ARM callbacks before returning to the original `0x08085454` callback.

The first and fourth additions use WSC 1.5 replacement resource records 50
and 49. Their P0/P1/P2 inputs map to complete native GBA views at
`0x080D44D8` and `0x080D4498`. Internal v35 constructs record 50 in unused
opening slot 3 (`0x030029F8`) before callback 7, then reconstructs record 49
in the same slot before callback 10. The slot is updated and included in the
two-object skip populations only for callbacks 7 and 10; callbacks 8 and 9
use the one-object population. This follows the proven non-overlapping WSC
lifetimes without overwriting the retained commercial auxiliary objects.

Callbacks 7/8/9 follow the bounded commercial template lineages with converted
timers, fades, motion, and event IDs. Callback 10 uses the exact seven-event
source order with converted durations and activates the record-49 object on
event `0x25`. The independent verifier checks the callback call targets,
successors, selectors, native construction/update/skip adapters, changed-byte
boundary, and event table in the v35 opening-linear intermediate retained by
current v53. These are static
implementation facts, not visual, audio, timing, transition, or skip runtime
proof. No v51..v53 runtime evidence was collected. See
`records/opening-presentation.md` for addresses and manifest hashes.

A hidden/chromeless WSC 1.0 capture attempt parsed its command line but did not
start the Lua script. It generated no frame, RAM, or completion evidence and is
classified as inconclusive. No monitor-visible window was used, and no further
runtime attempt was made in this milestone.

## Known implementation gaps

- Train vents/bounce behavior, Iraira suction, and remaining vertical-stage
  engine branches.
- Digimon Shoot external parent/controller connection, remaining rules/object
  callbacks, private transition state, reward, win/loss, menu, exit, and audible
  playback parity.
- Tag/reward/rating persistence and associated UI.
- Extended opening visual/audio/timing/transition/skip behavior on the final
  integrated candidate; runtime validation remains deliberately deferred.
- End-to-end added-fighter evolution paths and alternate-boss outcomes.
- Audio parity, save/load parity, reset behavior, and stability regression.
- Final BPS generation/round-trip validation after all content and QA gates.

## Corrected progress statement

The previous 55-60% / 57% figure mixed static implementation with assumed
runtime readiness and is withdrawn. Based strictly on behavior directly
observed from the exact corrected v32 candidate:

| Area | Runtime-evidenced progress |
|---|---:|
| Graphics/display | about 12% (through first retail arena entry only) |
| Game logic | about 1% (baseline battle transition only) |
| Input | about 5% (Start/A transitions and one battle direction only) |
| Audio | 0% |
| Save/load | 0% |
| Overall playable/release progress | no more than 8% |

This does not mean the committed static code is absent. It means that code has
not yet earned runtime credit under the recovery audit rules.

## Single next milestone

### Current v53 implementation delta, 2026-10-13

The first milestone remains **DIGIMON SHOOT RULES AND TRANSITIONS**, not complete.
The new implementation is in the main build and detailed in
[SHOOT-V53](records/digimon-shoot-runtime.md#shoot-v53):

- CF/D1 native audio scores and 33 lower-rule routines, including `810D`, `8AB8`,
  `8CDD`, both child constructors, and original same-update branches. The lower
  pursuit routine still has a bounded spatial precondition; audio timbre and
  audible modulation parity remain unverified.
- Dedicated stage-11 graphics/HUD/IRQ preparation. Compact palette state fits
  its original 32-byte allocation, repairing the previous overlap with live AI
  state. Actual source palette projection and disable/dim consumers are hooked.
- The actual loader's C9 bank and segment `383F` correct the prior Shoot asset
  extraction. Twelve maps use original 2-by-3 geometry; independent inversion
  checks 111 colors, 32,768 pixels and 6,048 map entries.
- Source `0E0B` stage update and flag-0400-clear display/normal IRQ are connected.
  Layer order, old-index reads and the commercial scanline bridge are verified.
  The flag-0400 path preserves its existing fallback exactly.
- Seventeen terminal phases, three result resources, fatal/nonfatal adapters,
  and four upper-state same-update repairs are resident. External damage hooks
  remain original. The terminal row-clear camera domain is not yet proved.

SRAM report `29304FA8...27295` is included as **UNRESOLVED_OBSERVER**, with no
dead-store or native-mapping claim. Source `1000:3CD8/3CDA` must not be confused
with normal fighter globals at `0C00:3CD8/3CDA`. The terminal IRQ's interrupted
DI dependency remains a separate gate. Full initializer `085C7800`, controller
hook and scene/menu route are absent. Dependency-gated scene/controller drafts
are not installed ROM code and their full ROM verifiers have not run.

Two fresh v53 full builds in `build/repro-v53-20261013-a` and
`build/repro-v53-20261013-b` reproduce all 29 ROM layers and 155 files with zero
relative-path or SHA-256 differences. Candidate SHA-256:
`455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48`.
Build-manifest SHA-256:
`C6FF837E60965776EF42AA09AA1ACC83B5148239D859657AE6087CE16EE66941`.
Comparison `build/repro-v53-20261013-comparison.json` SHA-256:
`8CC96F98AEF076D796FCE731D542BB4AAD179580A906A35F0C20A41329153666`.
There are 30,992 changed bytes from v52, all guarded by the four new layers.
The earlier v52 two-build result also matched all 25 layers and 142 files;
its candidate is `6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29`.
Original ROMs and both v50/v51/v52 candidates were rechecked unchanged; header
checksum remains `6C`. No save, CPU execution, emulator, or visible window was
used. Runtime evidence remains v32 and gains no completion credit.

### Preserved v51 implementation delta, 2026-10-13

The three new layers implement 367 ARM instructions: 60 rule-selection/application
instructions, 196 palette instructions, and 111 bounded initializer/constructor
instructions. The controller preserves the 64-way source decision table, signed
difficulty handling and exact RNG call cardinality. Independent finite checking
covers 262,144 decision partitions and rejects twelve meaningful corruptions.
The absent `810D`, `8AB8`, and `8CDD` continuations still prevent a complete
controller adapter; `9908` remains a boundary stub.

Palette projection is now tied to actual consumers: source rows 0..7 use native
BG0..7, rows 8..15 use OBJ0..7, and their zero colors also feed BG8..15 backdrop
lookups. The 512-byte mirror and 528-byte hardware projection are distinct. The
384-byte selective copy, sixteen gray zero colors and the white/black/target
operations are implemented without modifying high BG colors 1..15. The verifier
checks all emitted instructions, inverse colors, finite channel progression and
eleven corruptions. Known competing writers and source snapshot lifetime are
recorded in [palette ownership](records/shoot-palette-ownership.md).

The separate [scene ownership proof](records/shoot-scene-ownership.md) identifies
the input/battle task replacements that exclude the known pause and repeated
match-end producers, and preserves the source restoration/retirement order.
It locates the future adapter at the existing case-5 allocation `0833FD18` /
callback literal `0833FDB4`. This requires normal completed startup, no other
live pause/cutscene owner, and replacement of the selected scene rather than
allocation of another one. Priority does not deduplicate tasks. This conditional
proof has sixteen fixed evidence ranges and seven semantic mutation negatives;
its standalone report hash is
`5F9323F4641873B03A6187EFF37FF3F1C559E46D028F0CA2887EF2E938ECA291`.
It is separate from the frozen v51 build graph because v51 installs no scene caller.

Initializer components add four BG descriptor resets, staging resets, the existing
Shoot graphics clone, stage-manager preparation, timer initialization, the proven
`1000:0660` halfword clear, and two resource constructor adapters. The timer's
18,000 source ticks map to 14,400 native ticks through commercial producer and
HUD-consumer evidence. The initial zero write to `03D4` is preserved before the
other two flag clears and final `0x10` assignment.

All 35 P1 payload items of the `93E7`/`888B` resources are independently read back;
their thirteen nonzero per-item references resolve to six owned ten-byte records.
The native draw consumer uses dynamic staging, so the source fixed-VRAM P0
preloads are represented by native P0 resource binding. These adapters do not
allocate an object, choose its first event or implement the surrounding callbacks.

The complete initializer is still absent. `ES=1000:3CD8/3CDA` is not interchangeable
with `DS=0C00:3CD8/3CDA`; its bank/consumer attribution remains open. Dedicated
display/IRQ preparation, source HUD/font/map setup and whole entry lifetime must
be resolved before the resident phases can be connected in original order.
The first milestone is **not complete**. No supplied save or emulator was used.

The baseline path through one `FIRST RETAIL BATTLE` Right-input consumer is
complete for exact v32. The v51 build preserves the complete static
19-linear + 5-choice opening graph and installs the internally connected Shoot
child generator/callback family over the v36 resource layer plus the bounded
native `CE`/`D2` sound assets, the internally connected parent chain, and the
resident native auxiliary component and full resident upper-state graph. It
corrects constructor resource roles/player identities and adds the resident
`71D1..7394` player-binding phase without an external caller.
The five broken P0 descriptor populations are now repaired rather than
classified as valid zero-tile resources. This removes a concrete asset defect
but does not establish the remaining initializer or normal-play entry.
v49 additionally corrects the three shifted physics pointers and supplies the
resident other-player portion `73F0..74A2`. The surrounding palette/resource
steps and transition ownership are not replaced by this portion. v50 adds
resident `7394..73A9` and `74A2..74DA` resource segments. The HUD tile copy
uses the actual native tile-`3FC`/OBJ-palette-6 consumer, not the source tile
number `91`. The other two P0 preload sites are linked to later source presentation
constructors at `93E7` and `888B`; v51 supplies native constructor/resource adapters,
while the surrounding callback and allocation lifecycle remains open.
The next active implementation milestone returns to the largest known content
gap: **DIGIMON SHOOT RULES AND TRANSITIONS**. Corrected entry analysis proves
`9908` is a helper, not the external entry. The next integration must translate
the remaining Ver. 1.5 initializer `4090:7168` preparation, tail `73A9..73F0`
and `74DA..7534`, connect the resident player and resource phases,
establish its existing-object lifetime contract, and replace the `9908`
boundary with the real rules
controller and parent-`9083` assignment before enabling the menu transition.
The three native `0x5C` requests are already connected internally. The bounded stage-7 fighter
spawn copy is not a real stage-11 record: Ver. 1.5 bypasses that retail path
through its dedicated initializer. Remaining object/rule callbacks,
transition state, reward/menu outcomes, and exit must stay in the same
reproducible main build. Runtime verification remains deferred and
non-displaying until all declared content is integrated.

All further runtime checks must remain non-displaying unless the user changes
that requirement. `tools/mgba_headless_gdb_capture.py` provides the current
private-desktop, attributable frame-and-memory capture boundary.
