# Bounded title language component — 2026-10-23

This development component localizes the five existing native title events.
English retains its original resources; Japanese uses exact source layouts;
Korean uses reviewed-in-context drafts; Digicode uses the Japanese readings.
The original title logo, background, selection behavior, coordinates, palettes,
animation, and all other resources remain native. The six additional WSC 1.5
title events are outside this component. Whole-game four-language support is
not complete.

The only accepted predecessor is the independently checked recovery-table
candidate `build/character-damage-routing-20261023/current-candidate.gba`,
SHA-256 `A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71`.
The builder does not modify any frozen Options, glyph, action, or recovery tool.
It opens no save and launches no emulator.

## Source wording and exact producer

The WSC 1.0 title branch at raw `3C2916` tests the language. Its Japanese P0/P1/P2
are `2B0BA0 / 22FF80 / 2B5FC0`; the English alternative is
`2B14B0 / 2B4F60 / 2B5FF0`. WSC 1.5 fixes Japanese at `780148`
(`33 C0 33 C0 3D 00 00 75 51`). Its actual constructor arguments at
`780170 / 780179 / 780182` bind P2 `3D7EE0`, P0 `3C3FE0`, and P1 `3D3A80`.
This establishes the chosen language from the producer rather than guessing
from corresponding event numbers. The alternative English resources at
`3C43D0 / 3D3B70 / 3D7F10` are not the selected Japanese assets.

The selected source P0 has eleven layouts. The first five have
`17,22,22,22,22` parts. Its static descriptor at `3D8E90` binds the complete
142-tile atlas at `396300`, length `11C0`; the next descriptor is the terminator.
Only the first five layouts are installed, preserving every source part and
pixel while converting planar tile packing. Their source P1 event payloads and
timing records convert byte-for-byte to the original native five-event P1.
All four WSC 1.0/1.5 Japanese/English palette blocks convert exactly to the
original native P2. Existing P1 and P2 are therefore retained.

The actual Japanese source was rendered and inspected in
`build/title-language-source-20261023/japanese15-native-palette.png`.

| Event | Exact Japanese source | Korean draft | Digicode reading |
| --- | --- | --- | --- |
| 0 | スタートボタンをおしてね！ | 시작 버튼을 눌러 주세요 + native `!` | スタートボタンをおしてね + native `!` |
| 1 | ひとりでバトル | 혼자 대전 | ひとりでバトル |
| 2 | ともだちとバトル | 친구와 대전 | ともだちとバトル |
| 3 | オプション | 설정 | explicit おぷしよん |
| 4 | D-ARK | exact Japanese source frame | Latin D + native hyphen + Latin ARK |

The bounded small-`ョ` alias is explicit in `localization/title-labels.json`.
The user chart's small-kana example and the creator-reference mapping support
using the existing full-size `ヨ` glyph. The reference uses the same image and
uniform rendering for small and ordinary YO; evidence hashes are recorded in
[digicode-glyphs.md](digicode-glyphs.md). The frozen encoder, catalog, and glyph
bytes remain unchanged; all other unsupported input still fails. No English
translation or arbitrary romanization supplies Digicode wording.

The source contains Latin `D-ARK`, so only those four alphabetic letters use
the Latin Digicode table. Its hyphen is not converted into the Japanese
long-vowel glyph. Six exact native pixels at source event4 `x=-7..-2,y=-1`
are retained, including palette indices `14,13,13,13,13,14`. The source
exclamation is the exact 22-pixel slice of event0 `x=48..50,y=-4..3`.
Korean event4 also uses the exact Japanese hyphen-bearing frame; English keeps
its original differently styled separator. Root reviewed the static preview
and requested this Korean punctuation correction before the candidate froze.

## Native hookup and lifetime

Mode3 row `08015B94` binds initializer `080908A0`, constructor `08090BF4`,
and common callback `080159B0`. The initializer creates exactly five existing
presentations at `03002A78 + event*50`. Original resources are
P0 `0808FD08`, P1 `0808FC58`, and P2 `08090878`.

Only raw `090A18` is hooked. Its original word `E59F81A0` loads P0 into `r8`.
An unconditional ARM `B` reaches `0863FB00`; it does not overwrite LR.
The 48-byte, twelve-instruction helper saves `r0/r1`, saves CPSR flags, reads
the existing language byte `0300112F`, selects one of four P0 pointers, restores
flags and `r0/r1`, and branches to `08090A1C`. All registers except the original
destination `r8` are preserved, LR is unchanged, and the eight scratch stack
bytes are balanced. The twenty-byte literal tail contains the tag pointer and
four P0 values. `A0..A3` select English/Japanese/Korean/Digicode; every other tag
falls back to English without writing RAM. There are no new tasks or RAM owners.

