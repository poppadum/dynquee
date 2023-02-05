<!-- PROJECT LOGO -->
<div align="center">

![digimarquee startup image][project-image]
# digimarquee
A digital marquee for [Recalbox]

</div>


## Contents
- [Contents](#contents)
- [About digimarquee](#about-digimarquee)
- [Getting started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [To Do](#to-do)
- [Licence](#licence)


---

## About digimarquee

### What Is It?
A program to run a digital marquee for [Recalbox] on a second display connected via HDMI

### Why?
I was building a bartop arcade machine and I wanted to have a dynamic marquee which could change depending on what game system was selected and what game was being played.

I knew I wanted my arcade to run [Recalbox] and I already had a Pi4 to run it on. As the Pi4 has dual HDMI outputs I wanted to drive the marquee from the second HDMI output. 

The marquee display I had in mind was an [ultrawide 19" 1920x360 LED panel][DV190FBM] which is the perfect size for my build. Unfortunately it was a bit expensive so I settled for a [cheaper 14.9" TN panel][LTA149B780F] available on Amazon and ebay.

This project is my (more or less successful) attempt to get my digital marquee up and running.

### Goals
- work with Recalbox's installed software
- flexible: allow most settings to be changed via a config file
- reliable


### Requirements
- [Recalbox]
- a Raspberry [Pi 4B][pi4] or [Pi400][pi400] with dual HDMI outputs
- a second display for your marquee connected to the Pi's second HDMI port

It should be possible to get *digimarquee* running on a separate device (e.g. a [Pi Zero][pi-zero]) that just drives the marquee.
You will need to tweak Recalbox's MQTT setup to allow incoming connections from the local network.

**TODO**:
- try it out, provide instructions
- which file to edit


### How Does It Work?
It works very like [Recalbox]'s built-in mini TFT support:
it writes direct to the framebuffer using `fbv2` for still images and `ffmpeg` for videos.

With the Pi4's KMS graphics driver (which Recalbox v8.1.1 uses), both HDMI displays share a single framebuffer, so marquee images are also visible on the primary display when Emulation Station launches an emulator.

It's a bit of a kludge but it doesn't seem to break anything so I'm happy enough with it.

*digimarquee* is mostly written in [Python](https://www.python.org/)3 with a couple of helper shell scripts.

---

## Getting started
Steps to get *digimarquee* running on Recalbox:

- download the latest project release (**TODO**: link here)
- copy to your Recalbox
  - ftp or rsync
  - files live in `/recalbox/share/digimarquee`
- copy init script `S32digimarquee` to `/etc/init.d`
- reboot

**TODO**: provide a setup script?

Releases include some media files to get started (see [acknowledgements](#acknowledgements)) but is not a complete set. See the [media README][media-readme] for suggestions of where to find media files.


## Usage
Most settings can be configured in the config file [`digimarquee.config.txt`](digimarquee.config.txt).

For each [EmulationStation][emulationstation] action, the config file defines a search precedence rule: an ordered list of where to search for media (called `chunks` - must be a better name for this).

If no files match a search chunk *digimarquee* moves on to next chunk.
That way you can specify which media files to show in order of priority.

For example, when an arcade game is launched, we can get *digimarquee* to:
1. search for the game's marquee
1. if not found, search for the game's publisher's banner
1. if not found, search for a generic arcade banner

For full details please see the `[media]` section of the config file [`digimarquee.config.txt`](digimarquee.config.txt)


### Filename Matching
Searching for media files works as follows:

1. Names of games, publishers and genres are converted to lower case, and spaces are converted to dots.
    - e.g. `Sonic The Hedgehog` becomes `sonic.the.hedgehog`


**TODO**: should spaces be converted? Everwhere else in Recalbox e.g. p2k config the name without extension is used.


1. Names are then matched against the beginning of media filenames.
    - e.g. a ROM named `Chuckie Egg.zip` would match media files named `chuckie.egg.*`
    - a game published by `Atari` would match files named `atari.*`


### Adding Your Own Images And Videos
By default marquee media files live in `/recalbox/share/digimarquee/media`.
If for some reason you want to store them somewhere else, change the `base_path` setting in the `[media]` section of the config file.

Place your media files in the appropriate subdirectory (look at the included files for examples):

- game-specific media go in the appropriate system directory
    - e.g. for the arcade version of [Defender], put your file in `mame/` & name it `defender.<something>` e.g. `defender.01.png`

- `system/` is for game system media (e.g. console logos);
the file name must start with EmulationStation's internal system name (use the same name as in `/recalbox/share/roms/`)
    - e.g. for a [Sinclair Spectrum][spectrum] logo, name the file `zxspectrum.<something>` e.g. `zxspectrum.logo.png`

- `publisher/` is for publisher banners & logos

- `startup/` is for files shown when digimarquee first starts up e.g. a welcome banner

- `generic/` is for media that doesn't belong anywhere else, to be used if no other files match


### File Format Support
You can use any file format supported by [`fbv2`][fbv] or [`ffmpeg`][ffmpeg].
I recommend `png` for still images, and `mp4` or `mkv` for video clips.
Media is resized to fit the screen but the closer you can match the aspect ratio and resolution of your marquee display the better it will look.

---

## Contributing
Contributions of suitable marquee images and video clips are welcome.
Please include links to the originals so I can acknowledge the creator.

Bug fixes, improvements, documentation, & translations welcome.


## Acknowledgements
For convenience I have included some starter images collected from various sources.
These are not my own work: credit remains with the original authors.
See the [artwork README file][artwork-readme] for full details of where I got them.


## To Do
- [ ] Genre matching is very dumb: make it more intelligent. Is there a master list of genres that EmulationStation uses somewhere?

---

## Licence
TBD

BSD Licence - do what you like?


<!-- LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[artwork-readme]: artwork/README.md
[Defender]: https://en.wikipedia.org/wiki/Defender_(1981_video_game)
[DV190FBM]: https://www.panelook.com/DV190FBM-NB0_BOE_19.1_LCM_overview_32860.html
[emulationstation]: https://wiki.recalbox.com/en/basic-usage/getting-started/emulationstation
[fbv]: https://github.com/godspeed1989/fbv
[ffmpeg]: https://ffmpeg.org/
[LTA149B780F]: https://www.panelook.com/LTA149B780F_Toshiba_14.9_LCM_parameter_10941.html
[media-readme]: media/README.md
[pi4]: https://www.raspberrypi.com/products/raspberry-pi-4-model-b/
[pi400]: https://www.raspberrypi.com/products/raspberry-pi-400-unit/
[pi-zero]: https://www.raspberrypi.com/products/raspberry-pi-zero/
[project-image]: media/startup/startup.01.png
[recalbox]: https://www.recalbox.com
[spectrum]: https://en.wikipedia.org/wiki/ZX_Spectrum
