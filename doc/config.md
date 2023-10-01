![dynquee: dynamic marquee for Recalbox][project-image]  
*dynquee* Configuration Guide
===

## Contents
- [Introduction](#introduction)
- [Emulation Station Events](#emulation-station-events)
- [Search Rules](#search-rules)
- [Filename Matching](#filename-matching)
- [Adding Your Own Images And Videos](#adding-your-own-images-and-videos)
- [File Formats](#file-formats)
- [Scaling Media](#scaling-media)
- [Controlling When The Marquee Changes](#controlling-when-the-marquee-changes)
- [Starting And Stopping *dynquee* Manually](#starting-and-stopping-dynquee-manually)

---


## Introduction
Most settings can be configured in the config file [`dynquee.ini`](../dynquee.ini).

For each [Emulation Station event](#emulation-station-events), the config file defines a search precedence rule: an ordered list of search terms indicating where to search for media files.

If no files match a search term *dynquee* moves on to the next search term.
That way you can specify which media files to show in order of priority.

For example, when an arcade game is launched, *dynquee* can:
1. search for the game's marquee image
1. if not found, search for the game publisher's banner
1. if not found, search for a generic arcade banner

All media files that match a successful search term are displayed in a random order as a slideshow that loops continuously. How long each image or video is shown can be adjusted in the `[slideshow]` section of the config file.


## Emulation Station Events
A full list of Emulation Station events can be found in the [Recalbox wiki][wiki-es-events]. They are referred to as *events* or *actions*: the terms are used interchangeably.

The most useful are:

* `systembrowsing`: user is browsing the list of systems
* `gamelistbrowing`: user has selected a system and is browsing the list of games
* `rungame`: user has started a game
* `endgame`: user has exited a game
* `sleep`: EmulationStation has entered sleep mode
* `wakeup`: EmulationStation was woken up after sleep
* `runkodi`: user has started Kodi


## Search Rules
Search rules are defined in the `[media]` section of the config file,
one rule per Emulation Station action.

A search rules consists of one or more of the following search terms:

* `rom`: ROM-specific media e.g. marquee image for the selected game
* `scraped`: the selected game's scraped image
* `publisher`: media relating to the publisher of game e.g. Atari or Taito banner
* `genre`: media relating to genre of game e.g. shooters, platform games
* `system`: media relating to game system e.g. Sinclair Spectrum or SNES banner
* `generic`: generic media unrelated to a game, system or publisher
* `screensaver`: media to be shown when EmulationStation goes to sleep
    and the screensaver is active
* `blank`: blank the display e.g. when EmulationStation goes to sleep  

Search terms can be combined at the same precedence level with the `+` character
e.g.  
  ```ini
  rungame = rom+publisher+system genre scraped generic
  ```
will first try to locate media for the rom, publisher and system and show all
files matching those search terms.

**Notes**:
1. No search rule is defined for the `endgame` action as Emulation Station
   sends another action (usually `gamelistbrowsing`) immediately after
1. The `wakeup` action causes *dynquee* to repeat the action that occurred immediately before the `sleep` event
1. The `blank` search term causes dynquee to stop processing a search rule, so you can't combine it with other search terms
1. If you want *dynquee* to ignore an action completely, comment out or remove its search rule.

## Filename Matching
Media filename matching works as follows:

1. ROM filenames have their file extension (everything after the last `.`) removed
    - e.g. `Sonic The Hedgehog.zip` becomes `Sonic The Hedgehog.`

1. Names of publishers and genres are converted to lower case and a dot is added to the end
    - e.g. `Data East` becomes `data east.`

1. Recalbox's internal system ID for game systems has a dot added to the end:
    - e.g. `mame` becomes `mame.`
    - e.g. `neogeocd` becomes `neogeocd.`
    - Note: there is an option to treat all arcade system IDs as a single system named `arcade` (see the option `arcade_system_enabled` in the config file).

1. Names are then matched (case insensitively) against the beginning of media filenames.
    - e.g. a ROM named `Chuckie Egg.zip` would match media files named `Chuckie Egg.*` or `chuckie egg.*`
    - or a game published by `Bally Midway` would match files named `bally midway.*`


## Adding Your Own Images And Videos
By default marquee media files are located in `/recalbox/share/dynquee/media`.
If for some reason you want to store them somewhere else, change the `media_path` setting in the `[media]` section of the config file.

Place your media files in the appropriate subdirectory (look at the included files for examples):

- *game-specific* media go in the appropriate game system directory; for example:
    - for the Mame version of [Defender] with a ROM named `defender.zip`, put your media file in `mame/` and name it `defender.<something>` e.g. `mame/defender.01.png`
    - for the Megadrive version of [Aladdin] with a ROM named `aladdin.zip`, put your media file in `megadrive/` and name it `aladdin.<something>` e.g. `megadrive/aladdin.mp4`
    - Note: if the config file option `arcade_system_enabled` is on, put your arcade media files in `arcade/`

- `system/` is for game system media (e.g. console banners and logos);
the file name must start with Emulation Station's internal system name (use the same names as in `/recalbox/share/roms/`)
    - e.g. for a [Sinclair ZX Spectrum][spectrum] logo, name the file `zxspectrum.<something>` e.g. `system/zxspectrum.logo.png`
    - If the config file option `arcade_system_enabled` is on, all arcade games will have the system name `arcade`, so name your arcade files `system/arcade.<something>`

- `publisher/` is for game publisher banners & logos
    - e.g. for a game published by [Konami][konami], name the file `konami.<something>` e.g. `publisher/konami.01.png`

- `startup/` is for files to show when *dynquee* first starts up e.g. a welcome banner or video.
    Filename does not matter, but use the appropriate file extension e.g. `startup/welcome.png`

- `generic/` is for media that doesn't belong anywhere else, to be used if no other files match.
    If you have designed custom artwork for your Recalbox, place it here.
    Filename does not matter, but use the appropriate file extension e.g. `generic/my_games_machine.mkv`

- `screensaver/` is for files to show when EmulationStation goes to sleep and activates the screensaver

Feel free to delete any of the included media files you don't want, but I recommend you leave `media/default.png` (or replace it with your own custom image) as a file of last resort.


## File Formats
You can use any file format supported by [`fbv`][fbv] or [`ffmpeg`][ffmpeg].
I recommend `png` or`jpeg` for still images, and `mp4` or `mkv` with the H.264 codec for videos.


## Scaling Media
With default settings, still images are zoomed to fit the marquee screen but keep their original aspect ratio; videos are not resized.

If you want to scale videos to the height of the marquee, a helper script [`play_video_scaled.sh`](../play_video_scaled.sh) is provided for Raspberry Pi. The comments in the config file explain how to use it. Note that the script uses the `marquee_width` & `marquee_height` settings in the config file to calculate video output size, so change those settings to match your marquee screen. Bear in mind that video scaling can tax the CPU which will leave Recalbox fewer CPU cycles available to run emulators[^cpu-usage].

[^cpu-usage]: Here is the abbreviated output of `top` when running a scaled video at the same time as the Libretro Mame2003+ emulator on my Pi4 2GB: `ffmpeg` is using ~120% of the 400% available on a four-core CPU:

    ```
      PID USER      PR  NI    VIRT    RES  %CPU  %MEM     TIME+ S COMMAND
     2047 root      20   0  476.7m  50.1m 119.0   3.4   0:34.02 R ffmpeg -hide_banner -loglevel error -c:v rawvideo -pix_fmt rgb565le -filter:v scale=iw*2/2.58888:360 -fbdev -xoffset 320 /dev/fb0 -re -i /recalbox/share/dynquee/media/mame/cabal.mp4
     2057 root      20   0  637.0m 159.3m  19.6  10.7   0:07.37 S /usr/bin/retroarch -L /usr/lib/libretro/mame2003_plus_libretro.so --config /recalbox/share/system/configs/retroarch/retroarchcustom.cfg --appendconfig /recalbox/share_init/overlays/mame/mame.cfg|/recalbox/share/system/configs/retroarch/retroarchcustom.cfg
      515 root       9 -11  986.9m   7.4m   5.9   0.5   0:29.02 S /usr/bin/pulseaudio --exit-idle-time=-1 --log-target=syslog --daemonize --use-pid-file
     1380 root      20   0 1728.9m 236.9m   5.2  16.0   2:59.84 S /usr/bin/emulationstation
     …
     ```

The more closely you match your images and videos to the aspect ratio and resolution of your marquee display the better it will look.


## Controlling When The Marquee Changes

The config file defines a change rule for each [Emulation Station event](#emulation-station-events)  in the `[change]` section.
This allows you to control when the marquee will change its slideshow, so you can avoid the slideshow restarting every time you move up or down the list of games.

For each event the change rule can have one of the following values:

* `always`: this action always changes the marquee
* `action`: a change of action (different to previous action) changes the marquee
* `system`: a change of selected game system changes the marquee
* `game`: a change of selected game changes the marquee
* `system/game`: a change of EITHER the selected system OR game changes the marquee
* `never`: this action never changes the marquee

I recommend that the rule for the `sleep` event remain set to `always`.
Changing the rule for `sleep` may prevent the marquee being
blanked when Recalbox sleeps and cause [burn-in][screen-burn-in] on your marquee screen!


## Starting And Stopping *dynquee* Manually
You can start, stop or restart *dynquee* (for example, to reload a changed config file) by typing:  

Raspberry Pi: 
```console
/etc/init.d/S32dynquee start|stop|restart|status
```

PC:
```console
es start|stop|restart
```


Be aware that if you start *dynquee* when Recalbox is already in the sleep state,
it will stay on the startup media until Recalbox wakes up.
If there is only one startup image, that image could be shown for any length of
time and could cause [screen burn-in][screen-burn-in]!


<!-- LINKS & IMAGES -->
[Aladdin]: https://en.wikipedia.org/wiki/Disney's_Aladdin_(Virgin_Games_video_game)
[Defender]: https://en.wikipedia.org/wiki/Defender_(1981_video_game)
[fbv]: https://github.com/godspeed1989/fbv
[ffmpeg]: https://ffmpeg.org/
[konami]: https://en.wikipedia.org/wiki/Konami
[project-image]: ../dynquee.png
[screen-burn-in]: https://en.wikipedia.org/wiki/Screen_burn-in
[spectrum]: https://en.wikipedia.org/wiki/ZX_Spectrum
[wiki-es-events]: https://wiki.recalbox.com/en/advanced-usage/scripts-on-emulationstation-events#events