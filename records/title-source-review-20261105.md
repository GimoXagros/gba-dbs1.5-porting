# Title source and localization boundary — 2026-11-05

Follow-up: the source background identified below is now implemented and
independently verified, including an isolated ordinary-input title capture.
See `records/title-background.md` and `records/title-background-qa.md`.
The six additional menu events/controller tree remain open. This inventory
preserves the earlier read-only findings; its proposed BG work is completed.

Read-only review of the pinned WSC1.5 ROM, exact v65 candidate, existing
title builder/checker, and previously decoded source preview. No pixel,
ROM, save, or running emulator was changed during this review.

The existing four-language title component replaces only five sprite
labels. It does not port the source1.5 title logo/background or six further
menu frames. Extending its P0 alone cannot complete the source title.

## Source graphic consumers

Source initializer raw `780000..780287` selects Japanese explicitly.
Its C3 bank is `CA`; DS is `380C`, giving raw base `4A80C0` for these
banked background copies. The positive producer sequences are:

| Source producer | Selected source payload | Destination / population |
| --- | --- | --- |
| `780043..78006A` | `4AB6B0`, palette | `0000:FE20` and `0300:02D8`, `60` words /192 bytes each |
| `780070..780088` | `4A84B0`, planar BG tiles | `0000:7200`, `1980` words /13056 bytes |
| `78008A..7800AC` | `4A80C0`, BG map | `0000:0800`,18 rows of28 words,8-byte row padding |
| `7800F5..78010C` | `4AB790`, secondary palette | `0000:FF20`,16 words |

The alternative language branch uses offsets `6D60`, `3AE0`, and `36F0`
for the first three copies; the fixed zero branches select the Japanese
payloads above. These are the actual background data consumers, separate
from the menu P0/P1/P2 constructor arguments at `780170/179/182`.

The native title initializer is `080908A0`. Its background transfer uses:

| Native producer | Source | Destination / population |
| --- | --- | --- |
| `08090900..08090920` | `0808FB58` | palette `05000020`, staging `0201E400`,100h bytes each |
| `08090924..08090934` | `0808BB58` | VRAM `06003200`,`D88`32-bit words /`3620` bytes |
| `08090938..08090954` | `0808B768` | VRAM `0600F000`,18 rows of14 32-bit words,8-byte padding |
| `080909B8..080909C4` | `0808B748` | title palette staging `03002C38`,32 bytes |

These sizes follow native `08000B84`, which programs32-bit DMA3 and
advances source/destination by `r2*4`. They must not be interpreted as
byte counts. Other initializer transfers at `08090998/9A8` load shared
data from `08080140/08080DC0`; they should be preserved unless a separate
source dependency demonstrates a required change.

The source Japanese BG geometry is28x18 cells, matching the native
row-copy geometry. The source planar tile/palette packing and map
attributes still require explicit conversion. Replacing raw WSC bytes in
the native transfers would be incorrect. A minimum source-title component
therefore converts and independently compares all selected source BG
pixels, map attributes and palettes, allocates one complete translated BG
resource, and reconnects these transfers while preserving VRAM ownership,
fade/staging copies and the native224x144 placement within GBA output.
The current five-label language selector should remain separately owned.

## All eleven menu frames

The existing source preview
`build/title-language-source-20261023/japanese15-native-palette.png`
shows all eleven frames from P0`3C3FE0`, P1`3D3A80`, P2`3D7EE0`.
The static atlas is raw`396300`,142 tiles/`11C0`bytes. Events are
single-frame. Events0–4 are already installed; the remaining frames are:

| Event | Source bitmap wording | Proposed English / Korean wording | Japanese-reading Digicode input |
| --- | --- | --- | --- |
| 5 | コレクション | Collection / 컬렉션 | これくしよん |
| 6 | Ver.1.5とバトル | Battle Ver.1.5 / Ver.1.5와 대전 | source Latin Ver + version digits retained as source tokens; とばとる kana |
| 7 | バトスピとバトル | Battle Battle Spirit / 배틀 스피릿과 대전 | ばとすぴとばとる |
| 8 | テイマータグ | Tamer Tag / 테이머 태그 | ていまーたぐ |
| 9 | デジモンシュート | Digimon Shoot / 디지몬 슈트 | でじもんしゆーと |
| 10 | ? | source question-mark frame / same | retain source punctuation |

English/Korean entries above are review proposals, not installed or
release-approved strings. The source source1.5 controller has a menu
state machine beyond the native five-row title. `780E40..780E66` selects
a starting event and increments it while laying out the current menu;
`780E68..780E8D` conditionally replaces a presentation with event10.
`780CFE` also compares the current event with10 and handles the unavailable
entry specially. Thus `?` is a lock/unavailable presentation, not a sixth
ordinary gameplay mode. The full destination/unlock controller tree was
not reconstructed in this bounded review. Adding six simultaneous rows
or exposing Shoot before its external controller is complete is unjustified.

## Existing localization review and minimum remaining scope

Current Japanese0–4 use exact source bitmap parts. Korean `혼자 대전`,
`친구와 대전`, `설정`, and retained `D-ARK` are short and clear.
The prompt `시작 버튼을 눌러 주세요!` is readable; a later polished pass
could use `START 버튼을 눌러 주세요!` if the desired convention names the
physical button. This is a wording preference, not a required correction.
Existing English retains `PRESS START`, `1P BATTLE`, `2P BATTLE`,
`OPTIONS`, `D-ARK`; no direct mistranslation was found in those five.

Current Digicode correctly follows Japanese wording rather than English
romanization. `オプション` explicitly normalizes smallョ to the reviewed
full-sizeヨ glyph (`おぷしよん`). Existing source exclamation and D-ARK
hyphen remain exact pixels; the latter must not become the long-vowel
mark. New events need the same explicit small-kana policy for
コレクション/シュート, voiced-kana support, Japanese long-vowel marks,
and a declared version-number/token policy. Latin letters should appear
only where the Japanese source itself contains Latin tokens.

The minimum complete next scope is source BG conversion first, followed
by the missing controller tree and only its reachable resource events,
then four-language artwork for those events. Recompute complete live-task
OAM and tile-staging totals: current maxima92/88/88/111 cover only the
existing mutually exclusive prompt/four-button populations. Neither those
bounds nor the old capture checker certify any expanded menu population.
Pixel production and independent visual QA must precede integration of
new Korean/Digicode frames. No new title language or BG payload was authored
by this review.

Skipped: full source menu destination/unlock tree and all background pixel
inversions. Risk: current five-label title evidence does not establish
a source1.5 logo/background or complete four-language title.
