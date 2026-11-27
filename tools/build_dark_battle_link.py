"""Add the D-ARK serial battle to the verified v1.0.3 parent."""
from build_boss_dark_fixes import FINAL as V103
from build_issue4_fixes import finish, inputs
import dark_battle

V103_OWNER = '0EFF5528BBCBDE9AB72BBB3E02E36E2796C8C5772E779A5C0F7175EB048ABC73'
FINAL = 'FA46FC35A84559C89CFE0D9BD3DF0E5C6657C00A7287C878A69470812EE5B9B5'


def install(parent, owner_path, original, dest):
    before, source, owner_bytes, owner = inputs(parent, owner_path, original, V103, V103_OWNER)
    image = bytearray(before)
    end = dark_battle.apply(image, source)
    return finish(before, image, owner, owner_bytes, dest, FINAL,
                  (('D-ARK serial battle', dark_battle.START, end - dark_battle.START),))
