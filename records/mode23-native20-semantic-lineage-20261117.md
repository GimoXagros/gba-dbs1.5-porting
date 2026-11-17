# Mode23 completion and native mode20 semantic lineage

Read-only continuation of `mode23-native-entry-gap-20261117.md`, using original WSC1.0/WSC1.5/USA and the frozen3FE5 candidate. The earlier44-root/4052-instruction mode23 traversal was not repeated. No ROM, main, save, emulator or Git changes were made.

The native mode20 handler is the commercial counterpart of source mode20's return-to-title fade and task handshake. This conclusion follows the registered callbacks, owned flags, two task chains, static title display and final transition request; it does not follow merely from the shared mode number. It supplies an existing completion service for a future mode23 implementation, but does not implement the missing game or establish complete WSC1.5 visual/timing parity.

## Registered callback lineage

WSC1.5 callback table74FACC has12-byte rows; row20 at74FBBC contains init81C8:0860 and constructor81C8:08B5, raw7824E0/782535. The WSC1.0 counterpart table3C57E9 row20 at3C58D9 contains C1A9:0860/08B5, raw3C22F0/3C2345. Both rows then point to their common mode service. Native table015B70 row20 contains08040448/08040470/080159B0. The source initializer's first53 bytes exactly match the old initializer. The remaining difference includes relocated display-control state (source0170 versus old0144).

Both source versions clear flag word0300:0112, prepare palette staging and create two tasks with priorities1000/F100. Native08040448 clears03004738, calls its shared palette initializer033FE1C, and constructor08040470 creates the same two priority tasks. Source task-local state begins at+10; native begins at+18. Native constructor literals404F0/404F4 install0404F8 and04063C.

| Role | WSC1.5 raw | WSC1.0 raw | USA native raw |
|---|---|---|---|
| Mode initialization |7824E0|3C22F0|040448|
| Two-task construction |782535|3C2345|040470|
| First fade then handshake |782592|3C23A2|0404F8|
| Set flag1, wait flag2, sound transition |782628|3C2444|040540|
| Second fade |7826A6|3C24C2|040594|
| Wait flag100, request transition0 and retire |782716|3C2532|0405DC|
| Project palette until flag1 |782780|3C259C|04063C|
| Install title background and set flag2 |7827CA|3C25E6|040668|
| Hold/project then retire phase |7828E0|3C26FE|04074C|
| Set flag100 and retire |782938|3C2756|040778|

The native first-task chain is404F8→40540→40594→405DC; its literals4053C/40590/405D8 directly resolve the successors. The second is4063C→40668→4074C→40778 via40664/40748/40774. Native40548/40554 uses the same flag1/flag2 handshake, and405E8 waits for flag100. Native40784 sets100. The native flag owner is03004738 (literals4046C/40588/40630/40740/407B4); the current-task pointer is0300133C.

Source782759/75E/761 writes config+4=1,+6=0,+8=0 and deletes its task. Old3C2575/57A/57D and native405FC/40600/40604 make the same typed writes; native4061C calls task deletion011BE4. Source mode20 row74FAA8 and native mode20 row015D2C both select title mode3 for transition0. Thus the specific terminal handshake and outgoing transition correspond.

## Presentation and timing are not fully equivalent

Source7827CA installs Screen2, resets scroll, selects bankCA/segment380C and copies the title map at4A80C0, tiles at4A84B0 and primary palette at4AB6B0. These are the same title assets already identified by `title-background.md` and `title-source-review-20261105.md`. Native040668 installs its retained title map8B768, tiles8BB58 and palette8FB58; those addresses are explicitly shared with the ordinary title and another presentation path in the existing title audit. The earlier title repair intentionally redirected only the ordinary title's consumers, leaving these shared originals intact. Consequently mode20 still displays its retained commercial title background during this handoff.

Timing also differs visibly in the code: the source constructor seeds the second task with24h, old WSC1.0 uses25h, and native uses1Dh; their fade helpers perform different platform-specific work. This review establishes corresponding completion control, not equal frame counts or full source presentation. Source audio calls8719:01B8/0148 belong to the typed sound service; native4056C calls known sound-request080D15C0 with command0. They are not save writes. No SRAM access or new save authorization is inferred.

The entire native handler040448..0407BC remains byte-exact retail in3FE5, SHA-25687D92CFE33F9E0D189BA67BCC99735DF4078EA9EB2F848009A981BBC51C781BD. This is useful existing machinery, not a newly added feature.

## Remaining entry boundary

Source mode23 still needs its actual extra-menu flag producer, character-select transition5, six-column transition ownership, a registered mode23 handler and the separate local game's owned callbacks/resources/state. Mode20 can be recognized as the corresponding return-to-title completion handler once the game's cleanup requests transition0, but using its current commercial presentation would be an explicit remaining source-visual difference. This finding removes the numeric-identity uncertainty in the earlier bounded record; it does not justify a menu item that enters an absent scene. No implementation is proposed in this read-only record.
