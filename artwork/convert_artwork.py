#!/usr/bin/env python3

"""Convert sourced artwork in SVG format to PNG, adding a border and coloured background if needed:
  1. Recalbox EmulationStation theme's system images
  2. Dan Patrick's v2 Platform Logos

Requirements:
- python module `cairosvg`
- ImageMagick `convert` binary
"""

import os
import logging
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import cairosvg  # type: ignore  # suppress mypy 'missing typehints for cairosvg' error

# Uncomment for DEBUG
#logging.basicConfig(level=logging.DEBUG)

class Converter:
    """Generic artwork converter class"""
    # preferred output sizing
    OUT_WIDTH: int = 1280
    OUT_HEIGHT: int = 360

    BORDER_WIDTH: int = 10
    BORDER_HEIGHT: int = 10

    # preferred region: eu, us or jp
    REGION:str  = 'eu'

    def __init__(self, inPath:str, outPath: str, dryrun: bool = False):
        self._dryrun = dryrun
        self._inPath = inPath
        self._outPath = outPath

    def convertToPNG(self, infile: str, outfile: str):
        '''Convert infile to PNG format and write to outfile'''
        logging.debug("convertToPNG infile=%s outfile=%s", infile, outfile)
        cairosvg.svg2png(
            url = infile,
            write_to = outfile,
            output_width = self.OUT_WIDTH - (self.BORDER_WIDTH * 2),
            output_height = self.OUT_HEIGHT - (self.BORDER_HEIGHT * 2),
        )

    @classmethod
    def addBorder(cls,
        file: str,
        borderWidth: int = BORDER_WIDTH,
        borderHeight: int = BORDER_HEIGHT
    ):
        '''Add a transparent border around an image'''
        cmd: List[str] = [
            '/usr/bin/convert',
            file,
            '-bordercolor', 'none',
            '-border', f'{borderWidth}x{borderHeight}',
            file
        ]
        logging.debug("cmd=%s", cmd)
        subprocess.run(cmd, check=True)


class ThemeConverter(Converter):
    """Converter for theme artwork"""

    # light background colour
    LIGHT_BG_COLOUR: str = '#555'

    # system directories to skip: virtual systems
    _SKIP_SYSTEMS: List[str] = [
        '240ptestsuite', 'auto-allgames', 'auto-arcade-capcom', 'auto-lastplayed', 'auto-lightgun',
        'auto-multiplayer', 'auto-tate', 'default', 'favorites', 'imageviewer'
    ]

    # Recalbox-next logos & console images requiring a light background
    _SYSTEMS_NEED_LIGHT_BG: Dict[str, List[str]] = {
        'logo': [
            '3ds', 'amiga600', 'amiga1200', 'amigacd32', 'amigacdtv', 'amstradcpc',
            'apple2gs', 'atari800', 'atomiswave', 'bbcmicro', 'cavestory', 'cdi', 'channelf',
            'dragon', 'dreamcast', 'fds', 'gameboy', 'gamegear', 'gc', 'gw', 'intellivision',
            'kodi', 'macintosh', 'mame', 'moonlight', 'msx2', 'msxturbor', 'naomi', 'naomigd',
            'nds', 'neogeo', 'neogeocd', 'nes', 'odyssey2', 'palm', 'pc88', 'pc98',
            'pcenginecd', 'pcfx', 'pokemini', 'ports', 'ps2', 'ps3', 'psp', 'psx',
            'satellaview', 'supervision', 'ti994a', 'to8', 'vg5000', 'vic20', 'wasm4',
            'wonderswan', 'x1', 'zxspectrum', 'zmachine',
        ],
        'console': [
            '64dd', 'amigacd32', 'amigacdtv', 'amstradcpc', 'atari2600', 'atari5200',
            'atari7800', 'bk', 'channelf', 'colecovision', 'gamegear', 'intellivision',
            'jaguar', 'kodi', 'lynx', 'mastersystem', 'megadrive', 'model3', 'moonlight',
             'msx1', 'msx2', 'n64', 'neogeo', 'neogeocd', 'odyssey2', 'openbor', 'ps2', 'ps3',
            'psp', 'saturn', 'sega32x', 'segacd', 'supergrafx', 'uzebox', 'vectrex',
            'vg5000', 'virtualboy', 'x68000', 'zx81', 'zxspectrum',
        ],
    }

    _SYSTEMS_TO_RENAME: List[Tuple[str, str]] = [
        ('oric', 'oricatmos'),
        ('pc', 'dos'),
        ('wonderswan', 'wswan'),
        ('wonderswancolor', 'wswanc'),
        ('odyssey2', 'o2em'),
        ('to8', 'thomson'),
    ]

    @classmethod
    def _changeImageBackground(cls, file: str, bgColour: str):
        '''Add a solid colour background to an image'''
        cmd: List[str] = [
            '/usr/bin/convert',
            file,
            '-background', bgColour,
            '-alpha', 'remove', '-alpha', 'off',
            file
        ]
        logging.debug("cmd=%s", cmd)
        subprocess.run(cmd, check=True)

    def convertThemeImage(self, systemId: str, suffix: str):
        '''Convert a single logo/console image to PNG with a border;
            change to light background if required
        '''
        infile: Optional[str] = self.searchRegion(systemId, suffix, self.REGION)
        if infile is None:
            logging.warning("no %s image found for system %s", suffix, systemId)
            return
        outFile = f"{self._outPath}/{systemId}.{suffix}.png"
        print(f"convert {systemId}.{suffix}.svg: ", end='')
        if not self._dryrun:
            self.convertToPNG(infile, outFile)
            self.addBorder(outFile)
            if (suffix == 'logo' and systemId in self._SYSTEMS_NEED_LIGHT_BG['logo']) \
                or (suffix == 'console' and systemId in self._SYSTEMS_NEED_LIGHT_BG['console']):
                print(" (light b/g)", end='')
                self._changeImageBackground(outFile, self.LIGHT_BG_COLOUR)
        print(': OK')

    def convertAll(self) -> None:
        '''Convert a theme's logo.svg & console.svg files to PNG and
            place them in outPath named [systemId].logo|console.png
        '''
        # Look through all first level directories in inPath
        with os.scandir(self._inPath) as itr:
            for systemId in itr:
                logging.debug("found system: %s", systemId.name)
                # skip non-directories and virtual systems
                if systemId.is_dir() and (systemId.name not in self._SKIP_SYSTEMS):
                    suffix: str
                    for suffix in ['logo', 'console']:
                        self.convertThemeImage(systemId.name, suffix)
            itr.close()
            self.fixFilenames()

    def searchRegion(self, systemId: str, suffix: str, region: str) -> Optional[str]:
        """Search for a console or logo image in the data/ directory and region subdirectories
            @return str full path to the first image file found, or None if no image was found
        """
        for directory in ["data", f"data/{region}"]:
            infile: str = f"{self._inPath}/{systemId}/{directory}/{suffix}.svg"
            if os.path.isfile(infile):
                return infile
        return None

    def fixFilenames(self) -> None:
        """Fix media filenames to match Recalbox internal system names"""
        oldname: str
        newname: str
        suffix: str
        for (oldname, newname) in self._SYSTEMS_TO_RENAME:
            for suffix in ['logo', 'console']:
                print(f"{oldname}.{suffix}.png => {newname}.{suffix}.png")
                if not self._dryrun:
                    os.rename(
                        f"{self._outPath}/{oldname}.{suffix}.png",
                        f"{self._outPath}/{newname}.{suffix}.png"
                    )


