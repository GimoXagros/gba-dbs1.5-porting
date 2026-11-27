"""Reproduce the two private D-Project cartridge saves used in D-ARK link QA.

Usage: python prepare_dproject_link_save.py CORE_DLL DPROJECT_ROM OUTPUT_FOLDER
The only assisted step unlocks the registration PC on a copy of the initial
in-game save. Raising, care, registration, save and link selection use buttons.
"""
import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path

from wsc_dark_link import Core


INPUT_FILE = Path(__file__).resolve().parents[1] / 'records/fixtures/dproject-pc-roster-inputs.json'
BUTTONS = {'u': 'Up', 'd': 'Down', 'l': 'Left', 'r': 'Right',
           's': 'Start', 'a': 'A', 'b': 'B', 'y': 'Y1', 'w': 'Y3', '.': 0}
LOAD_GAME = '.300,s3,.80,s3,.160,a3,.360'
FIELD_SAVE = 'y3,.24,u3,.24,a3,.120'


def play(core, commands):
    """Comma joins sequential holds, a bare button taps one frame then rests seven.

    The number following * repeats the preceding comma-separated sequence.
    """
    for command in commands:
        sequence, _, repetitions = command.partition('*')
        for _ in range(int(repetitions or '1')):
            for segment in sequence.split(','):
                button = BUTTONS[segment[0]]
                for _ in range(int(segment[1:] or '1')):
                    core.frame(button)
                if len(segment) == 1:
                    for _ in range(7):
                        core.frame()


def verify_hash(data, expected, label):
    if sha256(data).hexdigest() != expected:
        raise ValueError(f'{label} differs from the recorded cartridge save')


def open_registration_pc(dll, rom, initial):
    with closing(Core(dll, rom, initial)) as core:
        play(core, [LOAD_GAME])
        # Story flag 1 enables only the room object for the registration PC.
        # Never write a character record. Let the cartridge update both checksums.
        ram = bytes(core.ram)
        state = bytearray(core.state())
        offset = state.find(ram)
        if ram[0x239F] != 1 or offset < 0 or state.find(ram, offset + 1) >= 0:
            raise ValueError('Unexpected RAM image or story flag before PC unlock')
        state[offset + 0x239F] |= 2
        core.restore(bytes(state))
        if bytes(core.ram) != ram[:0x239F] + b'\x03' + ram[0x23A0:]:
            raise ValueError('The private RAM copy differs outside the PC flag')
        play(core, [FIELD_SAVE])
        unlocked = core.save()
        changed = [i for i, (a, b) in enumerate(zip(initial, unlocked)) if a != b]
        if changed != [0x3F1B, 0x3F7C, 0x73FB, 0x745C]:
            raise ValueError(f'Unexpected save changes during PC unlock: {changed}')
        return unlocked


def prepare(dll, rom, folder, greymon=False):
    records = json.loads(INPUT_FILE.read_text(encoding='utf-8'))
    digest = sha256(rom.read_bytes()).hexdigest()
    config = next((item for item in records.values() if item['rom_sha256'] == digest), None)
    if config is None:
        raise ValueError('Select the original D-Project or the Korean v1.1 cartridge')
    if greymon and 'greymon' not in config:
        raise ValueError('The recorded Greymon training inputs use the Korean cartridge')
    roster = config['greymon'] if greymon else config
    species = 0x18 if greymon else 0x15
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        raise ValueError('Choose an empty output folder to preserve prior saves')
    with closing(Core(dll, rom)) as core:
        play(core, config['raising_inputs'])
        initial = core.save()
    verify_hash(initial, config['cartridge_save_sha256'], 'Game-earned save')
    (folder / 'before-pc.sav').write_bytes(initial)
    unlocked = open_registration_pc(dll, rom, initial)
    verify_hash(unlocked, config['unlocked_save_sha256'], 'PC-only unlock')
    (folder / 'pc-unlocked.sav').write_bytes(unlocked)

    with closing(Core(dll, rom, unlocked)) as core:
        play(core, [LOAD_GAME, *roster['field_to_entry']])
        if core.ram[0x1FCC] != species or core.ram[0x20E0] != 0xFF:
            raise ValueError('Unexpected field species or occupied registration slot')
        core.screen().save(folder / 'pc-entry.png')
        play(core, ['a3,.45,a3,.45,a3,.50,a3,.40,a3,.70'])
        if core.ram[0x20E0] != species:
            raise ValueError('The selected Digimon was not registered by the PC menu')
        core.screen().save(folder / 'pc-registered.png')
        play(core, ['b3,.100', FIELD_SAVE])
        registered = core.save()
    verify_hash(registered, roster['registered_save_sha256'], 'Registered save')
    (folder / 'registered.sav').write_bytes(registered)

    with closing(Core(dll, rom, registered)) as core:
        play(core, ['.300,s3,.80,s3,.160,d3,.20,a3,.120,d3,.20'])
        core.screen().save(folder / 'vs-swan-cable.png')
        play(core, ['a3,.100'])
        if core.ram[0x1F86] != 1 or core.ram[0x20E0] != species:
            raise ValueError('Expected one registered Digimon of the chosen species after cold boot')
        core.screen().save(folder / 'registered-select.png')
        play(core, ['a3,.40,u3,.40,a3,.100,d3,.25,a3,.80'])
        if bytes(core.ram[0x1F44:0x1F46]) != b'\x21\x6f' or core.ram[0x1F72]:
            raise ValueError('Expected the original cable wait before either peer transmits')
        core.screen().save(folder / 'ready.png')
        (folder / 'ready.State').write_bytes(core.state())
    print(f'{config["edition"]}: ready; cartridge save {roster["registered_save_sha256"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('dll', 'rom', 'folder'):
        parser.add_argument(arg, type=Path)
    parser.add_argument('--greymon', action='store_true',
                        help='Train the Korean Botamon on the punching bag, let it roam, then register its evolution')
    args = parser.parse_args()
    prepare(args.dll, args.rom, args.folder, args.greymon)
