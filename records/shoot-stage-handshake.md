# Shoot stage-transition effects and display boundary

Date: 2026-10-13. Static ROM-bound implementation, with no emulator, save-file,
or runtime timing access.

The connected stage update now performs source `5EEA:0E0B..0F62` through existing
native camera, map, display-shadow and stage-state owners. A complete bounded
translation of the display decisions and normal threshold IRQ is resident, but
the transition display remains unconnected: source `0DEC` reads interrupted
`DI`, which neither its dispatcher nor its preceding callback establishes.
That dependency is not normalized to a guessed `DI=EA` value.

## Frozen artifact and ownership

- Predecessor: `build/shoot-stage-assets-20261013/assets.gba`, SHA256
  `00C4A8F4710BC0E2F4A31810CDD6FE2610D9670D9A989273162ADF33167211E7`.
- Output: `build/handshake-integrated-v3-20261013/handshake.gba`, SHA256
  `F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF`.
- Manifest SHA256:
  `47E379AFA423C9D85557CF47FA9FAF877A31777758EEB5E9F5769FC122048D2A`.
- Independent verification report SHA256:
  `E9B32C9DBF53FA543D5CC2800C467764D4CE44C6659528EBFB353F8DFC9B5FF5`.
- Six-mutation/reproduction report SHA256:
  `9163B00E1B21C76DB9866D38797D99C76AE039C829C4D8E94F88C8D36017EA1C`.

The entire raw reservation `5E7000..5E9000` was FF before writing. A full-ROM
aligned pointer scan and ARM B/BL-like word scan found no inbound reference to
the reservation. The only modification outside it is raw `586244`, replacing
the exact resident stage-update BL to `080173BC` with BL `085E7000`.
`080173BC` handles generic entity effects associated with common flags4000/2000;
it is not the Shoot source helper's camera/map handshake.

| Entry | Source effect | Bytes / instructions | Connection |
|---|---|---:|---|
| `085E7000` | `0E0B..0F62` main update | 460 / 106 | Connected at `08586244` |
| `085E7400` | `0C3A..0D41` display decisions | 328 / 73 | Resident; no caller installed |
| `085E7800` | `0D42..0D86` normal threshold IRQ | 100 / 23 | Referenced only by the resident display |

All entries preserve r0-r12, LR and SP; CPSR is scratch. The display entry
requires r0 to contain a separately proved native implementation of source
`0D87`. The builder does not fabricate that pointer or a no-op callback.
Existing live entries `08587200/08587400` remain unchanged. The full-ROM diff
is exactly 877 changed bytes within the four Expected Writes.

Historical scratch artifacts are retained; only the `integrated-v3` result
above contains the final paired scroll correction and explicit IRQ enable
masking. No v51/v52 generator or earlier output was overwritten by this layer.

## Existing state owner and native consumers

Source `0300:00EA` maps to native `03004710`, independently proved by two
commercial source/native pairs rather than address adjacency:

1. WSC10 `3B5B21..3B5B79` and native `080893F0..08089450` initialize offsets
   0/2/4, write paired colors at6/C,8/E,A/10, and clear bytes12/13. The native
   owner literal at raw89730 is `03004710`; following converted colors are
   `7FFF,1F3F,023D`, matching source `FFF,FC3,E80`.
2. WSC10 `3B6B34..3B6B5F` and native `0808AD00..0808AD2C` write the same paired
   colors through the same owner; raw8ADAC is again `03004710`.

These establish at least20 bytes of the original owner. This layer uses only
the first14 bytes. The source terminal initializer `71F0:197A` at raw77387A
initializes them as `(0154,008F,008F,0000,IN11,0048,0000)`. The terminal scene
must perform that initialization before enabling flags0200/0400/1000/2000.
No new RAM allocation or memory framework is introduced.

Source `1000:01CE/020E` map to native `03002338/03002388`; their coordinate and
mode consumer is source `4FFF:3367`, native `08013DD4`. The commercial common
camera pair source `7CCF:1240` / native `08080040` supplies independent mode2/4
calls and the matching +1C/+1E fields. Calls retain the existing native stack
ABI `(mode, unused-segment=0, BG-object)`.

## Main update effects

With Shoot flag0200, each call writes BG1+1C=200. Odd remaining counts set
BG1+1E=80 and call camera mode9; even counts set +1E=0 and use mode2. The code
copies BG1+1A/+1B to display shadows `0300456E/F` in byte order, decrements
the 16-bit count, and on zero:

