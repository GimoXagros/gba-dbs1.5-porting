# Failed aim replay: verified timing and bounded geometry

The completed `bizhawk-shoot-checkpoint-aim-v87-20261117-a` capture ends in ordinary defeat at core93897, mode7, stage11, P1HP0/P2HP1. It does not establish a hit or gameplay success. The independent report is `build/shoot-checkpoint-aim-independent-20261117/actual.json`, SHA256 `59CABF71C60718399AA804EBB3548B16ABA311F32442756D5F35A4C5AA4BC2F2`; verifier `tools/verify_shoot_checkpoint_aim_capture.py`, SHA256 `DEDC7AA6E78E42E2B1D986B72D29F3C28A0F07F705A039511EE7FB918DEE3294`.

All49 finalized files, frozen scripts, ROM5284435A, and initial five RAM regions match their declared inputs. The loaded Core differs from the source checkpoint in15 explicitly reported bytes; CPU bank, native extensions and managed suffix match. This is not normalized full-Core identity. The sole authorized HP write occurs at89500, SECOND+64,37 to1. The sole eligible B decision occurs at the same core.

The captured actor at89501 is executing native callback083587F0 and event87, command0, countdown2. Its command durations are3,5,6,3,3,3,6,5; source durations are4,6,8,4,4,4,7,6. Executing actual native animation instructions from this captured state first reaches command3's active rectangle in reconstructed state89515. Thus a15-frame prediction from the B decision matches this captured-state epoch; the precise collision-producer epoch is not retained and is bracketed by adjacent frames.

The source and native command3 rectangle are identical: signed center(-352,-160), half extents136/136. Command4 is(-496,-128),120/104. The recorded victim has half extents112/112. Actual native attack-list instructions preserve the negative x offset when facing left and negate it when facing right; they add signed y unchanged. Actual native overlap instructions return no intersection for all active reconstructed states and each adjacent recorded target epoch. The target crosses from left to right before the attack becomes active and is moving downward. No left-facing implementation fault is established.

These results are a reconstruction using actual native animation, rectangle and overlap instructions, not direct observation of the early collision producer. They assume one unpaused update per frame, consistent with the captured callback and zero freeze values. The rectangle belongs directly to FIRST; this evidence does not describe a spawned projectile. A revised input policy should predict target position at attack activation and use the signed rectangle center, preserving all existing owner, HP-write and outcome guards.

Reproduce with:

```text
python tools/verify_shoot_checkpoint_aim_capture.py --capture build/bizhawk-shoot-checkpoint-aim-v87-20261117-a --source <original-WSC1.5> --report <fresh-report.json>
```
