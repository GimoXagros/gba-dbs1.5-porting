# Added-character audio score population

The complete P1 event population requires five Ver.1.5-only sounds. Native
IDs 5F..63 now represent source BC/C6/C8/CB/CC respectively. This is a bounded
score conversion, not verified equality of audible hardware synthesis.

`build_character_audio.py` preserves the existing 95 song entries and relocates
the complete 100-entry table to raw 683200. Five native table consumers at
37C2A4/37C2D8/37C324/37C378/37C3AC are updated with exact Expected Writes.
Appending at the old table would overlap the existing CE score at 5BA700.
The allocation 683200..683A00 passes prior-byte and all-offset inbound checks.

Source phrases at 3F872C/3F8816/3F8848/3F88BE/3F88D0 are hash-bound and explicitly
parsed. Native finite scores retain discrete note/rest durations, onset times,
volume steps and right-only pan. A key shift of 12 represents C6's high note
129 without violating the seven-bit note operand. Native KEYSH and signed pitch
consumers were checked; the CGB noise consumer clamps its frequency domain.
Three native voice records provide a bounded waveform approximation.

The conversion does not reproduce source A1 hardware sweeps or establish
WonderSwan timbre/noise-frequency parity. Those remain final audio QA work;
these sounds are not silently replaced with zero or claimed complete.

Independent `verify_character_audio.py` reconstructs all five phrases, checks
all old table entries and the actual native consumers, restores the predecessor
by inverse writes, and rejects 14 deliberately corrupted cases.

- Input: `973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D`
- Output: `10372B5606647673F829EC676853C1987F17E64BA19EA51EB751F92FA22B3354`
- Verification report: `191A6B7E03D8C0A994834CBD84F4A12CB038B41EAFFCD1DA8F1DA92E9E8E1217`
