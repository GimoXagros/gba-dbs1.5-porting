# Missing0D87 scanline step: exact boundary, no new layer approved

**There is no missing0D87 row-clear implementation.** Source0D87 changes vertical scroll, advances two state words, schedules another compare and finally replaces its IRQ callback. The actual map-row clearing belongs to0E0B and is already connected. A standalone0D87 worker cannot yet be connected to the real IRQ path without supplying a proved0DEC continuation. No new worker, ROM or reservation is proposed for emission at this gate.

## Already present in the current candidate

The inspected025C1C5E candidate retains the exact existing update649BFCFB, display019D8C1B, normalIRQD96879AA and router9DE06824 code hashes. Hook08586244 calls085E7000. That update already clears448 halfwords at0600F240 on0200 completion and, with0400 and state2 divisible by8, clears32 halfwords at0600F000 plus `64 * (((state8_low + state2_low) & 255) >> 3)`. Exact periodic clear call is085E710C→08001064. Existing bounds/camera refill remains connected separately; no duplicate clear/refill implementation is justified.

Router085E7A00 sends0400-clear display to085E7400, whose normal IRQ is085E7800. With0400 set it still selects retail080C97B8. This prevents the resident display transition branch from installing its required native0D87 pointer. The existing display transition logic itself already resets state6, copies state2 tostate4, decrements state2's low byte, handles its zero flags and schedules the first compare.

## Exact missing effects

Source0D87 is raw75FC27..75FC8C, SHA256 `5EFB9FC3AF1DC09F382B11137969A9392BCE46D2F6BEB099240C9B97D5CAD0A8`. It establishes its own DI=EA under segment0300, so its state accesses do not have0DEC's interrupted-DI ambiguity. Its eight offsets are0,2,4,7,10,13,17,21.

For existing state owner03004710 and index=state6 in0..7:

1. Read source compare port03; compare it against `(state4_low + offsets[index]) & 255`.
2. On equality, write `(state8_low - offsets[index]) & 255` to source vertical-scroll port11, then increment full16-bit state4 and state6.
3. When the incremented state6 becomes8, source75FC67/6D installs5EEA:0DEC in the IRQ callback slot.
4. On mismatch, write stateA_low to port11 and leave those two counters unchanged.
5. In either path, read port03 again and schedule its low-byte increment, then restore interrupted registers/flags and return.

It performs **no map-memory write**. The native bridges are already concrete:08000C4C reads DISPSTAT, whose high byte maps to source compare by subtracting8 modulo256;08000F44 projects source port11 through logical shadow030012B9 and BG1VOFS;08000C10 schedules the converted next compare. Callback slot030012E0 is established by the existing display/IRQ machinery. These require no new RAM or guessed state owner.

## Why a live hookup is still blocked

Actual IRQ dispatch0801140C..20 loads030012E0 intoR9, setsLR and branches. It does not supply a final-callback argument inR0; that register belongs to interrupted execution. A worker requiring an invented R0 live-in is therefore not an actual IRQ callback. It would move the missing continuation contract into a new caller rather than close it.

A real0D87 callback could use an immutable ROM literal for its final native callback address, requiring no additional RAM. However, that literal must identify a proved implementation of0DEC. No such target currently exists: source0DEC75FC98 reads0300:[interruptedDI+A] and writes horizontal port10. Neither replacing it with state+A, retaining0D87 after index8, disabling the next interrupt, nor using a no-op preserves that contract. A placeholder constant is not an integration-ready implementation.

After0DEC's actual native contract is established, the smallest coherent layer is one actual0D87 callback plus its exact eight-byte table/final-handler literal, and the existing0400 router's binding to085E7400 with that callback. It should preserve the already implemented display/update/refill bodies. Independent actual-ARM QA should cover all eight indices and compare match/mismatch, byte wrapping,16-bit counter carry, second compare read, exact scroll-helper effects, final slot replacement only on the eighth match, register/stack/flag behavior, and a full eight-match chain through the real final callback. Strict erased/no-inbound ownership and full inverse remain required then.

No code, ROM, main/runtime, save, guest memory or Git changes were made for this assessment. The executable boundary remains the actual0DEC continuation, not map clearing. This proposal does not reopen the complete camera or RAM-state proof.
