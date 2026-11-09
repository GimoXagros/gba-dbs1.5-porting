# Capture-free palette-call production gate

PASS. NEW `tools/verify_shoot_palette_dim_calls_production.py` SHA256 `0CACBFB6D878F2D0CED87CA35E29F704D42ED9DD52654EB4859DE56AD3DB9C9B` produces `build/shoot-palette-dim-calls-production-qa-20261109/final-report.json` SHA256 `94F9FD0FC4B95F64CA7BFB4F424DF333EF29170B8CDA32A1CA2FB4BEF0BDC840`. A second fresh output under `path-stability/` is byte-identical.

It checks exact1477→FF3A plus original WSC1.5, author66E70D72 and fresh manifest6E44701A. Independent PC+8 arithmetic binds all four NE/link call words to the existing5C6FD4 helper; source bright/half-nibble projector and existing helper/stage gate/blink producer remain byte-bound. Sixteen declared/twelve changed bytes invert completely to1477; ten corruption controls reject. Every tracked manifest dependency is rehashed. No new storage or RAM owner is introduced.

The tool imports no builder or capture parser and reads no historical capture, ignored report, RAM or State. Frozen actual ARM report18FBCD5B is cited by hash only;286 projector/128 helper semantic cases and old4096-color mathematics are not rerun. CLI: `--before ROM1477 --after ROMFF3A --source ORIGINAL --manifest FRESH_COMPONENT_JSON --report FRESH_REPORT`.

This is a future main packaging gate; it does not claim terminal runtime or later guard acceptance. No emulator, root/main edit, guest write, State load/edit or Git operation occurred.
