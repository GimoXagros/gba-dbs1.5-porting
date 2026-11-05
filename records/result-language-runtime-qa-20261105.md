# Four-language ordinary result capture audit — 2026-11-05

All four completed root-owned private-desktop runs pass independent capture
QA on exact v67 `A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F`.
The captures prove native Options commit, selected title presentations,
natural battle→mode8 result entry, selected result initializer/draw resources,
and the actual visible WIN/WINS label. They do not prove LAST CHANCE or DRAW.

| Run directory suffix | Language | Actual visible label | Complete label parts/pixels | Active OAM at +300 |
| --- | --- | --- | --- | --- |
| `bizhawk-result-v67-20261105-b` | Korean | shared Japanese-source WIN | 30 / 1,508 | 105 |
| `bizhawk-result-v67-20261105-c` | Digicode | shared Japanese-source WIN | 30 / 1,508 | 105 |
| `bizhawk-result-v67-20261105-d` | English | original WINS | 35 / 1,666 | 110 |
| `bizhawk-result-v67-20261105-e` | Japanese | Japanese-source WIN | 30 / 1,508 | 106 |

Each run has eight complete memory/display/screenshot captures,61 frozen
top-level files, one actual native writer entry, seven result initializer
visits,88 draw visits, and exact +120/+300 result-age captures. The two unique
draw log entries per run are the selected result label and separate winner
name. The full label proof is event0/layout0. Actual last-chance observation
is false in all four runs. The difference in total Japanese OAM population
does not change its label's30 complete parts or visible pixels.

## Independent checker and reproduction

`tools/verify_result_language_capture.py` SHA256:
`840FD003C6946DF7D29FCB701692BE9C33AFA8CC4AD803899CBBC350596F2194`.
The checker reuses only the established native resource decoder from
`verify_result_language.py`; it does not import builders, launch an emulator,
write guest memory, inspect process state, or open any save/state file.
It writes its report outside the frozen capture directory.

```text
python -X utf8 tools/verify_result_language_capture.py CAPTURE ROM RETAIL_GBA OBSERVER OUTPUT_JSON
```

