# Change Log

## v0.9.8

- Added support for new games systems in Recalbox v9.1
- Media file matching is now case-insensitive  
  e.g. a rom named `Star Wars.zip` now matches media files named `star wars.*`
- Added config option `shuffle` (`[slideshow]` section) to control whether matching media are shown in a random order (`shuffle = yes`) or in sequential filename order
- Added config option `arcade_system_enabled` (`[media]` section) to treat all arcade systems as a single 'arcade' meta-system
- Added link to a short demo video in the README
- Added more sources of marquee images to the media README file

### Fixes
- Fixed bugs in install scripts; improved PC script for locating display outputs
- Fixed bug in theme update script `artwork/update.sh`
- Fixed typo in artwork converter script `artwork/convert_artwork.py`
- Fixed malformed header block in RasPi manual install instructions

### Other Changes
- Documentation improvements
- Installation script improvements
- Refactored artwork converter script
- Renamed remote install script for consistency
- systemd unit file (for remote machine use) now starts program with `python3 -m dynquee`
- Code linting fixes


## v0.9.7
New feature: can now show media files while screensaver active (configurable)


### Changes
- PC config file uses `--quiet` option to `mpv` to reduce log noise

#### Documentation improvements
- add Changelog
- add Discord link to help section of README
- manual install instructions: add step to remove release ZIP file
- update `install/README.md` and `media/README.md`


## v0.9.6
Add support for Recalbox on PC

### PC Support
- README applies to RasPi & PC
- update install script to detect if we're installing on Raspberry Pi or PC
- add manual install guide for PC
- add script to assist user finding video outputs
- add PC-specific config file
- update 'after upgrade' instructions

### Other Changes
- include all docs in releases
- init script: start program with python3 -m dynquee
- make scaled video play script executable


## v0.9.5 pre-release
### Additions
- add support for running on a non-Recalbox machine
- add support for compound search rules
- add console images from recalbox-next theme
- add startup images
- add config file entry to control time between files in slideshow


### Fixes
- install script: add link to latest release
- interpolation in config files was broken

- event handling
    - now stores ES state before sleep, restores on wakeup
    - event after 'endgame' now always changes state
        - was not seeing a state change when a game exited and
            `gamelistbrowsing` change rule was `system/game`

- slideshow fixes:
    - now clears marquee screen when a video exits
    - was starting next slideshow before current slideshow had exited
    - now moves to next file when video finishes
        - uses `WaitableEvent` class by [Radek Lát](https://lat.sk)
    - single image slideshow was calling viewer many times per second

### Changes
- make default marquee size 1280x360
- config file now defines one media change rule per action
- add bash helper script to play videos scaled to marquee size
- artwork:
    - fix incorrect system name: `oric` -> `oricatmos`
- add BUILD file to release archive to identify installed version
- improve log output
- move install & init scripts to `install/`
- exits with non-zero return code on uncaught exception

#### Documentation improvements
- add local & remote install script URLs to README.md
- much more detailed comments in config file
- document how to restore init script after Recalbox upgrade
- add explanation of media scaling to configuration guide


## v0.9.4 pre-release

## v0.9.3 pre-release
