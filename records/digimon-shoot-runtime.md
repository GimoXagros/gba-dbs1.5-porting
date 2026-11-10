# Digimon Shoot runtime boundary

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

[전체 빌드](repro-v76-inventory-qa-20261110.md) ·
[실제 종료](shoot-native-terminal-display-store-capture-qa-20261110.md) ·
[일반 전투](result-v76-capture-qa-20261110.md) ·
[원본 음악](wsc-original-evolution-bgm-20261110.md).

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

[빌드 검수](repro-v75-inventory-qa-20261110.md) ·
[일반 전투 검수](result-v75-capture-qa-20261110.md) ·
[종료 중단의 실제 순서](shoot-native-terminal-bg-epoch-capture-qa-20261110.md).

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

[전체 빌드 검수](shoot-native-v74-build-qa-20261109.md) ·
[일반 전투 검수](result-v74-runtime-qa-20261109.md) ·
[실제 적중 검수](shoot-positive-hit-aim-capture-qa-20261109.md) ·
[종료 관찰 절차](shoot-native-terminal-probe-20261109.md).

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

[첫 입력 검수](shoot-first-native-input-qa-20261109.md) ·
[새 중단 원인](shoot-child-attack-pointer-cause-20261109.md).

## 2026-11-09 실제 Shoot 초기화·조작 대기 도달

별도 개발 ROM `84D6FA3F…CA43B`에서 대상 포인터를 함수 호출 뒤에도 보존하도록
5곳을 고쳤다. 실제 보스 격파 뒤 초기화67786→67788, 체력4 복원68815,
컨트롤러 복귀68926, 조작 대기68927을 창 없이 관찰했다. 새 치트 쓰기는0회다.
주 빌드는 아래 v73 그대로이며, 첫 입력·비치명타·종료는 이어서 검증한다.

저장 복원 시 CPU·게임/그림 메모리는 같지만 사운드·통신 상태12바이트가 달랐다.
수정 전 ROM의 무진행 대조에서도 동일하게 재현됐다. 코드 수정과 무관함을
확인했지만 원본 저장 전체 일치 검사는 실패로 유지한다. E5와 최종 완성은 미해결이다.

[실행 결과와 독립 검수](shoot-native-entry-replay-capture-qa-20261109.md).

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

[통합 기록과 고정 해시](shoot-terminal-integration-v73.md).


## Evidence boundary

This record uses the hash-identified clean Ver. 1.5 WSC ROM and the commercial
WSC 1.0/USA GBA originals for comparison. The supplied SRAM has not been
opened. All conclusions below are static control-flow observations; they
do not claim that the internal GBA build runs the mode.

The fixed, hashed source regions are generated by
`tools/extract_wsc15_shoot_runtime.py` in
`evidence/wsc15-digimon-shoot-runtime.json`.

## Confirmed mode split

Digimon Shoot is stage ID 11, but it is not an ordinary two-fighter arena.
The general WSC battle loop at raw `0x74583E` reads the actual stage ID and
branches to the dedicated routine at raw `0x747E72`. Consequently, adding
stage graphics and a normal initializer/update entry cannot complete the
minigame.

The dedicated mode depends on four connected boundaries:

1. the stage-11 route into the dedicated battle loop;
2. overlay update entry 11 at relative `0x2067`, its display callback
   `5EEA:0C3A`, transition helper `5EEA:0E0B`, and palette tables;
3. stage-11 object/presentation branches at raw `0x760229` and `0x771F73`;
4. the dedicated exit path at raw `0x772553`, which calls `71F0:1750`.

The mode fade path produces word `1000:03D4` bit `0x8000`. The progression
integration already reserves that bit as the Digimon Shoot completion input,
but the producer is not yet present in the GBA build. It must be generated by
the dedicated mode path before the progression gate can be considered
connected.

## Current implementation state

Internal stage build v30 contains the converted palette, tiles, eight maps,
two resource descriptors, stage initializer slot 11, update-table slot 11,
and safe mappings for unrelated legacy stage-index tables. Its relocated
object-configuration table contains the native stage-11 pair and translated
presentation callbacks `4090:432F`/`4090:43E6`.

The update slot now translates the WSC entry's camera threshold scan and its
three-rate palette helper. Commercial stage-7 code proves these address
mappings: WSC `1000:01CE`→GBA `0x03002338`, WSC
`0C00:3CE0/3CE2`→GBA `0x03004D44/46`, WSC `1000:0174`→GBA
`0x03003D30`, and WSC `1000:03D8`→GBA `0x0300450A`. The 32 threshold
halfwords are retained byte-for-byte. All 202 colors selected through the six
source pointers at WSC overlay `0x225F` are converted to BGR555, while the
original 8-tick, 10-frame, 8-frame, and 7-frame cadences are preserved.

The update now registers a GBA translation of the Shoot-only normal display
callback `5EEA:0C3A`. Direct comparison with the commercial WSC
`9070:072C`→GBA `0x080C97B8` conversion proves the callback slot and the
current/saved threshold position and index mappings. Its normal path connects
a translated scanline threshold callback from `5EEA:0D42`. When Shoot flag
`0x400` requests the separate transition family, it deliberately falls back
to retail callback `0x080C97B8`; WSC `5EEA:0D87/0E0B` uses additional state
whose GBA RAM/hardware mapping is not yet proven.

The commercial GBA main routine at `0x083700F0..0x0837024C` exactly matches
the retail WSC path at `4090:583E`. v27 hooks its first literal load and checks
the actual stage ID at GBA `0x0300231E`: stages 0–10 reproduce the displaced
`0x03004D42 += 0x140` operation and rejoin commercial code, while stage 11
enters a static ARM translation of WSC `4090:7572..7641`. The translated loop
uses the proven player globals `0x0300489C/A0`, scanline records
`0x03001428`, common flags `0x03004506`, Shoot flags `0x0300450A`, scroll
state `0x03004D40`, and input `0x030012B4`.

WSC `4090:7642..76D0` is also translated as its exact signed scroll state
machine. Its 48 BGR444 colors at `4090:76D1..7730` become BGR555; a centered
pointer and `state >> 2` select sixteen colors written to BG palette memory at
`0x20`-byte spacing. The positive `0x3F` reset, negative `-0x80` clamp to
`-1`, and zero-settling behavior are retained.

v28 replaces the timer-expiry call with a static translation of Shoot-only
`4090:989C..9907`. The source chooses three 38-byte WSC runtime-palette blocks
at physical `0x3D4B20 + 0/0x26/0x4C`. Before converting them, the build proves
the same selection and 38→40-byte record rule against all three blocks used by
the commercial WSC `4090:6FDE` / GBA `0x083731A0` pair. This family differs
from character palette records by carrying the source count in the two-byte
GBA trailer. The callback retains both source position comparisons and calls
the scroll helper only when Shoot flags `0x4000`, `0x20`, and `0x10` are all
clear.

## Rules callback boundary

The complete first rules unit is now bounded statically, but only its first
child-object family is installed in the GBA candidate.
`tools/analyze_shoot_rule_callback_graph.py`
starts at controller `4090:9908`, its four selected families, and every
callback pointer reached from them. The source-verified graph contains 2,051
instruction starts, 6,096 code bytes in 16 ranges, 43 callback entries, 46
callback-pointer edges, and 14 same-overlay calls.

All three indirect jumps are resolved rather than left as guessed exits:

- controller `996A` indexes the exact 64-word table at `996F`; its targets are
  `99EF` (18 entries), `99F1` (10), `9A0E` (20), and `9A1B` (16);
- shared object constructor `173D` has six source table cases, while the three
  reachable Shoot call sites pass only cases 0 and 2, selecting `174E` and
  `175D`;
- Shoot state dispatcher `8F24` has ten entries at `8FDB`; state 0 selects
  `8F29`, while states 1..9 select `8F65`.

The graph imports ten WSC runtime routines: `4FFF:0BA4`, `0BC7`, `19A8`,
`19BF`, `1BD9`, `1CB5`, `23F4`, `24CB`, `26CB`, and `2862`. A separate
commercial-lineage proof now binds three callbacks and five of those imports
without assigning names from guesswork:

