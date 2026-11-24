# Mode 23 F4 music track fragmentation

The allocator needs separate objects for the three F4 tracks that exceed the available contiguous blank areas. The new isolated bundle splits native song 79 tracks 0–2 into three, five and two fragments. The seven inserted forward logical edges use existing MP2K GOTO commands with relative u32 fixups. Each new fragment stays within 12,000 bytes, including its jump. Cuts occur at decoded command starts with no tied note open. The final loop event and its original target inside each first fragment remain intact.

The native command table at 0837DBD4 points to Thumb 0837BA2D for GOTO. The handler reads the four address bytes and stores the resulting command pointer to track +40. The native sequencer at 0837BCAC updates running status at track +7 for opcodes BD and higher. B2 therefore preserves running status and takes the common post-dispatch wait check without changing the track clock. This also matches the published MP2K assembly. [MP2K sequencer and GOTO implementation](https://raw.githubusercontent.com/pret/pokeemerald/master/src/m4a_1.s)

The independent checker inverts the fragmented logical tracks to the original bytes, verifies all 50 prior fixups and seven new targets, and checks all 112 existing song table entries. It decodes the original and two sparse physical layouts, one placing the fragments in reverse address order, to compare the full note, control, wait and running-state traces through the opening and two complete repetitions. The three original tracks enroll 46,057, 76,301 and 32,009 effective commands in this comparison. Loop ends occur at native update counts 28,313, 51,865 and 75,417 in each pass. All seven branch sites execute on each pass.

The original 9EC8B6CD bundle and its source-timing verification are retained. The new bundle is a placement dependency. This check does not establish live mixer parity or the final installed addresses.

- Splitter E5AEC32529DB2820BB9CD04ADDF1C6B4A32A3123B47D45B80AAFB86E0C5CA0FD
- Fragment bundle D8F83AA300234C64A6B3963AF2ED4BA0CE32BB52D88CC2F62EC2AABF53FE6CA7
- Fragment manifest C1F83D6EE13179A856539FEBF2FAB15A9B252EE9FCE106AD8947819FDD32EBD1
- Independent checker 3BE78CA1DAFEFEBCE8C69F23ECC692ADA9B07C1F1F20E1B13B801B01AD084FDB
- Independent report 079F083C02BBA981B5DDA679503C450FD098091DE0EBDD4E2276040EE0687AD2

