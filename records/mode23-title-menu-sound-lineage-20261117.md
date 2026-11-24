# Source title cues and their retained native songs

The title adapter can issue ordinary native song requests with the following source-backed aliases. All three retain source request priority 1 and delay 0. The native queue entry is `080D15C0`, with song ID in R8, priority in R9 and delay in R10.

| Action | WSC 1.5 sound request | Paired WSC 1.0 request | Native request |
| --- | --- | --- | --- |
| Move selection | 78 at `7807A7` and `7807E0` | 78 at `3C2E8C` and `3C2EC8` | 1E at `080910E0` and `08091108` |
| Confirm | 79 at `7804E2` and `780D3E` | 79 at `3C2C3E` and `3C2F0D` | 1F at `08090D9C` and `08091128` |
| Reject locked row or go back | 7A at `780D15` and `780D89` | 7A at `3B778D` and `3B9309` | 20 at `08081CAC` and `080C006C` |

The two 7A anchors each carry a distinct matching action signature. WSC `3B7776` and GBA `08081C94` check bit 1, play the sound, set state 2 and clear the neighboring timer. WSC `3B92F4` and GBA `080C0050` check bit `80`, play the sound, clear state bit 4 and decrement the timer with saturation at zero. WSC 1.5's expanded title applies that same sound to event 10 refusal and the B back-action. Those title paths preserve the existing priority and delay.

The WSC banks at `2D0000` and `3F0000` bind each ID using its six-byte typed descriptor. Commands 78, 79 and 7A have identical descriptor prefix words `002A,0002` across the source releases and exact matching command payloads of 14, 28 and 14 bytes. The corresponding SHA-256 values are `E055E928FF3CAD269A5E12BDB58DB93B86FBE3C6801A1C194B201FF3DD8A2069`, `0778F90D9E5545229830648B6BF9585549907FD30465B831581ECBF47F5F7F49`, and `993AAB670B16B739B58B93F580287DAFE2D6038AF584BA1C7B71CDAFC17B840E`.

The source comparison used WSC 1.0 `58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735`, WSC 1.5 `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`, and the commercial GBA `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED`. These are request-to-existing-song mappings through the retail native engine. Playback in the new menu remains a runtime check.
