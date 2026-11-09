# Bounded native Shoot entry observer — 2026-11-09

The new driver/module observe only the separate experimental ROM
`D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C`.
They do not change the ROM, main builder, previous observers or provided saves.
This author did not launch an emulator. Runtime arrival is not yet claimed.

The driver loads frozen `bizhawk_probe_gba_collision.lua` with an isolated Lua
environment, reusing its bounded frame loop and complete 8 MiB loaded-ROM dump.
Only that environment's input, frame-advance, exit and old callback registration
are replaced. The old overlap filter rejects valid Shoot types1A/1B; the new
module accepts0..1B and independently retains the generic dispatch-target check.
The old files and global BizHawk APIs remain unchanged.

Required userdata keys:

| Key | Value |
| --- | --- |
| `output` | Fresh isolated `W:/build/<name>` directory |
| `frames` | Integer1..120000; default120000 |
| `probe_sha256` | Full experimental ROM hash above |
| `score_authorization` | `user-approved-development-score999` |
| `boss_authorization` | `user-approved-development-boss-once-per-stage` |
| `start_frame` | Optional ordinary Start delay; default2970 |

The ROM hash token is a host identity pin, not a Lua-computed hash. The host
must independently compare the copied and complete loaded ROM with this hash.
No source ROM or save is an input to these scripts.

The ordinary input state machine reuses the existing verified result-language
observer's title/options route. It selects Options via the actual title cursor,
selects difficulty row1 and presses Right until the real difficulty byte is2,
then presses B and returns to title row0. The native Options UI caps difficulty
at2; the observer does not pretend that three presses select3. Character
selection uses fresh A only and verifies both selected fighter and variant0.
The frozen12Down character-selection presses are not used. Right4560 onward
in that older script was battle input, not character selection.

Combat profile is explicitly `approach-jump-no-up`: the existing A/B97/29 and
horizontal720-frame pattern, including the initial Right approach, without Up
evolution input. This ordinary-input variant is root-approved to retain the
bounded default base0 path. It does not freeze any form or guest field.
Mode9 stops at Continue. The actual case5 selector predicate and selected R8
are recorded; an ineligible stage7 predicate stops the experiment.

Authorized writes occur at the real post-collision/pre-HUD08373638 boundary.
Both real input/battle task headers must be active and own callbacks08374FF4
and083735BC. Mode7 and control4529 lowbits clear are required. Ordinary stages
0..10 excluding7 require gamekind0; boss7/Shoot11 require gamekind2. Actual
FIRST/SECOND pointers must be distinct aligned active task payloads, have
self+14 and reciprocal+18 identities, expected kinds/indexes and FIRST ID0.
Boss SECOND additionally requires active IDF (the initializer overwrites the
constructor's temporary C), kind3, and the active global auxiliary kind6 with
SECOND+28=aux, aux+28=SECOND and aux+18=FIRST. Positive FIRST HP is mandatory.

Only ordinary FIRST+66 WORD999 and stage7 SECOND+64 WORD1 are writable. Each
boss stage is consumed before the attempted write and never rearms on pointer
reuse or Continue. This entry-only observer enables stage7 only; stage11 HP
writes are disabled. No player HP, timer, mode, stage, progression or register
is written. Every attempted write has a permanent outer-frame ledger entry,
including adjacent-word/player-health checks; it is not lost in the rolling
collision journal.

Real boss damage is observed before0836E5E4 and immediately before0836E5E8,
requiring actual FIRST attacker and SECOND victim. Native signed subtraction
can produce a negative WORD from HP1; the observer records that computed
value and its exact subsequent store instead of forcing zero. Healthy root5
must follow this actual fatal hit. The scene's positive savedHP at5C8070,
initializer call/return5C853C/8540, pre-store restore5C8B2C and tail5C8D50
are joined with the positive outer-frame restoredHP, actual input/battle
owners, active Shoot bit and retired scene owner. Success saves a genuine
`healthy-activation.State`, then stops before stage11 attack input.

Producer353C70/353D24/3776E4 records preserve the first invalid type, source B,
actor selector, presentation event/command and pointer provenance. The rolling
256-entry journal also observes list-type writes, overlap and scratch writes/
reads. First failure context is retained independently. Generic grab354FB8,
upper event48 frame consumers128A4/128BC and8EF3 refusal5CC1C0 are read-only
hooks. A null upper frame is reported without attempting to repair it.

CPU callbacks copy registers and scalar state. Root explicitly authorized one
immediate scalar-only `shoot-entry-first-failure.txt` file on the first failure,
including its registers, state and rolling scalar journal. This survives a core
stall before frame return. Full memory, images, savestate and normal ledger/
capture writes happen after outer frame-advance returns. Capture
metadata distinguishes before-instruction registers from later outer-frame
memory. Multiple hooks in one frame can therefore share the later RAM image;
their register/scalar facts are not represented as instruction-time RAM dumps.

Primary outputs are `shoot-entry-trace.txt`, `shoot-entry-writes.txt`, numbered
checkpoint memory/images, `loaded-rom.bin`, optional genuine healthy state,
and the final `shoot-entry-done.txt` marker. Marker values distinguish healthy
activation, a named failure and bounded absence of activation. Independent
execution self-check and root-owned runtime/capture review are separate work.

Complete scene lifetime, terminal gameplay, E5 causal resolution and release
approval remain open. No prior static or runtime suite was rerun by this author.

## Frozen implementation and independent execution check

| Artifact | SHA-256 |
| --- | --- |
| `tools/bizhawk_probe_gba_shoot_entry.lua` | `D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D` |
| `tools/bizhawk_gba_shoot_entry_observer.lua` | `E620B76A96ED09E6E19DED5E3EE8134D14E62A6022A332D899E08E3493FF76FF` |
| Reused frozen collision driver | `7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9` |
| Independent `tools/verify_gba_shoot_entry_observer.py` | `77B47BEC9431511605544E6956AEDA141C2C50FFD0435D4CAF5A020B57CA77E3` |
| Independent final failure-evidence report | `8BBAE0F6B5A9F47F7ED1C6F7F3ACAB1EE78963E02D234656B12C7CC2AE431588` |

The independent reviewer executed the real Lua54 files with mocked BizHawk
APIs, not an emulator. Five execution groups passed and16 semantic controls
were rejected. Coverage includes every256 score-stage byte, ordinary0/boss2
ownership gates, one-shot lifetime, both post-Options title callbacks,
direction-free default selection, healthy activation/early stop/state export,
valid1A/1B, copied firstE5 facts and immediate closed scalar failure evidence
that remains unchanged after later failures. No bulk capture occurred in CPU
callbacks. The report is
`build/gba-shoot-entry-observer-qa-20261109/final-failure-evidence-report.json`;
see [the independent record](shoot-native-entry-observer-qa-20261109.md).

These checks establish the observer's bounded behavior in the harness. Actual
campaign progress, rendering and healthy native activation require the separate
root-owned hidden run and capture audit.
