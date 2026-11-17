# Genuine result modes12 and13

The normal result request selects mode12 and then13 before the already reviewed11→20→3 tail. These two modes have autonomous animation/timer phases. The observer should retain neutral input while they run, recognize their genuine native constructors and exit requests, and continue checking the unmodified result triplet. No name-entry or forced mode11 transition is justified by these bodies.

Mode12's actual row is initializer080BAF94, constructor080BBC24, common080159B0. Its constructor allocates the three tasks080BBD1C,080BCAC8,080BDAD8. Final callback080BD8A4 decrements0201D29C; only the1→0 transition requests config2314/2316/2318=1,0,0 and retires its current task. Incoming0 wrapsFFFF and does not exit. Source76EEC4..76EF1F performs the corresponding0300:0BBC+0C decrement, zero test, request and current-task retirement.

Mode13's row is080C9EB0,080CA24C,080159B0. The constructor allocates080CA2C0 and080CBDB0 and stores the latter handle at03004278. Its final080CBC7C body retires that handle and the current task, writes the same1,0,0 request, and disables line IRQ. Source75B6BC..75B71D contains the corresponding handle0300:0410/current retirement, request, and B2 interrupt-mask update. The source also has an earlier empty-population exit at75AADA; nativeCA338..CA3A0 is its counterpart.

`tools/verify_result_modes12_13_exit.py` executes both native constructors and these terminal bodies across all16 NZCV patterns, including four mode12 timer inputs. All80 cases pass in `build/result-modes12-13-independent-20261117/final.json`. It also binds the source rows and exact source request bytes. This is not an execution of every intermediate animation or a visual audit. Mode12's other-task cleanup occurs before its final body and must remain observable in the real run.

Useful read-only hooks are mode12 BD8A4=`E92D403F`, request BD8C8=`E92D0020`, retirement BD8EC=`EBFD51CF`; mode13 CBC7C=`E92D403D`, request CBCAC=`E1C590B4`. Bind each hook to actual config mode12/13 and the current task at0300133C, recording its callback and active flag. Constructors and callback changes are observations, never permission to write these owners.
