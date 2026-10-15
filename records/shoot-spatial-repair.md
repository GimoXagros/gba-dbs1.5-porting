# Shoot collision and same-call terminal repair — v54

2026-10-15. Implemented over exact v53; no external scene hooks opened.

Source resources 39/40 at 3B5178/3B5190 select collision bank B3,
segment 2CA2, offset zero: raw 33CA20..33F960, 56x54 four-byte cells.
The prior native resources 29/30 had null collision pointers. Native loader
08013BF8 copies record+0C to BG+28; the existing movement pass reaches
080C86B4 and reads that pointer. Seven commercial grids match source bytes.
The complete Shoot grid now resides at raw 607000..609F40 and both native
resource pointers select it. Row 50 has solid floor across all 56 columns.
This does not itself prove every actor-position bound.

Source 193B has no RETF after its successful callback assignment and falls
directly into 197A. The former translation delayed that work until the next
invocation. A 12-byte adapter at raw 60A000 assigns the callback, calls 197A,
then uses the original stack-restoring epilogue. The unsuccessful bit-4 path
is unchanged. The old camera-domain guard is deliberately retained.

Expected Writes cover only the grid, two pointer fields, success branch,
and adapter. The entire allocation was FF with no pointer/ARM-branch encoding
into it. The initially considered 600000 allocation failed this guard and
was not used. Independent verification reverses all 3,024 cells, checks
actual native consumers, and rejects ten semantic mutations.

Candidate SHA-256:
`CAB43EA68A6620D150CA853FC51D4690AAF0889A6D7351D90F99128FE5DD2C69`.
Verifier report SHA-256:
`3BB0886B55FB760CD423BBFF58582049FDCD5F8CA52CE90D90A2F307D22548E4`.
Two full original-input builds have identical 158-file path/hash sets.

Remaining: full initializer and external route, source SRAM observers,
terminal interrupted-DI/row-refill behavior, actor/camera bounds and full
product runtime QA. A complete playable Ver.1.5 port is not claimed.
