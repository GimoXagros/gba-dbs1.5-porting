# Waterfall entry: source-supported foreground occlusion

Date: 2026-11-17. Read-only analysis of current candidate
`75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F`
and original WSC1.5 `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
No ROM, renderer, main builder, frozen checker, emulator or Git changes.

The hidden P1 in `build/bizhawk-type8-corrected-v81-20261117-a/09-campaign-active-02.png`
is consistent with the original Waterfall foreground policy. This sample does
not justify raising sprite priority, making the waterfall transparent, or
reversing the background owners. The separate later CPU exception is not
explained by this visual overlap.

## Observed frame and exact priority producer

Sol's capture audit decoded twelve P1 parts at X72–103/Y24–55, palette0,
OBJ priority3: 503 opaque sprite pixels, none matching their sprite colors in
the PNG. BG0 has priority2 and is opaque at all503 points. Train gives503/503
matching pixels using the same decoder. P1 presentation is `(80,48)`, camera
and Waterfall scroll are zero; P1 presentation+8 is440A, versus Train640A.
These are observed values, not evidence of a missing sprite submission.

Direct original disassembly at74382E..74384E reads stage byte1000:004E+0E;
unsigned stages below9 or above10 OR2000 into presentation+8. Stages9 and10
skip that OR. Current native08353424 loads presentation+8,08353428 calls
08584940, and0835342C stores it. The helper reads actual03002310+0E and
performs the same two comparisons and conditional OR. It neither clears
other flags nor changes the actor's position. The additional three matching
constructor sites are already documented in `stage-runtime.md` and
`iraira-floor-launch.md`; their historical suites were not repeated.

Source renderer752ABF..752ACD copies presentation+8 and XORs only presentation
status+C000. At752B71..752B7D it masksE000 and XORs those bits into the sprite
attribute. The same operation appears on the nonclipping path752BF3..752C01.
Thus bit2000 is the actual hardware sprite priority bit, not a movement flag.
For this exact captured Guilmon layout0, source record0 P0 is3399D0. All12
source layout attribute words have bit2000 clear; their48 bytes exactly equal
the native layout pointed to by080D7A58. There is no layout-level priority
inversion hidden by the presentation comparison.

Current native renderer08012C94 loads presentation+8. At08012D34 it tests2000;
08012D38 emits OAM attr2 priority3 when clear,08012D3C priority2 when set.
These are the real copied-renderer instructions, and agree with the hardware
OAM observed by Sol. The source priority bit is interpreted as behind
Screen2 when clear; the ares implementation explicitly rejects a low-priority
sprite pixel when Screen2 is opaque ([official ares sprite implementation](https://github.com/ares-emulator/ares/blob/master/ares/ws/ppu/sprite.cpp)).

## Foreground owner and transparent mask

Original initializer77DB44..77DB88 assigns source resource35 to1000:020E,
sets its map base1000, and its scroll ports12/13. The scenery resource36
uses1000:01CE, map base0800, scroll ports10/11 at77DB8B..77DBCF.
This is the Screen2/Screen1 distinction, respectively. The previously proved
native translation maps source display bit2 to BG0 and bit1 to BG1. The
existing repair correctly assigns Waterfall to03002388/BG0 map0600F800 and
scenery to03002338/BG1 map0600F000. Native control word1E031F02 makes BG0
priority2 and scenery priority3. Low-priority OBJ3 is consequently below
Waterfall and remains above the scenery on equal priority.

Re-executed only the read-only `asset_contracts` function from the existing
independent `verify_waterfall_display_repair.py` against current75BD and
original WSC1.5. All3024 cells across six maps inverse-convert exactly,
all32768 retained tile pixels match the original planar source, and111
palette entries match their original conversion. This does not rerun the
old display/palette/runtime suite.

An additional direct read-only calculation checked the actual503 occupied
P1 coordinates from hardware OAM and OBJ VRAM. Source resource35 first map
descriptor is3B4C50, source map4D40E0, native ROM map5A4100. At every sampled
coordinate, current BG0 VRAM map word atF800 inverse-converts to that source
map cell (source row stride28, hardware stride32). Source planar tile pixels
from4D00E0, with the source map flips, equal the captured native BG0 pixels
at every one of those503 coordinates. All503 source pixels are nonzero.
Source map bank1 correctly selects its tile payload; this is not a comparison
against an unrelated tile bank. No whole live-VRAM equality is claimed.
The original 4bpp transparent index is zero; ares' original pixel decoder and
opacity predicate confirm the planar bit order and nonzero opacity
([official ares pixel memory implementation](https://github.com/ares-emulator/ares/blob/master/ares/ws/ppu/memory.cpp)).

This proves the sampled native occluding mask is source data. Combined with
the source constructor and actual source layout flags, it supports foreground
occlusion as intended for this location. It is not a claim that every camera,
window, display-enable, animation or future frame has full hardware parity.

## Capture pins and remaining scope

All following files share stem09-campaign-active-02 in the capture directory:

| Region | SHA-256 |
|---|---|
| ewram | 2FCE7AA754DFF4A80BE353DF7C7D4A5D20FB47803D213C70D97C62A833EDA340 |
| iwram | 50DE9C1D3D82EDDC2CDA5BE858EF0D7AAC5EF89EB55523257DBC83C18D893FD5 |
| vram | 4A130371EF3BCE87A667FA65AE5E0A9AA406973AF058109DF86F61614C2D9E90 |
| oam | DC58878372E84DDEA99253C33851FC40456CF3F300F9D7BA44EA2D424CF748C4 |
| display | CF483D2120A79D209668EBC8C8A7ADC5039548FF99678C38E9CFBBECC365447C |
| palette | DF5E676E4EE424F47F269376E53780495877A873FAADC56C85FDEE6E124235A7 |

No original-game emulator was launched and no full-playthrough visual claim
is made. The later finalized capture has a separate CPU undefined exception;
its native indirect-call cause is owned by the independent reviewer. This
record rules out changing the sampled foreground contract merely to expose
the player sprite. No isolated repair is created for this visual sample.
