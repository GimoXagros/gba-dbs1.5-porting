# Ordinary-input jump hold v3 independent review

The frozen v3 wrapper is ready for a fresh, bounded original-source observation. This is host-policy QA, not a successful campaign or Shoot-entry claim. No emulator, core, save, guest write, or ROM modification was used in this review.

Wrapper `tools/bizhawk_probe_wsc_shoot_short_hard_v3.lua` SHA-256 is `DA9F8E3F76EEEBF425E577C1FA8D4C5FB8B0FF50C929C67B02FE9EE760405905`. It retains the exact v2/E382/collector/hard dependencies and applies `full_jump(wall_escape(keys))` immediately before the real setter. An upstream A rising edge begins a twelve-sample hold, counting that first sample. Further upstream edges during that hold do not extend it indefinitely. B is suppressed only during those twelve samples; directional keys and other fields are preserved. Target/orb changes cannot cancel the hold because they are not hold-state owners.

Mode changes, Shoot stage11, invalid player handles, stage/player changes, or nonconsecutive frame samples discard the pending hold. In excluded modes the policy passes the caller's keys through. The inherited final release invokes the separately captured original setter, bypassing collector, recovery, and hold layers.

The source checker pins the held-input short-jump latch, full/short velocity selection, the signed animation countdown and event completion. The default evolved character's two duration3 startup rows complete after seven animation updates; the following actor callback is launch frame8, requiring nine uninterrupted held input samples. Twelve is sufficient for that checked startup, without claiming immunity to hit/pause interruption. The checked evolved vectors are full `(-804,16)` and short `(-512,20)`.

Independent execution of the author's actual nested Lua harness passed 22 full routes, 14 hold edges and nine source/policy mutations. Report `build/shoot-jump-hold-qa-20261106/full-independent.json` matches the author's frozen report. It retains UI timer90/hard3, normal collection, stage7 HP combat, bounded capture, positive stage11 row-clear/IRQ completion and final unconditional release.

New independent `tools/verify_wsc_jump_hold_edges.py` runs the actual extracted Lua policy in 487 scenarios: every starting phase0..89 with five pulse lengths, overlapping requests, rearming immediately after expiration, target changes, nil input, the last valid slot, stage/player/mode/frame resets, and steady excluded modes. Six semantic mutations are rejected. Checker SHA-256: `2EDC6F7486A54812FA68CF26E98F5B8C613F9CFA1D12140A60DED29555DBD846`. Report `build/shoot-jump-hold-qa-20261106/edges-a.json` SHA-256: `62CE4CE460FA957A902523193D66B4D6A1719BB7A8EBCC5535D054D601062EC2`.

Read-only launcher review covers `build/run_wsc_short_hard_v3_20261106.py`, SHA-256 `A2BA73539F8C08A11CE91B0578B9542C649B4B52AEC52A6F1A3E4CBC94802045`. It requires the exact reviewed wrapper hash, verifies all frozen dependencies and original/core identities, creates fresh isolated paths, uses a private desktop, disables background input and automatic save loading/writing, and retains the 120000-frame/1500-second bounds. A host stop request exits the process context and reports a truthful incomplete run rather than synthesizing a completion marker.

Reproduce from the repository with the bundled Python runtime:

```text
tools/verify_wsc_shoot_short_hard_v3.py ORIGINAL_WSC15 --output FRESH_FULL_JSON
tools/verify_wsc_jump_hold_edges.py --output FRESH_EDGE_JSON
```

Frozen v2 and all production ROM components remain unchanged. Root owns any subsequent runtime observation.