P1/P2 loads at `090A08/090A28`, initializer call `090A54`, event-selection call
`090AD8`, presentation flags, and native renderers remain unchanged. The helper
runs for every existing title object through the actual native init loop.

| Owned raw span, end exclusive | Purpose | Bytes |
| --- | --- | ---: |
| `090A18..090A1C` | P0-load branch | 4 |
| `63A800..63BBA4` | Japanese five-layout P0 and source atlas | 5028 |
| `63D000..63DB60` | Korean five-layout P0 and 75-tile atlas | 2912 |
| `63E000..63ED64` | Digicode five-layout P0 and 88-tile atlas | 3428 |
| `63FB00..63FB44` | P0 selector and literals | 68 |

All allocation bytes were FF in A18. Ownership guards scan encoded pointers
at every byte alignment, ARM branches/PC-relative loads/address construction,
and Thumb literal/address construction. Complete expected-write ranges are
disjoint, and reversing them restores the exact predecessor. Native title,
task scheduler, palette helper, and renderer dependencies are protected.

## Complete title population and preserved pixels

The title has three task roles: priority0 mode controller, priority1000 main
title callback, and priority `FFFFF000` palette fade. The constructor allocates only
the latter two. The title common callback is `BX LR`. Fade `080914E4` calls
only `0801207C`, which writes palette RAM and invokes arithmetic division;
it emits no sprite presentation. The title's other artwork is background data.

The main callback uses these mutually exclusive phases:

| Callback | Draw site | Complete population |
| --- | --- | --- |
| `08090C7C` prompt | `08090DD0` | Event0, or hidden by blink |
| `08090E58` slide | `08090F30` | Events1–4, four iterations |
| `08090FA0` menu | `08091240` | Events1–4, four iterations |
| `08091310` exit | `08091414` | Events1–4; selected item may blink |
| `08091598` timeout | none | No title sprites |

Start replaces the current main task callback at `08090D54`, then branches
to the prompt epilogue at `08090DB0`; it does not fall into the menu loop.
The scheduler loads the task callback at `08011DCC` and advances to the next
task at `08011DF0`. A replacement callback therefore runs on the next visit,
after the native frame queue has been consumed/reset. Priority0 transitions
run before the main title task; they cannot add the next mode after the old
title draws within the same traversal. Prompt and menu counts do not overlap.
The builder pins the callback words, draw sites, loop populations, constructor,
coordinates, and palette helper under `manifest.native_population`.

Native initial positions are `(112,104),(-48,36),(-48,72),(-48,108),(-48,200)`.
All four menu objects count, including the offscreen D-ARK at Y200. The real
renderer permits the latter's part coordinates below 232, so display clipping
does not remove its queue cost. X animation, highlight choices, and blink can
only decrease the conservative counts below.

| Language | Parts for events0–4 | Prompt | All four menu objects | Peak staged bytes |
| --- | --- | ---: | ---: | ---: |
| English | 8,22,22,26,22 | 8 | 92 | 2944 |
| Japanese | 17,22,22,22,22 | 17 | 88 | 2816 |
| Korean | 24,22,22,22,22 | 24 | 88 | 2816 |
| Digicode | 26,30,33,24,24 | 26 | 111 | 3552 |

These bounds retain all native title objects and remain below 127 entries and
4096 staging bytes. No clamp or renderer change is used. Full Digicode buttons
are 80/88/64/64 pixels wide and 18 pixels high, retaining complete borders,
text, outlines, and all 196 pixels of each native colored marker. Korean menu
buttons retain native dimensions; source Japanese layouts are exact. Every
authored frame round-trips through the native 8x8 tile format without pixel loss.

## Candidate, reproducibility, and limits

The A18-based candidate is
`build/title-language-a18-20261023-a/title-language.gba`, SHA-256
`143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80`.
Its manifest SHA-256 is
`225523736BF3A36F3C2FEED807312878620E4E042ABF58C1EBF2DE59061F3F25`.
The `-a` and `-b` builds independently reproduce identical ROM, manifest, and
static preview. The preview at `previews/title-all-languages.png` displays all
twenty language/event combinations with normal and highlighted native palettes;
it is not a runtime screenshot. Prompt highlight is illustrative only.

