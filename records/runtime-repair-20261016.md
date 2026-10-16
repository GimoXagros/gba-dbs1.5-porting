# Headless runtime repair evidence — 2026-10-16

Resume baseline: `d6f976c84c150b6a1fc172024b31fa887435c879`.
All emulator runs use a private Windows desktop, verified endpoint process ID,
and read-only loaded-ROM identity samples. The supplied WSC save was not opened,
hashed or used. Input comes through normal keys; no game-memory edits are used.

## Crash attribution

The previous three-pointer reversal experiment did not prove a physics cause:
its saved frames/RAM were identical across purportedly distinct conditions.
Fresh provenance-bound probes instead found the same intro fault before the
native physics constructor in both the far-tile and other-player layers.

The actual failure is an opening presentation table selector of 13 against an
11-row retail view. The wrong P1 yields frame E1D1, and the wrong P0 yields
descriptor count 00F223F3 and pointer 00F2223F. A write watch records the renderer
passing the 128-object boundary at 03001828. It eventually overwrites copied
IWRAM code/stack and stops with S04. See the independent analysis and record
`opening-presentation-routing-repair.md` for instruction-level evidence.

The corrected table literal retains the physics fixes. Candidate E2B700…62AE4D
reaches the title, menu and first battle without the observed S04 in bounded
headless runs. This is a bounded observation, not whole-game completion.

## Resource ABI candidate

Candidate `3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065`
includes complete added-character P0/P1 and canonical resource tables.

- `build/runtime-resource-routing-battle-20261016`: 70-second run, Start at50,
  A at55 and60, first battle timer1:57. Capture manifest SHA
  `1D74ACABB06E2248770C48515A4D1134C35713FACDE0796D4A37594AD65C16A6`.
  Final S02, no recorded asynchronous fault; copied renderer intact.
- **Remaining visible defect:** fighters are absent in that captured battle.
  Hardware OAM has zero enabled objects; native producer count030012CA is zero.
  The shadow buffer has old attributes, which alone does not prove current
  drawing or a failed transfer. Actual producer/visibility/camera investigation
  is required. Do not call this fully playable.
- `build/physics-consumers-added13-20261016`: Start50, A55, eleven Down pulses
  at56..61, A65 naturally select ID13. Native083530CC is reached with r1=13,
  r8=08485000, caller08352C30; second player ID1 uses08352C74. Probe SHA
  `5339B57382619D28989A02C4D32FEA4C384561C4A05F2A43177AE15F322D507F`.
  This proves reachability of the actual physics lookup, not later animation
  or complete gameplay for ID13.

Right changes palette variant in this menu; it does not advance character ID.
Earlier Right-based attempts therefore do not test added-character selection.
The capture/probe tools now also expose Down, based on the actual menu consumer.

## Verification infrastructure

The transport handles pending stop packets before and after acknowledgements.
Two socket tests and six process/ROM-provenance checks pass. Captured region
sizes/hashes, renderer integrity and OAM geometry are independently checked by
`verify_native_capture_invariants.py`. Its PASS explicitly excludes visual and
full-game correctness. Any future fix requires a fresh capture of its exact ROM.

## Retail control for the missing fighters

`build/runtime-retail-control-20261016` runs the unmodified USA ROM with the same
70-second/Start50/A55/A60 input schedule. Its first-battle frame shows both
fighters at timer1:57, and the native OAM producer count is30. The candidate
frame has count0. This controls for emulator rendering support and distinguishes
the candidate defect from a normal blank battle frame. Write-only GBA IO reads
may return open bus; they must not be treated as authoritative scroll-register
values when comparing these captures.

## Fighter-display regression resolved in 1B1AA23C

The relocated spawner retained an old PC-relative stage-state load. It read
FFFFFFFF instead of03002310, selected table offset218 instead of10, and copied
ARM instruction halfwords9003/03A0 as initial coordinates. This is proven by
the first coordinate write before movement, not inferred from the final frame.
The guarded six-byte repair installs the correct stage-state reference.

Candidate `1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995`
shows both fighters at the same bounded first-battle checkpoint with34enabled
objects and an intact renderer. The fixed write probe at
`build/player-world-writes-fixed-20261016/probe.json` has SHA
`56BB8799F65403CEDF0151E863BE35D10F7B11C7BF90807F063CC0A898456F47`; its first
spawn write at08582F4C now usesoffset10 andwritesX1080, matching the source
stage1spawn. The next movement shows1088/0700. See
`player-spawn-literal-repair.md` for the complete source/native consumer proof.
The earlier missing-fighter section is retained as pre-fix evidence.
