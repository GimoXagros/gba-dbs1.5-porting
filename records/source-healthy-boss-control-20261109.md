# Minimal healthy stage7 ordinary-input contract

Read-only source/checkpoint finding,2026-11-09. No controller, guest memory,
emulator, save or ROM change by this investigator. SourceWSC1.5 SHA256
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
The separate controller author/root own implementation, QA and runtime.

The actual healthy checkpoint is
`build/bizhawk-wsc-continue-boss-20261109-a/fresh-boss-ram.bin` plus SRAM,
core95931: mode7/stage7,difficulty3,progress0280,timer17999,HP8/44,
FIRST pending damage byte+58=0 and all submitted buttons false.

FIRST1784 is ID0,callback668E:115D,X0DF0/Y1080,+6=9800,+8=0,
presentation+9E=640A (right-facing). SECOND1894 is kind3/index1/IDF,
callback4090:649A,X0C40/Y0B66,sourceP1=0:2F23:BC. Its current event1 body
at3CF3D6 is(type0,x-16,y-96,halfW168,halfH232). The target is432 coordinate
units left and1306 higher. An immediate ground neutral B neither reaches
that height nor uses the desired initial facing.

## Jump availability and attack ordering

Known grounded ID0 idle115D/walk11C9 accept fresh A through668E:01D6 at
766AB6, which tests actor+20 bit0040 and installs16E8. The source requires
a fresh global edge: input poll750759 precedes scheduler75075E even during
intro;751912..920 computes3858=newHeld&(oldHeld XOR newHeld). Active07FA
copies3854/3858 to actor+1E/+20. Cleared intro actor controls do not reset
global previous-held state. Release before the first intended fresh press.

Jump16E8→1721/1743 retains a held-A decision until actual takeoff76804D.
Releasing early sets+8C=1 at76800F and selects the short impulse; holding
until the actual airborne flag is set selects the full impulse. This is an
observed-state rule, not a guessed number of frames. At current stat record
3B847E, full vertical velocity/acceleration are-992/+32; short are-512/+20.
Under the source accelerate-before-SAR4 free-flight update their upward
excursions are930 and403 units. This is conditional free-flight geometry,
not a claim that moving enemies or terrain stay fixed.

Base neutral air B selects P4action4/P1event91, damage1/type8. Its four
rectangles are(x,y,halfW,halfH):(-160,-240,112,168),(-128,-144,88,128),
(-48,-160,88,128),(0,-256,112,168). Against the captured boss event1 body,
their possible vertical root-delta union is-312<dy<560. Thus the full jump
can make the captured1306-unit height gap reachable; the short jump cannot
if the target remains near its captured height. No actual hit is inferred.

Ground idle/walk poll B0224 before movement/facing06A6. Presentation+9E
bit4000 set means right/X2/held2; clear means left/X4/held8. A fresh neutral
ground B should wait until actual facing matches the requested direction.
The ordinary airborne1845 callback instead calls face/movement06E5 before
air B02BA; the ground stale-facing veto must not be applied universally to air.

The bounded proposed controller therefore starts fresh A only in the known
ground-input callbacks when the target is higher, holds it through jump
startup until takeoff, and avoids B during that startup. In actual1845 air
input it may use a fresh neutral B with permissive horizontal distance only
(the earlier abs(dx)<0300 gate); it does not require anchorY to be within0200.
The source collision engine decides the eventual hit. This is a legal-input
candidate, not a win guarantee or an invulnerability/health intervention.

## Positive healthy Shoot entry must be observed

Require FIRSTHP>0 at the actual lethal hit and native root5. That alone is
insufficient if later deferred damage occurs before the scene saves HP.
The exact post-save hook is772E42:772E3F stored real HP to sceneSI+46;
the next772E42 instruction will write temporary FIRSTHP1. SI equals
C00:[8]+10, its active header callback is71F0:0EEA,DI=liveFIRST andAX is
the saved HP. Stage is still7 here. Retain that scene identity and positive
savedHP; after real747A68 initializer execution, an outer-frame stage11,
preactivation/bit4-clear snapshot with the same active71F0 scene and+46>0
is the useful genuine checkpoint. Temporary FIRSTHP1 alone is not evidence.
The earlier savedHP0 checkpoint is explicitly unsuitable for this purpose.