- captures the logical source IN11 byte from `030012B9` into state+8;
- zeros BG1+1C/+1E;
- separately clears Shoot0200 then sets Shoot0400, preserving write order;
- clears448 halfwords at `0600F240..0600F5C0`.

With0400 and `(state2 & 7)==0`, it subtracts8 from the low byte of state+A and
clears one32-halfword map row. Source byte arithmetic reduces exactly to
`row=((state8_low+state2_low)&255)>>3`; state8 was zero-extended by the port
read. All8192 relevant byte combinations preserve the source row calculation.

With1000, a pending2000 request clears both bits when state+C bit3 is zero.
Otherwise the 16-bit counter advances; every fourth call sets BG0+1E=200,
uses mode1 or4 according to bit2, and copies BG0+1A/+1B to `0300456C/D`.

The native map-selector helper `08000FEC` uses raw1030's table
`1E 1E 1F 1F 1C 1D 1B 1B`. Source map0800 therefore maps to screenblock30,
native `0600F000`. Source0A40 is offset240 inside that same map. This is the
existing renderer's screenblock mapping, not a new map buffer.

## Scroll and scanline bridges

The source and native layer numbers must not be equated by hardware name.
The actual commercial display pair proves the four port translations:

| Source producer | Native consumer | Logical shadow |
|---|---|---|
| WSC10 `39076F..39077D`: source0300:3C/D, OUT12/13 | `080C97C4..97E0`: native0300456C/D, F5C/F74 | `030012BA/BB` |
| WSC10 `390796..39079F`: auxiliary+BE, OUT10,AX | `080C97FC..C9810`: auxiliary+E0/E1, F2C/F44 | `030012B8/B9` |

Thus source IN11 is `030012B9`. F44 stores that byte before subtracting8 for
native BG1VOFS. F74 instead writes `030012BB`. The earlier scratch main used
BB and the inherited old display swapped the layer writes; the final new
routines correct both using this paired consumer proof.

Two separate commercial scanline algorithms establish
`native_compare=(source_OUT03+8)&255`:

- WSC10 `3BF8E1..3BF923` reads source port02, bounds90, computes a >>2 table
  index, and schedules source line+4. Native `080C90F0..080C9164` reads
  DISPSTAT through C4C, subtracts8 from its comparison byte, performs the same
  bounds/index algorithm, then passes logical line+0C to C10.
- WSC10 `3BFB6A..3BFB9F` uses >>3 and schedules line+8; native
  `080C92C8..080C9328` subtracts8 on readback and schedules logical line+10.

The new display and normal IRQ explicitly add8 before C10. This is not an
inference from the otherwise unused C2C helper's name or implementation.

## Resident display and normal IRQ

The resident display disables native IE bit4, writes map selector21, writes
all four scroll bytes in source order using F5C/F74/F2C/F44, and preserves the
display high byte while applying source low-bit flags. The source B2bit10 to
native IEbit4 bridge is independently established by commercial WSC10
`3BC801..3BC898` and native `080D0B24..080D0BC0` around identical task replacement,
flag and palette effects.

Normal display saves the current threshold position and index, increments
the saved index in memory only, and schedules using the **old register index**.
The transition branch sets the required external IRQ callback, zeros state6,
copies state2 to state4, decrements AL only while retaining AH, and on AL=0
clears common0400 and sets Shoot0900. It schedules the decremented AL.

The native display queue convention remains the existing common C9000 tail
used by the commercial display family. IRQ bit4 is enabled after that tail.
Source itself pops an available queued callback near entry; the native
commercial display family consumes its native queue at the tail. This layer
reuses that native queue contract and does not replace its representation.

The resident normal IRQ similarly increments only the saved memory index,
uses the old index for both the triangular palette-high-byte calculation and
threshold lookup, preserves display low bits, and schedules source threshold
minus position plus8. It applies the regular CF8 backdrop projection even
when the high byte is zero. These correct the old resident code's next-index
lookup and exceptional hardcoded zero-color behavior.

## Exact remaining interrupted-DI dependency

Source segment5EEA has physical base75EEA0. Its normal callback0C3A begins at
75FADA; transition IRQ0D87 is75FC27; final IRQ0DEC is75FC8C. The complete
observed installation chain is:

`stage11 update76AFD7 -> display0C3A -> (Shoot0400) install0D87 -> after eight
matched scanline steps install0DEC -> IRQ dispatcher750F25 lcall[0C00:375E]`.

