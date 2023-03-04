![dynquee: dynamic marquee for Recalbox][project-image]  
A dynamic digital marquee for [Recalbox]
===


<!-- **TODO**: add photos / demo video of it working? -->

## Contents
- [About *dynquee*](#about-dynquee)
- [Getting Started](#getting-started)
    - [Quick Installation](#quick-installation)
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


### Status
*dynquee* is now pretty stable but there may still be bugs.

I've tried to minimise the risk of displaying the same image for a long period of time
because I'm concerned about [image persistence or burn-in][screen-burn-in].
While this shouldn't be too much of a problem if you're using an LCD  display for your marquee,
I still recommend keeping an eye on it.

---

## Getting Started

To get *dynquee* running on your Recalbox follow the instructions below.

To get *dynquee* running on a different machine see [the separate instructions here][different-device].

Releases include a few media files to get started (see [acknowledgements](#acknowledgements)) but not a complete set. See the [media README][media-readme] for suggestions of where to find media files.


### Quick Installation

Follow these steps to install *dynquee* using the install script:

<!-- **TODO**: check link -->

1. Connect to your recalbox with `ssh` (the [Recalbox wiki][recalbox-ssh] explains how)
1. Copy and paste this command and press enter:  
    ```sh
    bash -c "$(wget -qO - https://github.com/poppadum/dynquee/raw/main/install/install.sh)"
    ```
1. If all goes well you should see the *Installation complete* message


### Manual Installation
If you prefer to install everything manually, follow [this guide][manual-install].

---

## Usage
Most settings can be configured in the config file [`dynquee.ini`](dynquee.ini).
Read the comments in that file and read the [configuration guide][config-guide] for full details.

---

## Help

If things aren't working, first check the log files in the `logs/` directory:  
- `logs/dynquee.log` contains the summary log
- `logs/dynquee.debug.log` contains the full debug log

The logs should provide some clues as to what is wrong.

**TODO**
If you still can't get it working, post on forum **TODO: link needed**

Please paste your config and debug log files on [pastebin][pastebin] and provide a link.

---

## Contributing
Bug reports/fixes, improvements, documentation, & translations are welcome. When reporting bugs please include a copy of your config file `dynquee.ini` and the debug log file `logs/dynquee.debug.log`.


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
[artwork-readme]: artwork/README.md
[config-guide]: doc/config.md
[different-device]: doc/Running_on_separate_device.md
[dinky-definition]: https://dictionary.cambridge.org/dictionary/english/dinky
[DV190FBM]: https://www.panelook.com/DV190FBM-NB0_BOE_19.1_LCM_overview_32860.html
[emulationstation]: https://wiki.recalbox.com/en/basic-usage/getting-started/emulationstation
[licence]: LICENSE.txt
[LTA149B780F]: https://www.panelook.com/LTA149B780F_Toshiba_14.9_LCM_parameter_10941.html
[manual-install]: doc/manual_install.md
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
[screen-burn-in]: https://en.wikipedia.org/wiki/Screen_burn-in
