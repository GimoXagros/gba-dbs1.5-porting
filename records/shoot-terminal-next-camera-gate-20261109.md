# Next terminal camera/IRQ gate: existing refill wiring

Read-only investigation of exact v71 `35D46BB3...`, 2026-11-09.
No camera ROM repair is justified: the source-equivalent native refill path
is already connected. Existing graphics/handshake proofs are reused, rather
than rerun.

The actual source stage11 bounds table word at `77DEAA` selects `15AF`,
raw `77E29F`. That arm passes AX=1, BX=2, BG1 and two E0 limits to
`77E0C5`. Its `77E0E8..EC` copies BG0 vertical velocity to BG1;
`77E196` calls the actual camera/map consumer `4FFF:3367`.

The current native actual-stage hook `085C6C14` selects `085C6B00` for stage11.
Its `085C6B24` calls retained `0807FEB0` with BG0=`03002338`,
BG1=`03002388`, R0=1, R1=2 and E0/E0 stack limits. The actual
`0807FEF0..F4` copies the same vertical velocity and `0808000C` calls
retained `08013DD4`, including its existing map-refill consumers.
Adding another refill implementation would duplicate this live path.

The concrete remaining display difference is the `085E7A00` router:
Shoot0400 selects retail fallback `080C97B8`, bypassing the source-style
`085E7400` transition branch and the still-unimplemented `0D87/0DEC`
continuation. Source `0DEC` reads `0300:[interrupted DI+A]`; it cannot be
replaced by a guessed transition-state pointer. Source refills remain allowed.

The alternative all-black-palette argument is rejected by the independent
[BG1 population check](shoot-bg1-palette-population-20261109.md): actual BG1
maps use palettes0/1/6. For example map8 cell299 is `2000`, stage-bank tile0,
palette0, whose pixel(7,5) is index14 / RGB444 `97D`. Terminal `1A95` fades
only palettes3/4/5 colors2..9, so it does not suppress that positive pixel.
This is an asset counterexample to blackness, not an observed viewport.

The actual stage11 router `772564..56E` calls terminal1750 directly.
The inspected terminal1750/17DF/182F wrappers establish HP/input/scene timing,
but do not establish a restricted P1 callback entry set on the low-Y branch.
At `773776..796`, unsigned Y<=0C00 selects197A without replacing the actor
callback or entering193B's grounded wait. The other branch explicitly installs
`668E:1E51` at `7737C6..CA`. No arbitrary incoming actor-state theorem is used.

There are75,32,75 required scene timer decrements after19F2 accepts its second
100 request, followed by340 source0200 stage decrements from the initialized
0154 scratch count before0400. This is a conditional callback-count budget;
scene and stage work may share a scheduler pass, so522 is not asserted as an
exact elapsed-frame bound. It does not itself prove motion has settled.

The remaining finite gate is either an actual low-Y P1 callback/position
lifetime or a source-equivalent interrupted-DI/visible-refill argument.
No freeze, additional ground wait, callback normalization or IRQ approximation
is proposed. Investigation stops here pending a concrete next implementation;
no new analyzer, ROM/main change, emulator, save/state access or guest write.
