"""Install the verified issue 4 fixes and the follow-up Train stage layer."""
import json
from pathlib import Path

from build_mixed_compatibility import FINAL as RELEASE, sha
import issue4_dimensions
import issue4_opening
import issue4_train
import issue4_waterfall
from verify_issue4_waterfall import verify as verify_waterfall
from verify_mode23_scene_component import empty


V101 = '95E5A25622AFFC038BF7073FEA26B0950EAEBEF1AD9E576AED5B3A4E830E3EB7'
ROAMER_SHA = 'F32BEFB1673B57A94498BAAB6E62D0A1351C3AE3614601B3F8F3EC1C7EFE0090'


def changed_ranges(before, after):
    if len(before) != len(after):
        raise ValueError("Issue 4 patches must preserve cartridge size")
    first = None
    for index, (left, right) in enumerate(zip(memoryview(before).cast('I'), memoryview(after).cast('I'))):
        if left != right:
            if first is None:
                first = index * 4
        elif first is not None:
            yield first, index * 4
            first = None
    if first is not None:
        yield first, len(after)


def inputs(parent, owner_path, original, expected_image, expected_owner):
    before = parent.read_bytes()
    source = original.read_bytes()
    owner_bytes = owner_path.read_bytes()
    if sha(owner_bytes) != expected_owner:
        raise ValueError("Unexpected allocation record for issue 4 layer")
    owner = json.loads(owner_bytes)
    if sha(before) != expected_image or owner['output_sha256'] != expected_image or sha(source) != owner['source_sha256']:
        raise ValueError("Unexpected input ROM or WonderSwan source for issue 4 layer")
    return before, source, owner_bytes, owner


def install(parent: Path, owner_path: Path, original: Path, dest: Path):
    before, source, owner_bytes, owner = inputs(
        parent, owner_path, original, RELEASE, 'A4BC34DC742437426ECD7A12901B605C7AB29C946F267F6335882ACC0162A44F')
    image = bytearray(before)
    issue4_opening.apply(image, source)
    issue4_waterfall.apply(image, source)
    issue4_dimensions.apply(image, source)
    issue4_train.apply(image, source)
    verify_waterfall(image)
    cpu = empty(image)
    for stage in range(12):
        cpu.r[1] = stage
        cpu.run(0x0803EE70, {0x0803EE84})
        row = issue4_dimensions.SOURCE_TABLE + stage * 4
        expected = int.from_bytes(source[row:row + 4], 'little')
        if cpu.get(0x03004568, 4) != expected or cpu.r[1] != stage:
            raise ValueError(f"Wrong stage dimensions for {stage}")
    return finish(before, image, owner, owner_bytes, dest, V101,
                  (('opening fade transitions', 0xE787D0, 52), ('train spring gravity', issue4_train.START, 128)))


def finish(before, image, owner, owner_bytes, dest, expected, regions):
    ranges = list(changed_ranges(before, image))
    writes = [
        dict(offset=start, size=end-start, before_sha256=sha(before[start:end]), after_sha256=sha(image[start:end]))
        for start, end in ranges
    ]
    result = sha(image)
    if result != expected:
        raise ValueError(f"Unexpected issue 4 output: {result}")
    prior = owner['prior_excluded_extents'] + [[a['start'],a['end']] for a in owner['allocations']]
    allocations = []
    for label, start, size in regions:
        end = start + size
        if any(a < end and start < b for a, b in prior) or before[start:end] != b'\xff' * size:
            raise ValueError(f"Conflicting ROM allocation for {label}")
        allocations.append(dict(label=label, start=start, end=end, size=size, alignment=4))
    owner.update(prior_excluded_extents=prior, allocations=allocations)
    owner.update(input_sha256=owner["output_sha256"], prior_owner_sha256=sha(owner_bytes), output_sha256=result, writes=writes)
    dest.mkdir(parents=True, exist_ok=False)
    (dest/'component.gba').write_bytes(image)
    (dest/'manifest.json').write_text(json.dumps(owner,indent=2)+'\n',encoding='utf8',newline='\n')
    return result


def install_train_roamer(parent: Path, owner_path: Path, original: Path, dest: Path):
    import issue4_train_roamer

    before, source, owner_bytes, owner = inputs(
        parent, owner_path, original, V101, 'E595987D8D043E0EBBBF5EF3789090CF4FE16812A911B3CF18E5300934445E93')
    image = bytearray(before)
    issue4_train_roamer.apply(image, source)
    return finish(before, image, owner, owner_bytes, dest, ROAMER_SHA,
                  (('Train roaming actor', issue4_train_roamer.START, issue4_train_roamer.END - issue4_train_roamer.START),))
