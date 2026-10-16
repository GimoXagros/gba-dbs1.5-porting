# GBA development references used on 2026-10-16

The user supplied these five primary projects during active port implementation.
The port retains the native USA engine and its proved resource/ABI consumers.
These references support independent checks and future native components; they
do not establish game-specific source behavior or authorize guessing missing data.

| Reference | Checked evidence and practical use |
| --- | --- |
| [devkitPro](https://devkitpro.org/wiki/Getting_Started) / [official installer](https://github.com/devkitPro/installer) / [GBA examples](https://github.com/devkitPro/gba-examples) | Native compiler/toolchain and examples. Wiki returned HTTP403; official GitHub was accessible. `arm-none-eabi-gcc`, `arm-none-eabi-objdump`, and `make` were not found on PATH; `C:\devkitPro` was absent. No installation or compiler validation is claimed. Existing reproducible assembly pipeline remains usable. |
| [Butano](https://github.com/GValiente/butano) | C++ GBA engine on devkitARM or Wonderful, with asset import, asserts, logging and profiling. Useful reference for resource ownership and import validation. Its renderer/audio/interrupt ownership cannot simply be overlaid onto the current native game. No engine code copied or linked. |
| [Tonc sprites](https://www.coranac.com/tonc/text/regobj.htm) / [DMA](https://www.coranac.com/tonc/text/dma.htm) | Immediately applied: OAM is1024bytes containing128eight-byte object records with affine fields interleaved. `verify_native_capture_invariants.py` checks capture identity, exact OAM extent, and the game's DMA-copied renderer integrity. The actual copy addresses still come from the retail ROM, not the tutorial. |
| [GBA Studio](https://github.com/MachoMan117/-GBA-Studio) | README describes an early work in progress with scene editor/import/build functions. Kept as a tooling reference; its stated feature list is not evidence of compatibility with this game or production completeness. |
| [BPCore](https://github.com/evanbowman/BPCore-Engine) | C++ core plus Lua, manifest-driven resource bundle appended to a prebuilt engine. Author limits intended use to small minigames because Lua is expensive on GBA. Resource packaging is relevant as a reference; replacing the native fighting-game engine with this runtime would require a separate rewrite and does not resolve the observed resource-format defects. |

No third-party runtime is embedded by this review. Reusing a particular library
later requires pinned version/license and concrete ownership/ABI validation.
The practical change made now is the independent native capture invariant
checker; source pointer, event-population, collision-tail, and far-tile repairs
continue from actual game evidence.
