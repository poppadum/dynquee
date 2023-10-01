#!/usr/bin/env python3

"""Convert a single theme system image (console or logo) to PNG with border
    and lighter background if necessary
"""

import sys
from pathlib import Path
import logging
from convert_artwork import ThemeConverter

def usage():
    """Print usage message"""
    print(f"usage: {sys.argv[0]} <system> <logo|console>", file=sys.stderr)


### main ###
if __name__ == "__main__":
    # check for correct args
    if (len(sys.argv) != 3) or (sys.argv[2] not in ['logo','console']):
        usage()
        sys.exit(1)

    artwork_dir: Path = Path(__file__).parent
    logging.debug("artwork_dir=%s", artwork_dir)

    inPath: Path = artwork_dir.joinpath("recalbox-next")
    outPath: Path = artwork_dir.parent.joinpath("media/system")
    logging.debug("inPath=%s outPath=%s", inPath, outPath)

    # convert theme image
    tc: ThemeConverter = ThemeConverter(
        inPath = str(inPath),
        outPath = str(outPath),
        dryrun = False
    )
    tc.convertThemeImage(sys.argv[1], sys.argv[2])
