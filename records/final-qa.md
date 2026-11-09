# Final QA gate

## 2026-11-09 explicit development observation authorization

The user now permits a **copy of the supplied WSC save** for hidden, original-game-only development observation. This supersedes the earlier prohibition on reading, hashing, copying or loading that input within this scope. It does not authorize modifying the user's original file, injecting guest memory/registers, or treating development observations as completed port/final QA.

The protected source and the new ignored copy at `build/wsc-user-save-copy-20261109/supplied-copy.sav` both hash `051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F` (32,768 bytes). `copy.json` records the authorization and equality check. Each emulator run uses another isolated copy. Earlier invalidated observations remain invalidated; this permission applies to new work. All final-port completion requirements below remain open.

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
