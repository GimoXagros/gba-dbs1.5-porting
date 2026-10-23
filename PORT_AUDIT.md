# Port recovery audit

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