| WSC 1.5 callback | WSC 1.0 physical ancestor | Commercial USA GBA callback |
|---:|---:|---:|
| `94C1` | `56D9` | `0x08372110` |
| `9570` | `577A` | `0x083721FC` |
| `9617` | `5821` | `0x08372320` |

The paired commercial call sites prove `4FFF:1BD9`→GBA `0x08012560`,
`19BF`→`0x0801233C`, `19A8`→`0x08012348`, `24CB`→`0x08012874`, and
`2862`→`0x08012A84`. The completion state's `4090:181E` object-release path
has commercial GBA counterpart `0x083524C4`. The deterministic reports are
generated as `build/shoot-rule-graph-v2.json` and
`build/shoot-commercial-lineage-v2.json`. Their reproducible SHA-256 values
are `37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281`
and `7F705C9F2623C93E0C90682DB9C90990188789A0ED6BCD8B633FB7C8040B7602`,
respectively; they claim static source lineage only and do not claim working
GBA rules. The prior v1 lineage report used the correct callback addresses and
call-target mapping, but accidentally hashed `0x371xx` byte slices while
labeling `0x372xxx` ranges. v2 corrects that byte attribution; no callback
address mapping changed.

The graph-wide lineage pass also binds the child-object generator `9229` to
WSC 1.0 physical `5A93` and commercial GBA `0x0837273C`. That commercial
function proves the native GBA object allocator at `0x08352374` and the
presentation constructor at `0x080127E4`. The new generator's three far
resource arguments resolve to:

| Kind | WSC 1.5 physical source | Deterministic GBA-form analysis output |
|---|---:|---:|
| P1 command container | `0x3D1E30` | 384 bytes, three commands / 20 payload items |
| P0 animation container | `0x22FF80` | 128 bytes, two layouts / 80 layout-record bytes |
| P2 palette | `0x3D7AF0` | 40 bytes, converted BGR555 palette |

`tools/analyze_shoot_spawn_resource_conversion.py` verifies the rules against
the exact WSC 1.0/GBA resource ancestors before converting the Ver. 1.5
sources. The Shoot-specific P1 oracle covers seven commercial commands and 42
payload items: `FFxx` timing scales by 4/5, a nonzero sixth word moves to the
two GBA extension words as `(word + 0x032C, 0x0835)`, and all payloads and
8-byte A records then match the commercial GBA byte-for-byte. The P0 oracle's
784 logical bytes match exactly; the remaining eight bytes in the comparison
belong to the next commercial structure. The P2 oracle matches all 40 bytes.
Two independent reports reproduce SHA-256
`E8C1F9318EC605427781F00BF848AE464B0BEE3B9F89B96456212B3ECBFA7614`.
## Installed disconnected resource layer (v36)

`tools/build_shoot_rule_resources.py` now regenerates the three child assets
from the hash-identified source ROMs after rerunning the complete commercial
oracle above. `tools/build_shoot_resource_integration.py` installs P1 at
`0x5B9000` (384 bytes), P0 at `0x5B9200` (128 bytes), and P2 at `0x5B9300`
(40 bytes). The input is exact v35, the builder asserts the complete
`0x5B851C..0x5B9328` ownership window is still `FF`, rejects any pre-existing
aligned ROM pointer into the planned range, and confines the final diff to the
three Expected Writes.

`tools/verify_shoot_resource_integration.py` does not import the converter.
It independently checks the fixed asset hashes, three-command/20-item P1
topology, two-layout/zero-descriptor P0 topology, 20-word P2 palette, and the
complete aligned pointer population. The only pointers into the new interval
are eleven internal container pointers; no callback or external consumer
reaches the assets. Its deterministic report SHA-256 is
`1047C6163FCC7C40D0F4CED65305108BFE16CD5ED2C9E3DF84ADA757AC504E3F`.
Two clean original-source builds reproduce internal v36 SHA-256
`4028AB75706FDE162E7F247B2AD52CAB20E9B30E487C306B70EE1E1F38E2F45C`.
This is storage and container evidence only, not runtime reachability.

## Installed resident child/parent families and sound assets (v39/v40/v41)

`tools/build_shoot_child_integration.py` installs translations of generator
`9229` and callbacks `94C1`, `9570`, and `9617` at `0x5B9400`, `0x5B9800`,
`0x5B9C00`, and `0x5BA000`. The generator constructs child ID `0x410B`,
connects the v36 P1/P0/P2 resources, sets the initial callback, and emits event
0. It then issues the proved native GBA sound request. The initial and homing
callbacks use the proved native angle, X/Y trig,
event, and presentation-update calls; they advance internally to `9570` and
then `9617`. The completion callback releases the child and clears Shoot flag
`0x40`.

The builder requires exact v36 input, exact WSC 1.5 source-range hashes, exact
commercial GBA oracle hashes, a builder-owned all-`FF` interval, no
pre-existing aligned pointers into the code window, and four Expected Writes.
`tools/verify_shoot_child_integration.py` is independent of the builder. It
checks the exact changed-byte set and fixed function hashes, disassembles the
final-placement ARM7TDMI code, rejects unsupported instructions, verifies all
native branch targets, and proves the three resource pointers and internal
callback chain. Its report SHA-256 is
`ACA1CE4BABEC56324AA5F06D216F462DB50FD7F3128FF7BD9C233321D8058F05`.

`tools/analyze_shoot_audio_lineage.py` checks the complete local population of
eleven WSC 1.0 sound-queue writes against the eleven same-order commercial GBA
calls. Repeated source IDs map consistently and request type is preserved in
all eleven rows. The analyzer then follows each six-byte WSC sound-table entry
to its command payload instead of assuming that equal IDs survived the 1.5
table expansion. WSC 1.5 `A7` has the exact 36-byte payload of WSC 1.0 `A5`,
not WSC 1.0 `A7`; commercial WSC 1.0 `A5` maps consistently to GBA ID `0x4A`.
Both WSC 1.5 request sites in parent `912A` and generator `9229` use `A7`,
request type 1; v39 installs the generator-side call with
`(r8,r9,r10)=(0x4A,1,0)` through native writer `0x080D15C0`.

Parent initializer `9083` separately requests sound `CE`, request type 1.
Its 30-byte command payload is unique to Ver. 1.5 and has no exact match in
the 185 independently bounded WSC 1.0 payloads `00..B8`; therefore no retail
GBA sound ID is claimed for it. The upper state graph also issues sound `D2`,
request type 2, at offsets `7976`, `79F9`, and `7CC6`. Its 32-byte command
payload is likewise unique to Ver. 1.5 and has no exact WSC 1.0 match, but it
is decoded and installed by the later v43 layer as native ID `0x5C`; v46 now
connects all three request sites inside the resident upper-state graph, although
that graph remains externally unreachable. The deterministic
expanded lineage report SHA-256 is
`0CD28C17EB6DC3F1FE88F0FB755910434EC0B05DD06AD2F164A078BBEE60997E`.
Two clean original-source builds reproduce internal v39 SHA-256
`35B2F717A96573B0823E43433A547B5398CC13129DAEECED6646153FC69F5492`.

v40 supplies that missing asset as a bounded GBA-native reconstruction rather
than claiming a false retail correspondence. It copies commercial song IDs
`00..5A` byte-for-byte into a relocated 92-entry table, appends ID `0x5B`,
and retargets the five native song-table lookup literals. The new one-track
M4A asset uses commercial square voice `0x14`; WSC packed note `0x10` becomes
MIDI note 48, the initial `0x14`-tick segment becomes W20, and the WSC volume
steps `9,6,3,1` separated by four `0x0A` waits become GBA volumes
`76,51,25,8` separated by four W10 events. Both schedules total 60 ticks; the
note is held across that schedule by M4A N72 opcode `0xF7`.

