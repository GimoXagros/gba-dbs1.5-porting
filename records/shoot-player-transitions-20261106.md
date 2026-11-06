# Shoot player transition owners — 2026-11-06

This continuation preserves the earlier 607-action/35-landing checker and its
frozen evidence. It adds positive source contracts without modifying a ROM or
opening the external Shoot route. No emulator, supplied save, or guest write
was used.

## Grab belongs to the input callback

Ordinary input `4090:07FA` reaches the pair-grab routine through
`741305..741312`: it loads the actual `1000:065E/065C` actors and calls `743001`.
Its kind-2 dispatch reaches the common tail `74129D`, which can still reach this
call. Thus the omission of hit, pair-command and body-push consumers from battle
`0B8B` does not, by itself, exclude grabbing.

The terminal input callback `4090:07D6`, however, has a complete, checked body
`7410D6..7410F9`. Its sole callee `7424C6` only clears the three collision-list
counters. It neither calls the grab routine nor writes either actor's controls.
That supplies the missing positive input-owner exclusion **during this terminal
callback's lifetime**. It does not apply after pursuit restores `07FA`.

The opponent's grab decision at `74309A..7430AD` requires edge `+20:0080`, no
vertical held bits and at least one horizontal held bit. The corresponding
branch installs P1's `5FFD:2D78` victim callback at `743176`. Generic construction
initializes both input words, but Shoot reuses the existing `065E` actor at
`747AD1`; its scene reset does not itself reset those words. A complete pursuit
exclusion still requires the actual predecessor and callback/effect write
ownership. No whole-ROM opcode-absence argument is substituted for that proof.

## Terminal landing and the branch that skips it

Terminal `182F` zeros P1 held/edge input at `773752/773757` and centers X in the
strict interval `0DC0 < X < 0E40`. Its `773776` comparison is **unsigned**:
`Y <= 0C00` goes directly to `197A`, bypassing the `193B` ground wait. A
post-ground stationarity argument cannot cover that branch automatically.

For the other branch, the actual forced-jump parameters are `FC43/0010/000C`,
with field `+92=1`, byte `+5C=14`, and callback `668E:1E51`. `193B` waits for
actor `+6:0004` before installing `197A`. These exact values should replace any
informal description using another jump's constants.

Ordinary landing clears airborne, zeros all four velocity/acceleration words,
and installs `668E:1D5E`. Its animation-end branch reaches the idle initializer;
idle `113C/115D` zeros motion and has six exact input helpers. With both control
words zero, all six take their inert return branches. This proves those
callbacks' local motion behavior, not the absence of every external owner.

The ground sampler can still align Y on the first grounded update. The checker
uses its actual pixel-radius footprint and every subpixel X in the center
interval. Across **32,512** center landing cases, row 42/type 2 normalizes to
`1500` (336 pixels), and row 50/type 1 to `1900` (400 pixels). Each normalized
coordinate is a fixed point on the next zero-displacement ground sample.
Therefore even this grounded path must not claim current/previous equality
before that first alignment has been accounted for.

## Drop-through is not covered by the ordinary displacement cap

At `741911/741914`, the object loop saves Y and delta-Y before the ordinary
signed `±127` displacement cap. While drop-through flag `+6:0002` remains set,
`741971/741974` restores those pre-cap values after collision processing, then
`7419C9` commits the restored delta. Consequently the cap alone cannot prove
that drop-through samples an intervening empty row.

Using the exact ground footprint, all **25,920** combinations of X in
`03E0..181F` and rows 45..49 read empty ground. Expanding this X interval by
one unit on either side produces a positive wall-overlap counterexample.
The actual drop callback clears its flag when ground low bits are zero at
`768619..768629`. This narrows the remaining proof to sidewall-retained X and
the actual drop velocity/sampling cadence; it does not assert either as an
already closed whole-route invariant.

## Reproduction and frozen outputs

```powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/analyze_shoot_player_transitions.py 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --output build/shoot-player-transitions-20261106/recheck.json
```

- Source WSC SHA-256: `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
- Checker SHA-256: `6CC0996B85E68F5045ACE18EA78E86BCDA3423C92E6B6626DDB172A4A4C25B9A`.
- Frozen `build/shoot-player-transitions-20261106/evidence-final.json` SHA-256:
  `91610A442105A2F8FB103CAA5CCB0D91E37B5D4625B30D4697D59F3F72A531DE`.
- Six direct semantic mutation negatives reject a changed grab caller, terminal
  branch signedness, drop restoration, neutral input gate, ground alignment,
  and empty-gap cell. Mutation checks bypass identity to exercise the predicates.
- Output creation refuses to overwrite existing evidence.

No source-correct native repair follows from these bounded facts alone. The
remaining pursuit lifetime and direct terminal branch must be handled before
removing the lower selector guard. A clamp or idle substitution is not a fix.
