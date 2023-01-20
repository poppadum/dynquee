#!/usr/bin/python3

# Convert Recalbox EmulationStation theme's SVG images to PNG for display by mpv or ffplay

import os, logging, cairosvg
from typing import List

# theme name
THEME: str = 'recalbox-next'

# input & output paths
BASEDIR: str = os.path.dirname(__file__)
IN_PATH: str = f"{BASEDIR}/themes/{THEME}"
OUT_PATH: str = f"{BASEDIR}/media/out.tmp"

# output sizing
OUT_WIDTH: int = 1200
OUT_HEIGHT: int = 360


# preferred region: eu, us or jp
REGION:str  = 'eu'

# directories to skip: not actual systems
SKIP_SYSTEMS: List[str] = ['auto-allgames', 'auto-lastplayed', 'auto-multiplayer', 'default', 'favorites', 'imageviewer']


# Uncomment for DEBUG
#logging.basicConfig(level=logging.DEBUG)
logging.debug(f"DEBUG: IN_PATH={IN_PATH} OUT_PATH={OUT_PATH}")


def convertToPNG(infile: str, outfile: str) -> None:
    '''Convert infile to PNG format and write to outfile'''
    cairosvg.svg2png(
        url = infile,
        write_to = outfile,
        output_width = OUT_WIDTH,
        output_height = OUT_HEIGHT
    )



# Look through all first level directories in IN_PATH
with os.scandir(IN_PATH) as it:
    for systemId in it:
        logging.debug(f"DEBUG: found system: {systemId.name}")
        # skip non-directories or any virtual systems
        if systemId.is_dir() and (systemId.name not in SKIP_SYSTEMS):

            # look for a file named data/logo.svg, or /data/$REGION/logo.svg
            for dir in ["data", f"data/{REGION}"]:
                infile = f"{IN_PATH}/{systemId.name}/{dir}/logo.svg"
                print(f'looking for /{infile}... ', end='')
                if os.path.isfile(infile):
                    print('found')
                    convertToPNG(infile, f"{OUT_PATH}/{systemId.name}.png")
                    # if we've found a logo, no need to look further for this system
                    break
                else:
                    print("NOT FOUND")
    it.close()


