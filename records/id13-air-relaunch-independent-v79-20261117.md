# ID13 aerial relaunch: independent implementation verification

The isolated FBD9CD19 component passes the new independent offline review.
It restores the source's ID13-specific fall transition and four callbacks.
This report does not claim runtime gameplay, hardware timing, or final port
completion. Root owns integration and runtime observation.

## Frozen scope

- Before: C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1.
- After: FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD.
- Component manifest: 64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD.
- Independent verifier: `tools/verify_id13_air_relaunch.py`, SHA
  CC077B90609E4E9D93D6C8740D154EC94184F642B2A5910F729E00E3E64A54CE.
- Independent result: `build/id13-air-relaunch-independent-v79-20261117/audit.json`.

The verifier imports no production builder. Its behavioral reference is
transcribed from the original WSC1.5 instructions at785797..785992, and its
strict ARM interpreter and reference scanner are existing hash-pinned
independent verification dependencies. The source and retail ROM hashes
are checked before use; no original input is modified.

## Source and native entry coverage

The complete source graph hash is95AF262178FE267C49AB7DE8DC687C93BDEE5D87430F5DB08567BE75C66E3F77.
All direct source stores of callback8522:0577 occur at7682FA,7684D3,
7688DF,768AD1. The source states map as follows:

| Source state | Source raw entry | New native entry |
|---|---|---|
| 0577 initialize | 785797 | 08D3F200 |
| 0593 ready | 7857B3 | 08D3F280 |
| 066E boosting | 78588E | 08D3F500 |
| 0701 spent | 785921 | 08D3F700 |

The three installed native hooks are08357054,0835732C,083578D4. A separate
aligned byte-pattern comparison of the existing signed-descent, one-shot
flag, and special-mode gate sequence finds exactly the three corresponding
gate entries08357030,08357308,083578B0. Each hook precedes the ordinary
held-input test. ID13 must select the new initializer even with A released;
the source initializer itself establishes the held/released latch.

The native outer predicates remain unchanged: vertical velocity must be
signed-positive, actor+A6 bit1 must be clear, and actor+8 bit100 must be
clear. Other identities retain the displaced input load, all registers,
stack/return state, and NZCV flags. For ID13, the adapter writes the new
callback and consumes exactly the existing common-fall saved return address.

Iraira does not need a fourth native hook. Its installed08627C40 branches
to0835774C; the retained launch sequence at08357780/84 assigns083577A8,
which reaches the common jump/fall family. This is a decoded branch and
callback assignment, not an assumed literal pointer in the Iraira block.

## Fields, units, and callback lifetime

The relevant map is source+90/+92/+94 to native+A6/+A8/+AA respectively.
The initial review request's +92/+94→A6/A8 shorthand was incorrect.
Concrete anchors include the common-fall one-shot test at083578BC and
the existing02BD writer08357EE0, which stores the source+94 descending
flag at actor+AA. The existing class5 path likewise maps source+92 to+A8.

A8 is a packed held latch/count, not a globally unique allocation. INIT
overwrites it with0100, including any stale prior action value. Each fresh
relaunch clears AA, installs source velocityFD80 and acceleration0018,
increments only the low byte of A8, and preserves the high byte. Release
clears the entire high byte with AND00FF. The descending transition sets
AA once and chooses acceleration0016/event10 for phase1, otherwise001E/
event7. The third completed relaunch selects SPENT; a fourth held input
cannot start another relaunch.

Other native callbacks reuse A8/AA. For example, action installation writes
the new callback at08355608 before descriptor fields at08355674..680
replace A8/AA. The actor scheduler invokes the single current callback at
083525BC..C4. Collision reactions and other actor families have separate
writers; these fields are not claimed to be globally exclusive. The new
graph introduces no new writable global or pool. The verifier checks exact
actor write ownership and adjacent-byte preservation across its cases.

Native special-air lineage retains source literals such as gravity2,
velocity64, duration126, and horizontal128 in existing callbacks. The
retained physics adds acceleration+48 into velocity+44, then shifts the
velocity by4 for the body-motion delta. The new constants remain in that
per-update fixed-point convention. No invented platform multiplier is
applied. This establishes a native unit contract, not wall-clock or
real-hardware trajectory equivalence.

