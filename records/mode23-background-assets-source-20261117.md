# Mode23 standalone background asset dependency

The source-defined background dependency is now prepared as four standalone native-format binary files. It is not installed in a ROM and does not implement or expose mode23. Original ROMs, current574F, frozen main6479, native RAM/VRAM allocations, menus and running full builds remain unchanged. The first-task contract is in `mode23-initial-task-native-contracts-20261117.md`; the prior44-root graph was not retraversed.

New LF converter `tools/build_mode23_background_assets.py` is frozen at1F4977A4441A20DBC13E8C7AB319DB3B4E1CFAFC88F59FBEC82A5C40FBFBF9AA. It accepts only original WSC1.5 C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7 and a fresh output directory. Original execution exited0. Output `build/mode23-bg-assets-20261117/manifest.json` hashes2FCDB897F0CE4E6A2D1BE57E69EA18359AB7950A50C8A77C0DE2698E8BE67DDC.

| Output | Bytes | SHA-256 |
|---|---:|---|
|tiles.bin|1728|C6E61F2F94EC8B086B94C5FC9A077512C940D7A0F5D47D49AA3838E8E98B68F7|
|map.bin|2048|E8CBC32BE5B5591E753DC4FA79521761B9825FFD6A4EE9654B610DF4010CEE9F|
|palette.bin|30|99C6CE91792D98A9FD150D34182128CD32B95F803E5DECEF4EFD28E9AE0466E5|
|palette-dim.bin|30|FDEDB07EEB218F504A544FF4A6C279B0D3FC6F8308099A0C2FE3E720D90C60D2|

## Exact source ownership

Initial controllerA59F calls859A:034A at74AEA2, passing source screen destination1000. Loader785CEA..785DDC selectsC3 bankC1 andDS3F73. Its tile copy startsSI0100, destination8000 and count0360 halfwords:54 tiles,1728 bytes from physicalROM41F830. Its palette copy deliberately skips color0: sourceSI07C2, destinationFE02 and15 halfwords fromROM41FEF2. The256-byte source pattern begins atROM41F730. The converter resolves these addresses through the known30000..3FFFF C3 window and rejects out-of-window or crossing extents.

The complete loader code hashesA77CD1D5EA3BEB815B6A25689AA684148E4017C1A75B288B96FA0C1CBACC6368. Rectangle copier7530B9..753137 hashes566183C711ABF63C610CBC54E9AE112130EC199C0DDCDA8F2CE9497377EF61D3. Caller74AE9F..74AEC3 hashesC7BCFCE96EEB4FBC7BB1C06586C9E3E9D409671D9934DF8AF6A5DBF1C0559C9B. All complete anchors are pinned in addition to the whole original image.

## Eight rectangles, complete map

The converter decodes and evaluates the bounded straight-line argument producer785D22..785DCD. Every far call must be exactly4FFF:30C9; unsupported instructions or argument shapes fail. The source callee preserves the producer's registers, reads nine stack arguments, copies16 columns by8 rows from the same pattern and uses its nonzero wrap flag to wrap destination X within32 cells. Its AND3F/FFC0 sequence wraps each row; Y advances by40 bytes without wrapping.

The decoded destinations are(0,0),(16,0),(8,8),(24,8),(0,16),(16,16),(8,24),(24,24). Each of the1024 destination cells is written exactly once. The resulting asset is the full32x32 tile map; it is not cropped to28x18 and does not select a future native viewport. The second and fourth8-row bands wrap the rectangle atX24 back toX0, retaining the source alternating offset.

Native entry semantics reuse the already-proved `build_stage_assets.convert_map` primitive only, not that tool's stage addresses or stage metadata. Its fixed504-cell API is applied to temporary chunks; only the final temporary chunk is padded and all actual1024 output cells are retained. Every result is additionally checked against the explicit source tile/bank/flip/palette fields. Source screen-bank bit2000 becomes native tile-index bit0200, source flip bitsC000 become native0C00 and source palette bits1E00 become nativeF000. Every actual pattern cell uses bank1, tile0..53 and palette0, so native entries reference512..565. This defines a relative tile-index requirement, not a reserved native character base or physical VRAM address.

Tile packing reuses `build_poc.convert_planar_tile`; all3456 pixel indices are checked directly against the original four source bitplanes. The manifest records the hashes of these reused primitive files and `convert_wsc_palette_block.py`. No old converter, stage metadata or original resource was modified.

## Palette and dimming boundary

The normal palette file contains precisely source colors1..15 converted by the established RGB444-to-native channel mapping. The dim palette applies the actual source operation first: `(source_color & 0x0EEE) >> 1`, then converts each resulting channel. Caller74AEB7 shiftsAX and74AEB9 masks0777, which is equivalent. The prepared output is not obtained by halving an already rounded native RGB555 color; at least one actual source color distinguishes those operations.

Physical source color0 is not loaded by785CEA. The caller nevertheless loops over all16 colors beginningFE00, so it also dims the inherited source color0. Neither30-byte output invents that color or claims it is black. The manifest explicitly leaves this runtime dependency open. Future scene integration must establish the preceding palette0 owner/value and reproduce that dimming, while loading these15 defined colors beginning at native palette entry1. No arbitrary bank, viewport or color0 assumption is made.

## Reproduction and remaining work

`python tools/build_mode23_background_assets.py --source <exact-WSC1.5> --output-dir <fresh-directory>` creates only tiles.bin, map.bin, palette.bin, palette-dim.bin and manifest.json. Existing directories are rejected. The manifest contains source offsets and code hashes, all eight decoded rectangles, full coverage, tile index requirements, primitive hashes and exact output hashes. It explicitly states actual_runtime_verified:false and mode23_implemented:false.

The independent reviewer owns a separate source decoder and verifier. Native screen/character-base ownership, native private state, palette0 lifetime, the actual controller/participants/input/rules and complete cleanup still need implementation before normal mode23 entry can be exposed. These prepared files are a concrete completed asset dependency, not a substitute scene or a final port-completion claim.


Independent verification completed: `tools/verify_mode23_background_assets.py` SHA-2565CD9B8B560A7380A0558BC9BE7D7871AA534246DCDBF037AD05BCD6837E33542 produced `build/mode23-bg-independent-20261117/report.json` SHA-256F8C50ACBC289402F43A2FC92C92386E651914B7B0690ED8A3EBDD561A3FE4AC1. Its separate source argument decoder and pixel/color conversion import no author conversion functions; all54 tiles,3456 pixels,1024 cells and15 normal/dim colors pass. Its exhaustive16-bit dim-equivalence check also passes. The palette0, allocation and scene-implementation limitations above remain unchanged.
