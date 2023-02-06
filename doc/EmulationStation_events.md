# EmulationStation events

When an event occurs, the event details are written to `/tmp/es_state.inf`.
This file has Windows-style CRLF (\r\n) line endings.

## Actions

The following actions are used by `digimarquee`:


### 1. action = `systembrowsing`

User is browsing the list of game systems

Params:
- `systemId` = internal name of game system selected

Examples:

```ini
Version=2.0
Action=systembrowsing
ActionData=Mame
System=Mame
SystemId=mame
Game=
GamePath=
ImagePath=
DefaultEmulator=libretro
DefaultCore=mame2003_plus
State=selected
```

```ini
Version=2.0
Action=systembrowsing
ActionData=Nintendo Entertainment System
System=Nintendo Entertainment System
SystemId=nes
Game=
GamePath=
ImagePath=
DefaultEmulator=libretro
DefaultCore=nestopia
State=selected
```

### 2. action = `gamelistbrowsing`

User is browsing the list of games

Params:
- `systemId` = internal name of game system selected
- `Game` = display name of game selected
- `GamePath` = full path to the game (rom) selected

Optional params:
- `ImagePath` = full path to the game's scraped image
- `Developer` = game developer
- `Publisher` = game publisher
- `Genre` = game genre(s); free text field to hard to match against media files
- `GenreId` = numerical genre id; TODO: find docs on this

Examples:

```ini
Version=2.0
Action=gamelistbrowsing
ActionData=/recalbox/share/roms/mame/1942.zip
System=Mame
SystemId=mame
Game=1942 (Revision B)
GamePath=/recalbox/share/roms/mame/1942.zip
ImagePath=
IsFolder=0
ThumbnailPath=
VideoPath=
Developer=
Publisher=
Players=1
Region=
Genre=
GenreId=0
Favorite=0
Hidden=0
Adult=0
Emulator=libretro
Core=mame2003_plus
DefaultEmulator=libretro
DefaultCore=mame2003_plus
State=selected
```

```ini
Version=2.0
Action=gamelistbrowsing
ActionData=/recalbox/share/roms/mame/chasehq.zip
System=Mame
SystemId=mame
Game=Chase H.q.
GamePath=/recalbox/share/roms/mame/chasehq.zip
ImagePath=/recalbox/share/roms/mame/media/images/Chase H.q. 8fe63f9509e4679f78768a0d10d70258.png
IsFolder=0
ThumbnailPath=
VideoPath=
Developer=Taito
Publisher=Taito
Players=1
Region=wor
Genre=Race 3rd Pers. view,Race, Driving
GenreId=1537
Favorite=0
Hidden=0
Adult=0
Emulator=libretro
Core=mame2003_plus
DefaultEmulator=libretro
DefaultCore=mame2003_plus
State=selected
```

```ini
Version=2.0
Action=gamelistbrowsing
ActionData=/recalbox/share_init/roms/zxspectrum/Genesis (Retroworks).tzx
System=ZXSpectrum
SystemId=zxspectrum
Game=Genesis - Dawn of a New Day
GamePath=/recalbox/share_init/roms/zxspectrum/Genesis (Retroworks).tzx
ImagePath=/recalbox/share_init/roms/zxspectrum/media/images/Genesis (Retroworks).png
IsFolder=0
ThumbnailPath=
VideoPath=
Developer=RetroWorks
Publisher=RetroWorks
Players=1
Region=
Genre=Shoot'em Up-Shoot'em up / Horizontal
GenreId=260
Favorite=0
Hidden=0
Adult=0
Emulator=libretro
Core=fuse
DefaultEmulator=libretro
DefaultCore=fuse
State=selected
```


### 3. action = `rungame`

User is playing a game

Params: as `gamelistbrowsing` except
- `State=playing`

Example:

```ini
Version=2.0
Action=rungame
ActionData=/recalbox/share/roms/mame/chasehq.zip
System=Mame
SystemId=mame
Game=Chase H.q.
GamePath=/recalbox/share/roms/mame/chasehq.zip
ImagePath=/recalbox/share/roms/mame/media/images/Chase H.q. 8fe63f9509e4679f78768a0d10d70258.png
IsFolder=0
ThumbnailPath=
VideoPath=
Developer=Taito
Publisher=Taito
Players=1
Region=wor
Genre=Race 3rd Pers. view,Race, Driving
GenreId=1537
Favorite=0
Hidden=0
Adult=0
Emulator=libretro
Core=mame2003_plus
DefaultEmulator=libretro
DefaultCore=mame2003_plus
State=playing
```

### 4. action = `endgame`

User has finished playing a game; usually followed immediately by a `gamelistbrowsing` event

Params: as `rungame` except
- `State=selected`

Example:

```ini
Version=2.0
Action=endgame
ActionData=/recalbox/share/roms/mame/chasehq.zip
System=Mame
SystemId=mame
Game=Chase H.q.
GamePath=/recalbox/share/roms/mame/chasehq.zip
ImagePath=/recalbox/share/roms/mame/media/images/Chase H.q. 8fe63f9509e4679f78768a0d10d70258.png
IsFolder=0
ThumbnailPath=
VideoPath=
Developer=Taito
Publisher=Taito
Players=1
Region=wor
Genre=Race 3rd Pers. view,Race, Driving
GenreId=1537
Favorite=0
Hidden=0
Adult=0
Emulator=libretro
Core=mame2003_plus
DefaultEmulator=libretro
DefaultCore=mame2003_plus
State=selected
```

### 5. action = `sleep`

EmulationStation entered sleep state


### 6. action = `wakeup`

EmulationStation woken from sleep state


### 7. action = `runkodi`

User is using kodi

Example:

```ini
Version=2.0
Action=runkodi
ActionData=
System=kodi
SystemId=kodi
Game=
GamePath=
ImagePath=
State=playing
```
