# Shoot assets selected by the actual source loader

Recorded 2026-10-13. The older stage asset builder remains reproducible, but
its Shoot bank-base assumption and two-by-two resource geometry are incorrect.
This repair is a later guarded layer; it does not rewrite prior artifacts.

Source `7CCF:0FC4` sets bank C3 to `C9` at raw `77DD2C` and DS to `383F`
at `77DD44`. The physical window offset is therefore `83F0`, not zero.
The initializer copies 111 colors beginning at source color 1, then 512
tiles beginning at relative `E0`. Actual source addresses are:

| Payload | WSC1.5 raw range | Native destination |
|---|---|---|
| Palette, including source color zero | `4983F0..4984D0` | 111 converted colors at `085A8000` |
| 512 planar tiles | `4984D0..49C4D0` | packed tiles at `085A8100` |
| Twelve 28-by-18 maps | `49C4D0..49F410` | `085EF000..085F1F40` |
| Twelve native map descriptors | derived from source descriptors | `085F1F40..085F1FA0` |

The seven source transparent slots contain `FFFF`. Only their twelve color
bits reach WSC palette hardware, so these become native `7FFF`. Other source
high bits are rejected. The first source color remains excluded from the
111-color copy; the dedicated initializer explicitly preserves its white
backdrop as recorded in [graphics initialization](shoot-graphics-initializer.md).

Source indices `27` and `28` (hex) select records `3B5178/3B5190` through
table `2497:0460`. Both contain width 2 and height 3. Their descriptor tables
at `3B4C88/3B4CA0` contain six bank/mode/offset entries each. The map reader
at `75301E` combines the selected bank, segment `383F`, and each offset.
The resulting addresses are exactly twelve consecutive `3F0`-byte maps.
The corrected dimensions match the independently established 448-by-432
stage extent, instead of truncating the last two maps of each layer.

Native clone calls at `08582A64/08582AE0` select resources 29 and 30 from
`08580000`. Commercial decoder `08013BF8` reads each record's dimensions
and descriptor pointer into the native background object. Initial map draw
`08013C64` uses the initial zero coordinate; scrolling at `08014850` indexes
eight-byte native descriptors. The repair changes the two resource records
to 2-by-3, keeps all other fields, and selects the relocated tables. The
older eight maps remain untouched and are no longer selected by these records.

The relocation window `5EF000..5F2000` is entirely `FF` in the exact input
and has no aligned ROM-pointer or ARM-branch-like inbound values. The
proposed earlier `5E0000..5E4000` interval was rejected because such values
already named it. No payload was written there.

## Build and independent proof

`tools/build_shoot_stage_assets.py` takes the v52 graphics candidate
`6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29`
and the hash-checked WSC1.5 original. Six Expected Writes change 27,569 bytes.
Output SHA-256:
`00C4A8F4710BC0E2F4A31810CDD6FE2610D9670D9A989273162ADF33167211E7`.

`tools/verify_shoot_stage_assets.py` imports no generator or converter. It
checks source instructions and actual native consumers, reconstructs all
32,768 tile pixels, reverses all 6,048 map entries and 111 palette colors,
and rejects nine semantic mutations. The maps use palette rows 0 through 6.
Their 4,261 common-bank cells reference only tile zero; all other cells
use the corrected stage tile bank. Report SHA-256:
`213203E94233DA124057CC5BE7D9481BBA98F838D475F40C03EEC28EDAEE1E25`.

This is source/consumer and data verification, not rendered gameplay.
The complete scene entry, initial common blank-tile lifetime and final
rendered-scene QA remain separate obligations. No CPU, emulator or save was
used. This record supersedes the old `495000` eight-map palette sample as
evidence for actual Shoot background maps.
