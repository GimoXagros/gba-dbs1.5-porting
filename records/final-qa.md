# Final QA gate

## 2026-11-24 v94 전투 보조와 오프닝·효과음

검수판 `EF8BBC67`에서 전투 보조를 네 언어의 옵션 메뉴에 연결했다. 네 번째 오프닝의 두 캐릭터와 시작 버튼 전환 시간을 원본과 대조하고, 추가 캐릭터 효과음 다섯 종류를 복원했다. [조작·검증·빌드 기록](playable-battle-assists-v94.md).

## 2026-11-24 v93 검수 범위

검수판 `D432DBE9`에서 빈 저장 공간으로 시작한 어려움 난이도 캠페인이 94,893프레임에 타이틀로 돌아왔다. 중간 상태를 불러오거나 컨티뉴하지 않았다. 두 보스의 실제 격파, 마스터 태그와 이름 저장을 확인했다. 이 실행은 허용된 D-스피릿 및 보스 체력 보조를 사용했다. 통신 대전의 실제 승급과 재시작, 양 기종 15인 선택 목록, 네 언어 메뉴 52화면과 초상화 60장도 검수했다. [원본·실행 검수 기록](four-language-release-v93.md).

원본과의 세부 차이가 남아 있다. 추가 캐릭터 효과음 5종은 원더스완의 음높이 변화와 노이즈 음색을 모두 복원하지 못했다. 열차 무대의 흔들림 루틴도 원본에서 누가 호출하는지 확인해야 한다. 전체 원더스완 완료 세이브와의 진행 상태 대조는 일반 1인 대전의 캐릭터 목록과 해금 상태까지 마쳤다. [효과음](character-audio-completion.md) · [열차 무대](train-shake-source-contract-20261117.md) · [완료 세이브 대조 범위](completed-save-roster-comparison-20261124.md).

## 2026-11-09 actual preactivation failure and verified checkpoint replay


The new baseline and genuine checkpoint replay completed normally. FIRST already had HP0/event005B
at the actual boss hit/root5 (91708). The following scene saved0 at payload2334+46, temporarily set
HP1, then restored0 at93549 before input activation93570. The earlier carried-survivor-HP1 inference
is withdrawn; a fresh jump cannot repair this captured entry. No3030 damage pair occurred.

The restored complete native+managed core equals the genuine checkpoint. All2810 recorded FIRST/stage
contexts and seven shared activation RAM/SRAM/PNG outputs match. Original save and GBA v72 are unchanged.
Terminal/DI remain unobserved. Next: ordinary Continue from the proven final state to fresh stage7 HP8,
with no P1 HP or progression writes. Stage11 is mechanically the second boss; do not conflate this
repository's Shoot label with the separate menu mode23. E5's first invalid writer remains unknown.
See [corrected cause](shoot-actual-input-boundary-20261109.md) and
[completed capture/replay QA](wsc-shoot-boundary-checkpoint-qa-20261109.md).

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
See [independent capture QA](wsc-boss1-capture-qa-20261109.md) and
[actual input boundary](shoot-actual-input-boundary-20261109.md).

## 2026-11-09 additional boss-HP1 authorization

After the score999 run reached stage7 but ended at Continue, the user explicitly authorized setting the boss's HP to1 and landing one actual attack to continue the original-reference test. The approved implementation reduces the active boss HP word once after its intro; it never writes0, repeatedly holds1, changes P1 HP, or forces progression. A later real damaging hit must cause the original victory/Shoot route. This is a new hidden development observation on a save copy, not a final GBA cheat or completion claim.

## 2026-11-09 additional score-only cheat authorization

The user explicitly permits fixing D Spirit at999 when ordinary play cannot reach stage7. New original-reference runs may write only the verified P1 D Spirit score word, with an address/value/timing ledger. This narrowly supersedes the guest-write prohibition below; it does not authorize changing HP, stage, progression, registers, the source save, or the final GBA candidate. Runs remain hidden and use isolated save copies. Cheat-assisted observations must be identified separately from ordinary play and final port QA. Stage7 requires an HP victory, so a score cheat alone does not prove Shoot entry.

## 2026-11-09 explicit development observation authorization

The user now permits a **copy of the supplied WSC save** for hidden, original-game-only development observation. This supersedes the earlier prohibition on reading, hashing, copying or loading that input within this scope. It does not authorize modifying the user's original file, injecting guest memory/registers, or treating development observations as completed port/final QA.

The protected source and the new ignored copy at `build/wsc-user-save-copy-20261109/supplied-copy.sav` both hash `051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F` (32,768 bytes). `copy.json` records the authorization and equality check. Each emulator run uses another isolated copy. Earlier invalidated observations remain invalidated; this permission applies to new work. All final-port completion requirements below remain open.

The new original title/menu observation completed with ordinary Start input and independently passed audit `E28DD2E2878ECB0F03A8B193CB657DCBC870A4891B75E49DA5AB305F64A1C169`. The entire live cartridge SRAM matches the copy after two exact source startup stores; no arbitrary fields were ignored. [The observation record](wsc-authorized-save-menu-qa-20261109.md) preserves the initial comparison failure and separate prelaunch Windows-path failure. This establishes neither Shoot entry nor final GBA compatibility.

## Deferred reference input

| ID | Platform | Supplied filename | Size | SHA-1 | SHA-256 | State |
|---|---|---|---:|---|---|---|
| `wsc-15-completion-save` | WSC | `Digimon Tamers - Battle Spirit Ver 1.5.sav` | 32,768 bytes | `94F3E4AC489B3E83FF40F02D6850C134C04B98F3` | `051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F` | Registered; final run still blocked |

The save remains an external, read-only user input. The project records only
its identity and does not copy it into the workspace.

## Invalidated premature observation

An isolated emulator copy of the save was accidentally booted after the
character/evolution bundle had been integrated but before the wider Ver. 1.5
scope (stages, extra boss path, Digimon Shoot, tag/progression additions, and
opening changes) had been integrated. The source save remained read-only and
its SHA-256 stayed unchanged, but this run violated the activation gate and is
not final-QA evidence. Its capture directory is retained only as an invalidated
audit artifact and must not be cited for completion. Do not run the save again
until the complete scope passes the gate below.

## Activation gate

Do not load, parse, convert, or run this save until all declared Ver. 1.5
content has been integrated into a single GBA candidate build and that build
has passed the project's static integrity checks. Fix the exact candidate ROM
hash before starting save-based tests.

## Final test purpose

After the gate opens, use the save with the exact WonderSwan reference ROM to
establish the completed/unlocked reference state. Compare every reachable
roster entry, mode, stage, presentation asset, and relevant progression state
against the fixed GBA candidate. The WSC save must not be loaded directly as a
GBA save; platform-specific state must be reproduced or converted only after
its format has been independently mapped and validated.

## Display requirement

All emulator-based final validation must run on a non-interactive/private
desktop or through a genuinely headless harness. No emulator, debugger, test
frame, or validation window may be shown on the user's monitor. Evidence may
be captured to ignored files for later hash/trace comparison, but it must not
be opened visibly during the run. Static build and binary-integrity checks may
continue in the background before this gate; they do not authorize opening or
parsing the supplied save.

## Evidence boundary

Registration and hashing are not runtime tests and do not support a port or
compatibility claim. Record emulator versions, screenshots or traces, observed
results, candidate ROM hash, and any save conversion hash only when final QA is
actually performed.
