# 93E7 child as an aerial hit-cycle target — 2026-11-06

A fighter hitting a 93E7 child cannot obtain actor `+A` hit bit4 or block bit10 from that collision. This excludes that particular source of the base14 action cycle `22 → 18 → 20 → 19 → 22`. It does not exclude outgoing child attacks, other targets, existing flags or later unrelated collisions.

The child constructor at749C52 passes flags4104 to the ordinary allocator, which writes actor+4 at7420BC. Its kind is4 and side is1. The constructor captures upper+94 as childY, zeros all four motion fields, and installs4090:9798. That callback only advances the animation or releases the child.

The common collision prefix760033 sets attacker+A bit1 and victim+A bit2. Kind4 victim dispatch760055[4]=02DD selects7602AD. That handler can destroy the child, create a visual effect and freeze the attacker, but has no write to attacker+A. It then uses the attacker dispatch at76006F. Fighter kinds0..2 select760CFD; victim kind4 skips the fighter-victim call668E:074F. The only possible actor+A write in that continuation adds1000, which supplies neither hit4 nor block10. The freeze constructor and restoration have no direct actor+A writes. Visual and orb ownership checks reuse the frozen opponent-controls checker; its full callback campaign is not repeated.

The child resource's victim descriptor at3D2470 is `(type0, x4048, y4128, halfwidth0, halfheight0)`. It is not assumed unhittable: source overlap21B9 tests a positive sum of extents minus distance, so a point can overlap a nonzero attack rectangle. The flag-production exclusion is independent of this geometry.

The source checker rejects six direct mutations covering child kind, victim dispatch, common hit bit, attacker continuation bit, dummy descriptor and fresh-hit clearing. It does not change any frozen v69 dependency or certificate.

- Checker: `tools/analyze_shoot_child_hit_flags.py`, SHA-256 `A7BC8B8B335FF82C9DD201D191402C929C38A087DEE1078E0D5D7FD4A054293B`.
- Evidence: `build/shoot-child-hit-flags-20261106/evidence-final.json`, SHA-256 `38CF903EDED7FD56931FE08EADDA566F887461DE7FE0A35D7E6F6C6C5227118D`.
- CLI: `analyze_shoot_child_hit_flags.py SOURCE.wsc --output FRESH.json`.

No ROM, save, emulator or guest-memory mutation occurred.
