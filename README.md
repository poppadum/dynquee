![dynquee: dynamic marquee for Recalbox][project-image]  
A dynamic digital marquee for [Recalbox]
===


<!-- **TODO**: add photos / demo video of it working? -->

## Contents
- [About *dynquee*](#about-dynquee)
- [Getting Started](#getting-started)
    + [Quick Installation](#quick-installation)
    - [Manual Installation](#manual-installation)
- [Usage](#usage)
- [Help](#help)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [To Do](#to-do)
- [Licence](#licence)

---

## About dynquee

### What Is It?
*dynquee* (pronounced '[dinky][dinky-definition]') is a program to run a dynamic marquee for [Recalbox]. The name stands for **dyn**amic mar**quee**.

It was originally intended to run on a [Raspberry Pi 4B][pi4] with two displays, Recalbox using the primary display for games and *dynquee* driving a second display for the marquee, similar to the [PiMarquee2][pimarquee2] project for [Retropie][retropie]. But it can also run on a separate device and communicate with Recalbox via the network.

### Why?
I'm building a bartop arcade machine and I want to have a dynamic marquee which can change depending on which game system is selected and which game is being played.

I'm using [Recalbox] to run the machine on a [Raspberry Pi 4][pi4]. As the Pi4 has dual HDMI outputs I want to drive the marquee from the second HDMI output. 

The marquee display I have is an [ultrawide 19" 1920x360 LED panel][DV190FBM] which is the ideal size for my build. It was quite expensive and hard to obtain; another possiblity would be a [cheaper 14.9" TN panel][LTA149B780F] available from Amazon or ebay.

For testing I used a spare 19" TV running at 720p resolution.

This project is the result of my attempts to get a dynamic marquee working with [Recalbox].

### Goals
I wanted a solution which would be:

- fairly lightweight: work with Recalbox's environment, ideally needing no extra software to be installed
- flexible: allow most settings to be changed via a config file
- reactive: change the marquee in response to user actions


### How Does It Work?
It works very like [Recalbox]'s built-in mini TFT support: 
it listens to [Recalbox's MQTT broker][recalbox-mqtt] for events, and it writes media files direct to the framebuffer using `fbv2` for still images and `ffmpeg` for videos.

With the Pi4's default KMS graphics driver both HDMI displays share a single framebuffer, so marquee images are also visible on the primary display for a second or two when an emulator launches or exits. While this is a bit annoying, it doesn't seem to break anything so I'll put up with it.

*dynquee* is mostly written in Python 3.


### Requirements
- [Recalbox] v8.1.1 Electron or later
- Python v3.7 or later (Recalbox 8.1.1 ships with Python v3.9.5)
- EITHER:
    - a Raspberry [Pi 4B][pi4] or [Pi 400][pi400] with a second display connected to the Pi's second HDMI port
- OR:
    - a separate device with a connected display: an older Pi or [Pi Zero][pi-zero] should be ideal

I have tested *dynquee* running on a different device on the same network as the Recalbox machine.
It works fine but needs a few config file changes: see [Running *dynquee* on a different device][different-device].

---

## Getting Started

To get *dynquee* running on your Recalbox follow the instructions below.

To get *dynquee* running on a different machine see [the separate instructions here][different-device].

Releases include a few media files to get started (see [acknowledgements](#acknowledgements)) but not a complete set. See the [media README][media-readme] for suggestions of where to find media files.


### Quick Installation

Follow these steps to install *dynquee* using the install script:

>  **TODO**: get a permalink to latest release on github

1. Connect to your recalbox with `ssh` (the [Recalbox wiki][recalbox-ssh] explains how)
1. Copy and paste this command and press enter:  
    ```sh
    bash -c "$(wget -qO - https://github.com/poppadum/dynquee/raw/main/install/install.sh)"
    ```
1. If all goes well you should see the *Installation complete* message


### Manual Installation
If you prefer to install everything manually, follow these steps. 

<details>
<summary>Click to expand full instructions:</summary>

#### Download
1. Create the *dynquee* directory: `mkdir -p /recalbox/share/dynquee`
1. Change to that directory: `cd /recalbox/share/dynquee`
1. Download the *dynquee* release and unzip it:  
     ```sh
     wget https://github.com/poppadum/dynquee/releases/latest/download/dynquee.zip
     unzip dynquee.zip
     ```

#### Test
Try running the command `python3 dynquee.py`. If all goes well, you should see the startup image on your marquee display. Check that it responds to Recalbox actions by selecting a game system: the marquee should change to the logo or console image of that system.

Press Ctrl+C to stop the program.

If it doesn't work as expected, check the log files in the `logs/` directory:  
- `logs/dynquee.log` contains the summary log
- `logs/dynquee.debug.log` contains the full debug log

If you've checked the logs and still can't see what's wrong, see the [help section](#help).


#### Run At Startup
1. To get *dynquee* to run automatically at startup, remount the root filesystem read/write and copy the init script to `/etc/init.d/`:

    ```sh
    mount -o rw,remount /
    cp install/S32dynquee /etc/init.d/
    chmod +x /etc/init.d/S32dynquee
    mount -o ro,remount /
    ```
    
1. Check that *dynquee* can be started with:  

    ```sh
    /etc/init.d/S32dynquee start
    ```
</details>

---

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
    - e.g. a ROM named `Chuckie Egg.zip` would match media files named `Chuckie Egg.*`
    - or a game published by `Bally Midway` would match files named `bally midway.*`


### Adding Your Own Images And Videos
By default marquee media files live in `/recalbox/share/dynquee/media`.
If for some reason you want to store them somewhere else, change the `media_path` setting in the `[media]` section of the config file.

Place your media files in the appropriate subdirectory (look at the included files for examples):

- *game-specific* media go in the appropriate system directory
    - e.g. for the arcade version of [Defender] with a ROM named `defender.zip`, put your media file in `mame/` and name it `defender.<something>` e.g. `mame/defender.01.png`

- `system/` is for game system media (e.g. console banners and logos);
the file name must start with Emulation Station's internal system name (use the same names as in `/recalbox/share/roms/`)
    - e.g. for a [Sinclair ZX Spectrum][spectrum] logo, name the file `zxspectrum.<something>` e.g. `system/zxspectrum.logo.png`

- `publisher/` is for publisher banners & logos

- `startup/` is for files to show when *dynquee* first starts up e.g. a welcome banner or video

- `generic/` is for media that doesn't belong anywhere else, to be used if no other files match


### File Format Support
You can use any file format supported by [`fbv2`][fbv] or [`ffmpeg`][ffmpeg].
I recommend `png` for still images, and `mp4` or `mkv` for video clips.
Media is resized to fit the screen but the closer you can match the aspect ratio and resolution of your marquee display the better it will look.


### Starting & Stopping *dynquee* Manually
You can start, stop or restart *dynquee* (for example, to force it to reload the config file) by typing:
`/etc/init.d/S32dynquee start|stop|restart|status`

---

## Help

If things aren't working, first check the log files in the `logs/` directory:  
- `logs/dynquee.log` contains the summary log
- `logs/dynquee.debug.log` contains the full debug log

The logs should provide some clues as to what is wrong.

**TODO**
If you still can't get it working, post on forum **TODO: link needed**

Please paste your debug log files on [pastebin][pastebin] and provide a link.

---

## Contributing
Bug reports/fixes, improvements, documentation, & translations are welcome. When reporting bugs please include a copy of the debug log file `logs/dynquee.debug.log`.


## Acknowledgements
[`WaitableEvent`](https://lat.sk/2015/02/multiple-event-waiting-python-3/) class written by [Radek Lát](https://lat.sk) is used to wait for several events simultaneously.

For convenience, releases include some starter images collected from various sources.
Most of these are not my work: credit remains with the original authors.
See the [artwork README file][artwork-readme] for sources.


## To Do
- [ ] Genre matching is very dumb: make it more useful.  
  Is there a master list of genres that [Emulation Station][emulationstation] uses somewhere?

---

## Licence
This project is released under the [MIT Licence][licence].


<!-- LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[artwork-readme]: artwork/README.md
[Defender]: https://en.wikipedia.org/wiki/Defender_(1981_video_game)
[different-device]: doc/Running_on_separate_device.md
[dinky-definition]: https://dictionary.cambridge.org/dictionary/english/dinky
[DV190FBM]: https://www.panelook.com/DV190FBM-NB0_BOE_19.1_LCM_overview_32860.html
[emulationstation]: https://wiki.recalbox.com/en/basic-usage/getting-started/emulationstation
[fbv]: https://github.com/godspeed1989/fbv
[ffmpeg]: https://ffmpeg.org/
[licence]: LICENSE.txt
[LTA149B780F]: https://www.panelook.com/LTA149B780F_Toshiba_14.9_LCM_parameter_10941.html
[media-readme]: media/README.md
[pastebin]: https://pastebin.com/
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
