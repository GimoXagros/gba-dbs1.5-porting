# Independent actual-Lua DI v3 observer QA

The new read-only DI observer passes independent execution under Lua5.4 with isolated host API mocks. This validates observer behavior and source/core contracts; no emulator, save or actual Shoot runtime was used.

| Item | SHA256 |
| --- | --- |
| Observer, `tools/bizhawk_observe_wsc_shoot_di_v3.lua` | `BD01DF5A399D5D33B9859BBC484F0068B6E6406EFCD7DAAD07AB7AF38DD0E15B` |
| Independent verifier, `tools/verify_wsc_shoot_di_v3_independent.py` | `842AE0F7031252F777225136D28513EA96D288112A35841DA6958121EB6102C9` |
| Report, `build/wsc-shoot-di-v3-qa-20261109/audit.json` | `EE215465AE30C87C034A5AE7EC9F9CD218936367F3B833EEB61E8C277C3FCBD2` |
| Original WSC input | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |

The verifier/report use LF. The report records the actual Lua runtime DLL hash and seven complete archived BizHawk2.11.1 source hashes. No author validator or production builder is imported.

## Four exact instruction hooks

| Raw source | System Bus callback address | Actual instruction |
| --- | --- | --- |
|750EBD|50EBD|`push ax`, one byte, calibration|
|773650|73650|`mov ax,0C00`, three bytes, terminal marker|
|75FC98|5FC98|`mov ax,es:[di+0A]`, four bytes including prefix, pre-read|
|75FC9C|5FC9C|`out 10,al`, two bytes, post-read|

These instructions are decoded independently from the exact original. The actual Lua also checks its surrounding source bytes at initialization. V30MZ fetch increments PC before its execute callback, so each delivered callback must have `(PS*16+PC) mod100000 = callback_address+1`. Both wrong-address and wrong-PC deliveries are rejected.

Pinned managed callback registration is R,W,E while its native declaration is R,E,W. Consequently native opcode fetch delivers the managed write callback, exposed here as `on_bus_write`; it does not write guest memory. The independent mock models that dispatch rather than directly calling an arbitrary registered function. Changing registration to `on_bus_exec` prevents calibration and fails the suite.

“System Bus” is only a callback scope in this core, not a readable memory domain. The mock exposes only ROM/RAM/SRAM domains, and actual Lua runs without requesting a System Bus read. Managed callback values are0 and cannot identify consumed bytes. The observer separately labels backing-domain peeks and compares them with the full post-instruction AW register.

## Physical address and register checks

The pinned register definitions establish DS1=ES and IY=DI. DS0/IX are deliberately different in fixtures. The V30MZ effective offset truncates `DI+0A` to16 bits before adding ES; word access reads the next **physical** byte rather than re-wrapping the segmented offset. Independent execution exercises all65,536 DI values with ES0300 and checks the actual private operand/peek functions reached through the installed Lua closure.

Important cases include DI CFF5, where the low byte is RAM physical0FFFF and high byte is SRAM physical10000; DI D000, which reads SRAM1000A/B; DI FFF5, whose high byte is physical13000; and DI FFF6, where the effective offset wraps and the word is back in RAM03000/1. A separate20-bit case checks FFFFF→00000 for the high byte. Actual private mapper peeks also exercise10000,17FFF,18000 and1FFFF: physical bank1 maps into the32K SRAM domain modulo8000, not a fictitious64K SRAM buffer. Out-of-window addresses are rejected.

At each completed pair, the independently computed backing word must equal the entire AW, not just AL. Wrong high bytes with correct AL, callback value0, wrong ES, changed DI, orphan posts, duplicate pre-hooks and unfinished pairs are rejected.

The initial draft did not bind post PS/PC to the pending pre-hook beyond independent physical-address validity. A valid aliased PS:PC pair could therefore satisfy each site separately. The author corrected this before freeze: pending PS/PC is saved, post PS must match, and post PC must equal pre PC+4 modulo16 bits. The independent actual-Lua suite rejects a post using another valid physical PS:PC alias; removing the stream-pair assertion is a rejected semantic mutation.

## Bounds and actual Lua execution

The positive hook sequence completes512 actual pre/post pairs using synthetic registers and backing bytes. It emits16 distinct DI snapshots, each consisting of a complete64K RAM and32K SRAM request, plus exactly one terminal snapshot. Repeated terminal hits do not overwrite the first snapshot. Extra pairs after the cap add no pair log or snapshot; there are always four fixed registered callbacks. These remain installed after the pair cap and still validate delivered sites, while `finish()` makes all four inert. Finishing twice or with a pending pre-read is rejected.

There are22 invalid scenarios, including missing calibration, wrong source/backend/domain/freshness conditions, invalid addresses, fetch mismatches and register/word/pairing errors. Ten in-memory Lua mutations are rejected:64K physical aliasing, segmented high-byte re-wrap,64K SRAM aliasing, SI-for-DI, DS-for-ES, wrong managed callback, AL-only comparison, missing instruction-stream pairing, pair cap513 and distinct-snapshot cap17.

Empty observations and other-stage callbacks explicitly leave `actual_final_irq_observed=false`. No local test result claims that the real game reached these hooks.

## Reproduction and limits

```text
python tools/verify_wsc_shoot_di_v3_independent.py <original-C415.wsc> tools/bizhawk_observe_wsc_shoot_di_v3.lua <distinct-output.json> --core-source build/wsc-shoot-di-v3-20261109
```

Use the pinned Python runtime. The verifier loads the existing Lua5.4 DLL and executes the actual observer text, with in-memory file outputs and explicit read-only host mocks. Snapshot request domains/sizes/counts are checked; their synthetic contents are not real game captures. The test does not execute the V30MZ core or repeat unrelated game-graph proofs.

Source/core archives cover managed/native callback order, register identities, fetch timing, effective address arithmetic and the32K mapper. The future launcher still owns exact ROM/backend hashes, input and save provenance, output freshness, bounded execution and capture verification. The observer itself installs no input policy, frame loop, register assignment, RAM write or savestate operation. No original save was read, emulator launched, core/main tool changed or actual Shoot-entry authorization inferred by this QA task.
