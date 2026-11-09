# v72: bounded terminal projectile clear integration

The terminal common-tile clear now also reaches the exact93E7 projectile resource at fixed base6D. A76-byte selector and the existing dispatcher pointer are the only changes from v71:80 declared bytes,73 changed. The six prior code/hook spans remain byte-exact. No new RAM or task is allocated. The selector reuses the verified owner and renderer, translating only a nonzero four-tile mask by36 tiles. All other presentations retain the prior path.

The source condition is the retained normal callback graph and exclusive ordinary scene ownership. The independent source composition excludes a later side1 companion reload in that domain; this does not close the unresolved8F24 domain or authorize external Shoot entry. No side1 companion pixel substitution is included. See [implementation](shoot-projectile-clear-20261109.md) and [independent QA](shoot-projectile-clear-qa-20261109.md).

## Frozen implementation and checks

| Artifact | SHA-256 |
|---|---|
| Main builder | `23C6FA4BD215ECDA2A688FE71D8438E1E4669BCA8DE528BDBCE1276C81383480` |
| Development ROM | `025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA` |
| Independent component verifier | `21379A50F4C14C174D13E9DB7FFE02719914C867D39871A6DA43E988E283689D` |
| Independent component report | `95458CCEBEBDBCD5BE5D2CE703D32490F106629BE58DDEAAC280203DA0830C38` |
| Runtime capture verifier | `507D7A372E4519B5D41A460E9F1B800C600771A1C69F4C64B60AF70813F1D738` |
| Complete build audit | `1643B67D7179360B1DAB8E8D34E5CEA8F0556A5276E42D5DF2180A2D6178F6D1` |
| Hidden runtime audit | `62FE91FAE6245EA2F28DBD419D12E0AA70ED62CA65B5EEED37C6E75A0534BDB6` |

Independent QA executes4,585 ARM cases:456 selector/owner boundaries,3,669 complete projectile renders and460 existing fallback cases. All eight projectile layouts,28 clear positions and16 live-bit states are included;512 parts are positively blanked. Nineteen negative controls reject wrong selection, stack/mask/continuation changes, altered source semantics and undeclared writes. The complete inverse restores exact v71; strict placement finds no incoming references to the erased76-byte reservation.

The main build retains v71 as shoot-static-companion-clear.gba/json. It regenerates the lower callback graph and reload proof inside each new build's intermediate directory. An explicit lower-graph parameter removes dependence on the ignored historical build/shoot-rule-graph-v2.json artifact. Regeneration preserves graph37BAFE3E and proof2E96EEEE. The runtime verifier accepts only exact025C through its inverse to v71; eight corrupted images are rejected before capture I/O.

Fresh original-input fullbuilds `build/repro-v72-20261109-a` and `-b` both exited0. All289 relative file paths and hashes match. The independent audit recomputes113 manifest entries per build, the exact new two-write inverse and unchanged prior artifacts; it reuses frozen component/source proofs instead of manually rerunning them again. See [complete build QA](shoot-projectile-v72-build-qa-20261109.md).

The exact new ROM then completed a private-desktop ordinary-input Korean Options save→title→battle→WIN→300-frame observation at `build/bizhawk-result-v72-20261109-a`. The independent runtime audit checks61 files,8 snapshots,1,508 exact WIN pixels and5 negative controls. The entire trace, all observed timing pairs,8 screenshots and complete EWRAM/VRAM/palette/OAM buffers match v71. Raw IWRAM stack differences and the first-label36-byte display difference remain recorded; no complete RAM/performance equivalence is asserted. Actual Shoot/active93E7 blanking is not claimed by this ordinary-battle observation.

## Remaining terminal work

The existing native BG1 refill connection is already source-equivalent; adding another camera path would duplicate it. The proposed uniformly-black transition shortcut is false: actual BG1 assets use palettes0/1/6, outside the relevant fade. See [next actual display gate](shoot-terminal-next-camera-gate-20261109.md) and [independent palette population](shoot-bg1-palette-population-20261109.md).

The actual0400 display/IRQ continuation, interrupted-DI semantics, other tile owners, real Shoot entry/exit and E5 cause remain open. Whole1.5 content, complete localization and final QA remain incomplete. This is a development checkpoint, not a final port or release patch. These GBA component/build checks do not use supplied saves. Separately, the user explicitly authorized a supplied WSC save copy for hidden original-game development observation on2026-11-09; see [the updated permission boundary](final-qa.md).