`tools/verify_shoot_ce_sound_integration.py` independently confines the v40
layer to 790 changed bytes, checks that all old table references are removed
and exactly five new references remain, verifies the preserved 91-entry
prefix and new ID `0x5B`, then parses the WSC and M4A command streams. Its
independent duration table also proves that opcode `0xF7` is N72 rather than
the shorter N30 opcode `0xE9`. Its
report SHA-256 is
`98EB32D4CA01A8AF1F824D1FAB6E88E2F735CB620DE012D819182498D72EC748`.
Two clean original-source builds contain 73 files each with no path/hash
differences and reproduce v40 SHA-256
`9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B`.

v41 installs the six-function parent sequence
`9083 -> 90F3 -> 912A -> 91AB -> 91EF -> 88F7` at `0x5BA800`, `0x5BAC00`,
`0x5BB800`, and `0x5BBC00`. The commercial WSC 1.0 generator `5A93` and GBA
counterpart `0x0837273C` directly prove that WSC linked-object field `+0x1C`
maps to GBA `+0x28`; the earlier provisional `+0x24` inference was corrected
before main-build integration.

The parent initializer clears four motion fields, copies the target position
with the source `-0x300` Y offset, emits presentation event 0, owns the linked
object's bit 0, requests native `0x5B`, and advances to the wait callback. The
remaining callbacks preserve events 1/2/3, phase-byte Y oscillation, timers
60 and 38, Shoot flag `0x40`, the call to resident generator `9229`, the later
native `0x4A` request, and final object/link cleanup.

`tools/verify_shoot_parent_integration.py` independently confines v41 to 695
changed bytes, disassembles all six final-placement ARM7TDMI functions,
checks their native call graphs and five internal callback literals, and
asserts the translated fields, timers, events, flags, generator edge, and
audio request words. Its report SHA-256 is
`3989E33CD893742F9DD116D7050D9F33071763A04D9A174321EEC0A723755D13`.
Two clean original-source builds contain 77 files each with no path/hash
differences and reproduce v41 SHA-256
`B192AC03F75FB1B55B3BCB3BA6363836EDDFCBBAC8379DAF6D9DAB08B9AD2E06`.

This is resident internal-chain evidence, not runtime reachability. No pointer
outside the inserted parent window reaches `9083`; controller `9908/9A1B`
remains unimplemented. Audible playback and timbre parity remain unverified;
the timing correspondence is static only.

The entry boundary is now corrected by
`tools/analyze_shoot_upper_state_graph.py`. Raw `0x773143` calls the dedicated
initializer `4090:7168`. That 1,034-byte source range assigns callback `7792`
to the active player and `88F6` to the rules object. The later stage-11 branch
at raw `0x760197` assigns `7AB1` and `7D8D` to the linked players. Walking all
four seeds finds 745 instruction starts, 2,320 code bytes in four ranges, 26
callback entries, 24 callback edges, six imports, and no unresolved indirect
transfer. Controller `9908` is reached only by direct calls at `8057` and
`80AF`; it is not an external callback entry. Two independent report builds
reproduce SHA-256
`55B6AD9E1FA162C67AE6B14A125F6D02E257506F80FB16786D54B678B49C75A0`.

`tools/analyze_shoot_initializer_resources.py` now resolves every direct
resource argument used by `4090:7168`. The two presentation-constructor calls
resolve to P2/P0/P1 physical triples
`3D4B20/3D5F80/3CF410` and `3D7640/3914E0/3BD730`. Seven additional direct
loads resolve to P2 `3D4B20`, `3D7640`, `3D7A90`, `3D6B16` and P0 `3D44E0`,
`3D0CA0`, `3D7D30`. The report guards all nine call signatures as well as the
complete initializer/local-table hash.

All five P0 containers have deterministic relocatable GBA builds: the largest
contains 50 layouts, 61 descriptors, and 35,616 tile bytes; the other four are
small layout-only containers. All four P2 sources convert to fixed 40-byte
blocks. `3D4B20` is byte-identical to the source already used for the installed
Shoot spawn P2, while converted `3D6B16` already exists in the commercial GBA
at `0x080D3078`.

The P1 source boundary is now resolved. `3CF410` contains six logical
commands/34 payload items, has maximum payload word-1 index 3, and includes one
non-null 10-byte B record. `3BD730` contains thirteen commands/109 payload
items and has maximum word-1 index 49. These indices address the paired P0
containers, which expose exactly 4/50 layouts; they do not size A data. Each
P1 source references one eight-byte A record, and the two records are
byte-identical. Adjacent bytes are excluded from the record boundary. The
existing generic parser rejects the first on a terminal zero-count table
interpretation and the second on a leading B-record underflow; the Shoot spawn
converter is also incompatible because it forces every B pointer to zero. The
direct-format commercial oracle below proves payload, A-record, and B behavior.

The same report statically binds `ES:065C/065E` to GBA player pointer slots
`0x0300489C/0x030048A0`. The rules presentation uses Ver. 1.5-only auxiliary
object slot `ES:071E`, allocated by `4090:172A` with callback `5134` and ID
`0x343`. That initial resource report did not yet resolve its commercial
counterpart. Two independent report runs reproduce SHA-256
`4367C6588F904C282DD857E37CC6F67AC9B8E5DAB8FA8D222239655D7522C1C5`.
The analyzer reads only the three hash-identified original ROM inputs; it
modifies no candidate and uses neither an emulator nor the supplied save.

`tools/analyze_direct_p1_commercial_oracle.py` separates command-payload, A
record, and B behavior from unrelated adjacent data. Twelve guarded commercial
WSC 1.0→USA GBA pairs contain 92 commands and 283 payload items. All 283 match
the full Shoot-lineage expansion, including 17 spawn items that require the
word-5 tail relocation; the other 266 match the zero-tail rule directly. The
pair at WSC `2B09C0`→GBA `34DFE0` also proves six non-null 10-byte B records
byte-for-byte, while all 86 null B commands remain null. Every one of the 92
A references, covering 14 unique source/target mappings, preserves its exact
eight-byte record.

Both Ver. 1.5 initializer P1 sources have zero non-null word-5 items, so their
34/109 payload items, one A record each, and null/non-null B behavior are now
commercially bounded. The report does not interpret adjacent bytes and
reproduces SHA-256
`21B9DF5B7248E069FF4AC750C34305D42B6974FE5141C667B31A231B2E19D82B`.
It performs no ROM writes, runtime validation, or save access.

The dedicated builder emits both native P1 containers at
`0x085D0000..0x085D0A4C`. The 2,636-byte blob contains 19 commands, 143
converted payload items, two unique A records, and one non-null B record; its
SHA-256 is
`778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2`.
An independent verifier re-parses the WSC source and checks every final pointer
and payload/A/B byte; report SHA-256 is
`A435A75BA9D68D4D937125F3B0523BE54980A21D58EBE86E137A665B1DA3CBAD`.

v42 installs that P1 blob with all five P0 containers and both non-reused P2
blocks at `0x5D0000..0x5DB768`. The ownership window was all `FF` in exact v41
and had zero aligned pre-existing pointers. The Expected Writes layer changes
44,696 bytes inside eight declared placements. Independent verification proves
198 internal pointers, zero external pointers into the new window, exact asset
hashes, and unchanged gaps; report SHA-256 is
`7114A9C7B8CA51F8C52254EB03C3771F90B0CBB63B2D19D3D9B50ABA34A3576B`.
Static intermediate v42 SHA-256 is
`AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E`.
No initializer or menu code points into this resource window yet.

`tools/analyze_shoot_d2_sound.py` guards the source `A0`/`A1`/`A2`/`A3`
handlers and proves D2 setup `A1=09`, `A2=01`, `C1=00`, `A3=20`. Nine packed
notes `20,18,17,16,15,14,13,12,11` last 40+8×5=80 ticks, with right-only
source volume `0x0F`. Commercial WSC 1.0 sound `B5` uses the same `A2=01`
wave and maps to USA GBA sound `0x56`, whose track selects voice `0x1F`.
Analysis report SHA-256 is
`ECB4780B4EC38D44B6F5FC0B11D7E45A7BF0D30214474D5A45778F91CC231E0B`.

