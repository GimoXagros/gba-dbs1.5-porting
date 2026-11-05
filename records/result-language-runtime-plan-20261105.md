# Ordinary four-language result observation — 2026-11-05

Prepared observer and mocked host self-check only. Root owns all invisible
emulator execution. This record does not claim a successful game run.

Input is the independently verified result component
`A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F`.
Root must retain the existing private-desktop, exact loaded-ROM comparison,
isolated SaveRAM/config directories, no physical background input, no
autoload, and no guest-memory-write launch controls. No supplied save or
savestate is an input. The observer dumps the complete loaded8MB ROM.

## Root launch parameters

Use `tools/bizhawk_probe_result_languages.lua` with one fresh process and
new isolated output directory per language:

```text
--lua=W:/tools/bizhawk_probe_result_languages.lua
--userdata=output:W:/build/<new-run>;language:2;frames:24000;start_frame:2970
```

Language0/1/2/3 selects English/Japanese/Korean/Digicode. The first requested
observations are Korean2 and Digicode3, sequentially. The host deadline can
reuse480seconds; a deadline remains incomplete evidence. Wait for
`result-done.txt`, which is deliberately written only after all snapshots,
screenshots and the final summary have closed. There is no `done.txt`.
Pin both the script and actual loaded ROM in each launch manifest.

## Ordinary input and state checks

1. Start is held for15 relative frames at2970. At3150 the observer begins
   adaptive title navigation. It reads the active priority1000 task's actual
   callback: prompt08090C7C receives Start; settled menu08090FA0 is navigated to
   row2 using cursor byte03002C5E, then A enters native Options mode14.
   This avoids assuming a fixed frame is already the menu.
2. Options row is halfword0300473E. The observer scans52 active native task
   slots at02010000, stride118, header active bit2 at+10, and finds priority
   1500. Its payload+0/+2/+4 are pending language, entry language and I/O error.
   Ordinary Down reaches row4, then Left/Right reaches the requested pending
   value. Endpoints0..3 are respected. Four-frame presses are separated by
   at least26 released frames; transitions release any in-flight press.
3. `options-staged` captures row/pending evidence. A on row4 performs the
   existing native commit. A read-only execution hook at0801FC5C records the
   actual writer entry while in that phase. The observer requires mode14 to
   exit to title, tagA0..A3 to match the request, at least one observed writer
   call and the native C0-byte checksum to match its stored word. Native
   I/O error causes a captured failure; it is never silently bypassed.
4. On title re-entry all five native presentations must use the selected
   title P0 and the expected tag. `title-committed` captures that state.
   Ordinary Up/A selects row0, then A confirms native selection modes4–6
   with default choices. Battle mode7 is captured. The observer sends no
   combat or result input, allowing the ordinary battle/timeout to choose
   its natural result. Continue before any result is an explicit failure.

The script checks the actual result selector's four literal P0 values
before emulation. Expected resources are English080B8210,
Japanese08651AE0, Korean086DA640 and Digicode087DFC20. It never substitutes
state, pointers, timing, score, identity or controller memory.

## Actual result consumers and captures

Six initializer-return hooks at08998C/0899F0/089C00/089C64/089DA0/089F38
retain actual r5 destination handles and initialized P1/P0/P2 pointers.
The original initializer preserves r5, so it identifies the presentation
passed on the stack. Its selected P0 must equal the requested language.
Registers and callback instruction addresses are logged separately.

The three actual text draw calls at0808B0AC/0808B170/0808B19C log actual
presentation r5, event, layout, flags and pointers. Only a draw with selected
result P0 and native event0/1/3 marks label visibility. Event3 specifically
marks actual last-chance use. A winner name drawn from its separate P0 does
not count as the requested result label.

Frame-boundary captures include `result-enter`, `result-first-label`,
`result-plus120` and`result-plus300`. They write complete IWRAM/EWRAM,
VRAM, PALRAM, OAM, display registers04000000..0400005F and a screenshot.
The current known initialized presentation handles and actual fields are
logged at each capture. `options-staged`, `options-committed`,
`title-committed` and`battle-enter` supply the route evidence.

If the result exits early, `result-exited` records that boundary; absent
120/300 or last-chance observations remain false in the summary. The script
does not force a draw or keep a result alive. Init/draw visits establish
resource use, while the screenshot and native hardware buffers still need
independent decoder/visual review.

Terminal outcomes distinguish `result-label-observed`,
`result-label-observed-early-exit`, `bounded-no-result` and explicit failures.
The summary retains commit/title/battle/result/label/last-chance/+120/+300
booleans and writer/init/draw counts. All eleven controller buttons are
released before the final summary and completion marker.

## Host self-check

`tools/verify_bizhawk_probe_result_languages.py` runs the actual Lua script
through the bundled Lua5.4 library with mocked APIs. Four ordinary language
routes, native commit-error handling and bounded no-result are covered.
It checks adaptive row/pending movement, commit/checksum/title checks,
all eight normal captures, heading versus event3 detection, complete input
assignment/release, and that the completion marker's close is the final
write before exit. It opens no ROM or save and launches no emulator.

The self-check passes. It requires Start at each prompt and ignores A there;
both title-to-menu passages must actually advance through Start. Real core
hook delivery, normal route timing and result screenshots remain root-owned.

## Native prompt correction after the partial Korean run

The first Korean run proved Options commit and selected title-resource
initialization, but the initial observer sent A while in the title prompt.
It remained there until the native attract/demo transition. Root stopped
the run and preserved it as incomplete; this is not evidence of a ROM bug
or of a visible translated title menu.

Exact input consumers explain the correction. Native08090D38 reads
0300130A;08090D40 tests mask20. Only that Start branch replaces the prompt
callback at08090D54. WSC1.5 source78047E readsC00:385C, and780482 tests
the same20 mask before780485 branches into prompt advancement. The native
settled menu instead tests A40 at080910B4, with Up1/Down4 at080910A4/AC.
Both observer prompt branches now pulse Start; menu confirmation remains A.
The mock has the same distinction and requires two prompt Start advances.

Skipped: emulator execution, fresh-process language reload, forced draw or
last-chance reproduction and hardware testing. Risk: a successful normal
WIN/DRAW route alone cannot certify actual last-chance rendering.
