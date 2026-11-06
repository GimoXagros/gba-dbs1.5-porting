# Minimum jump hold after the observed stage1 trap

The v2 capture demonstrates two finite back-away movements, not a successful escape. Starts18586 and19185 both begin at X02E0; their ends reach0714/0698 before the ordinary chase returns to the same obstruction. The first PNG shows the player beside the left obstruction below a higher row of blocks. No new campaign success is claimed.

The first immutable escape RAM snapshot has SHA256 `1C77C078F317FFA27FF9C72C7A7E9DEB85FCD7B6036FF1B0D9E8D3A0284CA909`. Actor0C00:1784 is default identity0, evolved flags8=C008, params4E=006E, callback668E:19D0, short-jump latch8C=1, X/Y02E0/0FC8. Its observed short branch is a concrete input-policy discriminator; it does not identify every earlier jump or establish terrain reachability.

Source jump edge40 at766AB6 selects event4 and callback668E:16E8. Initialization767FCC clears8C. During startup768001 checks held40 before observing animation completion: release sets8C=1 unless actor6:80 is set. Launch768068 initially loads short vectors from params+14/+16, and768079 replaces them with full +4/+6 only when8C is not1. Actual evolved params3B84CE contain full VY=-804/AY16 and short VY=-512/AY20. The short branch therefore has substantially less height.

Default base event4 at32E08C has FF01,FF03 durations; evolved event4 at3ACCFC has FF03,FF03. The source animation decrements through zero and sets the completion flag on its following update. With the event selected on input frame0, base completion is observed for launch atframe6 and evolved atframe8. Therefore an uninterrupted evolved startup requires nine held input samples, whereas the old eight-sample pulse releases exactly at that launch boundary. Hit interruption, pause and a later eligibility start can alter timing; widening a modulo window alone would not establish a minimum hold.

The new wrapper applies a final-key hold after both the collector and wall-recovery policies. Every requested A rising edge starts twelve consecutive held samples; B is suppressed during that bounded hold. A target or orb change does not cancel an ongoing hold. Mode, stage, player or frame discontinuity resets it; nonbattle, Shoot stage11 and invalid player handles cannot arm it. The inherited original final-release setter still bypasses both policies. The frozen90/8 chase,45/5 collector and60-frame recovery schedules remain intact underneath this final hold. No terrain planner, character change, guest writes, state loading or emulator launch was added.

Frozen implementation:

- `tools/bizhawk_probe_wsc_shoot_short_hard_v3.lua`: `DA9F8E3F76EEEBF425E577C1FA8D4C5FB8B0FF50C929C67B02FE9EE760405905`.
- `tools/verify_wsc_shoot_short_hard_v3.py`: `4B7FE7CCD8CF734DE40F08F1C4E332D8885937A8C3AD75F1F26198BA2A270284`.
- `build/shoot-short-hard-v3-20261106/mock-a.json`: `1EE175FD19BC665A7E101F2B96E7DF13EAE9020B7870E6CAC8223967E1D03455`.

The verifier executes the actual Lua chain for22 inherited routes and14 hold scenarios, including a late-window one-sample request, changing target, bounded rearm, all reset classes and final release during escape. Nine source/host mutations are rejected, including eight-sample hold, wrong collector/recovery ordering, Shoot leakage and unbounded hold. This is preparation for a root-owned fresh ordinary-input test. It does not prove successful navigation, actual Shoot entry or terminal completion.

Launch uses the unchanged fresh isolated configuration and userdata schema, with only the Lua entry replaced by `W:/tools/bizhawk_probe_wsc_shoot_short_hard_v3.lua`; hash-check v3 plus frozen v2, E382, hard and collector dependencies. Keep the existing120000-frame/1500-second bound, positive Shoot/clear/IRQ completion checks, at-most-three escape PNG/RAM captures and honest partial-stop handling. Root alone owns the launch after independent review.

Independent review passed: terminal reviewer reran the full chain with byte-identical report1EE175FD and separately executed487 actual-policy scenarios with6 negative controls (checker2EDC6F74/report62CE4CE4). It also reviewed launcherA2BA7353. See records/shoot-jump-hold-v3-qa-20261106.md. DA9F is frozen and ready for the root-owned bounded run; runtime success remains unclaimed.
