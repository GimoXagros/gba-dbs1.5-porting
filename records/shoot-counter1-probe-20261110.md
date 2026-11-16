# Natural earliest-counter probe: author scope and frozen contract

The new read-only probe resumes the existing genuine280D checkpoint
`19-irq-final-install.State`, frame69935. It observes at most200 ordinary
neutral advances while waiting for natural counter1. It does not replay
the proved healthy→kill→terminal prefix, force a counter, change HP, write
RAM/MMIO/registers or alter the supplied source State. Root owns the new
private host, independent runtime authorization and emulator execution.

Frozen Lua `tools/bizhawk_probe_gba_shoot_counter1.lua` SHA256:
`C625D710C9B2DE44D128D1846066B4F5C2326E7EC37B6875FFF98805B0A59C6C`.

## Host arguments and source binding

The three required UserData arguments are `output`, `checkpoint_dir` and
`probe_sha256`. Both paths must be distinct W:/build paths; ROM identity is
exactly280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7.
The checkpoint directory contains the original19-irq-final-install.State
and its five corresponding iwram/ewram/vram/palette/oam.bin files. The
original `.txt` may also be staged; the Lua does not interpret it.

The host must bind these copied artifacts to completed source launch
9F943EBE and final independent capture audit9F909134. The source State's
decompressed Core is32A904634D2E9F941853496BE03431EBE276234A1C7E28A9DAD3129387C05583,
frame69935,mode7,stage11,FIRST/SECOND HP1/0. The host retains strict whole
Core/restored-difference/CPU/extensions qualification and uses the existing
genuine State parser. Lua rebinds only its three UserData arguments after
loading, requires frame69935 and exact terminal/actor/display ownership,
and compares all five complete restored RAM regions to copied source dumps.
It exports the complete loaded ROM for independent host identity checking.

No prior boss-approval module executes and no new intervention token is
required. The checkpoint already contains the approved earlier trial's
history; this probe has no guest-memory write API.

## Fresh-cycle and timing contract

The saved69935 State is mid-cycle. Initial IRQ callbacks are therefore
ignored until a fresh actual086FF75C cheap-stub success and its following
native initialization are observed. That success binds R0=086FFE10,
LR086FF6EC, current/last/display task020120D0 and the original active
scene/actor/opponent/owner links.

The additional readonly hook085E74D8 runs after the real initialization:
085E74AC stores the IRQ slot,74B8 clears the match index,74C0 installs the
counter and74D4 stores the decremented base. The probe latches only when
that fresh initialization has counter1,index0,base0,slot086FFE10 and
R5=03004710. It requires the same display core and an actual VCOUNT no
later than8. Ordinary prior/future counters do not become synthetic1.

The target cycle logs its first actual IRQ entry, all compare/match/store
records, final slot installation and actual final callback. Every compare
binds index/offset/counter/registers. The compare operand comes from the
**programmed DISPSTAT compare byte minus8**; actual VCOUNT is separately
logged and must meet the first deadline. These quantities are not silently
identified. Target1 is expected to match programmed line9; an earlier
initial compare can be programmed line8/compared line0. The probe records
the actual first sample and rejects a first compared value above1 or
actual VCOUNT above9. It does not fabricate a line8 match.

All eight offsets0/2/4/7/10/13/17/21 and counter/index stores must execute
in order. The final slot must be086FFEBC with counter9/index8 and an actual
call after its installation. A missing first compare, late initialization/
deadline, wrong owner, bad counter store or incomplete cycle cannot pass.
No-target within200 frames remains an explicit bounded failure.

## Bounded evidence output

Callbacks only perform scalar reads, bounded in-memory logging and local
observer bookkeeping. The maximum is100 scalar records. File I/O, complete
RAM reads and State saving occur only outside callbacks. Every submitted
button is false; final release is also false.

Completion file is `counter1-done.txt`. Success is exactly
`earliest-counter1-irq-complete\n`; failures are `failure:<reason>\n`.
Output files are:

- `loaded-rom.bin`.
- `restored.State`, five `restored-<region>.bin` dumps and `restored.txt`.
- `counter1-first.State`, five matching dumps and `.txt` if target1 is seen.
- `final.State`, five matching dumps and `final.txt`.
- `counter1-trace.txt`, `counter1-captures.txt`, `counter1-summary.txt` and
  the completion marker; `counter1-error.txt` only on a script exception.

No PNG or System Bus display dump is requested. All capture metadata says
outer-frame-boundary and distinguishes event core from export core. If
first compare and completion occur during one advance, first/final States
may be the same outer State; neither is claimed as an instruction-time save.

## Small author gate

`tools/check_gba_shoot_counter1_probe.py` executes the actual Lua with the
installed Lua54 DLL and explicit read-only mock APIs. Six affected cases
cover positive target1, missing first compare, late first deadline,
misleading restored mid-cycle callbacks, wrong display owner and the exact
200-frame no-target bound. Three mutations removing deadline/compare/
owner protection are rejected. Callback bulk reads, callback file I/O,
callback State saving, guest-memory writes and non-neutral input are denied
by the fixture. This is author contract testing, not actual timing evidence.

- Checker SHA256:
  `4A188C9F387FE4CEBA105C3F6248AC9C3EB45AE38A4BF5420AC229C6526EF2A5`.
- `build/shoot-counter1-probe-20261110/author-report.json` SHA256:
  `6186EDA71CEB539B51333E5998D417DF0A9E2CEDFA82927293E7871CB757F70D`.

```powershell
python -u -X utf8 tools/check_gba_shoot_counter1_probe.py --output <new-report-path>
```

No emulator was launched. Existing observer/State/capture/ROM/host/main/Git
files were untouched; only the new Lua, checker, author report and this
scope note were written. Actual earliest-counter timing remains pending
the root-owned independent gate and completed private capture.
