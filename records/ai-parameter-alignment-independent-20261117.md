# AI parameter alignment independent verification — 2026-11-17

The source-aligned component passes the new ARM7-aware verifier. `tools/verify_character_ai_parameter_alignment.py` SHA-256 is `526263526AFDDFEFA6A386B930149FF22A3035F0F3D8172089533D5B9AAC3EEC`. Report `build/ai-parameter-alignment-independent-20261117/report.json` is `34CB670213FC84344BB76C6052E812DEAB079DC78F85AC46211D8DC389677664`.

The prior real DEEE capture established a discrepancy missed by the earlier bounded interpreter: row 9 begins at odd address 08D88899. Its source bytes E4 02 mean 02E4, but native LDRH reads aligned halfword E40F and rotates it by eight bits, producing R0=0F0000E4 and storing 00E4. The new verifier reproduces exactly that captured value and store before checking the repair. It has its own narrow ARM7 handler; no shared interpreter or frozen B1B21 checker was modified.

The repaired image is `E6B2C30E3E7D880BFFEE82A3201D0F69AE3DE0EBBEE5B523D24DD6D03FA08CF4`. Ten source rows are represented at D8AB00 with an 18-byte native stride and one zero padding byte each. The fifteen readers and MOV stride are the only existing bytes changed. Row 9 starts at even address 08D8ABA2; both halfword reads are aligned. The saved normalized identity still feeds the 384-byte behavior stride.

The independent whole-image reconstruction verifies 17 spans, 244 declared bytes and 196 changed bytes, with an exact inverse to DEEE. The whole D8AB00–D8AC00 reservation is blank in DEEE and has no incoming references under the conservative scanner. It is disjoint from the existing AI reservation. Old tables, action and behavior views, normalization helper and all other code remain byte-exact.

Execution checks cover all fifteen parameter fields across thirteen input identities and all sixteen NZCV combinations (208 cases), plus 507 full initializers over three difficulties and thirteen progress values. The 234 even-row cases preserve complete register, flags and memory state. The 273 odd-row cases intentionally restore source halfwords instead of the commercial truncation. For row indices 0–9, old first words were `[740,80,592,228,592,80,740,80,592,228]`; repaired/source words are `[740,592,592,740,592,592,740,592,592,740]`. There is no blanket legacy-behavior equality claim.

CLI: `python tools/verify_character_ai_parameter_alignment.py --before <DEEE> --after <aligned image> --source <WSC1.5> --owner <DEEE component.json> --report <fresh path>`.

This is static native-execution evidence. No aligned live witness or complete campaign result is claimed here; root owns the next private run. The earlier DEEE campaign success and its qualified AI prefix remain separate historical evidence.
