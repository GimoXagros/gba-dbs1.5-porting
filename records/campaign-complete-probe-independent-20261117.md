# Complete assisted campaign probe: independent composition check

The new campaign probe passes independent Lua preflight. The checked wrapper
`tools/bizhawk_probe_campaign_complete.lua` is
`F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF`.
The checker is `tools/check_campaign_complete_probe.py`, and its final report
`build/campaign-complete-independent-20261117/final.json` is
`AF3F215A2F6F13084BD84F48B443DF9E4A8DAC7C681BA564E934DFE957027ED4`.

This is preflight of the observation program, not evidence that an emulator
has completed the campaign. It preserves the previously authorized assisted
profile: score WORD999 on ordinary stages and one guarded stage7 boss-HP
WORD1 write. The runtime still requires an actual FIRST-player fatal hit,
the existing healthy-health handoff and normal Shoot activation. No stage11
write is enabled.

## Composition and unchanged boundaries

The new checker executes the actual frozen D40 driver and actual adapted
7513 observer under installed Lua54. It does not replace the observer's
pair/live/failure/flush/finish API with success stubs. The collision frame loop
is a scripted boundary, allowing exact hook/outer-frame scenarios without a
game core. Memory, native instruction effects, saves, screenshots and input
delivery are modeled and are explicitly not runtime witnesses.

The effective driver matches
`D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D`
byte-for-byte. The effective observer reverses exactly two adaptations—ROM
host pin933C and readable ROM end09000000—to frozen
`7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59`.
All original write, typed-owner, fatal-hit, source-health, stopped and
checkpoint guards therefore remain present and execute in the composed test.

The effective collision loop reverses exactly two changes to frozen
`7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9`:
the loaded-ROM dump is expanded from8 to16 MiB and its log truthfully identifies
the retained assisted writes. The input profile and bounded frame driver are
not edited. The wrapper itself contains no memory-write, register-write,
save-state or joypad-write calls. The retained observer still owns its
explicit authorized writes and checkpoint saves.

## Fourteen composed cases

The positive fixture supplies ordered producer exits0..10, a stable source RNG
row, the source stage/CPU/form map, actual typed active owners at each entry,
and correct progress9/10 VRAM words. It then supplies the retained native
fatal-hit pre/post, root5, saved-health/restore and activation facts. Only
that complete combination produces the new combined success marker.

The negative cases cover a missing producer, changed RNG row, wrong CPU,
wrong HUD tile, missing HUD, missing active owner, wrong active CPU, early
activation, retained invalid collision type, typed-owner refusal, a bounded
run, missing authorization and a wrong ROM identity. Campaign failures are
checked by their exact expected reason, not merely by accepting any error.
Missing campaign evidence fails before the original observer can accept a
healthy activation. A retained invalid type remains `failure:invalid-overlap-type`.
Typed-owner refusal performs no assisted write and cannot yield success.

In the positive mock, the actual retained observer performs ten score writes
and one boss-HP write. Each address, width, value and stage is checked by the
mock memory boundary; stage11 performs zero writes. This validates wrapper
composition with the guarded write path, while the already completed broad
write/controller suites are not rerun.

Every new CPU hook is scalar/queue-only. Any attempted binary capture or
screenshot inside a hook makes the check fail. The actual observer exports
queued bulk data only after hook return at the outer boundary. Actual driver
cleanup releases every button. The existing observer's completion file and
the new campaign trace must both be closed before the combined completion
marker opens; success, handled failure and bounded outcomes exercise this.

The first drafted checker report `preflight.json` is retained. The final
report adds exact failure-reason and finish-order assertions. The wrapper
was not changed by independent review. Its `active-owner` labels identify
observed active tasks and actor ownership; they do not assert a separately
measured decreasing gameplay clock. Root owns the hidden run and later
artifact/visual verification.