v43 appends native ID `0x5C` while preserving IDs `00..5B`. It changes only
the eight-byte table entry and 67-byte song. Independent verification checks
all pitches/times, 80 total ticks, right pan, voice `0x1F`, native pitch MOD,
diff containment, and pointer population; report SHA-256 is
`A636C763D0AF93DA8E47D9BC67DDBD8F1895D1A4BF95C1AE0029CF2A3C79B473`.
Conditional source hardware-channel-3 sweep and audible parity are deferred.

The interpreter decode also corrects CE `A1 72`: it is hardware sweep control,
not note duration. The source schedule remains 60 ticks, with M4A `FINE`
ending the longer gate. CE's header and `A0` steps all have zero left nibbles,
so v44 changes one pan byte from center to right and preserves D2. Independent
report SHA-256 is
`A087DCD31E27A17615AEB897BD037F090F69C699D1EB2C6384674D4B2F0A0ABA`.
Static v44 intermediate SHA-256 is
`000683972B02F1E58369517F6AC32B270854ED2BBA4FC292BCA54E9E9700FBEB`.
No emulator or supplied save was used.

The dedicated lifetime analyzer closes the auxiliary-object mapping without a
guessed RAM allocation. Its exhaustive reference scan proves Ver. 1.5
`ES:071E` is the relocated form of WSC 1.0 `ES:06A2`: both use allocation ID
`0x343`, pool selector 5, the same object role, and equivalent screen-effect
consumers. The exact commercial GBA counterpart allocates into slot
`0x03004D3C` through `0x08352374` with callback `0x083703EC` and the same ID
and pool. The allocator implementation proves the seven-argument ABI, while
the commercial WSC/GBA constructor pair proves the complete field mapping;
225/400/420 source ticks map to 180/320/336 native ticks at 75→60 Hz. Two
report runs reproduce SHA-256
`8F7E38A3C835503B5F1598CD9CD2468A7E229A1B483307F8A918D5ED10097F50`.

v45 installs a resident 436-byte ARM constructor at `0x085BC200` and a
four-byte `BX LR` translation of source idle callback `88F6` at `0x085BC600`.
It uses native slot `0x03004D3C`, allocator ID `0x343`/pool 5, commercial
callback `0x083703EC`, player slots `0x0300489C/0x030048A0`, and the installed
initializer rule resources. The layer changes 434 bytes, has no constructor
caller, and therefore cannot affect retail flow before the upper graph is
connected. Independent final-placement verification report SHA-256 is
`BC3B8E04C681C6DB7EF3A3A9A1BDF02B320E7478590877E0C5513C3327610228`.
v46 installs the remaining 25 members of the source's 26-callback upper-state
population after v45's `88F6`. Its three source code ranges plus idle byte total 2,320
reachable bytes and 24 callback edges. The native placements cover
`0x085BC800..0x085C0D40`, including the independently converted fourth P2
record, seven-row intro palette, eight-row movement target table, platform
presentation/trigonometry/RNG/P2-loader bindings, and the `0x4A`/`0x5B`/`0x5C`
sound-request population. Timing constants use the documented 75→60 Hz 4/5
policy; source-cadence counters use a resident 1,1,1,2 phase.

The layer changes exactly 4,144 bytes across 29 declared placements. Final
disassembly verifies every native call and internal callback target. Both
source `9908` call sites reach a resident `BX LR` boundary at `0x085C0A00`;
no pointer outside the ownership window reaches any external graph entry.
Independent report SHA-256 is
`504A375A5A4F98A6F92975D06044FC46791481915E3A7FF528FA21ECF38353EE`.
Two clean 107-file output trees match completely. Historical static v46 SHA-256 is
`034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC`.
No emulator, monitor-visible window, or supplied save was used.

The same report binds WSC `4FFF:1CB5` to native GBA routine `0x08012600` as
the platform random-number ABI. The guarded commercial GBA oracle calls it
four times without arguments and masks the fourth result by seven, matching
the WSC call/return role. This proves a usable native role, not identical
cross-platform random sequences.

No GBA menu hook, complete dedicated `7168` translation, normal-play caller for the
resident auxiliary constructor/upper-state graph, broader presentation branch,
rules, reward, win/loss, or exit hook is claimed yet. The transition-state and
fighter-spawn fallbacks are explicit release gates. Ver. 1.5 has no ordinary
16-byte fighter-spawn record for stage 11; the current copied stage-7 record
only bounds an otherwise invalid table access until the dedicated initializer
bypass is ported.

The next implementation unit must finish the `4090:7168` initializer and
bind its preparation and remaining tail to the resident graph and
verified P1/P0/P2 resources. The same guarded connection must replace the
`9908` boundary with the real rules controller and parent-`9083` assignment
before enabling the menu route. Installing controller `9908` alone would
remain unreachable.
Installing isolated completion-bit writes would bypass the source mode and is
not an acceptable completion path.

## v47 consumer-driven constructor correction and player binding

The v45/v46 hashes above remain historical, reproducible intermediates; their
earlier checks did **not** prove constructor argument roles or player identity.
Inspection of the native consumer `0x080127E4` found two P1/P2 inversions: the
resident child and auxiliary constructors passed the palette as the animation
command container. Its 16-byte prologue means entry-SP `+48/+36/+24` are stored
at presentation `+44/+48/+4C`, respectively P1/P0/P2. The retail child call at
`0x08372868` independently supplies `0x08350248/0x083505E8/0x08352240` in exactly
these roles. The existing commercial resource-conversion oracle establishes
those resource types. Unchanged literal inventories alone missed the error.

The auxiliary links also reversed the source's player identities. Source
`71D1/71D9` reads `ES:065E` as active and `ES:065C` as other; `730F..731B`
writes them to source `+1C/+14`, and `7388..7394` establishes the active player's
back-links. The commercial source setup at raw `0x394897` and GBA setup at
`0x0836FD0C` prove active slot `0x030048A0`, other slot `0x0300489C`, HP
`+50 -> +64`, thresholds `+54/+56 -> +68/+6A`, and difficulty byte at
`0x03002310 + 0xF`.

`tools/build_shoot_player_binding.py` applies six exact dependent word writes
over v46: four PC-relative resource loads and two player-slot literals. It does
not swap shared resource literals, so the auxiliary direct P2 loader remains
correct. The literal `0x4000/0x1800` constructor parameters are retained, as
the retail child constructor uses exactly those values too.

The same layer installs a 420-byte phase at `0x085C1000` (384 bytes / 96 ARM
instructions plus 36 literal bytes). It implements source `4090:71D1..7394`:
active-player flags, fifteen-character HP lookup and difficulty adjustment,
half/quarter HP thresholds, cleared positions/movement fields, bounds,
callback `7792`, active P1/P0/P2 construction and palette load, auxiliary
reconfiguration, and both active-player links. The thirty-byte HP table at
`0x085C1400` is extracted directly from source `7554..7572`.

The eight-byte entry `0x085C1300` creates the exact old constructor's stack
frame and branches to its post-allocation body `0x085BC244`. The old return
restores the matching frame. This reuses the already existing auxiliary object
instead of allocating a second one. The new phase preserves `r0..r12/LR` and
requires all three object globals to be valid and the other character ID in
`0..14`; the future outer initializer must establish this contract. Source
`4090:36C0` is a bounded stage-manager setup, not the previously hypothesized
fighter allocator. Its exact range is raw `0x743FC0..0x7440C7`, SHA-256
`A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6`.
No claim is made yet about the complete upstream object's lifetime during the
future menu transition.

`tools/verify_shoot_player_binding.py` reads actual pushed arguments and the
native consumer's stores independently of the builder. It reproduces all
three v46 defects without consulting a failed whole-file hash and rejects
each of the six individually reverted correction words. It also checks the
HP branches/fields/table, P2 direct loads, callback, stack matching, full code
boundaries, and all 459 changed bytes within nine declared writes. The builder
round-trips all 98 generated instructions through Keystone/Capstone after
placement, keeping literals separate. Independent report SHA-256:
`8427FBAD3FDD00EB15CCDF69D55BD39E0341E21629B86CD2B143AFFCC07F9930`.

