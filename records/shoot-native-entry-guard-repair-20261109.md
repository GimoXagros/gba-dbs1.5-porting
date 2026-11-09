# Native boss observation guard repair

The first private-desktop native campaign reached stage7 and stopped at
Continue, core70147. Its26 approved score writes succeeded, but no boss HP
write occurred. The capture is an observed failure, not Shoot activation.
Independent capture report91B14B25 preserves the full inventory and outcome.

The positive-health refusal snapshot at core64230 proves FIRST HP8 and SECOND
HP37, with all existing actor/controller/reciprocal-link checks satisfied.
The ordinary boss auxiliary has flags0343, hence kind3. Native construction
36FE84/36FE9C/352444 creates that value. Shoot later changes the auxiliary to
kind6 at5BC274..284. The observer incorrectly required6 for both stages.
This was an observer guard error; it is not evidence of game-memory corruption.

The repaired observer accepts only these complete stage-specific profiles:

| Stage | Auxiliary kind | SECOND P1/P0 | Auxiliary P1/P0 |
| --- | --- | --- | --- |
|7|3|0834DFE0 / 0834E27C|08341C00 / 08341E70|
|11|6|085D0000 / 085D1000|085D029C / 085D1100|

Other stages and crossed resources are refused. Existing live task, actor
identity, health, controller and one-shot ownership checks remain in place.
The approved writes are still ordinary FIRST+66 WORD999 and stage7 SECOND+64
WORD1 once. Stage11 writes and player-health/progression/register writes remain
disabled. The ROM and input driver are unchanged.

After the first stage7 write, a safe outer-frame checkpoint stores genuine
stage7-hp1.State and core/input-relative/consumed metadata. Named failures also
attempt a diagnostic failure-observed.State. These files allow later work to
resume without repeating the campaign. No synthetic state is constructed.

The prior observer assigned a healthy outcome before checking the save API.
Actual Lua fault injection proved that a false return could leave a false
healthy marker. The new helper catches false/nonboolean returns and exceptions;
healthy success is assigned only after the real save and metadata succeed.
The first capture never claimed healthy activation, so its failure audit stands.

Module SHA256:7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59.
Driver remainsD40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D.
Independent verifier:7C3676A5B6CB8AECF83C87EF633734FB514008A13B0E4598B4DB9FB2601D3D35.
Independent delta report:351EB70B82D7C5126EFA1D16E8D2D160406EE505642E3C04018889CA593E724B.

Actual Lua execution used the captured64230 RAM, checked17 crossed ownership
refusals and7 checkpoint guard denials, and rejected10 semantic mutations.
Save failure/exception and diagnostic-failure paths were explicitly exercised.
All bytes outside the changed guard, checkpoint/flush/finish and flag match
frozenE620. Prior general suites were not repeated. This permits the next
bounded hidden observation; it does not establish runtime Shoot arrival.

See [actual failure diagnosis](shoot-native-boss-owner-refusal-20261109.md),
[first capture audit](shoot-native-entry-capture-qa-20261109.md) and
[original observer contract](shoot-native-entry-observer-20261109.md).
