#!/usr/bin/python3

# Convert Recalbox EmulationStation theme's SVG images to PNG for display by mpv or ffplay

import os, logging, cairosvg, re
from typing import List, Dict

# Uncomment for DEBUG
#logging.basicConfig(level=logging.DEBUG)

# top-level project directory
BASEDIR: str = os.path.dirname(__file__)
logging.debug(f"BASEDIR={BASEDIR}")


# preferred output sizing
OUT_WIDTH: int = 1200
OUT_HEIGHT: int = 360

# preferred region: eu, us or jp
REGION:str  = 'eu'


def convertToPNG(infile: str, outfile: str) -> None:
    '''Convert infile to PNG format and write to outfile'''
    cairosvg.svg2png(
        url = infile,
        write_to = outfile,
        output_width = OUT_WIDTH,
        output_height = OUT_HEIGHT
    )


def convertTheme(inPath: str, outPath: str, dryrun = False) -> None:
    '''Convert a theme's logo.svg files to PNG and place them in outPath named [systemId].png'''

    # system directories to skip: virtual systems
    _SKIP_SYSTEMS: List[str] = ['auto-allgames', 'auto-lastplayed', 'auto-multiplayer', 'default', 'favorites', 'imageviewer']

    # Look through all first level directories in inPath
    with os.scandir(inPath) as it:
        for systemId in it:
            logging.debug(f"found system: {systemId.name}")
            # skip non-directories and virtual systems
            if systemId.is_dir() and (systemId.name not in _SKIP_SYSTEMS):
                # look for a file named data/logo.svg, or /data/$REGION/logo.svg
                for dir in ["data", f"data/{REGION}"]:
                    infile = f"{inPath}/{systemId.name}/{dir}/logo.svg"
                    logging.debug(f'looking for {infile}... ', end='')
                    if os.path.isfile(infile):
                        print(f"converting '{infile}' -> {outPath}/{systemId.name}.png")
                        if not dryrun: convertToPNG(infile, f"{outPath}/{systemId.name}.png")
                        # found a logo: no need to look further for this system
                        break
                    else:
                        logging.debug(f"'{infile}' not found")
        it.close()


def convertDanPatrick(inPath: str, outPath: str, dryrun = False) -> None:
    '''Convert SVG files in inPath/[category] to PNG and place them in outPath/[category]'''
    CATEGORIES: List[str] = ['publisher', 'system']

    for cat in CATEGORIES:
        # scan inPath/cat/
        with os.scandir(f"{inPath}/{cat}") as it:
            print(f"Scanning directory {inPath}/{cat}")
            for image in it:
                if image.is_file() and image.name.endswith(".svg"):
                    # strip .svg extension & force lower case
                    basename = os.path.splitext(image.name)[0].lower()
                    # replace spaces, brackets & dashes with dots
                    basename = re.sub('[ \(\)\-]', '.', basename)
                    # strip non-standard characters ; : , 
                    basename = re.sub('[\;\:,]', '', basename)
                    # condense multiple dots to single dot
                    basename = re.sub('\.+', '.', basename)
                    # prefix filenames starting with 'arcade' with 'mame' so they match Recalbox's systemId
                    if basename.startswith('arcade'):
                        basename = 'mame.' + basename
                    logging.debug(f"basename={basename}")

                    # TODO: multiword publishers e.g. 'Sammy Atomiswave', 'Video System Co' have dots instead of spaces

                    outFullPath = getUniqueFilename(f"{outPath}/{cat}", basename, 'png')
                    print(f"converting '{inPath}/{cat}/{image.name}' -> {outFullPath}")
                    if not dryrun: convertToPNG(
                        infile = f"{inPath}/{cat}/{image.name}",
                        outfile = outFullPath
                    )
        it.close()


def getUniqueFilename(dir: str, basename: str, ext: str) -> str:
    '''Compute a unique file name to ensure we don't overwrite existing files'''
    _index = 1
    while True:
        # add index to end of output filename unless this is only file with that name
        if _index == 1:
            _outFullPath = f"{dir}/{basename}.{ext}"
        else:
            _outFullPath = f"{dir}/{basename}_{_index:02}.{ext}"
        if not os.path.exists(_outFullPath):
            # found a unique output filename: stop searching
            break
        else:
            # increment index and try again
            _index += 1
    logging.debug(f"getUniqueFilename({dir}, {basename}, {ext}) -> {_outFullPath}")
    return _outFullPath


### main ###

convertTheme(
    inPath = f"{BASEDIR}/artwork/recalbox-next",
    outPath = f"{BASEDIR}/media/system",
    # dryrun = True
)

convertDanPatrick(
    inPath = f"{BASEDIR}/artwork/Dan_Patrick_v2_platform_logos",
    outPath = f"{BASEDIR}/media",
    # dryrun = True
)