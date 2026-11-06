# Stage-seven predecessor shake — 2026-11-06

The actual stage-seven graphics entry is `77D932`. Dispatcher `77CF94` indexes the stage initializer table at CS:003C; stage7's entry at raw77CD3A is0C42. That initializer falls through `77D9C1..77D9DE`, zeroing0300:0112..011B. The previously described generic reset is therefore positively mapped to the actual stage-seven predecessor.

Zero is not the lifetime invariant. Stage update `7693FD` selects stage7's entry1901 at raw7693BA, reaching76A871. Its final call76A8C5 reaches the computed shake writer76A519. That writer takes flags1000:03D6, selects one of three eight-byte tables at76A501/509/511, and writes the first half to0300:0112 using a phase masked to0..3. The signed values it can write are exactly{-2,-1,0,1}; unchanged updates and the known boss zero-resetters preserve that set. The checker tests512 combinations of previous value, low flag bits, counter and phase. Thus this field can retain a small nonzero offset into Shoot; assuming it always zero is unjustified.

The actual stage11 update entry is2067 at raw7693C2, reaching76AFD7. Its complete body calls only5EEA:0E0B and76B1DB. The latter is a palette leaf with no callees. In particular, the generic camera-shake body76B3D2..76B476 is not called by this dispatch arm, and neither is stage7's0300:0112 producer. This closes that specific suggested camera-writer path. Existing stage11E0B has its own later camera shake; this check does not remove or suppress it.

`tools/analyze_shoot_predecessor_shake.py` verifies the actual dispatch tables and instructions, table values, source resetters, complete stage11 call population and six direct semantic mutations. It is a narrow owner/dispatch proof, not an exhaustive scan of all RAM writes or a proof that terminal BX belongs to a safe camera subset. No ROM, emulator, save or guest memory was changed.

Frozen checker SHA-256: `88E7FD59F564701A6FB019DE7575E4A73708D8647150F3D1F5038383BEED52AC`.
Evidence `build/shoot-predecessor-shake-20261106/proof-a.json` SHA-256: `312356DD94FB42315BD7FF400AB414FF9314751CA84D8A2091203F7D7939B605`.
