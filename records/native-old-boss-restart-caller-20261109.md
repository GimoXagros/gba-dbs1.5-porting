# v72 old boss restart hook: actual caller classification

Read-only bounded inspection of exact v72
`build/repro-v72-20261109-a/current-candidate.gba`, SHA256
`025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA`.
No ROM/main/runtime modification or E5-cause claim.

The retained words are real:08340344=`EB09CCED` calls085B3700;
0836FDE8=`EB090E04` calls085B3600;0833FD04=`E59F80A8` still loads its
retail callback literal0833FDB4=`0834059C`. A word check alone does not
establish that the old restart executes on the active boss root5 path.

08340344 belongs callback083402C4. This callback waits for its countdown or
both actors to become grounded, writes117, loads FIRST/SECOND, then compares
their HP. Its paired source is71F0:03A7/raw7722A7..231F. The native default
root allocation at0833FD50..64 uses0833FDBC=`083400B4`; its ordinary result
family installs08340254 via literal08340250, then083402C4 via083402C0.
At08340338 FIRST HP0 skips the old hook. Otherwise08340344 obtains SECOND
HP through the hook, and08340348..50 chooses the ordinary result effects.
This is the default/root0 result family, not the active boss-victory detector.

Root5 is selected earlier by0833FCD8's argument5 compare. It takes
0833FCE0..FD20 and selects0834059C at0833FD04, the ordinary source0653
counterpart; it bypasses083402C4/08340344. The future guarded Shoot selector
is deliberately planned at0833FD04. Thus the retained restart word does not
prove that it preempts native root5 or source-equivalent Shoot entry.

The hook also has a narrower actual live-in than its old description implies.
08340328..34 loads r4 from FIRST global0300489C and r5 from SECOND030048A0.
085B370C loads `[r5+18]`, the SECOND opponent link (source+14), then085B3710
reads that linked actor's ID at+11 and requires15. Under this caller the ID
guard checks FIRST's ID, not SECOND's ID. Default playerID0 fails that guard
before the private-phase8000/restart path, even if the default result family
reaches the hook with SECOND HP0. This is a concrete guard classification,
not a claim about arbitrary malformed actor links or every possible caller.

The source active battle branch is separate:7417F3 invokes root5 on signed
SECOND HP<=0, while7417DB invokes root4 for FIRST HP0 with death-event3E.
Source root5 chooses the extra scene for stage7 when eligible and0653→1750
for stage11. A future external-route integration should review old hooks in
their actual lifetimes; removing085B3700 as an assumed root5 fix is not
justified by this inspection. No change is proposed here.
