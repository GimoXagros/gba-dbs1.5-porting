# Shoot spatial domain: bounded independent review

This review accepts the conditional lower-object X calculation and source initialization facts. It does **not** establish the complete reachable domain of source8EF3, and does not authorize external scene entry. No builder, ROM, emulator or save was changed. The source is the already pinned WSC1.5 SHA256 `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.

## Positive initialization and lifetime facts

The existing accepted other-player tail, source4090:73F0..74A2/raw747CF0..747DA2, operates on saved first-player065C. Its unconditional reset at747D74 sets actor+4=E700, +6=0040, +8=0 and+A=0. Thus terrain8000 starts enabled, bypass0800 starts clear, drop-through+6:2 starts clear and parent-transfer+8:0200 starts clear. At747D8E..747D9D both current/previous X become0E00 and both current/previous Y becomeFF80 (-128). Native085C1500 implements the mapped fields, and the140-byte initializer calls it in the accepted tail. The scene does not inherit an arbitrary old player position.

Scene1331 later clears first-player+6:0040;139C waits for+6:0800 before proceeding. Scene1540 restores the ordinary input/battle callbacks. These are useful initial conditions, but waiting for a ground flag is not proof of all subsequent ordinary fighter states.

The lower object copies its initial X from its linked first player at7495F1..7495F7. The225-count phase at749684 performs224 tracking updates; its expiring update retains the previous horizontal velocity. At7496A6..7496AC it copies the linked player's Y into+8C. The following20-count phase has19 direct tracking updates and one stop update; the later call7497A3 invokes8EF3 before the subsequent X reset.

## Independent conditional lower-X calculation

I independently evaluated the unsigned source comparisons and16-bit coordinate wrap using algebraic possible-action predicates, without importing the sibling's target-partition implementation. For arbitrary target X in0..1BFF on every tick, the first tracking phase permits delta−24 iff unsigned currentX>16; delta+24 iff currentX<1BEF; and delta0 iff currentX<=1C0F. The direct-follow phase permits−24 iff currentX>0, +24 iff currentX<1BFF, and0 iff currentX<=1BFF.

Starting at every X in0..1BFF with velocity0, retaining the actual phase timing, the calculation visits5,462,663 abstract states over245 updates. Its signed range is−5839..7198, with maximum1C1E strictly below1E00. At updates223/224/243/244 the state populations are23045/23045/23531/9220 and maxima7174/7198/7190/7190. Negative wrap is preserved; it is not clamped or replaced by idle behavior.

This is a complete finite result **under** the target-X domain, own±0180 velocity→±24 integration, no external coordinate/velocity writer and exact callback timing assumptions. It is not evidence that those assumptions are automatically true for every reachable player state.

## Wall clamp and audit correction

The source wall clamp does set currentX to `width-radius-1` on the beyond-world branch. I initially misread the compact instruction listing and reported that only previousX was decremented. The lifetime owner identified the omitted common one-byte instruction; direct re-decoding of the immutable source confirms `76FEED:E90600` jumps to `76FEF6:4B` (`DEC BX`), followed by `76FEF7:895D26` (`MOV [DI+26],BX`). The within-grid branch also reaches that same decrement. I withdrew the contrary concern and notified the parent immediately.

Thus the already claimed upper bound below width is correct under the stated collision/radius arithmetic domain; no additional positive-radius assumption is needed to repair an off-by-one issue. This local proof still depends on the real terrain path being active and does not establish all player callback lifetimes.

## Why terrain alone is insufficient

The source/native grid and live dimensions are concrete supporting evidence:56×54 cells, width1C00, height1B00, solid bottom rows50..53 and the last drop-through row44. However, ordinary physics7418C7 applies the signed±127 displacement cap only when actor+4:8000 is set and bypass+4:0800 is clear. Drop-through+6:2 saves/restores Y and its displacement around terrain collision. The parent-transfer path+8:0200 is also distinct. Initial reset of those bits does not prove their preservation across every reachable callback and external actor write.

Vertical collision76FD6B writes Y=`oldY+delta` and then zeroes the displacement. It is not a universal positional clamp to the top of the solid row. The ordinary landing routine668E:03C3/raw766CA3 checks collision+48 low bits and clears the airborne bit; the actual active callback and subsequent gravity/update order remain part of the invariant. A complete lower barrier argument must cover every reachable fall/attack/special callback and the timing of the Y capture, not just the existence of solid cells.

The drop-through routine768619 clears+6:2 when ground+4A low bits become0. The empty gap beneath the last one-way platform is promising, but its cell coverage and sampling cadence must be proved for every possible horizontal footprint/trajectory. An interior-only gap assertion does not by itself establish a world-wide invariant.

A direct literal writer scan was used only to identify leads, not to claim full ownership. Apparent flag writes767042/767047 are positively classified as scheduler priority writes:767031/767034 first subtract10 from SI/DI, then mutate task-header links. The generic callback743B5C is preceded by delayed-item callback743B3D and the0670/067E object-list release743ADB; it is not the ordinary player landing routine. Other child/collision owners and indirect or computed flag writes still require their actual object identity and reachability to be checked.

The remaining acceptance contracts are: first-player current-X domain including valid radius arithmetic and all direct coordinate writers; terrain/bypass/parent-transfer flag preservation; drop-through clearing before the solid barrier with actual update ordering; all reachable landing/gravity behavior; and lower-object exclusive movement ownership through8EF3. There is no basis here for removing an unsafe-domain guard, inventing a clamp or accepting an idle fallback. The external route remains gated.