Run `tools/build_title_language.py` with positional arguments:
`before gba wsc10 wsc15 font license output`, plus `--manifest` and optionally
`--render-directory`. The builder pins the original ROM inputs from
`analyze_language_consumers.INPUT_HASHES`, the licensed Galmuri11-Condensed BDF
and license hashes from the frozen Korean component, and the reviewed 98-cell
Digicode row-byte SHA-256
`E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195`.

The independent `tools/verify_title_language.py` passed on both143E builds.
Its report `build/title-language-a18-20261023-a/verification.json` hashes to
`9974145ADB151ABE505E0CB09467C38342DE899CBEC848740999BC4534FCC724`;
the checker source hashes to
`941F07EE2CC0775765A3620EBBE90EC8EFF6E6638F27A78986DAD0DF7931C6BC`.
It imports no producer and checks all twenty frames, complete source palettes
and event metadata, 8,192 tag/flag register cases, LR/SP/CPSR preservation,
eight-byte stack headroom, the three-task population, all 11,440 written bytes,
full inverse, and ARM/Thumb allocation references. Its 112 negative cases pass.
WSC 1.0/1.5 Japanese menu pixels1–4 match; their prompt differs, and the selected
Japanese prompt is explicitly the WSC 1.5 one.

Independent checker positional arguments are
`BEFORE AFTER GBA WSC10 WSC15 FONT LICENSE MANIFEST OUTPUT`, optionally
`--digicode-font FONT_JSON`. Use
`build/digicode-glyphs-20261023/font-8x16.json` for the independently decoded
row-byte input. Repeated-build comparison is
`build/title-language-a18-20261023-comparison.json`, SHA-256
`879502C22B1CB8ED5B585C4C6DBBCDBE102877BFFA66DA3AACA5D104FE9F2889`.

Root-owned exact143E runtime observations, with no visible emulator window:

| Capture under `build/` | `capture.json` SHA-256 | Observed result |
| --- | --- | --- |
| `runtime-title-digicode-commit-20261023` | `27E857F56CFB47883EBEDE75A277DA0F85754395B5A02C0A0110F777C4EE4E86` | Saved Digicode; title prompt, 26 OAM, screenshot reviewed |
| `runtime-title-digicode-menu-20261023` | `89AE09EACE2E91B65EB2B0EF899BAAF4550A3C89B5225DD69DC5EF118836550B` | Fresh process menu, exactly111 OAM; all four X112, including Y200 D-ARK |
| `runtime-title-korean-commit-20261023` | `36D66444DD25F62E795796113856D4CAF7D3CE3EB4DD614BB59CE1D08CD1E730` | Saved Korean; title prompt, 24 OAM, readable screenshot reviewed |
| `runtime-title-korean-menu-20261023` | `2B9FB3B2D1EE46D3DFFA6B4A418EE739701DC77C3F6E10D86AA90C4488AF1352` | Fresh process menu, exactly88 OAM; readable screenshot reviewed |
| `runtime-title-japanese-commit-20261023` | `D63FEB3691D91C3CEF22A66A69732D76C68AE6F2EA6F64A09191716F157F5880` | Saved Japanese; source title prompt, 17 OAM, screenshot reviewed |
| `runtime-title-japanese-menu-20261023` | `B1C1380C2A807E4E4D462EAF8E757EE97A12C8E00FF058DE0170C77ED3D1C03D` | Fresh process menu, exactly88 OAM; source Japanese screenshot reviewed |

Each root checker verifies actual P1 command/auxiliary fields, event/layout
identity, native0408 flags, coordinates, selected resources, complete staging,
and physical OAM/VRAM. A settled menu requires the exact four-object sum, not
just an upper bound; prompt blinking is handled separately. These bounded
observations do not certify every transition, all other consumers, font
authentication, translation release approval, or whole-game completion.

The final integrated A3E candidate
`A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61`
retains the title component exactly through the independently checked hit-layer
inverse. Root repeated the Korean persistence/title observations on that exact
candidate and reviewed both screenshots:

| Capture under `build/` | `capture.json` SHA-256 | Observed result |
| --- | --- | --- |
| `runtime-integrated-title-korean-commit-20261023` | `C3067BC8B0BB872A8D186E740852CDBB2033145314F9CFC28E12E0C120B85A02` | Saved Korean; complete title prompt,24 OAM, checker PASS |
| `runtime-integrated-title-korean-menu-20261023` | `F684F5772191536A0EDA86C3F151345FEC1E1284C912A7B491CBC93FD71F01BE` | Fresh process; four Korean menu objects, exactly88 OAM, checker PASS |

The language worker read only the capture manifests and verification reports;
the parent owns emulator execution and generated persistence files.
