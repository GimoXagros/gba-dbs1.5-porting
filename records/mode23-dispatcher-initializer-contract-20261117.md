# Mode23 initializer and native scheduler contract

The source mode23 row at74FACC+23*12 selects4090:A040 (raw74A940),
a RETF initializer, constructor4090:A041 and common4FA3:0287
(raw74FCB7), also RETF. Mode23 does not manufacture a zero return flag.

Source dispatcher4FA3:028B (raw74FCBB) calls initializer at02AD and
uses JCXZ at02B2 to choose deferred construction when incoming CX is zero.
The nonzero path calls the constructor immediately; the zero path stores it
for the shared readiness callback. The initializer's absence of instructions
means the scheduler-provided CX must survive.

Native dispatcher080159B4 calls the initializer via table15B70 and tests R2
at159F4. Scheduler11D94 loads R2 from active count03001338, saves it with
R5/LR at11DC8 and restores it at11DD8. When traversing the active tasks it
clears R2 only after finishing the priority segment at11DFC. Thus R2 is
live scheduler context, not an undefined initializer result. Native mode7
initializer080B81FC is BX LR and preserves the same register contract.

The source no-op mode23 initializer and common callback can reuse native
080159B0 (BX LR). Adding MOV R2,0 would change constructor timing and is
not a faithful port. New scene callbacks still require independent ownership,
resource/service checks and real execution before the menu is exposed.

This record does not claim that the native callback/transition tables already
contain mode23. The new route must cover all readers listed in the existing
mode23-native-entry-gap record together with the real constructor and exit.
