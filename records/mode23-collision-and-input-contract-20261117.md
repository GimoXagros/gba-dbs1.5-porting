# Mode23 collision translation and input contract

New `tools/mode23_collision_rules.py` emits a linked ARM body for source `4090:BF42` through its actual `C774` return (raw `74C842..74D075`, exclusive). It allocates no ROM region, global RAM or tasks. R4 is the controller context; R4..R11, SP and LR are preserved. Actor handles are read through the scene's typed actor helper. The source auxiliary pickup tail is included through `m23_collision_pickup`, whose presentation transaction belongs to the scene author.

The translation retains descending collision-field clearing, ascending participant pairs, inactive-bit tests, signed position shifts, 32-bit squared distance, the source Newton square-root termination, halfword truncation, the unusual final `SAR AX,1` after eight signed product shifts, both asymmetric velocity responses, collision-count averaging and callback order. The second response overwrites the first response's projected fields exactly as the source does. Averaging truncates signed division toward zero. Source `C831` angle-difference semantics are embedded, including its `>=127` boundary. The first auxiliary hit clears the global active flag before the already-powered or pickup paths.

All three source strength-threshold branches request sound D9 with priority 1 and have no other differing effects. Their unused stack strength calculation is omitted; the source's potentially uninitialized strength word consequently cannot introduce a new native read. Sound-service gating itself remains the scene adapter's responsibility.

The private `m23_bf42_atan` helper accepts signed16 R0=y/R1=x and returns the source signed16 angle. It translates the source quadrant and ratio approximation, rather than using floating-point trigonometry. The Newton helper preserves the source wrapped16 addition and stop at absolute signed16 delta <=2 or 40 iterations; it is not floor square root. Trigonometric lookup uses the shared `m23_sin`/`m23_cos` adapters: source `7519C9..751BC9` is byte-identical to native `12360..12560` (256 signed halfwords). Source 19A8 is sine/native12348; source19BF is cosine/native1233C. Adapter preservation and invocation are separate scene integration obligations.

Author check `tools/check_mode23_collision_rules.py` executes the generated ARM against a source-derived model. Final report `build/mode23-collision-author-r2-20261117/report.json` SHA256 `15789EAC9EEDAF918CF420E18238E9650A4759ADDDA5B32203BB060930ECDB4A` passes 732 arithmetic cases and 128 complete collision scenes with 3–6 participants, including pair and auxiliary paths. The additional32 scenes begin with zero velocities and nonzero stale response fields, preserving the source's subsequent stale-field accumulation. It checks preserved registers, SP/LR, callback/sound order, changed halfwords and write extents. Task, callback, sound, trig and pickup adapters are explicit fixtures. This is author verification, not independent review, installed-scene execution or gameplay evidence. Initial report008D8769 remains preserved separately.

Generator SHA256: `608083CE5EF46D601AACAA853B6CD9C0B52C603FB3EB9623BFC869088B207A8F`.
Checker SHA256: `829BBD28CC18E42C5B29BA3BF25BAA4B7AFE31A41CE0DF4BF235070B162AC602`.
Source collision extent SHA256: `82923DC77B00F1AC7060143D9768494E330E21FC1426E8B935A85EC1A7F57701`.

Source `atan(0,0)`, `sqrt(0)` and overflowing x86 quotient are outside the defined arithmetic contract because the source divides by zero or faults. No zero-vector gameplay behavior or clamp is claimed. Reachable scene inputs still require integration verification. No emulator, main build, frozen gate, ROM or Git changes were made by this module's author.

## Current versus previous input

The source poller at `751889` stores the current B5 bank into `0C00:3854`; `7518A2/7518BC` merge the remaining banks. `75190D..190F` complements the value into `3856`. `751912..1920` computes `(newheld XOR previousheld) AND newheld` into `3858`, using previousheld `3852`. Thus the correct native correspondence is:

| Source owner | Native owner | Meaning |
|---|---|---|
| 3852 | 03001300 | Previous held |
| 3854 | 03001302 | Current held |
| 3856 | 03001304 | Complement of current held |
| 3858 | 03001306 | Newly pressed |
| 385A | 03001308 | Newly released |

Native `118C0/118C4` retain the previous held word, `1192C` stores newly mapped input, `119A4/119A8` writes its complement, and `119AC..119BC` computes newly pressed. The earlier input mutation fixture's label calling source3856 held was incorrect; it does not change the correct native held1302/pressed1306 addresses. Frozen historical tools remain unchanged.

## Common frame and OAM ownership

Source `7506F6` selects DS0C00 and `7506FB` increments word[4] in the frame service. Native `114EC` checks the frame-service flag030012D5; `11504..11510` loads, increments and stores the counter at030012D0 (literal1154C). Source mode23 reads the low byte of[4], so `LDRB030012D0` retains the relevant wrapping byte despite the native counter being32 bits. Address03001338 is the task count, not a frame counter, and must not be used for blink/selection timing.

The renderer at native12C58 appends entries to03001428 and advances cursor030012CA (literals12DBC/DC0). The common frame display service155C, specifically1170C..117CC, copies the cursor's entries into physicalOAM07000000 and copies their32-byte dynamic tiles from02000000 to06010000. It hides remaining OAM entries through128 at1179C..117C4, then clears the cursor at117C8/117CC. These are existing global frame services, not a scene child task. Native source-OAM helper counterparts12710/12714/12718/1271C are BXLR wrappers; a translated source extra OAM-reset task would duplicate ownership.

The retirement contract is therefore to stop every scene-owned producer by retiring its tasks, then permit the existing common frame service to flush/hide the previous entries. Individual children must not clear shared OAM staging while other scene producers are still live. Background tiles use06000000..0600FFFF, disjoint from this dynamic OBJ upload region; the scene builder must still establish its explicit background character/screen allocation and palette0 lifecycle.

## Display shadows and source window coordinates

Source port00 maps to the native shadow030012B6. Common155C maps source bit0 Screen1 to nativeBG1 enable0200, bit1 Screen2 toBG0 enable0100, bit2 sprites toOBJ1000, and bit20 window toWIN1 enable4000. It also enablesBG3. It preserves the existing character/screen-base bits ofBG0CNT/BG1CNT, changing only their priority bits to2/3; a new scene must establish the intended bases explicitly.

Source window ports08(left),09(top),0A(right),0B(bottom) map respectively to native shadow bytes030012BC,030012BE,030012BD,030012BF. The native common service adds its8-pixel margin and assemblesWIN1H/WIN1V; adapters must not add that margin again. In particular, the rule helper is `m23_window_top`, storing source OUT09 into030012BE. Scroll ports10/11 map to12B8/12B9 (Screen1→BG1HOFS/VOFS); ports12/13 map to12BA/12BB (Screen2→BG0HOFS/VOFS). The common display service subtracts8 when projecting these scrolls.

Correction after independent execution of the actual display projector: the earlier horizontal addresses12C2/12C3 in this record were wrong. Native1163C..11660 reads12BC/12BD and writes WIN1H04000042;11664..11688 reads12BE/12BF and writes WIN1V04000046. The other four bytes12C0..12C3 belong to WIN0H/WIN0V. The earlier summary-only window fixture did not establish hardware projection. Scene author and independent reviewer corrected the horizontal adapters before installation; collision/input generator code itself contains no horizontal adapter.
