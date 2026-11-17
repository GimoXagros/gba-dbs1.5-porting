# Iraira rendering consumer review — 2026-11-17

The isolated 3FE5 image passes `tools/verify_iraira_render_consumers.py` (SHA-256 `E86C60BF7EF9C390A995BEFBF8A8E014D6F9D15437541C26ADCFC04918B54263`). Frozen report `build/iraira-render-independent-20261117/report.json` is `0112FDCC4B6EB2A64DB67A22CB57583847840FEC6A96DA11ACB91614702DABCC`.

The complete source resource descriptors resolve maps at 4CA1C0, following the actual palette at 4C60E0 and tile data at 4C61C0. Independent inverse checks cover all 4,032 map entries, 32,768 tile pixels and 111 copied palette colors. The earlier asset path used the palette region as map data. All 22 repair spans are bounded and invert to E6B2 exactly: 25,382 declared bytes and 23,155 changed bytes. The 17 aligned-AI writes remain unchanged. D8AC00–D8B400 is blank in the input and has no conservative inbound references.

Native background construction now sends source resource 37 to descriptor 03002388 / Screen 2 / map F800 and resource 38 to 03002338 / Screen 1 / map F000. Both existing 2×2 resource descriptors remain. The full native initializer, using existing explicit copy/BG service summaries, verifies the descriptor, map and port bindings, LR stack balance and source phase clear.

Source Waterfall and Iraira display callbacks are exactly the same 117 bytes, respectively 75F9EE–75FA63 and 75FA64–75FAD9. The repair reuses the already established 08628300 callback byte-for-byte. Its separate display phase remains at 03002568 and is cleared at the graphics initializer tail without changing the adjacent owner at 0300256A.

The palette counters use 03003D30, whose existing initializer 08628400 clears exactly 32 bytes. The next owner, 03003D50, is live AI state. The new cycle writes only five halfword counters at offsets 0–8; it neither writes the old 03002568 display state nor stores a large source color buffer across the AI boundary. The projector derives the five immutable color groups from those counters and writes exactly the source palette destinations at offsets 42, 62, 82, A2 and C2. A complete 3,360-tick period closes; 336 phase/dim projection cases match all 38 source colors and preserve palette gaps. Three suppression cases and 288 routing cases verify the gates and preservation of all other stage paths, including the dedicated Shoot route.

The stale clone backdrop value 023D is replaced by zero. This is a real palette owner: native 08377BEC–08377BF8 reads 03002654 and writes hardware palette color 0. Source common initialization clears its 0380 counterpart, and the Iraira initializer does not replace it. Thus the correction restores the source black backdrop instead of changing an unrelated field.

CLI: `python tools/verify_iraira_render_consumers.py --before <E6B2> --after <3FE5> --source <WSC1.5> --manifest <Iraira component.json> --alignment-owner <aligned AI component.json> --report <fresh path>`.

## Read-only replay delta

`tools/check_ai_iraira_delta_independent.py` produced `build/ai-iraira-delta-independent-20261117/report.json`, SHA-256 `FA07E06E715BF2C7B5FF3EFBD47AF6F331854FE85AD386D45758911E36353849`. It executes the actual outer wrapper C32E0 and checks its exact adaptations over frozen 45490 and 4A2. The new observations consist of one native after-clock-store hook and one display-phase write watch, with five pinned opcodes. Code review checks the 32-row phase bound, 121-clock bound, typed owner and consecutive decrement predicates. Author A1F11727 supplies the composed clock/phase mock cases; old suites were not repeated.

Host `2E68861ADF5D4CC5BC9CFE404557D62F37DDCAD54EFA3227DF8A2B9460161140` reverses through exactly seven substitutions to F139. Pins `56E388FF5987CF82CBE019C21C82197AE2228AD9C3DA50F1865BF5CCCF6E67D0` preserve all old files and add only the new observer. Input, authorized write guards, bounds and strict healthy-Shoot terminal condition remain unchanged.

These are source, instruction and instrumentation checks. No emulator or visual result is claimed here; root owns execution and separate capture QA owns visual acceptance.
