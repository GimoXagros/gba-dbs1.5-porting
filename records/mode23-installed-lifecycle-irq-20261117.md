# Mode23 installed native lifecycle and VCOUNT ownership review — 2026-11-17

The independent bounded gate passes on the r3 isolated component. This is an actual ARM instruction-interpreter review of the installed bytes with explicit immediate-DMA and MMIO semantics. It is not emulator gameplay, audible playback, or approval of an arbitrary entry into the scene. The title menu producer is still unexposed.

## Frozen artifacts

- Component `build/mode23-scene-v88-r3-20261117/component.gba`: `B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE`.
- Component manifest: `3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B`.
- New verifier `tools/verify_mode23_scene_component.py`: `DDAD7AB354403BE0DA0BAEA9E5F32D1FBCB1D53F83116361B262C584382F3A23`.
- Final report `build/mode23-scene-independent-r3-20261117/final.json`: `30B5BE9E19253E3DFB8B5CF514006A9D1808DA99374AE5D60FBB6CD4210ADC4D`.
- Predecessor `5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC`; source `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.

The 187 disjoint writes contain 264,294 declared bytes and 262,190 changed bytes. Whole-image inversion exactly reconstructs the predecessor. All 163 new asset allocations and the complete code/root reservation are FF in the predecessor and pass the conservative encoded-inbound census without exemptions. All installed linked bytes reconstruct exactly; 512 direct branches and 19 native veneers are checked. Reconstruction establishes composition identity, not independent source semantics of every callback. Separate source/controller/collision/resource gates remain applicable.

## Real predecessor and registration

The fixture executes native allocator `08011AC4`, retains a real shared dispatcher task, and calls charselect constructor `080818C0`. Its six callbacks are `0819E8`, `082C7C`, `082324`, `082714`, `082098`, and `08313C` (all under ROM base `08000000`). The five producer terminal routines set completion mask `0F80` and individually unlink their tasks. Actual controller waiter `08081F70` rejects each missing completion bit; after all five are present it retires the controller, resets the logical camera and requests normal choice 5. The live dispatcher survives. The actual transition consumer selects mode23, and `080159B4` invokes the registered installed constructor.

This proves the normal ownership handoff with a synthetic reachable task fixture, not an arbitrary cold call. Five negative proof fixtures reject a wrong mode, live charselect producer, pending queue, unknown IRQ callback, or unexhausted raster counter. These are verifier preconditions: the production helper has **no runtime guard**.

## Retired raster channel

The real native queue producer `0801F590`, transfer `0801F2F4`, startup-relocated `080C9008..080C9074` helper, and `0801F5EC` callback execute. Their four compare epochs are 16, 21, 136, 144, producing queue counts 2, 1, 0, 0 and counters 1, 2, 3, 4. Final compare remains 144, not 152. Short-term callback returns after the counter check do not establish perpetual retirement: native halfword wrap can resume old cases. The corresponding source word counter also has a wrap hazard, with different signed comparison behavior.

The approved target-specific transfer at `08DB22D8`, sole direct caller `08DB19F4`, runs immediately after display disable in the registered constructor:

1. Clear only IE.VCOUNT (`04000200 & ~4`).
2. Clear only DISPSTAT.VCOUNT-request-enable (`04000004 & ~20`).
3. Acknowledge only IF.VCOUNT (`04000202 = 4`, write-one-to-clear).

It leaves callback storage and compare value intact. The 512 actual-ARM cases preserve every other IE/pending bit, HBlank/VBlank request bits, compare/status fields, CPSR, SP, LR and nonargument registers. Three mutations that affect HBlank IE, request enable, or pending IF are rejected. Finite enumeration of all 228 physical scanlines and 256 compare settings proves a disabled VCOUNT request cannot relatch that IF bit during arbitrarily long idle; this is hardware algebra, not a claim to have run millions of frames. Other pending sources are preserved. No blanket IRQ disable is used.

The hardware model follows pinned mGBA commit `fa977ccbc815efc93aefad9acddc9af0577d7827`: [IF W1C implementation](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/io.c#L518), [VCOUNT request and DISPSTAT writes](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/video.c#L230), and [IF assertion/IE gating](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/gba.c#L581). Local supplemental source hashes are `io.c 1AD8F623A720EBCEE955ADA12685A143F30F2C206B07C593602B91418DFFC46F`, `video.c 77F6BD32B19A5E78F06B0826CF3B5135ABFCC3BE24E08BD278829CDC564EDA4D`, and `gba.c E84EABA17F6C96AC7B78431AFAEE79D7633DD50118F92E31E4432793F80C4C7B`. These downloads are not a verifier input. Native IRQ acknowledgement at `0801133C` uses the same selected-bit halfword store.

Mode20 is **not** claimed to install a fresh raster queue. A subsequent legitimate charselect owner is checked separately: its actual producer/transfer installs callback, queue and compare16 before native `08000D18` re-enables request bit5 and IE bit2. The tested mode23 paths do not reinstall the retired channel.

## Installed shared-resource lifecycle

The actual linked scene constructor allocates three roots; all seven source round populations `3,2,4,4,5,6,4` then use the native allocator, resource/presentation constructors and event consumers. Private context links remain valid. Maximum scene ownership is nine tasks, plus the retained dispatcher.

Actual native drawing and common `08011708` upload produce respectively `16,12,20,25,22,33,24` OAM slots for the bounded initial round poses. Used OAM and OBJ tile staging match the physical uploads; every remaining slot is hidden and the shared cursor resets. This is an initial-pose capacity check, not a claim that every gameplay pose was exhaustively rendered. Cleanup individually retires participants and roots, and the next shared empty flush hides all128 OAM slots.

The linked intro installs BG0/F800 and BG1/F000 with character base0. Actual window projection maps shadows `030012BC/BD` to WIN1H and `BE/BF` to WIN1V, including native +8 margins. The resident palette snapshot executes, then installed fade-in completes at16 calls and alternating fade-out at32; both owned palette halves restore/clear correctly. The mirror is exclusive because all old charselect producers retired and the retained dispatcher performs no palette work during mode23. Inherited palette0 and bank0 tile0 remain the separately established normal-entry contract in `mode23-entry-palette-tile-lifetime-20261117.md`; this fixture does not turn zero seeding into a new proof of their predecessor initialization.

Actual cleanup requests `1,0,0`; common native dispatcher `08015AB4` selects mode20, clears the request and restores its initializer callback. MP2K start/stop are recorded service boundaries; native request/reset/service instructions execute, but audible mixing is outside this gate.

## Reproduction

Run from the repository root, choosing a fresh report path:

```powershell
python tools/verify_mode23_scene_component.py --before build/shoot-child-contact-20261117/component.gba --component build/mode23-scene-v88-r3-20261117/component.gba --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --manifest build/mode23-scene-v88-r3-20261117/manifest.json --source-audio-report build/mode23-sound-dependencies-20261117/report.json --audio-contract build/mode23-audio-assets-20261117/manifest.json --report build/mode23-scene-independent-r3-20261117/final.json
```

The two explicit audio artifacts bind source contract `4FD32310...` and conversion contract `3F59CECB...`; no emulator capture or private checkpoint is required. Earlier r2 and draft reports remain unchanged.