Internal v47 SHA-256:
`ECE3D7E6428A81C93767FC72F79BC8EA5BD7E243E814FBEDCC6FFB079CEFDFC0`.
Two clean main builds (`build/repro-v47-a` and `build/repro-v47-b`) produce
110 files each with identical relative paths and SHA-256 values. The build
manifest is `223B3241826CC524218CED5C927379098E278945B8DB354C67F36444935068D2`.
Its player phase now assigns upper entry `7792` internally, but the new phase
itself has no external caller. The outer `7168` preparation, tail from `7394`,
controller `9908/9A1B`, and menu route remain unimplemented. The boundary stub
is unchanged. This is a static correction, not a runtime or completion claim;
no emulator, monitor-visible window, or supplied save was used.

## v48: repair of omitted far-addressed P0 tiles

The earlier assertion that five P0 resources legitimately had zero tile
descriptors was wrong. `build_full_asset_poc.parse_wsc_descriptor` recognized
only records whose third word was `0x2000`; callers treated rejection as the
end of the table. This word is a **source segment**, not a destination.
WSC loader `4FFF:226E` at raw `0x75225E` loads descriptor `+2` into SI, `+4`
into DS and `+6` into C2. Indexed loader `4FFF:2E6E` at raw `0x752E5E` uses
the same fields after multiplying the P1 descriptor index by eight.
The physical source is the selected ROM bank plus `DS*16 + SI - 0x20000`
within the C2 window. Unknown or crossing mappings are rejected.

The native sprite consumer at `0x08012C80..0x08012CA4` reads the P1 frame's
word 2, selects P0's descriptor (dynamic flag 2), then loads its tile pointer.
At `0x08012D50` it reads the layout's low tile byte and copies the corresponding
32-byte native tile. Flip/palette bits in the other layout byte are preserved.
The prior tables pointed at zero or FF padding, not valid source payloads.

| Resource | Source P0 | Source table | Descriptors | Tile bytes | New native table |
|---|---:|---:|---:|---:|---:|
| Child | `22FF80` | `3D5C20` | 15 | 6,528 | `085F2120` |
| Active player | `3D5F80` | `31FF10` | 28 | 3,584 | `085F3B20` |
| Extra `6D` | `3D44E0` | `3D8DC0` | 1 | 768 | `085F4A00` |
| Extra `137` | `3D0CA0` | `3D8DB0` | 1 | 1,568 | `085F4D20` |
| Extra `91` | `3D7D30` | `3D8DF0` | 1 | 128 | `085F5360` |

The two dynamic populations are proved by all source P1 descriptor selections
(`0..14` and `0..27`) and the immediate FF terminators. The three direct-load
populations each have one descriptor and an FF terminator. Native P1 pairs,
all source/native layout bytes and each layout tile read fit the selected
payload. This covers 46 descriptors / 12,576 tile bytes / 393 tiles.

The existing converter now exposes a strictly bounded far-descriptor path;
it reuses the established planar-to-packed tile conversion. Its historical
probe recognizer remains unchanged to reproduce prior layers, but is expressly
not a general zero-tile validator. `build_shoot_far_tile_repair.py` changes
only the five P0 `+4` pointers and five complete descriptor/tile payloads.
Code, P1, palettes and P0 layouts are unchanged. The owned expansion interval
is `0x5F2120..0x5F5420`; payloads end at `0x5F5400`. The input contains no
aligned pointers or valid ARM7TDMI B/BL encodings into that interval. These
static placement checks are not runtime proof of asset lifetime.

An independent commercial oracle checks the **complete** WSC 1.0 child
population at P0 `2AD910`, table `2B3EF0`, against GBA P0 `083505E8`, table
`083508F8`: 21 descriptors, 6,304 tile bytes, 6,472 total descriptor/payload
bytes are identical after conversion. SHA-256:
`3331B32AF828EB6EA0B2E1232B621EFF0E73F040CDF6E9E590199B21B78E280E`.
This supersedes the earlier layout-prefix-only oracle for zero-tile claims.

`verify_shoot_far_tile_repair.py` imports neither builder nor converter. It
checks the original DS/SI/C2 and native indexing instructions, inversely
decodes every packed tile to source bitplanes, checks every P1/layout pair,
and confines 12,400 changed bytes to the ten declared writes. All five reverted
pointers and all five last-pixel corruptions fail semantic checks before the
whole-file hash is tested. Two exact address-boundary cases and eleven malformed
descriptor/image cases also passed the decoder contract check.

Independent report SHA-256:
`25C5C3F6F96B8335ADA627D199630264D361CECD3C70342D0646E384E802105C`.
Layer manifest SHA-256:
`D23574C6D43D9114E480AA479661AA85D10805BCCF52FBD2D8C702A2CC1F536E`.
Historical internal v48 SHA-256:
`11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E`.
Two clean main builds produce 113 identical files each; build manifest:
`E8B13CFDC1D4CCCCDE2A43FB9CAEED0915632AE6FB1252D0E986A793566D11C7`.

No emulator, monitor-visible window, or supplied save was used. The old v36
and v42 resource verifiers still describe historical intermediates, not the
corrected final tables. Initializer tail `7394..7534`, outer preparation,
existing-object lifetime, menu/controller/rules and final non-displaying QA
remain gates. In particular, restoring a direct-load resource does not prove
that the as-yet-untranslated initializer tail consumes it.

## v49: actual physics-pointer repair and resident other-player restoration

The next source portion is `4090:73F0..74A2`, raw
`0x747CF0..0x747DA2`, 178 bytes, SHA-256
`993C6E36E3700166E7C837D0E7FC82C1EAC4B497D28D98BB558612EF187B9FA8`.
It conditionally removes the other player's evolved form, restores its
resources and two palette rows, resets animation, returns to base physics,
and then resets flags, timer, presentation visibility and current/previous
positions. The native implementation is resident at `0x085C1500..0x085C1614`:
66 ARM instructions / 264 code bytes and three four-byte literals.

The mappings are established from actual native consumers, not object-field
offset arithmetic:

- Source physics `+4E` becomes a **32-bit pointer at native `+60`**, not a
  halfword at `+62`. Native initializer `0x083530CC..30E4` stores that pointer
  and reads bounds at record `+24/+26` into object `+52/+54`.
  Native de-evolution `0x0835A6E8` subtracts `0x50` from the pointer.
- Native `0x08353304` restores the character resources. Its commercial caller
  at `0x0835A730..A750` pushes slot, character, then form zero, so entry-SP
  `[0,4,8]` contains `[form,character,slot]`. The resident phase sets `r11=0`
  before entering this routine and preserves all entry `r0..r12/LR`.
- Source position pairs `+26/+2A` and `+28/+2C`, explicitly written together
  at `4090:2D8E..2DA4`, map to native `+34/+38` and `+36/+3A`; native
  `0x08353174..3190` independently writes those pairs. This phase retains
  source coordinate constants `0E00/FF80`; visual placement is unverified.
- The two 16-halfword source palette copies `FF00 -> 04EA` and
  `FF80 -> 056A` become OBJ palette rows `05000200 -> 0203E200` and
  `05000280 -> 0203E280`. Native P2 loader `0x08013308..3328` proves OBJ
  palette addressing. Native `0x0833FDD0..FE14` already copies hardware
  OBJ `05000200..05000300` into mirror `0203E200..0203E300` with DMA.
  This proves the storage representation; the future Shoot transition must
  still establish ownership/lifetime of the shared mirror before calling
  the phase. No new RAM buffer is allocated and no fade-parity claim is made.

Checking the first native physics consumer exposed an older, independent
placement defect. The converter padded to the second declared record before
appending the first, while its pointers and manifest still named the earlier
coordinates. The actual complete records already existed one record later:

