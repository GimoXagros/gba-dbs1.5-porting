# Terminal reciprocal-owner trial: independent wrapper/host QA

PASS for frozen 1F9E wrapper/B159 host/C98E pins and exact 46B3 component
binding. This affected delta audit does not establish actual terminal,
IRQ, cleanup or mode8 completion. No emulator or genuine state was loaded.

Actual Lua54 executes the new wrapper and its entire raw frozen 964B
observer. The generated observer is byte-identical to 964B except the
unique 1477 ROM literal becomes 46B3, and the unique stationary_reason
predicate changes auxiliary +18 to +28 and its refusal name to
native-guard-aux28-not-upper. Effective SHA256 is
`57A52032F2AFB153B41A043188B7CC8226F49A029D1B0043ACBD3A05B9BAB7EF`.
All other bytes, including the typed initial auxiliary +18=FIRST and
+28=SECOND checks, are unchanged. The raw original retains 353 LF/0 CRLF.

The positive synthetic full phase route explicitly retains the real
opponent/owner links: auxiliary +18=FIRST02011710, +28=SECOND02011828,
upper +28=AUX02011940. The old harness's synthetic +18=SECOND rewrite is
removed. These values match actual guard core69932 in the already frozen
91E07 capture audit. The composed observer accepts queue substitution and
the complete synthetic IRQ/next-scroll/cleanup/mode8 route with these
links. Two additional affected routes corrupt auxiliary +28 or upper +28
only at guard time; both log the new owner refusal, skip queue selection
and cannot claim success. The sole observed guest-write API remains the
late first-fresh-B16-bit SECOND HP37→1 attempt, with consumed closed ledger,
neighbor protection, ordinary Right/B inputs and final input release.
Native FIRST HP1 in the synthetic terminal route remains allowed.

Seven wrapper binding failures reject before any generated observer load
or execution: wrong ROM token, missing/duplicate ROM literal,
missing/duplicate owner predicate, missing source file and failed read.
Six semantic mutation controls are rejected: wrong target ROM, accepting
duplicate ROM or owner bindings, dropping either generated suffix and
retaining the wrong owner field. All three affected fixture routes use
the real Lua54 runtime. The prior 43-case suite is not rerun.

The exact whole-file host comparison reconstructs B159 from frozen F6EC
with only description/run/pin/component paths and identity, observer path,
and the reviewed additional four-byte ROM word repair. The read-only
host prefix runs its complete 84D→6D→1477→FF3A→46B3 reconstruction:
after the four palette BLNE repairs it proves FF3A, asserts word
006FFC00=E5960018 and replaces it with E5960028. The resulting whole ROM
must equal 46B3. It also verifies script pins, genuine healthy frame68927,
source whole Core6A81, all five original RAM regions and emulator binary.
The prefix reaches executable validation and stops before directory or
process construction; only this review's new report directory is created.

Beyond those explicit delta groups every host byte equals F6EC. The
approval token, healthy starting checkpoint, input/late one-word policy,
closed ledger verification, private desktop configuration,180-second
bound, outcome gate and strict complete-Core qualification are unchanged.
No audio or serial normalization is introduced. A previously stalled
terminal state is not substituted as the starting checkpoint.

Frozen artifacts:

- Wrapper `tools/bizhawk_probe_gba_shoot_terminal_owner.lua`:
  `1F9E5F52D486A8C9646988B9164CA9D6DD65C4F475D0A944DF540B84E051BECB`.
- Host `build/run_gba_shoot_terminal_owner_20261109.py`:
  `B1595A5B1DF397FF01DF83776904BCE804E74ECBB0F9561473938641B481CC0E`.
- Pins `build/gba-shoot-terminal-owner-pins-20261109.json`:
  `C98E217BC26FACC838B140D43549A034F1F0684A174FCA91082D4AACCE69F54C`.
- NEW independent verifier `tools/verify_gba_shoot_terminal_owner_wrapper.py`:
  `0D39EBF680CABA0D88B73933B64673C8EB07A91DBDF7F0C3C2FE8021CF54AF7F`.
- Report `build/gba-shoot-terminal-owner-wrapper-qa-20261109/report.json`:
  `3AAA9BE2B0E41A7A012E805A0F75185707DD20BD831BDA2DDCD8A4A038BEB3FB`.

```powershell
python -u -X utf8 tools/verify_gba_shoot_terminal_owner_wrapper.py --output <new-report-path>
```

Prior wrapper verifier B6D3, terminal verifier85CE, palette wrapper report
EE0CEB4C and actual capture audit91E07B23 are hash-bound as provenance.
No existing evidence, source observer, ROM, host, main build or Git state
was edited. Synthetic acceptance remains a bounded observer-contract
check; actual native eligibility, visible IRQ effect, cleanup handoff,
mode8, historical E5 and final port completion remain separate gates.
