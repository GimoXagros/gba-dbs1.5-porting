"""Apply the issue 4 corrections to the verified v1.0.0 payload."""
import json
from pathlib import Path

from build_mixed_compatibility import FINAL as RELEASE, sha
import issue4_dimensions
import issue4_opening
import issue4_train
import issue4_waterfall
from verify_issue4_waterfall import verify as verify_waterfall
from verify_mode23_scene_component import empty


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


def install(parent: Path, owner_path: Path, original: Path, dest: Path):
    before = parent.read_bytes()
    source = original.read_bytes()
    owner_bytes = owner_path.read_bytes()
    owner = json.loads(owner_bytes)
    if sha(owner_bytes) != 'A4BC34DC742437426ECD7A12901B605C7AB29C946F267F6335882ACC0162A44F':
        raise ValueError("Unexpected v1.0.0 allocation record")
    if sha(before) != RELEASE or owner['output_sha256'] != RELEASE or sha(source) != owner['source_sha256']:
        raise ValueError("Unexpected v1.0.0 base or WonderSwan source")
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
    ranges = list(changed_ranges(before, image))
    writes = [
        dict(offset=start, size=end-start, before_sha256=sha(before[start:end]), after_sha256=sha(image[start:end]))
        for start, end in ranges
    ]
    result = sha(image)
    if result != '95E5A25622AFFC038BF7073FEA26B0950EAEBEF1AD9E576AED5B3A4E830E3EB7':
        raise ValueError(f"Unexpected issue 4 output: {result}")
    prior = owner['prior_excluded_extents'] + [[a['start'],a['end']] for a in owner['allocations']]
    allocations = []
    for label, start, size in (
        ('opening fade transitions', 0xE787D0, 52),
        ('train spring gravity', issue4_train.START, 128),
    ):
        end = start + size
        if any(a < end and start < b for a, b in prior) or before[start:end] != b'\xff' * size:
            raise ValueError(f"Conflicting ROM allocation for {label}")
        allocations.append(dict(label=label, start=start, end=end, size=size, alignment=4))
    owner.update(prior_excluded_extents=prior, allocations=allocations)
    owner.update(input_sha256=RELEASE, prior_owner_sha256=sha(owner_bytes), output_sha256=result, writes=writes)
    dest.mkdir(parents=True, exist_ok=False)
    (dest/'component.gba').write_bytes(image)
    (dest/'manifest.json').write_text(json.dumps(owner,indent=2)+'\n',encoding='utf8',newline='\n')
    return result