| Character ID | Incorrect pointer through v48 | Correct pointer in v49 | First halfword read before -> required |
|---|---|---|---|
| 12 | `0848503C` (zero padding) | `084850B4` | `0 -> 320` |
| 13 | `084850B4` (ID 12 data) | `0848512C` | `320 -> 360` |
| 14 | `0848512C` (ID 13 data) | `084851A4` | `360 -> 357` |

`build_character_physics_assets.py` now produces correct pointers by default
and checks the data actually reached by every added pointer. Existing payload
coordinates and the reserved hole are preserved. The explicit
`--legacy-v48-layout` option only reproduces pinned historical layers for the
guarded main pipeline; it must never be treated as a correct release asset.
The final dependent layer repairs the three pointers. The final ROM's entire
540-byte physics blob must equal the separately generated corrected asset,
SHA-256 `93C735C0A3EE3A9DF09243246BE38129B97AF6A88F5C4546C0229FB7339753C3`.
No physics payload, retail record or existing code is moved or rewritten.

The independent verifier imports no builder. It checks all generated
instructions, native call ABI, palette row extents, conditional paths, and
the whole output diff. Its field oracle first reproduces 660 halfwords from
commercial IDs 0..10, then checks all 180 halfwords reached by added IDs
12..14. ID 11's commercial special form is preserved, not normalized.
All fifteen base-form bounds are checked. Reverting each of the three pointers
reproduces a wrong full record, even when two characters happen to share
identical bounds. Fourteen semantic negative cases are rejected before the
output hash check. Report SHA-256:
`6F0B0191F2CC84961908C512F1CEA016FA72EBD9CE5E6A4876940630915B3F20`.

The four Expected Writes change 273 bytes: 269 in the new resident phase and
four bytes across the three physics pointer words. There are no existing
aligned pointers or ARM7TDMI B/BL references into `5C1500..5C1700`, and no
external caller is added. The phase is **not a complete 7168 initializer**.
Still unresolved are `7394..73F0` and `74A2..7534`, outer setup and object
lifetime, the shared palette transition, controller/menu, and remaining rules.
In particular, the source tail sets ES to `1000` before writing `3CD8/3CDA`,
whereas the common fighter initializer writes these offsets with ES=`0C00`.
Those are different source addresses; do not substitute native `030048AC/AE`
solely because the offsets match. No such global clear was installed here.

Further palette evidence, not yet adopted as a replacement: retail WSC 1.0
`AFFE:0101/0156` at raw `3B00E1/3B0136` uses counter `1000:036C` and palette
mirror `1000:036E`; Ver. 1.5 uses `03E8/03EA`. Its commercial GBA counterpart
`0x08377BD0/7C1C` instead invokes `0x0833FE58/FE94`, using native fade state
`0203F000` and hardware blending. The source increment-to-target function
`4FFF:1EF5` corresponds to native `08012178`, but no direct retail ARM BL
calls to that native entry were found. This is not proof of an unused buffer
or authority to omit the Shoot-specific palette preparation.

Current static v49 SHA-256:
`93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E`.
Two clean main builds in `build/repro-v49-a` and `build/repro-v49-b` generated
118 files each, with zero relative-path/hash differences. Main manifest:
`32F8C29ABE44503C178562D41E55890D5F0B1F808ED1E894054F8FE7EE06A9AA`.
Final layer manifest:
`F6EDFA1E308FA7FD561E69CDD4300B91735C3522ECE85F00CAEC304543735DEF`.
All three original ROM hashes remain unchanged. No emulator, visible window
or supplied save was used. Runtime-evidenced progress remains at most 8%.

## v50: tail resource consumers and resident HUD/OBJ binding

The two resolved resource segments of `7168` now have native entries:

| Source segment | Native resident entry | Effect |
|---|---|---|
| `7394..73A9` | `085C1700..085C173C` | Load source `3D7A90`, installed at `085DB740`, into OBJ slot 5 |
| `74A2..74DA` | `085C1800..085C186C` | Reload four HUD tiles, load OBJ slot 6, clear `03004D40` scroll state |

The late tile load must not retain the WSC tile number `91`. Source direct
P0 `3D7D30` resolves to the 128-byte payload at `3D5DA0`; all four converted
tiles are byte-identical to commercial GBA `080D2FD0..080D3050`, SHA-256
`FED06ADACACA6083C841FD002EB50BFAAD16CD70BBDC5B7A7C476871B76C70C7`.
Retail `080D161C..080D1724` copies that entire payload to `06017F80` using
32 word pairs. Its literals are at `080D1770/1774`. The OAM producer at
`08370148/14C` selects `67FC`, through literal `08370268`: tile `3FC`, OBJ
palette 6. Tile `3FC * 32 + 06010000` equals the same `06017F80` destination.
The existing Shoot main loop retains this native OAM selection. The new
late phase therefore copies the exact existing commercial pixels to their
actual consumer address; no duplicate graphics payload is added.

The two P2 calls use `080132EC`. Its entry stack has
`[slot,index,unused,unused,P2]`; the loader advances by `index * 34`, reads
the source palette base, maps `(base - 8 + slot + 16) * 32` into GBA palette
RAM, skips color zero, and writes exactly fifteen halfwords. The early call
uses base 8 / slot 5 and writes `050002A2..050002C0`. The late call reuses
commercial `080D3078` (source `3D6B16`), base 14 / slot 0, and writes
`050002C2..050002E0`. Both preserve color zero. All sixteen source palette
colors are checked independently by inverse conversion, while the actual
loader's fifteen-color write extent is checked separately.

The other two preload identities are no longer unexplained. Source P0
`3D44E0` (tile base `6D`) appears in the later presentation constructor at
`93E7..9415`, paired with P1 `3D23B0` and P2 `3D7AC0`. P0 `3D0CA0`
(tile base `137`) appears at `888B..88BA`, paired with P1 `0DFEC0` and
P2 `3D7A90`. Their constructor ranges have hashes
`513B405B41459A9A13109ACADECFCB4F7E3156FC5A8E54C885416B7260D0A138`
and `2C1580D4E6EBDF6A27F8C4E0AD854263E85781AB7CFBC92FE830F697A4903CA8`.
This identifies concrete consumers to translate; it does **not** prove that
their initial copies can be omitted or that their native lifecycle is ready.
The existing `9229` child entry is a different source generator and is not
credited with implementing the separate `93E7` construction.

`build_shoot_tail_resources.py` adds only these two resident resource segments
over exact v49. The total is 37 ARM instructions / 148 code bytes plus 20
literal bytes; two Expected Writes change 160 bytes. All instructions pass
the existing assemble/disassemble round trip. Both preserve `r0..r12/LR`,
not condition flags. There are no external callers or allocations. The
original `7394` and `74A2` ordering must be preserved by the future complete
initializer; the entries must not be treated as one contiguous replacement.

`verify_shoot_tail_resources.py` imports no builder. It checks both complete
instruction populations, the original native P2 and HUD producer/OAM
consumers, source pixel/palette inverses, pointer/slot/extent relationships,
the whole-image diff and ten semantic negative cases before checking the
output hash. The cases include wrong slots, tile destination/count/stride,
P2 source/base, scroll address, stack cleanup and the native color-zero skip.
Verifier SHA-256:
`56A41B0B88EA9BD49402F986A0CAEA63CF24C1156D019B4B99BCEB739CAFB87C`.

Remaining `7168` tail: `73A9..73D6` P0 preloads, `73D6..73F0` global-clear
mapping, and `74DA..7534` palette backup/white preparation. The ES=`1000`
versus ES=`0C00` ambiguity remains unresolved; no guessed native write is
installed. Outer preparation, object/palette ownership, lower rules and
controller/menu integration remain the same active milestone. These new
resource entries alone neither complete initialization nor prove gameplay.

