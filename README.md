#
![dynquee: dynamic marquee for Recalbox][project-image]  \
A dynamic digital marquee for [Recalbox]
#

<!-- **TODO**: add demo video of it working? -->

## Contents
- [About dynquee](#about-dynquee)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [To Do](#to-do)
- [Licence](#licence)

---

## About dynquee

### What Is It?
*dynquee* (pronounced '[dinky][dinky-definition]') is a program to run a dynamic marquee for [Recalbox] on a second display connected via HDMI, similar to the [PiMarquee2][pimarquee2] project for [Retropie][retropie]. The name stands for **dyn**amic mar**quee**.

### Why?
I'm building a bartop arcade machine and I want to have a dynamic marquee which can change depending on which game system is selected and which game is being played.

I want to use [Recalbox] to run the machine and I already have a [Raspberry Pi 4][pi4] to run it on. As the Pi4 has dual HDMI outputs I want to drive the marquee from the second HDMI output. 

The marquee display I've had in mind is an [ultrawide 19" 1920x360 LED panel][DV190FBM] which is the ideal size for my build. Unfortunately it's quite expensive so I may have to settle for a [cheaper 14.9" TN panel][LTA149B780F] available from Amazon or ebay.

For testing I used a spare 19" TV running at 720p resolution.

This project is the result of my attempts to get a dynamic marquee working with [Recalbox].

### Goals
I wanted a solution which would be:

- fairly lightweight: work with Recalbox's environment, ideally needing no extra software to be installed
- flexible: allow most settings to be changed via a config file
- reactive: change the marquee in response to user actions


### Requirements
- [Recalbox] v8.1.1 Electron or later
- a Raspberry [Pi 4B][pi4] or [Pi 400][pi400] with dual HDMI outputs
- a second display connected to the Pi's second HDMI port

It should be possible to get *dynquee* running on a separate device (e.g. a [Pi Zero][pi-zero]) that just drives the marquee.
You would need to tweak Recalbox's MQTT config to allow incoming connections from the local network.

<!--
**TODO**:
- try it out, provide instructions
- which file to edit
-->

### How Does It Work?
It works very like [Recalbox]'s built-in mini TFT support: 
it listens to [Recalbox's MQTT server][recalbox-mqtt] for events, and it writes media files direct to the framebuffer using `fbv2` for still images and `ffmpeg` for videos.

With the Pi4's default KMS graphics driver both HDMI displays share a single framebuffer, so marquee images are also visible on the primary display for a second or two when an emulator launches or exits. While this is a bit annoying, it doesn't seem to break anything so I'll put up with it.

*dynquee* is mostly written in Python3.

---

## Getting Started
Steps to get *dynquee* running on Recalbox:

>  **TODO**: get a permalink to latest release on github

1. Connect to your recalbox with `ssh`: see [Recalbox wiki][recalbox-ssh]
1. Copy and paste this command and press enter:  
    `wget -o dynquee.zip <dynquee-release> && unzip dynquee.zip && bash install.sh`
1. If all goes well you should see the `Installation complete` message


Releases include a few media files to get started (see [acknowledgements](#acknowledgements)) but not a complete set. See the [media README][media-readme] for suggestions of where to find media files.


## Usage
Most settings can be configured in the config file [`dynquee.ini`](dynquee.ini).

For each [Emulation Station][emulationstation] action, the config file defines a search precedence rule: an ordered list of search terms indicating where to search for media files.

If no files match a search term *dynquee* moves on to the next term.
That way you can specify which media files to show in order of priority.

For example, when an arcade game is launched, *dynquee* can:
1. search for the game's marquee image
1. if not found, search for the game publisher's banner
1. if not found, search for a generic arcade banner

For full details see the comments in the `[media]` section of the config file [`dynquee.ini`](dynquee.ini).

All media files that match a successful search term are displayed in a random order as a slideshow that loops continuously. How long each image or video is shown can be adjusted in the `[slideshow]` section of the config file.


### Filename Matching
Media file matching works as follows:

1. ROM filenames have their file extension (everything after the last `.`) removed
    - e.g. `Sonic The Hedgehog.zip` becomes `Sonic The Hedgehog.`

1. Names of publishers and genres are converted to lower case and a dot is added to the end
    - e.g. `Data East` becomes `data east.`

1. Names are then matched against the beginning of media filenames.
    - e.g. a ROM named `Chuckie Egg.zip` would match media files named `chuckie egg.*`
    - or a game published by `Bally Midway` would match files named `bally midway.*`


### Adding Your Own Images And Videos
By default marquee media files live in `/recalbox/share/dynquee/media`.
If for some reason you want to store them somewhere else, change the `media_path` setting in the `[media]` section of the config file.

Place your media files in the appropriate subdirectory (look at the included files for examples):

- *game-specific* media go in the appropriate system directory
    - e.g. for the arcade version of [Defender] with a ROM named `defender.zip`, put your file in `mame/` & name it `defender.<something>` e.g. `mame/defender.01.png`

- `system/` is for game system media (e.g. console logos);
the file name must start with Emulation Station's internal system name (use the same names as in `/recalbox/share/roms/`)
    - e.g. for a [Sinclair ZX Spectrum][spectrum] logo, name the file `zxspectrum.<something>` e.g. `system/zxspectrum.logo.png`

- `publisher/` is for publisher banners & logos

- `startup/` is for files to show when *dynquee* first starts up e.g. a welcome banner

- `generic/` is for media that doesn't belong anywhere else, to be used if no other files match


### File Format Support
You can use any file format supported by [`fbv2`][fbv] or [`ffmpeg`][ffmpeg].
I recommend `png` for still images, and `mp4` or `mkv` for video clips.
Media is resized to fit the screen but the closer you can match the aspect ratio and resolution of your marquee display the better it will look.


### Starting & Stopping *dynquee* Manually
You can start, stop or restart *dynquee* (for example, to force it to reload the config file) by typing:
`/etc/init.d/S32dynquee start|stop|restart|status`

---

## Contributing
Bug reports/fixes, improvements, documentation, & translations are also welcome.


## Acknowledgements
For convenience, releases include some starter images collected from various sources.
These are not my  work: credit remains with the original authors.
See the [artwork README file][artwork-readme] for sources.


## To Do
- [ ] Genre matching is very dumb: make it more useful. Is there a master list of genres that [Emulation Station][emulationstation] uses somewhere?

---

## Licence
This project is released under the [MIT Licence][licence].


<!-- LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[artwork-readme]: artwork/README.md
[Defender]: https://en.wikipedia.org/wiki/Defender_(1981_video_game)
[dinky-definition]: https://dictionary.cambridge.org/dictionary/english/dinky
[DV190FBM]: https://www.panelook.com/DV190FBM-NB0_BOE_19.1_LCM_overview_32860.html
[emulationstation]: https://wiki.recalbox.com/en/basic-usage/getting-started/emulationstation
[fbv]: https://github.com/godspeed1989/fbv
[ffmpeg]: https://ffmpeg.org/
[licence]: LICENSE.txt
[LTA149B780F]: https://www.panelook.com/LTA149B780F_Toshiba_14.9_LCM_parameter_10941.html
[media-readme]: media/README.md
[pi4]: https://www.raspberrypi.com/products/raspberry-pi-4-model-b/
[pi400]: https://www.raspberrypi.com/products/raspberry-pi-400-unit/
[pi-zero]: https://www.raspberrypi.com/products/raspberry-pi-zero/
[pimarquee2]: https://github.com/losernator/PieMarquee2
[project-image]: dynquee.png
[recalbox]: https://www.recalbox.com
[recalbox-mqtt]: https://wiki.recalbox.com/en/advanced-usage/scripts-on-emulationstation-events#mqtt
[recalbox-ssh]: https://wiki.recalbox.com/en/tutorials/system/access/root-access-terminal-cli
[retropie]: https://retropie.org.uk/
[spectrum]: https://en.wikipedia.org/wiki/ZX_Spectrum
