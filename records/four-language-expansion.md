# Four-language expansion — authorized 2026-10-16

The user expanded the final port scope to English, Japanese, Korean and Digicode.
Digicode must derive from Japanese text/readings, never from English localization.
This extends the active port; crash/resource repairs remain prerequisites.

## Concrete inputs and current state

- `localization/digicode-reference.json` records the 72 chart cells visible in the
  user's attachment: 46 unvoiced kana, 20 voiced kana, five semi-voiced kana and
  the long-vowel mark. Coordinates refer to the chart's rows and columns.
- `tools/encode_digicode_reading.py` maps explicit hiragana/katakana readings to
  stable reference IDs. NFC permits equivalent combining voicing marks. Unknown
  input raises an error; there is no Latin transliteration or missing-glyph fallback.
- These IDs are catalog identities, not assigned game codes or font pixels.
- The attachment was visible in chat, but its supplied Desktop path was absent
  when checked. No source-image hash, extracted pixels or font fidelity is claimed.
- Native language selection, persistence and rendering consumers are under
  investigation. Four working menu entries have **not** been implemented yet.

## Completion conditions

Trace every language selector, range check, table lookup and persistence consumer
before changing the native language domain. Preserve the original two languages.
Extract both text and graphics-based labels, retaining source/control tokens.
Provide Korean translations and readable glyphs on each actual rendering path.
Keep Japanese original strings and explicit readings linked to Digicode output;
resolve small kana, kanji readings, punctuation and digits against the actual
corpus rather than silently expanding, dropping or borrowing English symbols.
Identify the final font input and independently verify its glyph mapping.

Verify switching and fresh-session persistence for all four choices, all affected
menus and gameplay text, and missing-glyph/overflow failures. Use invisible runs
and newly generated test data only; the supplied WSC save remains forbidden.
Integrate into two reproducible full builds. Until these conditions pass, this is
an implemented reference catalog and conversion scaffold, not a completed feature.

## Additional user references

The user subsequently supplied a separate Latin alphabet chart and a detailed
Japanese chart with three examples: あぐもん, やがみたいち, and
でじもんあどべんちゃー. These are now reference comparison cases. Romanized
captions do not replace Japanese readings. The third example must be checked
for small ゃ and long-vowel treatment before finalizing that mapping; the current
strict encoder intentionally rejects the unresolved small kana. No blanket
small-to-large kana conversion has been adopted.

## Mixed-script policy — explicit user clarification

Latin letters already present in Japanese text use the supplied Latin Digicode
chart. Uppercase and lowercase share its 26 glyph identities. This is direct
character mapping, not translation into English or romanization of Japanese.
The reference encoder now supports mixed kana/Latin input while preserving
order. Kanji, unsupported small kana, punctuation and digits still fail until
their actual source usages and rendering policies are established.

## Verified native entry points

See `language-consumers.md` and `analyze_language_consumers.py` for the actual
five-row Options menu, both retained language atlases, and the bounded native
EEPROM record inventory. `localization/options-draft.json` preserves ten
Japanese text-frame transcriptions with Korean translation drafts, including
all three difficulty values and both confirmation choices; it is explicitly
not a product-build input or a complete text corpus.

`analyze_language_consumers.py --render-directory <directory> --all-frames`
now renders every event frame with complete sprite bounds, rather than only
the first value in each event. Source event/frame coordinates remain attached
to each preview row. Inspection corrected event 11 frame 0 from the mistaken
`ふつう`/`보통` to `いいえ`/`아니요`; `ふつう` belongs to event 3 frame 1.
All ten explicit readings pass the reference Digicode encoder. This proves
reference-glyph coverage for this draft only, not native rendering.
