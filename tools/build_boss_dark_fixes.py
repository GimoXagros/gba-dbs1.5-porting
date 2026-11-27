"""Install the roster-wide boss repairs and disconnected D-ARK scene on v1.0.2."""
from build_issue4_fixes import ROAMER_SHA, finish, inputs
import dark_entry_repair
import zeed_boss_hp
import zeed_roster_exit
from verify_zeed_roster_exit import check

FINAL = "8ABA49B14FFB4A1BABD3B99CD438846EA1D0CE7C0680F52D0B6F1A328A7CD508"
TRAIN_OWNER = "60C139D713495F90353E3E2BFE4CF2BB44CA121BBEBB7CBF01D92665360C7712"


def install(parent, owner_path, original, dest):
    before, source, owner_bytes, owner = inputs(parent, owner_path, original, ROAMER_SHA, TRAIN_OWNER)
    image = bytearray(before)
    zeed_roster_exit.apply(image, source)
    zeed_boss_hp.apply(image, source)
    end = dark_entry_repair.apply(image, source)
    check(image)
    start = dark_entry_repair.START
    return finish(before, image, owner, owner_bytes, dest, FINAL, (("D-ARK waiting scene", start, end - start),))
