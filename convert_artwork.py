#!/usr/bin/python3

# Convert sourced artwork in SVG format to PNG
# 1. Recalbox EmulationStation theme's system images
# 2. Dan Patrick's v2 Platform Logos

import os, logging, subprocess, re
import cairosvg  # type: ignore  # suppress mypy 'missing typehints for cairosvg' error
from typing import List

# Uncomment for DEBUG
logging.basicConfig(level=logging.DEBUG)


# preferred output sizing
OUT_WIDTH: int = 1280
OUT_HEIGHT: int = 360

# preferred region: eu, us or jp
REGION:str  = 'eu'


# Recalbox-next logos requiring a light background
_SYSTEMS_NEED_LIGHT_BG: List[str] = [
    '3ds', 'amigacd32', 'amigacdtv', 'amstradcpc', 'apple2gs', 'atari800',
    'atomiswave', 'cavestory', 'channelf', 'dreamcast', 'fds', 'gameboy',
    'gamegear', 'gc', 'gw', 'intellivision', 'kodi', 'macintosh', 'mame',
    'moonlight', 'msx2', 'naomi', 'naomigd', 'nds', 'neogeo', 'neogeocd',
    'nes', 'odyssey2', 'palm', 'pc88', 'pc98', 'pcenginecd', 'pcfx',
    'pokemini', 'ports', 'ps2', 'ps3', 'psp', 'psx', 'satellaview', 'to8',
    'wonderswan', 'x1', 'zxspectrum'
]


def _convertToPNG(infile: str, outfile: str) -> None:
    '''Convert infile to PNG format and write to outfile'''
    cairosvg.svg2png(
        url = infile,
        write_to = outfile,
        output_width = OUT_WIDTH,
        output_height = OUT_HEIGHT,
    )

def _convertTOPNGLightBackground(infile: str, outfile: str):
    cmd: List[str] = [
        '/usr/bin/rsvg-convert',
        '--width', str(OUT_WIDTH), '--height', str(OUT_HEIGHT),
        '--background-color=#444',
        '-o', outfile,
        infile
    ]
    logging.debug(f"cmd={cmd}")
    subprocess.run(cmd)



def convertTheme(inPath: str, outPath: str, dryrun: bool = False) -> None:
    '''Convert a theme's logo.svg files to PNG and place them in outPath named [systemId].png'''

    # system directories to skip: virtual systems
    SKIP_SYSTEMS: List[str] = ['auto-allgames', 'auto-lastplayed', 'auto-multiplayer', 'default', 'favorites', 'imageviewer']

    # Look through all first level directories in inPath
    with os.scandir(inPath) as it:
        for systemId in it:
            logging.debug(f"found system: {systemId.name}")
            # skip non-directories and virtual systems
            if systemId.is_dir() and (systemId.name not in SKIP_SYSTEMS):
                # look for a file named data/logo.svg, or /data/$REGION/logo.svg
                for dir in ["data", f"data/{REGION}"]:
                    infile: str = f"{inPath}/{systemId.name}/{dir}/logo.svg"
                    print(f'looking for {infile}: ', end = '')
                    if os.path.isfile(infile):
                        print(f"converting to {outPath}/{systemId.name}.logo.png", end='')
                        if not dryrun:
                            if systemId.name in _SYSTEMS_NEED_LIGHT_BG:
                                print(" (light b/g)", end='')
                                _convertTOPNGLightBackground(infile, f"{outPath}/{systemId.name}.logo.png")
                            else:
                                _convertToPNG(infile, f"{outPath}/{systemId.name}.logo.png")
                        # found a logo: no need to look further for this system
                        print('')
                        break
                    else:
                        print(f"not found")
        it.close()


def convertDanPatrick(inPath: str, outPath: str, dryrun: bool = False) -> None:
    '''Convert SVG files in inPath/[category] to PNG and place them in outPath/[category]'''
    CATEGORIES: List[str] = ['publisher', 'system']

    for cat in CATEGORIES:
        # scan inPath/cat/
        with os.scandir(f"{inPath}/{cat}") as it:
            print(f"Scanning directory {inPath}/{cat}")
            for image in it:
                if image.is_file() and image.name.endswith(".svg"):
                    # strip .svg extension & force lower case
                    basename: str = os.path.splitext(image.name)[0].lower()
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

                    outFullPath: str = getUniqueFilename(f"{outPath}/{cat}", basename, 'png')
                    print(f"converting '{inPath}/{cat}/{image.name}' -> {outFullPath}")
                    if not dryrun: _convertToPNG(
                        infile = f"{inPath}/{cat}/{image.name}",
                        outfile = outFullPath
                    )
        it.close()


def getUniqueFilename(dir: str, basename: str, ext: str) -> str:
    '''Compute a unique file name to ensure we don't overwrite existing files
        :param str dir: target directory
        :param str basename: base name of the file without extension
        :param str ext: file extension
        :returns str: full path to a non-existing file in the target directory
    '''
    index: int = 1
    outPath: str
    while True:
        # add index to end of output filename unless this is only file with that name
        if index == 1:
            outPath = f"{dir}/{basename}.{ext}"
        else:
            outPath = f"{dir}/{basename}_{index:02}.{ext}"
        if not os.path.exists(outPath):
            # found a unique output filename: stop searching
            break
        else:
            # increment index and try again
            index += 1
    logging.debug(f"getUniqueFilename({dir}, {basename}, {ext}) -> {outPath}")
    return outPath


### main ###
if __name__ == '__main__':
    # BASEDIR = top-level project directory
    BASEDIR: str = os.path.dirname(__file__)
    logging.debug(f"BASEDIR={BASEDIR}")

    convertTheme(
        inPath = f"{BASEDIR}/artwork/recalbox-next",
        outPath = f"{BASEDIR}/media/system",
        dryrun = False
    )

    # convertDanPatrick(
    #     inPath = f"{BASEDIR}/artwork/Dan_Patrick_v2_platform_logos",
    #     outPath = f"{BASEDIR}/media",
    #     dryrun = True
    # )
