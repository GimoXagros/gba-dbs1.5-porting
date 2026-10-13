# Shoot normal display route

Date: 2026-10-13. This separate layer connects the proved normal display from
the frozen stage-handshake layer. The existing Shoot0400 transition fallback
remains exactly `080C97B8`; this does not close the source0D87/0DEC handshake.

Predecessor is `build/shoot-terminal-20261013/terminal.gba`, SHA256
`39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D`.
Output is `build/shoot-normal-display-route-20261013/display.gba`, SHA256
`455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48`.
Manifest SHA256 is
`01DBDF3CD72253456B4E9CE05C1052E6AD5EC35604A012BEC3314F02411AC699`;
independent verification report SHA256 is
`7BD2283D660C034FFCC5A7C458E22126C06E55C208CFCB45E5A6B7A863A8752F`.

Only two Expected Writes occur: the first four bytes at raw587200 become a
non-link branch, and24 bytes at raw5E7A00 receive the router. The full-ROM diff
contains27 changed bytes. The64-byte reservation `5E7A00..5E7A40` is FF in the
exact predecessor and has no aligned pointer or ARM B/BL-like inbound word.

The router is exactly:

```text
085E7A00  ldr  r8,[pc,#0C]      ; literal0300450A
085E7A04  ldrh r9,[r8]
085E7A08  tst  r9,#0400
085E7A0C  bne  080C97B8
085E7A10  b    085E7400
085E7A14  .word 0300450A
```

The first three effects and the BNE destination reproduce the predecessor's
entry exactly. LR and SP are untouched, and r0-r7/r10-r12 are unchanged.
The0400-clear path reaches the new display without creating an artificial
transition IRQ pointer: its r0 live-in is only consumed by the0400 branch,
which this router excludes. Before the second flag test, the display calls
only FEC, F5C/F74/F2C/F44, CE8 and CFC; these native hardware/shadow helpers do
not set Shoot0400. The source main update that sets0400 is not called there.

The native callback dispatcher `0801140C..08011420` loads030012E0, sets LR and
branches to the callback, then rejoins the IRQ epilogue. The surrounding IRQ
entry `080112C0..08011398` preserves interrupted context and only returns to
the interrupted main program after the callback. The router introduces no
scheduler or task call that could resume the Shoot main update in between.
The extra register preservation of085E7400 is compatible with this callback
contract. The flags800 display suppression still uses the new normal body.

This activates the paired layer-scroll mapping, old-index threshold lookup,
source scanline+8 conversion, normal palette control and complete normal
display effects documented in `shoot-stage-handshake.md`. It leaves the live
transition fallback behavior and all scene/menu/terminal route gates intact.

The verifier imports neither builder nor assembler. It pins the predecessor,
final ROM and retail GBA; checks all five final instructions and the actual
literal; verifies the original branch boundary, IRQ dispatch and unchanged
proved display; scans inbound ownership; and checks the complete diff. All
65536 flag words preserve the transition selection, with32768 values in each
branch. Six semantic mutations to mask, condition, targets, LR behavior,
literal and hook are rejected. A second build is byte-identical.

No emulator, save, frame timing or runtime display test was used. The0DEC
interrupted-DI dependency, terminal camera-Y range and lower coordinate-domain
guards remain separate open contracts.
