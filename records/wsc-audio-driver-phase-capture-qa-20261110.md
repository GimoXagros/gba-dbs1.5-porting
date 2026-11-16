# Actual source driver timing

PASS. Report `build/wsc-audio-driver-phase-capture-qa-20261110/report.json` SHA256 `D18EC391802710A563C1031C276102352DB5C688D23BE27B3913C7F0E62BFFCF`; verifier `tools/verify_wsc_audio_driver_phase_capture.py` SHA256 `7EAF50E3F775F6E197B4F3835FE1F78CCD55E30F317EBE753205B384999C772B`.

Actual host is the separately named `build/run_bgm_driver_phase_r1_20261110.py`, B2CC988C. Interim3ABA was not used. The diagnostic preserves the previous source38 WAV, request trace, fixture and SaveRAM byte-for-byte. Complete inventory passes; all4400 consecutive frame samples are present. Thus the added read-only diagnostic has observed audio/request noninterference in this capture.

Phase06EE changes by1 on4386 intervals and0 on13. After initialization521, eleven missed increments occur at751,926,1099,1958,2069,2240,2421,2812,3463,3515,3516. No alternate-driver bit is set. Longest channel3 reaches cursorFFFF at3841:3320 outer frames, exactly3309 driver updates. Other channels end3372/3827/3372 after2843/3295/2843 updates. All12324 active fraction transitions and9989 eligible stable-cursor countdown transitions match source speed arithmetic.

The source score schedule is therefore exact in driver updates in this capture; equating those updates to every outer frame caused the apparent additional drift. Eleven skipped passes account for about0.14575seconds. Remaining PCM output after final cursor termination is about0.06367seconds; its mixer/filter cause is not separately established. No tempo retune is justified by these observations. The byte counter is modulo256; raw state transitions support the bounded0/1 interpretation without providing instruction-level tracing.
