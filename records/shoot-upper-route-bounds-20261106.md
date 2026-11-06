# Ordinary upper-object route Y bound — 2026-11-06

The eight source route trajectories stay within Y3451..6276, including endpoint overshoot. This is a bound on the ordinary route's own motion, conditional on its ownership of position, velocity and callback. It is not yet a bound covering external grabs, damage or other callback families, and it makes no native-motion equivalence claim.

The route table at7489CC supplies eight start/target pairs. The hidden-object branch7486D9 resets both velocities and reached bits, selects one row using RNG&7, and derives the two midpoint values. Callback7487BB adjusts each velocity by2 around its midpoint, clipping magnitude to128..768. A reached axis keeps its existing velocity while the other axis continues. Both velocities stop only when the sticky reached word equals3.

The finite check follows this exact two-axis behavior and the actor integrator's asymmetric rounding: X truncates the absolute velocity divided by16 before restoring sign; Y uses arithmetic shift, rounding negative values down. All1503 states across the eight deterministic trajectories terminate. The negative diagonals continue below targetY4544 to4489 while X finishes. The upward vertical route ends at3451, five units beyond target3456. The maximumY is6276. Pure state-preserving pauses add no new coordinate states.

The initializer clears acceleration and terrain-related flags at747B36..54. The checker pins the complete source route selector/update interval and motion integrator, plus constructor, route table and both-axis stop contracts. Five source mutation controls reject route-table, reached-stop, rounding, speed and acceleration defects.

The requested loose ordinary-route lower boundY1476 is therefore satisfied by a margin1975. Combining this with grab/throw and damage ownership remains separate work; this file does not change the frozen v69 OPEN_DOMAIN assessment.

- Checker: `tools/analyze_shoot_upper_route_bounds.py`, SHA-256 `F16426882B0A584EF486FAC84222C6B5E1D8BBDBD608E2AB5BF2D4262368B022`.
- Evidence: `build/shoot-upper-route-bounds-20261106/evidence-a.json`, SHA-256 `9F10EA0A080CB68D8C251297CF97F22B484F1303E4517ECD759A9B5C1BF789E5`.
- CLI: `analyze_shoot_upper_route_bounds.py SOURCE.wsc --output FRESH.json`.

No emulator, save, ROM or guest-memory mutation occurred.
