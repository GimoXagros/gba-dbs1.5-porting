# Mode23 entry: inherited blank tile and palette zero

This is a bounded source/native ownership review for the intended character-select→mode23 transition. It does not install that transition, rerun the44-root graph, execute an emulator or establish arbitrary direct-entry state. Original WSC1.5 is C415F227; native input is the reviewed5284435A image, whose character-selection and generic graphics services are unchanged by the child-contact layer.

Source character-selection initializer `77885F..77886A` clears exactly32 bytes at physical4000: XORAX, ES=0, DI=4000, CX=10, REPSTOSW. This is source bank0 tile0. Native counterpart `08081748..08081754` sets R0=0, R5=06000000 and R2=8 before calling native word-fill `0800104C`, also clearing32 bytes. The later source character-select static graphics are in bank1, and native dynamic OBJ uploads use06010000, not this BG tile. The mode23 graphics constructors use bank1 tiles at native06004000 onward; retaining the existing blank tile0 is therefore the source-shaped ownership choice. No additional arbitrary tile0 clear is needed on this normal entry path.

Source `778878` explicitly storesAX=0 toFE00 after loading the first palette. Native `08081768..08081770` likewise stores0 to05000000. Subsequent typed palette loads skip each bank's transparent color: source `7523CA` advances the destination by2 before its15-color copy; native `08013324` does the same. The palette header alone was not used to infer a destination.

Character-select's highlight service also excludes physical color0. Source `785B86..785BED` selects four offsets from the16-byte table at785B76 and adds each toFE00. The complete table is `[2,12,18,24,6,8,18,24,6,12,14,24,6,12,18,20]`; none is zero. Service `785A22..785A81` writesFE02..FE18 and those four generated pointers. Its pointer calculation, not just a scan for the FE00 literal, establishes exclusion ofFE00.

On confirmation, source `778BB5..778BE6` copies the live palette into both gradient buffers and clears the target buffer. Its native counterpart `08081C24..08081C5C` performs the corresponding copies and target clear. Thus the color0 interpolation has zero at both ends and remains zero. The source palette task copies its output buffer0522 toFE00 at `779EDC`; that full-buffer copy preserves this zero. The normal character-selection exit waits for the existing task-completion flags before requesting the transition; the mode23 entry integration must preserve that ordering and retire those tasks. This is an inherited black-color contract, not permission for concurrent character-select and mode23 palette producers.

Mode23 loader785CEA copies only15 colors beginningFE02, and A59F at `74AEAA..74AEC2` halves all16 existing entries using `(word >> 1) & 0777`. On this normal entry, inherited color0 stays black. The new generic per-channel inherited-color dim remains appropriate; hardcoding a nonzero gray or treating a synthetic fixture's7FFF input as the real entry value would be incorrect. The source bank0tile0/palette0 requirements apply to normal character-select entry; a future test-only direct entry must explicitly establish its own valid state.

The context's proposed local fade counter at+D4 is disjoint from the two native presentations34..83 and84..D3 and the FC self-pointer. The shared palette mirror0203E000/E200 can be reused only after scene/task ownership proves there is no concurrent old-scene/pause/fade producer. No new private global address is approved by this review.

Bounded byte pins supporting this review:

| Image/range | SHA256 |
|---|---|
| Source77885F..77887C | C32BF7701B05E7C7EC2700DD9AA11665B5EB48CA22586F04156E0473323614D4 |
| Source778BB5..778BE7 | 19A6A572ED69A8AE11A6E5627C8F745895B1885A25BE6405A9EB304538D6CA12 |
| Source752397..7523D3 | 29A79166B5E4F9D43648361E4B601EB354E663CA244732DC169CED331DA185EB |
| Source785B76..785B86 | E35E277EA15CE185798B5D4BF2537616226D218588EA820B2BC18AB832A3EF8E |
| Source785B86..785BEE | D28E50C36682EBD4CDF2B943C2D77FDC620A5CE7E382257B94F0F61BC5D06BE8 |
| Source785A22..785A82 | BCA1C3E963701663C50B7B29CF0F674229C14F2B333CC9372DFAAFE26924E5A5 |
| Source779EC9..779EDE | AF8CB98EC75920BB78E6C7123E3CFBC124F78D4EED68F93871BC2C2B88B9E943 |
| Native81748..81774 | B868CD18FFD03E50C49C18BCDEDAD18905F043E2D81716D4F6FECDB875A15490 |
| Native81C24..81C60 | 81239FD8333B7D80A9F99506239A473BBA8AA35DAC1BA4867B0376AA93E4DD2B |
| Native132EC..133A8 | 10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B |