The sole exact store of callback offset0DEC is at75FC67. A full8MiB source
search finds no packed far pointer `EC0DEA5E`, direct far call
`9AEC0DEA5E`, or direct far jump `EAEC0DEA5E`. The sole exact0D87 callback
offset store is75FB96. The separate wordEC0D at746A51 belongs to a relative
CALL displacement, not a far pointer.

The transition callback's complete listing is:

```text
75FC27 50             push ax
75FC28 53             push bx
75FC29 57             push di
75FC2A 06             push es
75FC2B 1E             push ds
75FC2C 9C             pushf
75FC2D BF0003         mov di,0300
75FC30 8EC7           mov es,di
75FC32 BFEA00         mov di,00EA
75FC35 268B5D06       mov bx,es:[di+6]
75FC39 E403           in al,03
75FC3B 268A6504       mov ah,es:[di+4]
75FC3F 2E02A7030E     add ah,cs:[bx+0E03]
75FC44 3AC4           cmp al,ah
75FC46 7531           jne 75FC79
75FC48 268B4508       mov ax,es:[di+8]
75FC4C 2E2A87030E     sub al,cs:[bx+0E03]
75FC51 E611           out 11,al
75FC53 26FF4504       inc word es:[di+4]
75FC57 26FF4506       inc word es:[di+6]
75FC5B 26837D0608     cmp word es:[di+6],8
75FC60 751D           jne 75FC7F
75FC62 B8000C         mov ax,0C00
75FC65 8ED8           mov ds,ax
75FC67 C7065E37EC0D   mov word [375E],0DEC
75FC6D C7066037EA5E   mov word [3760],5EEA
75FC73 E90900         jmp 75FC7F
75FC76 E90C00         jmp 75FC85
75FC79 268B450A       mov ax,es:[di+A]
75FC7D E611           out 11,al
75FC7F E403           in al,03
75FC81 FEC0           inc al
75FC83 E603           out 03,al
75FC85 9D             popf
75FC86 1F             pop ds
75FC87 07             pop es
75FC88 5F             pop di
75FC89 5B             pop bx
75FC8A 58             pop ax
75FC8B CB             retf
```

The eight immutable offsets at75FCA3 are `00 02 04 07 0A 0D 11 15`. Crucially,
75FC88 restores interrupted DI before the next interrupt. The final callback
initializes BX, but the actual ModR/M byte45 below addresses DI:

```text
75FC8C 50             push ax
75FC8D 53             push bx
75FC8E 06             push es
75FC8F 9C             pushf
75FC90 BB0003         mov bx,0300
75FC93 8EC3           mov es,bx
75FC95 BBEA00         mov bx,00EA
75FC98 268B450A       mov ax,es:[di+A]
75FC9C E610           out 10,al
75FC9E 9D             popf
75FC9F 07             pop es
75FCA0 5B             pop bx
75FCA1 58             pop ax
75FCA2 CB             retf
```

Dispatcher750F25 is exactly
`push ax; push ds; pushf; mov ax,0C00; mov ds,ax; lcall[375E]; in al,B6;
or al,10; out B6,al; popf; pop ds; pop ax; sti; iret`.
It neither saves nor assigns DI. This proves a dependency on interrupted
main-program DI, not that every execution is a source bug. A complete port
requires proving that register's possible values and timing, or an explicitly
approved behavioral repair. No such repair is silently performed here.

## Verification and explicit gates

`verify_shoot_stage_handshake.py` imports no generator or assembler. It checks
the three original ROM hashes, fixed predecessor/output hashes, independent
source/native guard ranges and decoded literals, all202 instruction boundaries
and reviewed ARMv4T shapes, allowed call targets, final literal tables, complete
register-save shape, unused reservation and full-ROM diff. It also proves no
inbound pointer or branch to resident display085E7400 has been installed.

Finite integer checks cover65536 AL decrements,8192 map rows,131072 shake
counter/stop combinations,340 alternating camera updates,256 affine scanline
values and32 palette indices. A second build is byte-identical. Six deliberately
mutated inputs/outputs are rejected. These are static effect models, not CPU,
frame, IRQ, gameplay or hardware execution.

The remaining gates are explicit: initialize the shared state through the
terminal owner before setting its flags; resolve0DEC's interrupted-DI read
before connecting transition display; separately establish the terminal row
clear's camera-Y input and the lower rules' coordinate domain. This layer does
not open menu/controller/scene-end routes or remove those other guards.
