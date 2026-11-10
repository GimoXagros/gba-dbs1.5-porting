# Actual two-frame background telemetry: independent capture audit

PASS for the completed scalar telemetry trial's integrity, exact prior
emulation comparison and recorded chronology. The actual outcome remains
**failure:bounded-no-completion** at71927 after3000 advances. The new20
scalar records expose shake→guard→clear→fallback ordering; they do not
establish IRQ, cleanup, mode8 or final port completion.

All187 immutable files match finalized launchED01EC46. Frozen8BC6 wrapper,
CD9E host,3DFC pins,E52F independent wrapper gate, unchanged964B base,
same46B3 copied/loaded ROM, healthy checkpoint copies and authorized
one-word ledger pass. Private launch arguments and configuration match
the previous owner trial after the explicit new run/script paths and
the emulator's later update-check timestamp. That configuration timestamp
difference is retained in the report. No Core byte is normalized.

All20 whole Core buffers—restored plus all19 snapshots, including final
71927—are **byte-for-byte identical** to the prior46B3 owner trial. Every
snapshot's five complete RAM dumps, PNG and96-byte display dump are also
byte-identical. All19 current states independently pass genuine ZIP/state
parsing and exact complete RAM-dump equality. Their UserData differs only
as expected for the new run paths and retains the same four approved
arguments. The original strict source-Core qualification is unchanged;
the prior nine non-CRC source differences remain honestly reported.

Removing only the20 new bg-epoch lines leaves the **entire331-line prior
trace exactly**, including all88 inputs, both actual refusal records and
the final bounded state. The sole16-bit SECOND HP37→1 ledger is identical.
The new logging therefore preserves the observed emulation and original
observer outcomes in this completed trial. The failure ring contains
exactly the current trace's last256 records before the final capture.

There are11 scalar records at69932 and9 at69933, within the reviewed
two-core/22-record maximum. Every site/core pair is unique and every
logged PC equals its reviewed hook address+4. The exact native sequence
at69932 is:

1. Shake-before085E716C has all four velocities zero and selector21.
2. Shake-after085E7170 has2356=0200, with2354/23A4/23A6 still zero.
3. Guard086FF9C0 sees that same2356=0200 and BG1CNT1E03; the unchanged
   observer then records BG-velocity refusal. Guard-return086FF698
   **directly records R0=0** in the new scalar telemetry.
4. Clear-before080D0C18 and clear-between080D0C1C still have2356=0200;
   clear-after080D0C20 has all four velocities zero.
5. Fallback080C97B8 follows. Map-call08000FEC has actual R0=12 while the
   stored selector is still21. Map-before08001010 has selector12,
   BG1CNT1E03 and planned1F03. Map-after08001014 records actual BG1CNT1F03.

At69933 there are no shake records. Guard sees all four velocities zero
and BG1CNT1F03, followed by the unchanged hardware-BG-mapping refusal
and a second **directly observed R0=0** return. Clear/fallback/map follow;
all logged velocities remain zero and actual map R0 remains12. No actual
R0=21 map call is observed in this two-core window. Selector21 existed
as the pre-call stored value; the source/ROM-table counterfactual21→1E
remains distinct from an actually executed21 call.

Guard-entry prepared/copied counts are1/1. Shake-before has copied0,
and clear/fallback also have copied0. These are explicitly different
native epochs. No final outer dump, raw I/O sample or synthetic mixed
epoch is substituted for these actual callback observations. The report
retains all20 scalar records with PC/R0, velocities, selector, BG0/BG1,
planned value and copied queue state.

There is no accepted queue, custom IRQ family, cleanup or mode8 event.
All previous native phase/camera results and final scene085CD510/timer0/
FIRST1/SECOND0 remain exact. Causal source interpretation and any proposed
repair remain separate work; this audit adds no guest mutation or retry.

Frozen independent files:

- `tools/verify_gba_shoot_terminal_bg_epoch_capture.py` SHA256
  `BAD70E7C5D0C2BBF2F7355FB390AF866EAC940D4BDB117DD40F15A5DFE3657EF`.
- `build/gba-shoot-terminal-bg-epoch-capture-qa-20261110/report.json` SHA256
  `F25BB7845FCB4196A3E555D1F8807057D1173588C811F939C0CFCE3735E99796`.

```powershell
python -u -X utf8 tools/verify_gba_shoot_terminal_bg_epoch_capture.py --root-completed --output <new-report-path>
```

No emulator or State was loaded by this reviewer. Existing evidence,
runtime files, ROM, main build and Git were untouched; no old full suite
was rerun. Source-DI identity, historical E5 and terminal completion remain
open.
