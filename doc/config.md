![dynquee: dynamic marquee for Recalbox][project-image]  
*dynquee* Configuration Guide
===

## Contents
- [Introduction](#introduction)
- [Emulation Station events](#emulation-station-events)
- [Search Rules](#search-rules)
- [Filename Matching](#filename-matching)
- [Adding Your Own Images And Videos](#adding-your-own-images-and-videos)
- [File Formats](#file-formats)
- [Controlling When The Marquee Changes](#controlling-when-the-marquee-changes)
- [Starting And Stopping *dynquee* Manually](#starting-and-stopping-dynquee-manually)

---


## Introduction
Most settings can be configured in the config file [`dynquee.ini`](../dynquee.ini).

For each [Emulation Station event](#emulation-station-events), the config file defines a search precedence rule: an ordered list of search terms indicating where to search for media files.

If no files match a search term *dynquee* moves on to the next term.
That way you can specify which media files to show in order of priority.

For example, when an arcade game is launched, *dynquee* can:
1. search for the game's marquee image
1. if not found, search for the game publisher's banner
1. if not found, search for a generic arcade banner

All media files that match a successful search term are displayed in a random order as a slideshow that loops continuously. How long each image or video is shown can be adjusted in the `[slideshow]` section of the config file.


## Emulation Station events
A full list of Emulation Station events can be found in the [Recalbox wiki][wiki-es-events]. They are referred to as *events* or *actions*: the terms are used interchangeably.

The most useful are:

* `systembrowsing`: user is browsing list of systems
* `gamelistbrowing`: user has selected a system and is browsing list of games
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
* `blank`: blank the display e.g. when EmulationStation goes to sleep  

Search terms can be combined at the same precedence level with the `+` character
e.g.  
  ```ini
  rungame = rom+publisher+system genre scraped generic
  ```
will first try to locate media for the rom, publisher and system and show all
files matching those search terms.

Notes:
1. No search rule is defined for the `endgame` action as Emulation Station
   sends another action (usually `gamelistbrowsing`) immediately after
1. The `wakeup` action causes *dynquee* to repeat the action that occurred immediately before the `sleep` event
1. The `blank` search term causes dynquee to stop processing a search rule, so you can't combine it with other search terms


## Filename Matching
Media filename matching works as follows:

1. ROM filenames have their file extension (everything after the last `.`) removed
    - e.g. `Sonic The Hedgehog.zip` becomes `Sonic The Hedgehog.`

1. Names of publishers and genres are converted to lower case and a dot is added to the end
    - e.g. `Data East` becomes `data east.`

1. Names are then matched against the beginning of media filenames.
    - e.g. a ROM named `Chuckie Egg.zip` would match media files named `Chuckie Egg.*`
    - or a game published by `Bally Midway` would match files named `bally midway.*`


## Adding Your Own Images And Videos
By default marquee media files are located in `/recalbox/share/dynquee/media`.
If for some reason you want to store them somewhere else, change the `media_path` setting in the `[media]` section of the config file.

Place your media files in the appropriate subdirectory (look at the included files for examples):

- *game-specific* media go in the appropriate system directory; for example:
    - for the arcade version of [Defender] with a ROM named `defender.zip`, put your media file in `mame/` and name it `defender.<something>` e.g. `mame/defender.01.png`
    - for the Megadrive version of [Aladdin] with a ROM named `aladdin.zip`, put your media file in `megadrive/` and name it `aladdin.<something>` e.g. `megadrive/aladdin.png`

- `system/` is for game system media (e.g. console banners and logos);
the file name must start with Emulation Station's internal system name (use the same names as in `/recalbox/share/roms/`)
    - e.g. for a [Sinclair ZX Spectrum][spectrum] logo, name the file `zxspectrum.<something>` e.g. `system/zxspectrum.logo.png`

- `publisher/` is for game publisher banners & logos

- `startup/` is for files to show when *dynquee* first starts up e.g. a welcome banner or video

- `generic/` is for media that doesn't belong anywhere else, to be used if no other files match


## File Formats
You can use any file format supported by [`fbv`][fbv] or [`ffmpeg`][ffmpeg].
I recommend `png` for still images, and `mp4` or `mkv` with the H.264 codec for videos.
Media is resized to fit the screen but the closer you can match the aspect ratio and resolution of your marquee display the better it will look.


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
blanked when Recalbox sleeps and cause burn-in on your marquee screen!


## Starting & Stopping *dynquee* Manually
You can start, stop or restart *dynquee* (for example, to reload a changed config file) by typing:  
```sh
/etc/init.d/S32dynquee start|stop|restart|status
```

<!-- LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Aladdin]: https://en.wikipedia.org/wiki/Disney's_Aladdin_(Virgin_Games_video_game)
[Defender]: https://en.wikipedia.org/wiki/Defender_(1981_video_game)
[fbv]: https://github.com/godspeed1989/fbv
[ffmpeg]: https://ffmpeg.org/
[project-image]: ../dynquee.png
[spectrum]: https://en.wikipedia.org/wiki/ZX_Spectrum
[wiki-es-events]: https://wiki.recalbox.com/en/advanced-usage/scripts-on-emulationstation-events#events
