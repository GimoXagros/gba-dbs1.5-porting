# Resident 93E7 preselector review

The proposed small selector is sufficient for the bounded resident 93E7-only clear extension, subject to independent execution of the resulting ARM bytes. This review authorizes no external Shoot route and emits no ROM. The existing static-companion component remains byte-exact.

## Source scope

The composed source proof in `shoot-p2-reload-eligibility-20261109.md` establishes no side1 companion reload after197A within the retained43-lower/775-upper/790-borrowed normal callback graph and exclusive ordinary scene/task ownership. The introduction task has retired. Thus the explicit93E7 preload remains the source pixel owner in this subset. New93E7 children and their static event changes do not reload the source tiles. No child-quiescence premise is required.

The existing4090:8F24 nonpattern targets0A80/EB4C/E59A and external entry remain the unchanged global gate. The extension recognizes only exact native P0 `085DB300`, fixed base `006D`, and presentation flag2 clear. It does not recognize side1 companions or888B. Resource93E7 occupies logical109..132; the retained clear captures can affect only109..131 of that interval.

## Actual ABI and mask translation

The exact input reviewed is corrected component SHA256 `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A`.

Native dispatcher08012C28 already pushesR0-R5/LR, obtains the presentation inR5, and loads its branch target intoR9. The existing clone entry086FEA00 pushesR9. Its positively decoded original-body entry is **086FEA50**, and its exit086FEBDC popsR9 before popping the original dispatcher frame and returning. Accordingly:

- An unrecognized selector path pushes nothing and branches to086FEA00.
- A recognized path pushesR9 exactly once, initializesR9 tozero, calls owner086FE800, conditionally reads owner+52, translates a nonzero mask, and branches directly to086FEA50.
- R0/R1 scratch is covered by the dispatcher frame. R5 remains unchanged; the selector must not use unsavedR6/R7. The owner preservesR1-R4/R8-R9/LR. The retained renderer replaces flags before their relevant use, and its epilogue restores the saved dispatcherLR.

The source capture stores eitherzero or `F | (live_bits << 8)`, with evenF74..128 and four live bits. Subsequent expiration only clears live bits. Subtracting36 from a **nonzero** mask transforms its low first-tile value to38..92 without borrowing from its four live bits. The retained test then computes `73 + relative_tile - (F - 36)`, exactly `109 + relative_tile - F`. Zero must remainzero; unconditional subtraction would create an invalid nonzero mask. Nonzero masks whose four live bits have expired remain harmless because their live-bit test still fails.

All28 captured F values,16 live-bit combinations and24 resource tiles were compared against the direct logical109-based predicate: **10,752 arithmetic cases passed**. This is a mask arithmetic check, not execution of a new selector.

R9 is already dispatcher scratch, not a caller-preserved register: changing the table target changes the value saved/restored inR9. Independent QA should compare its documented dispatcher role, not require the old table-address value after return.

## Strict placement

The proposed original gap6FEC88..6FEE00 is erased but fails the unchanged conservative inbound scanner with16 candidates. No exemption for interpreting existing ARM/data as Thumb was applied. Other6FE gaps likewise failed.

A whole-ROM scan of6FF200..6FF800 on the exact input found targets at6FF200,6FF20A,6FF23C,6FF2AA,6FF30C,6FF35A,6FF4B6,6FF57E and6FF582. The region is entirelyFF. An in-memory assembly of the proposed selector is76bytes and fits **6FF240..6FF28C**, with no incoming target. The nearest candidates6FF23C and6FF2AA lie outside. The existing frozen scanner SHA256 is7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D. No bytes were written to a ROM or emitted as a new component.

The isolated implementation can therefore add these76bytes and change only dispatcher pointer12C50 to086FF240, preserving every existing v71 code blob, capture hook and preload hook. Relative to v71, the prior renderer pointer is the one intended replacement; its previous value is086FEA00. A new build must independently pin this input, exact entry/epilogue, recognition contracts, source composition, strict erased/no-inbound span and full-ROM inverse.

Independent actual-ARM QA remains necessary for recognized/unrecognized owners, all8 layouts, all mask states and expiration, OAM saturation/exit paths, untouched BG/indexed dispatch, stack/register behavior and unchanged unrelated presentations. No emulator, save, guest memory, main build or frozen v71 files were changed by this review.