class DanPatrickConverter(Converter):
    """Converter for Dan Patrick's artwork"""
    CATEGORIES: List[str] = ['publisher', 'system']

    def convertAll(self) -> None:
        '''Convert SVG files in inPath/[category] to PNG and place them in outPath/[category]'''
        cat: str
        for cat in self.CATEGORIES:
            # scan inPath/cat/
            with os.scandir(f"{self._inPath}/{cat}") as itr:
                print(f"Scanning directory {self._inPath}/{cat}")
                for image in itr:
                    if image.is_file() and image.name.endswith(".svg"):
                        # strip .svg extension & force lower case
                        basename: str = os.path.splitext(image.name)[0].lower()
                        # replace brackets & dashes with dots
                        basename = re.sub(r'[()-]', '.', basename)
                        # strip non-standard characters ; : ,
                        basename = re.sub(r'[;:,]', '', basename)
                        # condense multiple dots to single dot
                        basename = re.sub(r'\.+', '.', basename)
                        # fixup names like "X classics" to "X.classics"
                        # so they match the bare publisher name
                        basename = re.sub(r'(\w+) +(classics|.old style.)', r'\1.\2', basename)
                        # prefix filenames starting with 'arcade' with 'mame'
                        # so they match Recalbox's systemId
                        if basename.startswith('arcade'):
                            basename = 'mame.' + basename
                        logging.debug("basename=%s", basename)

                        outFullPath: str = self.getUniqueFilename(cat, basename, 'png')
                        print(f"convert '{cat}.{basename}.png'")
                        if not self._dryrun:
                            self.convertToPNG(
                                infile = f"{self._inPath}/{cat}/{image.name}",
                                outfile = outFullPath
                            )
                            self.addBorder(outFullPath)
            itr.close()

    def getUniqueFilename(self, cat: str, basename: str, ext: str) -> str:
        '''Compute a unique file name to ensure we don't overwrite existing files
            :param str cat: category of image (publisher, system)
            :param str basename: base name of the file without extension
            :param str ext: file extension
            :returns str: full path to a non-existing file in the target directory
        '''
        index: int = 1
        outPath: str
        while True:
            # add index to end of output filename unless this is only file with that name
            if index == 1:
                outPath = f"{self._outPath}/{cat}/{basename}.{ext}"
            else:
                outPath = f"{self._outPath}/{cat}/{basename}_{index:02}.{ext}"
            if not os.path.exists(outPath):
                # found a unique output filename: stop searching
                break
            # increment index and try again
            index += 1
        logging.debug("getUniqueFilename(%s, %s, %s) -> %s", cat, basename, ext, outPath)
        return outPath


### main ###
if __name__ == '__main__':
    # BASEDIR = top-level project directory
    BASEDIR: Path = Path(__file__).resolve().parents[1]
    logging.debug("BASEDIR=%s", BASEDIR)

    tc: ThemeConverter = ThemeConverter(
        inPath = f"{BASEDIR}/artwork/recalbox-next",
        outPath = f"{BASEDIR}/media/system",
        dryrun = False
    )
    tc.convertAll()

    dpc: DanPatrickConverter = DanPatrickConverter(
        inPath = f"{BASEDIR}/artwork/Dan_Patrick_v2_platform_logos",
        outPath = f"{BASEDIR}/media",
        dryrun = False
    )
    dpc.convertAll()
