![digimarquee startup image][project-image]
# digimarquee
A dynamic digital marquee for [Recalbox]


> **TODO**:
> - make banner without Recalbox logo and ghost
> - add video of it working?

## Contents
- [About digimarquee](#about-digimarquee)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [To Do](#to-do)
- [Licence](#licence)


---

## About digimarquee

### What Is It?
A program to run a digital marquee for [Recalbox] on a second display connected via HDMI, similar to the [PiMarquee2][pimarquee2] project for [Retropie][retropie].

### Why?
I was building a bartop arcade machine and I wanted to have a dynamic marquee which could change depending on which game system was selected and which game was being played.

I knew I wanted my arcade to run [Recalbox] and I already had a Pi4 to run it on. As the Pi4 has dual HDMI outputs I wanted to drive the marquee from the second HDMI output. 

The marquee display I had in mind was an [ultrawide 19" 1920x360 LED panel][DV190FBM] which is the perfect size for my build. Unfortunately it's quite expensive so I may have to settle for a [cheaper 14.9" TN panel][LTA149B780F] available from Amazon or ebay.

For testing I used a spare 19" TV running at 720p resolution.

This project is my attempt to get a dynamic marquee working with [Recalbox].

### Goals
I wanted a solution which would be:
- minimal: work with Recalbox's environment, ideally needing no extra software to be installed
- flexible: allow most settings to be changed via a config file
- reactive: change the marquee in response to user actions


### Requirements
- [Recalbox] v8.1.1 Electron or later
- a Raspberry [Pi 4B][pi4] or [Pi400][pi400] with dual HDMI outputs
- a second display connected to the Pi's second HDMI port

It should be possible to get *digimarquee* running on a separate device (e.g. a [Pi Zero][pi-zero]) that just drives the marquee.
You would need to tweak Recalbox's MQTT setup to allow incoming connections from the local network.

> **TODO**:
> - try it out, provide instructions
> - which file to edit


### How Does It Work?
It works very like [Recalbox]'s built-in mini TFT support:
it writes direct to the framebuffer using `fbv2` for still images and `ffmpeg` for videos.

With the Pi4's default KMS graphics driver both HDMI displays share a single framebuffer, so marquee images are also visible on the primary display for a second or two when Emulation Station launches an emulator.

While this is a bit annoying, it doesn't seem to break anything so I'm happy enough with it.

*digimarquee* is mostly written in Python3.

---

## Getting started
Steps to get *digimarquee* running on Recalbox:

- download the latest project release (**TODO**: link here)
- extract the archive and copy it to your Recalbox
  - ftp or rsync
  - or direct to SD card
  - files live in `/recalbox/share/digimarquee`
- copy init script `S32digimarquee` to `/etc/init.d` and make it executable
- reboot

>  **TODO**:
>  - provide a setup script
>  - probably best to ssh into pi, `wget` archive and run setup script

Releases include some media files to get started (see [acknowledgements](#acknowledgements)) but is not a complete set. See the [media README][media-readme] for suggestions of where to find media files.


## Usage
Most settings can be configured in the config file [`digimarquee.config.txt`](digimarquee.config.txt).

For each [EmulationStation][emulationstation] action, the config file defines a search precedence rule: an ordered list of search terms indicting where to search for media files.

If no files match a search term *digimarquee* moves on to the next term.
That way you can specify which media files to show in order of priority.

For example, when an arcade game is launched, we can get *digimarquee* to:
1. search for the game's marquee image
1. if not found, search for the game publisher's banner
1. if not found, search for a generic arcade banner

For full details please see the comments in the `[media]` section of the config file [`digimarquee.config.txt`](digimarquee.config.txt).

All media files that match a successful search term are displayed in a random order as a slideshow that loops continuously. How long each image or video is shown can be adjusted in the `[slideshow]` section of the config file.


### Filename Matching
Searching for media files works as follows:

1. Names of games, publishers and genres are converted to lower case, and spaces are converted to dots.
    - e.g. `Sonic The Hedgehog` becomes `sonic.the.hedgehog`


> **TODO**: 
> should spaces be converted? Everwhere else in Recalbox e.g. p2k config the name without extension is used. Could just make glob match case-insensitive?


1. Names are then matched against the beginning of media filenames.
    - e.g. a ROM named `Chuckie Egg.zip` would match media files named `chuckie.egg.*`
    - a game published by `Atari` would match files named `atari.*`


### Adding Your Own Images And Videos
By default marquee media files live in `/recalbox/share/digimarquee/media`.
If for some reason you want to store them somewhere else, change the `base_path` setting in the `[media]` section of the config file.

Place your media files in the appropriate subdirectory (look at the included files for examples):

- *game-specific* media go in the appropriate system directory
    - e.g. for the arcade version of [Defender], put your file in `mame/` & name it `defender.<something>` e.g. `defender.01.png`

- `system/` is for game system media (e.g. console logos);
the file name must start with EmulationStation's internal system name (use the same names as in `/recalbox/share/roms/`)
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

Bug reports/fixes, improvements, documentation, & translations are also welcome.


## Acknowledgements
For convenience, releases include some starter images collected from various sources.
These are not my  work: credit remains with the original authors.
See the [artwork README file][artwork-readme] for sources.


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
[pimarquee2]: https://github.com/losernator/PieMarquee2
[project-image]: media/startup/startup.01.png
[recalbox]: https://www.recalbox.com
[retropie]: https://retropie.org.uk/
[spectrum]: https://en.wikipedia.org/wiki/ZX_Spectrum