Current internal v50 SHA-256:
`C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`.
Two clean main builds, `build/repro-v50-a` and `build/repro-v50-b`, each
produce 121 files with zero relative-path/hash differences. All nineteen ROM
layers are reproduced from the three original ROMs. Main manifest:
`5CDD5FB7595039958DB3B5D37D22168C3216A9CD69791234219E5E33C7F90EA5`.
Final layer manifest:
`CA392167BCD1430A295A56E084461E732DC0671B01CBDAF079709110EE93BE72`.
The final image is 8 MiB with unchanged valid GBA header, entry and `6C`
complement. Original input hashes are unchanged. No emulator, visible
window or supplied save was used; runtime-evidenced progress remains at most
8%. No BPS release or GitHub upload is claimed.

<a id="shoot-palette-01"></a>

## SHOOT-PALETTE-01: post-v50 investigation, not implemented

Recorded 2026-09-02 before the user-requested pause. Baseline is implementation
commit `02a987d` and exact v50 above. This is read-only source investigation,
not a v51 layer, executed transition, complete initializer, or progress increase.

### Selective backup and preparation

Source `4090:74DA..7534`, raw `747DDA..747E34`, is 90 bytes with SHA-256
`0415462B683CD87C9576DE4685A59D4F5BA6D3C201090C4D5B0A7A9F2FA40843`.
With DS=`0000`, ES=`1000`, it performs these half-open range copies:

| Hardware source (DS) | Saved target (ES) | Bytes |
|---|---|---:|
| `FE00..FF00` | `03EA..04EA` | 256 |
| `FF20..FF80` | `050A..056A` | 96 |
| `FFA0..FFC0` | `058A..05AA` | 32 |

It then writes the sixteen CS:`7534` gray-table halfwords into the saved
mirror starting at `03EA`, with destination stride `20`, and fills hardware
`0000:FE00..10000` with 256 halfwords of `FFFF`. The backup is **384 bytes,
not the full 512-byte hardware palette**. The earlier other-player phase
conditionally updates rows `FF00` and `FF80`; remaining mirror rows preserve
pre-transition values. Replacing this with an unconditional full backup would
change source behavior.

The native common capture at `0833FDC0..0833FE1C`, SHA-256
`6A80E9053418E0F07B8FA389EECC9ABB4F9E65464D58C0BC6FDDAF6DD03BF6CD`,
resets state at `0203F000` and uses DMA3 to copy 480 BG bytes from `05000000`
to `0203E000`, then 256 OBJ bytes from `05000200` to `0203E200`.
It does **not** capture BG15 (`0203E1E0..0203E200`) and overwrites all OBJ
rows 0..7. This is not an equivalent replacement for the selective Shoot
capture. The OBJ storage representation already used by v49 remains valid,
but ownership and the full source-to-native BG/OBJ row correspondence are
still unresolved. No new mirror or replacement capture is allocated.

### Gray-table lineage excludes the existing red table

The Ver. 1.5 table at raw `747E34..747E54` is the sixteen RGB444 levels
`0000, 0111, ... 0FFF`, SHA-256
`C5605A0084D6DFAB01687645085BD7C4CF07C383421BD5F90541F541681C2738`.
Its converted values are not the native table at `0837036C..0837038C`,
SHA-256 `CC4B6F9DECD675C813E001937DBA42E44FE8766256BAB94EB901F3B8B71B65BF`.
Inverse conversion of all sixteen native entries instead matches the retail
WSC 1.0 red table at raw `394C3D..394C5D`, SHA-256
`B08DBF7E5AF8256ABB2D8E3DA39E296099F91E4E3212FD7EA8669262A8BB2696`.
Thus reuse of the native loop does not authorize reuse of its table values.

The retail source loop at raw `394A7E..394A99`, SHA-256
`C10629CF823DE4A166573D61C06987F8B3DEC147F34625DAB529B69B6ABB26D9`,
writes sixteen halfwords to hardware `FE00` at stride `20`. Its native
counterpart `083700CC..083700F0`, SHA-256
`5835B7C0C6F8CC668C5080951175CE8787027068F01297D8C095F997EC4578AB`,
reads `0837036C` and writes hardware `05000000` at that stride.
This proves the bounded commercial lineage, not Shoot mirror ownership or
complete fade semantics. Retail WSC raw/logical addresses have a `0x200`
display-base trap here: CS:`453D` resolves to raw `394C3D` with base `390700`,
not `390900`. Retain the physical ranges until each overlay base is established.

### Following scene callbacks establish transition order

Ver. 1.5 raw `773143..77329C` has SHA-256
`1F72A027CDE79D65FB5185713D4B1347355286DFCC7BD01862614DC06C73020E`.
The call at raw `773143` invokes `4090:7168`, then sets task `+42` to `20h`
and assigns `71F0:1267`. The following sequence is source control flow only:

1. `71F0:1267`, raw `773167`: alternate palette halves using
   `(task[+42] & 1) << 8` and call `4FFF:1E9D`. Each nonzero RGB444 channel
   decrements toward black. The counter runs for 32 callback ticks.
2. `71F0:12C6`, raw `7731C6`: hold for `96h` / 150 ticks. At counter
   `82h` / 130 it requests sound `D2`. The native `0x5C` asset already exists,
   but this source request is not yet connected by the new transition.
3. `71F0:1331`, raw `773231`: for 32 callback ticks, alternate halves and
   call `4FFF:1EF5` toward saved mirror `1000:03EA + (parity << 8)`.
   On completion clear other-player flag `+6` bit `40` and assign
   `71F0:139C`, raw `77329C`.

The required order is **white -> black -> hold -> saved target**, not a
single white-to-target interpolation. These are source callback counts;
GBA timing in frames/seconds is not established. Helper `4FFF:1E9D` is raw
`751E8D`; `4FFF:1EF5` is raw `751EE5`. Native `08012178` increments 5-bit
channels one step at a time and is not automatically equivalent to the source
4-bit cadence. No direct ARM BL to that entry was found, which does not prove
it is unused. Native `08012228` also needs independent checking: its inspected
green comparison appears to mask the same operand twice. Do not adopt it
without resolving its actual caller contract.

### Next decision and reproduction

Resolve the saved-row ownership and all transition consumers before writing
`74DA..7534` or wiring a caller. The eight stage-map samples at
`495000 + index * 3F0` only use palette indices 0..5, but that bounded sample
does not prove that other BG banks are unused by the intro, HUD or UI. Keep
the unimplemented outer initialization and `73A9..73F0` work visible.

Use `tools/disassemble.py` with the corresponding hash-identified original,
the raw offsets/range lengths above and `--mode x86-16` or `--mode arm`.
For a native address subtract `08000000` to obtain the GBA file offset.
Use explicit source logical bases only where proved; passing a convenient
display base does not establish a segment mapping. Existing source palette
conversion can be independently inverted against the stated retail table.
These checks require ROMs only, never the supplied save. No new build or
runtime check was performed for this documentation-only handoff.

<a id="shoot-v51"></a>

## SHOOT-V51: implemented resident components, 2026-10-13

The user resumed actual implementation from clean HEAD
`f056934bbba3dfa9bbabf46404e12ddd6595b8e9` on `codex/progress-snapshot`.
The three exact original ROM hashes and both v50 candidate hashes were checked
before reuse and again after the final builds. No recovery audit restart, save
read/hash, emulator launch or visible verification window was performed.

### Implemented code and ownership

| Component | Native entry/range | Scope |
|---|---|---|
| Rule selection and application | `085C6000`, `085C6200`, table `085C6400` | 64 source decisions, signed difficulty, RNG cardinality and object effects; three required callbacks still absent |
| Palette snapshot | `085C1900` | 512-byte logical mirror using actual BG/OBJ consumers |
| Selective preparation | `085C1C00` | 384-byte selected copy, sixteen gray zeros and 528-byte white hardware projection |
| Fade operations | `085C1D00`, `085C1F00` | White-to-black and black-to-target channel steps, explicit remaining-count ABI, BG0 alias repair |
| Graphics subset | `085C4000` | Proven BG descriptor/map/staging resets plus existing Shoot graphics clone |
| Stage-manager subset | `085C4300` | Stage 11, native timer 14,400, source-order flag clears/set, existing expanded stage manager |
| Proven global clear | `085C4400` | Only source `1000:0660` mapped to native `030048A4` |
| Constructor resource adapters | `085C4500`, `085C4600` | Actual native fifteen-argument ABI for source `93E7` and `888B` |
| Relocated resources | `085C4800`, `085C4C00`, `085C5000` | Two complete P1 populations and P2; every nonzero per-item record pointer is local and source-identical |

