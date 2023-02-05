<!-- PROJECT LOGO -->
<div align="center">

![digimarquee startup image][project-image]
# digimarquee

A gigital marquee for [Recalbox]
</div>



- Explore the docs »
- View demo video
- [Report bug](issues/)


<!-- contents -->
## Contents
- [About digimarquee](#about-digimarquee)
- [Getting Started](#getting-started)
- [Usage](#usage)

---

## About digimarquee

### What Is It?
A program to run a digital marquee for [Recalbox] on a second display connected via HDMI

### Why?
I was building a bartop arcade machine I wanted to have a digital marquee which could change depending on what game system was selected and what game was being played.

I knew I wanted my arcade to run [Recalbox] and I already had a Pi4 to run it, and as the Pi4 has dual HDMI outputs it seemed a good idea to drive the marquee from the second HDMI output. 

The marquee display I had in mind was an [ultrawide 19" 1920x360 LED panel][DV190FBM] which is the perfect size for my build. Unfortunately it was a bit expensive so I settled for a [cheaper 14.9" TN panel][LTA149B780F] available on Amazon and ebay.

This project is my (more or less successful) attempt to get my digital marquee up and running.


### Requirements
- [Recalbox]
- Raspberry Pi4 or 400 with dual HDMI outputs
- a second display for your marquee connected to the Pi's HDMI2 port

It should be possible to get digimarquee running on a separate device (e.g. a Pi Zero) that just drives the marquee.
You will need to tweak Recalbox's MQTT setup to allow connections from the local network.

**TODO**: give link, more info.


### Built With
* mostly written in [Python 3 <img src="https://s3.dualstack.us-east-2.amazonaws.com/pythondotorg-assets/media/community/logos/python-logo-only.png" width="30">](https://www.python.org/)
* a few bash scripts


- works very like built in TFT support
- `fbv2` for stills, `ffmpeg` for videos
- writes to framebuffer

### Warnings
Pi4 with kms overlay, both displays share single framebuffer
so writing marquee to fb bit of a kludge
also visible on main screen when ES launches an emulator
doesn't seem to break anything so I'm happy

---

## Getting started
How to get digimarquee running on Recalbox

- download project
- copy to your Recalbox
    - ftp or rsync
- files live in `/recalbox/share/digimarquee`
- copy init script `S32digimarquee` to `/etc/init.d`
- reboot

**TODO**: provide a setup script?

Includes some media files I've collected
Could do with more

## Usage
Most things configurable in config file `digimarquee.config.txt`

For each ES action, defines a search rule: ordered list of where to search for media (called `chunks` - must be a better name for this).

If no files match that search chunk, moves on to next chunk.
So can have priority search rule e.g. for an arcade game:
- try game marquee
- if not found, try to find game publisher banner
- if not found, try to find generic arcade banner

**TODO**: refer to config file? Prob best to include here


### Search
How does search work?
- names converted to lower case, spaces => dots
    - e.g. `Sonic The Hedgehog` becomes `sonic.the.hedgehog`
- matches beginning of media filename
    - e.g. for ROM-specific media, game='Chuckie Egg', searches for files matching `chuckie.egg.*`


### Adding Your Own Images And Videos
- by default media files go in `/recalbox/share/digimarquee/media`
    - set in config file: `base_path` in `[media]` section
- put your media file in correct subdirectory
- look at included files for naming examples


- game-specific media in appropriate subdir of base_path
    - e.g. for arcade version of [Defender], put it in `mame/`
    - name it `defender.*` e.g. `defender.01.png`
- `system/`: game system logos
    - file name must start with ES's internal system name (same as in `/recalbox/share/roms/`)
    - e.g. for [Sinclair Spectrum][spectrum] name file `zxspectrum.*` e.g. `zxspectrum.logo.png`
- `publisher/`: publisher banners & logos
- `startup/`: media used when digimarquee first starts up. Can be used for e.g. a welcome banner.
- `generic/`: media that doesn't belong anywhere else, to be used if no other media matches


### File Formats Supported
- png
- mp4, mkv

---

## Contributing
- images/video welcome
- please include source so I can acknowledge the creator



## Acknowledgments
This project includes images collected from various sources.
These are not my work: credit goes to the original authors.
See the [artwork README file][artwork-readme] for full details.


## To Do
Genre matching is very dumb


## Licence
BSD Licence - do what you like?


<!-- LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[artwork-readme]: artwork/README.md
[Defender]: https://en.wikipedia.org/wiki/Defender_(1981_video_game)
[DV190FBM]: https://www.panelook.com/DV190FBM-NB0_BOE_19.1_LCM_overview_32860.html
[media-readme]: media/README.md
[project-image]: media/startup/startup.01.png
[recalbox]: https://www.recalbox.com
[spectrum]: https://en.wikipedia.org/wiki/ZX_Spectrum
[LTA149B780F]: https://www.panelook.com/LTA149B780F_Toshiba_14.9_LCM_parameter_10941.html