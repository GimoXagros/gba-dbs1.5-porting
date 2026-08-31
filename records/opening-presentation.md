# Opening/presentation evidence boundary

## Corrected structural result

The commercial GBA ROM has 18 aligned ARM calls to character/match consumer
`0x08088250`. WSC 1.0 bank `0x39` has 18 near calls to its common initializer
at `FCDA`, while WSC 1.5 bank `0x75` has 24 calls to the corresponding routine
at `A62F`. The WSC routines set display state, inspect the match-state structure
at `0C00:390E`, and make eight common object-setup calls. These signatures make
the population relevant to match presentation.

The extra six calls in WSC 1.5 form three candidate pairs arithmetically. That
is not yet proof that the cold-boot opening dispatcher reaches them, nor does it
identify their selection policy, skip behavior, or termination path. The old
phrase "population confirmed" was therefore too broad when read as runtime
opening proof. The corrected claim is: **the expanded initializer population is
confirmed; its cold-boot opening attribution and dispatch are pending**.

An ordered mnemonic-shape comparison also prevents a second unsafe shortcut.
The first six WSC 1.0/1.5 callback blocks correspond strongly (similarity
`0.96..1.00`), but the later ordered scores fall as the 1.5 code is rearranged
and changed. The six extra calls therefore cannot be treated as a simple
append-only three-pair patch. Their actual dispatch table and semantic pairing
must be mapped.

The result is reproduced from the three declared originals with:

```text
python tools/analyze_opening_initializer_population.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-initializer-population.json
```

The generated manifest records the exact source hashes, all call locations,
routine signatures, and the deliberately limited claim scope. The current
manifest SHA-256 is
`B44C4ACE23FB1212439F99CB7A5B28778C50C81459028A555535D36B847FA48E`.

## Non-displaying reference-capture attempt

On 2026-09-01 a WSC 1.0 no-input reference capture was attempted with BizHawk
using a hidden/chromeless process and no monitor-visible window. The process
parsed the command line but did not start the Lua capture; it produced no PNG,
RAM dump, completion log, or runtime evidence. This attempt is **inconclusive**
and must not be cited as validation. Per the minimal-validation gate, no further
emulator attempt was made in this milestone.

`tools/bizhawk_capture_wswan_intro_reference.lua` is retained as the exact
diagnostic script so the failed experiment is reproducible and does not need to
be reconstructed later.

## Remaining proof gates

1. Trace the cold-boot dispatcher to the initializer population in both WSC
   versions and map the extra six WSC 1.5 calls.
2. Translate the confirmed WSC 1.5 selection/dispatch policy into the GBA
   opening route without substituting a forced diagnostic path.
3. After the rest of the port is integrated, run one non-displaying cold-boot
   playback through the complete sequence and verify skip-to-title behavior.