## Independent tests and the defect caught before freezing

The first author draft advanced animation immediately after installing the
relaunch event. Source785819 jumps directly to RETF at785992. Independent
review identified that extra tick; the frozen candidate returns directly
after event72 and installing BOOST. The verifier includes a mutation that
reintroduces the extra tick and rejects it.

The final checks execute the actual emitted ARM instructions:

- 927 state cases cover signed velocity boundaries, every shared-service
  early return, gravity initialization, phase selection, held/released and
  directional input, evolved delegation, packed-byte overflow/high-byte
  preservation, count exhaustion, and SPENT input.
- 3,252 route cases cover all256 identity bytes, representative NZCV values,
  all three installed hooks, and the original outer gate boundaries.
- An11-update sequence starts with stale A8=0019, follows initialization,
  release/press transitions through three relaunches, and rejects a fourth.
  Physics boundary values are supplied as unit-test inputs; this is not a
  simulated complete gameplay trajectory.
- Seven meaningful mutations are rejected: wrong upward impulse, increment
  by2, missing special one-shot flag, extra same-update tick, exhaustion at2,
  packed-state aliasing A6, and selection of the wrong identity.

The short retained horizontal-input routine0835604C executes in the test
runner. Landing, attack, other interruption, event setter, and animation
tick are explicit imported-service boundaries with checked argument layout,
ordered calls, return partitions, and deliberate volatile-register/flag
clobbering. Their full game bodies are not executed by this verifier.

## Storage and inverse

There are ten writes: three four-byte hooks, three64-byte adapters, and
four callbacks of36/356/220/172 bytes. Total declared bytes988; actual
changed bytes968. The complete16MiB inverse restores exact C91, including
every byte outside those spans.

New code occupies the reserved rawD3F100..D3FA00 suballocation. Its entire
predecessor span is FF. Ownership is joined to the existing music reservation
D33000..D40000 and the preceding evolution-table tail beginningD3F05A.
All prior audio payloads and evolution-table writes remain exact. The
conservative whole-ROM pointer/ARM/Thumb reference scan finds no prior
incoming encoding into the new code reservation; all151 resulting new
reference encodings originate inside the declared new writes/hooks.

No emulator, live save, game-state forcing, main build, or Git operation was
performed by this independent review. Actual gameplay integration and timing
remain root-owned. The separate historical E5 crash still lacks its original
overlap/metadata chain; the newly captured malformed E5 producer does not
remove that qualification.

## Additional integration check: retained ID1-only special comparison

Root raised whether the unchanged native comparison at08357940 still omits
ID13 from the existing02BD route when the new automatic initializer gates
fail. A new focused source/native predecessor check resolves this without
another ROM change or rerunning the completed semantic suite:

| Source entry gate | Automatic0577 assignment / return | Existing02BD store | All failed outer predicates skip to |
|---|---|---|---|
| 7682DC | 7682FA / 768303 | 76835E | 768367 |
| 7684B5 | 7684D3 / 7684DC | 768537 | 768540 |
| 7688C1 | 7688DF / 7688E8 | 768943 | 76894C |
| 768AB3 | 768AD1 / 768ADA | 768B35 | 768B3E |

Each failing velocity/one-shot/special-mode predicate jumps beyond the
entire held-input and02BD-selection block. When those predicates pass,
ID13 assigns0577 and returns before reaching the later ID1-or-ID13 fallback.
Consequently that fallback is unreachable for ID13 through these ordinary
entry paths in the source as well. The candidate preserves the same skip
destinations:083570DC,083573B4,0835795C, each after its retained02BD store.
The already completed native gate tests assert those exact destinations.

A complete source scan for the direct8522:02BD callback-store sequence
finds exactly five sites: the four stores in the table and7857CC. The fifth
is the READY enhanced branch translated by the new graph and exercised by
the frozen independent ARM cases. Thus no additional ID13 comparison patch
is required to complete these source routes.

The additional asserted evidence is
`build/id13-air-relaunch-independent-v79-20261117/special-branch-coverage.json`.
FBD9, the verifier, and its original semantic report remain unchanged.