These add 367 ARM instructions and change 2,340 ROM bytes relative to v50.
They do not install an outer initializer, scene caller, menu entry or replacement
for the `9908` boundary. Actual write intervals are guarded independently; pointer
and ARM-branch-like values reaching untouched gaps are reported and preserved.
The palette PREPARE entry was moved from prospective `085C1B00` to `085C1C00`
because an existing aligned value already named the former address.

Detailed evidence and exact call contracts:

- [Palette representation and source lifetime](shoot-palette-ownership.md).
- [Rule selection and missing continuations](shoot-rules-continuation.md).
- [Initializer consumers, relocation and remaining effects](shoot-initializer-lifetime.md).
- [Conditional normal-entry scene ownership](shoot-scene-ownership.md).

### Independent validation and reproduction

The final verifiers import no generator/converter. They inspect every final
instruction, literal and resource consumer, invert the source representation,
check complete-ROM write containment, and reject semantic corruption. Rule
selection has 262,144 finite decision partitions and twelve negative controls;
palette code has finite channel/projection checks and eleven negatives;
initializer code/resources have eight negatives and all 111 instructions checked.
These are static specification and consumer checks, not CPU execution or gameplay QA.

Two fresh full builds generated 22 ROM layers and 131 files each in
`build/repro-v51-20261013-a` and `build/repro-v51-20261013-b`.
Every relative path and SHA-256 matches. Final v51 SHA-256:
`726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284`.
Build manifest SHA-256:
`F3C2B03E5608B5D0533D05F19F82D17D55E938360040C606CFBEB26F7E5705F7`.
The source and preserved v50 hashes are unchanged. The main builder rejects an
existing populated output folder; that refusal was checked before the two runs.

### Remaining first-milestone work

Bind the conditional scene-owner proof to the actual normal battle entry, retaining
both task replacements through restore and scene retirement. Close the dedicated
display/IRQ/HUD/font/map setup and bank-sensitive `ES1000:3CD8/3CDA` writes, then
connect the complete initializer in original order. Source `DS0C00:3CD8/3CDA`
fighter globals are a different physical location and cannot be substituted.

The `810D`, `8AB8`, `8CDD` continuations, complete lower rules graph, hold/audio
scheduling, rewards, win/loss, menu and exit remain open. Merely calling the new
selection or palette helper does not close these gates. First milestone completion
and normal-play reachability are not claimed. Runtime evidence remains v32 and
does not gain credit from this static work.

<a id="shoot-v53"></a>

## SHOOT-V53: lower rules, corrected graphics, display and terminal code, 2026-10-13

This continues the same first milestone after local v51 commit
`edb622d560f078e16b5defe166f98787536ef9b9`. No recovery audit was restarted.
Seven new main-build layers follow v51. Their complete code, Expected Writes,
source consumers and independent verification are documented separately:

| Layer | Concrete implementation | Evidence |
|---|---|---|
| Lower audio | CF/D1 native scores; commercial instruments and explicit audible limitations | [audio](shoot-lower-audio.md) |
| Lower rules | 33 routines, `810D/8AB8/8CDD`, `881A/933B` generators, native resources, same-update control flow | [lower rules](shoot-lower-rules.md) |
| Graphics | Dedicated stage-11 initializer, HUD, compact palette state within its original 32-byte owner, real dim/disable consumers | [graphics](shoot-graphics-initializer.md) |
| Stage assets | Actual C9:383F source palette/tiles, twelve maps, original two-by-three dimensions, native scrolling descriptors | [stage assets](shoot-stage-assets.md) |
| Stage handshake | Connected `0E0B` update, source layer order and old-index reads, commercial scanline bridge | [handshake](shoot-stage-handshake.md) |
| Terminal | Seventeen result/exit phases, resources, damage adapters, four same-update repairs; external damage hooks closed | [terminal](shoot-terminal.md) |
| Normal display route | Five-instruction router connects flag-0400-clear path and preserves existing 0400 fallback | [normal display](shoot-normal-display-route.md) |

The old stage extraction used the wrong bank offset and only eight maps.
The installed repair reads palette `4983F0`, tiles `4984D0`, maps `49C4D0`,
and the two original six-entry descriptor tables. Inverse verification covers
111 colors, 32,768 pixels and 6,048 map entries. Source HUD tile writes occupy
stage-bank indices 495..511; all nonzero map cells use indices at most 494.
The 4,261 common-bank map cells use only tile zero; its complete lifetime is
still a separate obligation. No rendered result is claimed.

The lower-rule verifier checks complete final code/stack/call contracts,
finite HP/direction/spatial populations and nineteen semantic corruptions.
The terminal verifier checks 587 ARM instructions, 26 complete blocks,
30 Expected Writes, native result-resource inverses and nineteen corruptions.
The normal display router checks all 65,536 flag values and six corruptions.
These are static computations over specifications and decoded code, not CPU
emulation. Commercial audio reset/identity and existing scene-object pools
have additional source-backed reports:
[transition audio](shoot-transition-audio.md),
[scene object pools](shoot-scene-object-pools.md).

### Reproduction

Fresh directories `build/repro-v53-20261013-a` and
`build/repro-v53-20261013-b` each contain 29 ROM layers and 155 files.
Every relative path and SHA-256 matches. Final candidate:
`455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48`.
Build manifest:
`C6FF837E60965776EF42AA09AA1ACC83B5148239D859657AE6087CE16EE66941`.
Full-tree comparison:
`8CC96F98AEF076D796FCE731D542BB4AAD179580A906A35F0C20A41329153666`.
The v52 checkpoint separately reproduced 25 layers and 142 files with candidate
`6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29`.
V53 changes 30,992 bytes from v52. Original ROMs and both v50/v51/v52 results
were rechecked unchanged. The GBA header checksum remains `6C`.

### Exact remaining gates

- [SRAM analysis](shoot-sram-boundary.md) returns `UNRESOLVED_OBSERVER`.
  Source `1000:3CD8/3CDA` writes are physically different from the usual
  `0C00` fighter globals. Neither deadness nor a native field mapping is proved.
  The [commercial lineage counterexample](shoot-sram-lineage.md) proves that
  native `030048AC/AE` are live regeneration timers; unconditional merging
  changes subsequent behavior. It does not assert reachability of the example.
- Terminal IRQ `0DEC` reads interrupted DI. Its preceding callback restores
  DI, and the dispatcher does not establish `EA`; no normalization is allowed
  without a real visibility/timing/ownership proof.
  [Focused IRQ evidence](shoot-stage-irq-observability.md) checks 1,678,080
  conditional prior-frame row-coverage cases, but common-bank tile-zero
  lifetime and preservation against camera refill are still unproved.
- Terminal `197A` row-clear is presently mapped only for camera Y 0..62;
  lower `8EF3` also requires upstream coordinate bounds. Neither guard proves
  source equivalence outside its domain.
  [Spatial-domain evidence](shoot-spatial-domains.md) preserves the exact
  16-bit source clear footprint and identifies the camera/cache consumers.
  Initializer Y zero and stage dimensions alone are insufficient.
- Full initializer `085C7800` and normal scene/controller/menu entry remain
  absent. The dependency-gated [scene/route drafts](shoot-scene-transition.md)
  and controller adapter are not installed, and their full ROM verifiers have
  not run. Fatal/nonfatal external hooks remain retail code.

The first milestone is **not complete**. No supplied save was opened or
hashed; no CPU/emulator or visible verification window was used. Runtime
evidence remains v32, with overall runtime-evidenced progress at most 8%.