Repository-root example, using the available Python runtime:

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 tools/verify_result_language_capture.py build/bizhawk-result-v67-20261105-b build/repro-v67-20261105-a/current-candidate.gba 'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' tools/bizhawk_probe_result_languages.lua build/result-language-runtime-qa-20261105/b.json
```

Repeat with suffix/output c,d,e. All four completed successfully. Reports:

| Report in `build/result-language-runtime-qa-20261105` | SHA256 |
| --- | --- |
| `b.json` | `1BE8827E762F9C59EFB65EAF3EFBA6445DFCA5E7DDC5F237EEC5D257D8C4B0B4` |
| `c.json` | `20328C64CF96D55AB6696C378FAA854569F7BB8249F4423B315F9E56282B4FE7` |
| `d.json` | `628C0AE10A1D281445C32E00417A724E7CDC27A0067DFAC01A36DE68C6D6E2A4` |
| `e.json` | `0364E3CA63CA899DEB140F37CB4484BF9FDC5A3B6765175C5D9B056D5BA95B76` |

Five small negative controls reject changed native checksum, invalid OAM
shape, copied-renderer corruption, changed actual label VRAM and changed
actual label palette. These are bounded evidence checks, not another full
component/static verifier.

## Provenance and actual route

Every report independently recomputes the complete final top-level file
inventory and each file hash. Full8MB `loaded-rom.bin` equals `probe.gba` and
the pinned final ROM. Launch completion, exact loaded identity and unchanged
script flags must all be true; `result-done.txt` must agree with the final
post-flush successful trace summary. The revised frozen observer is
`928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC`.
Its reviewed bytes contain no memory-write, register-write or state-load API.
The actual pinned EmuHawk executable and unchanged base observer are also
rehash-checked. All configured data directories stay in the run's private
directory; physical background input, last-slot loading, SaveRAM autosave,
and every recursive AutoLoad setting are false. No data subdirectory or
supplied save was opened by this audit.

The staged Options snapshot contains the actual active priority1500 task,
row4, requested pending language and zero I/O error. The actual0801FC5C
writer-entry observation falls between staging and committed snapshots.
The committed native RAM record has the correct A0/A1/A2/A3 tag and exact
sum of all C0 record bytes at030011E0. This proves current-session native
commit; it is not a fresh-process persistence test.

All five native title presentations contain the selected P0 and retained
P1/P2. These title snapshots were taken at the re-entered prompt before
visible OBJ upload: hardware OAM is zero. Their claim is selected title
resource initialization, not a visible settled translated menu.

The trace then reaches battle mode7 and naturally enters mode8 with no
combat or result button input. All seven constructor-return observations
have the selected result P0, and the actual draw carries native P1
080B9004/P2 080B9144. Hook addresses are independently checked against the
six constructor return sites and three text-draw calls; exposed ARM PC is
callback+4. Some event/layout fields at constructor return are still stale
because the following event setter has not executed. Those fields are not
accepted as initialized animation state; actual draws and later live
presentation snapshots supply that evidence.

## Visible pixels, hardware buffers and palette explanation

At +300 the checker follows the live label presentation and selected P0,
finds exactly one complete ordered layout in actual hardware OAM, and checks
all tile bytes in OBJ VRAM, every part coordinate/flip/priority/palette bank,
and all active staging bytes against OBJ VRAM. It accounts for the native
renderer’s +8/+8 viewport offset. Every nontransparent source-resource pixel
then equals the corresponding actual240×160 screenshot pixel using the live
RGB555 palette and emulator's nearest8-bit channel conversion. This proves
all1,508 WIN pixels or1,666 WINS pixels, not merely a resource pointer or a
nonblank screenshot. Root separately viewed all four result screenshots.

All128 hardware OAM records retain proper eight-byte affine interleaving;
active objects use the native regular8×8/4bpp form and sequential tile slots,
and count remains at most127. In all eight snapshots per run, the entire
384-byte copied renderer03000200..037F exactly equals retail ROM
08012C58..12DD7, SHA256
`D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685`.

The purple/blue WIN color is explained by a retained native winner-side
branch, not a newly introduced palette defect. Native08089A24 reads result
flags and08089A28 tests20. When set,08089A40/44 load destination05000240
and source08089374;08089A48 sets16 and08089A4C calls08000BA8. That copies
the original16-color alternate result palette. In all four +300 captures,
03004738 includes20 and the actual label uses OBJ palette bank2. All16 live
words exactly equal the retained table08089374..89393, palette SHA256
`2CBE7AACC4956D1BA5A6D119D16551B5CD8EF04FCD6BF5BD96D92329875416BB`.
The original English control run uses the same palette. The warm colors in
the static art preview are the base P2 palette; that preview does not apply
this ordinary runtime winner-side replacement. The checker verifies the
branch/literals, table, base palette, copier and renderer bytes remain equal
to the immutable retail GBA image. No palette repair was made.

## Timing and scope limits

The first result-label draw hook is not yet proof of hardware upload. In
Korean, first-label frame11775 still contains52 hardware objects; full WIN
appears in the later +300 frame11818 with105. +120 similarly predates the
label. The +300 hardware and screenshot independently close visibility.
Frame-boundary display-register dumps read DISPCNT6B40 and are not an active
scanline trace; this audit does not infer per-scanline OBJ enable timing from
them. The exact screenshot pixel comparison is the visible-output evidence.

Initial Korean run a remains a preserved partial observer-input failure
(A at a Start-only title prompt). It is not counted among the four successful
runs and does not indicate a ROM defect. No forced LAST CHANCE, DRAW,
campaign completion, physical hardware certification, complete language
coverage beyond these consumers, or Shoot lifetime closure is claimed.
