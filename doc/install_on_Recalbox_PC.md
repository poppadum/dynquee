![dynquee: dynamic marquee for Recalbox][project-image]  
Installing *dynquee* on Recalbox PC
===


## Contents
- [Install *dynquee*](#install-dynquee)
- [Identify Video Outputs](#identify-video-outputs)
- [Set Up Screen Layout](#set-up-screen-layout)
- [Test The Marquee Screen](#test-the-marquee-screen)
- [Set Screen Layout At Startup](#set-screen-layout-at-startup)
- [Configure *dynquee*](#configure-dynquee)
- [Configure Openbox](#configure-openbox)
- [Run *dynquee* At Startup](#run-dynquee-at-startup)
- [Final Check](#final-check)

---

To install *dynquee* on Recalbox running on PC, follow these steps.

**Note**: these instructions are for installing *dynquee* on your Recalbox machine;
if you're installing on a separate machine, see [the guide for running on a separate device][different-device]

## Install *dynquee*
1. Install *dynquee* either using the [install script][quick-install] or following the [manual install guide][manual-install].

1. Stop *dynquee*:
    ```sh
    /etc/init.d/S32dynquee stop
    ```

1. Remove the init script (we need to autostart *dynquee* a different way):
    ```sh
    mount -o rw,remount /
    rm /etc/init.d/S32dynquee
    ```

## Identify Video Outputs

1. Log in to recalbox as user `root` either [via ssh][recalbox-ssh] or via the console.

1. Type `xrandr` to get a list of available video outputs.
    Look at the list and identify which output you want to be the primary for Recalbox,
    and which output you want to use for your marquee.


### Example 1: Samsung NP305VC laptop
This laptop has a built-in display and both HDMI and VGA outputs.
I connected my second display via HDMI:
```
# xrandr
Screen 0: minimum 320 x 200, current 1366 x 768, maximum 16384 x 16384
LVDS-1 connected primary 1366x768+0+0 (normal left inverted right x axis y axis) 344mm x 193mm
   1366x768      60.06*+
...
VGA-1 disconnected (normal left inverted right x axis y axis)
HDMI-1 connected (normal left inverted right x axis y axis)
   1920x1080i    60.00 +  50.00    59.94  
...
DP-1 disconnected (normal left inverted right x axis y axis)
```
In this case `LVDS-1` is the primary (Recalbox) display and `HDMI-1` is the marquee.

### Example 2: Intel Atom net-top PC
This PC has HDMI and VGA outputs.
I connected my primary display via HDMI and my marquee display via VGA:

```
# xrandr          
Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 8192 x 8192
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 16mm x 9mm
   1920x1080i    60.00*+  50.00    59.94  
...
VGA-1 connected (normal left inverted right x axis y axis)
   1920x1080     60.00 +
...
```
In this case `HDMI-1` is the primary (Recalbox) display and `VGA-1` is the marquee.



## Set Up Screen Layout

Test your screen layout by entering:
```sh
xrandr --output $PRIMARY --auto --primary --output $MARQUEE --auto --right-of $PRIMARY
```
replacing `$PRIMARY` and `$MARQUEE` above with the device names of
your primary and marquee displays that you discovered above.

Your marquee display should turn on and show a blank screen.

Double-check by entering `xrandr` again. The output should show the marquee display's resolution and offset,
for example: `HDMI-1 connected 1920x1080+1367+0 ...`

Make a note of your `xrandr` command for later.

### Example 1: Samsung NP305VC laptop

```
# xrandr --output LDVS-1 --auto --primary --output HDMI-1 --auto --right-of LVDS-1
# xrandr
Screen 0: minimum 320 x 200, current 1920 x 1848, maximum 16384 x 16384
LVDS-1 connected primary 1366x768+0+0 (normal left inverted right x axis y axis) 344mm x 193mm
   1366x768      60.06*+
...
HDMI-1 connected 1920x1080+1366+0 (normal left inverted right x axis y axis) 16mm x 9mm
   1920x1080i    60.00*+  50.00    59.94
...
```

### Example 2: Intel Atom net-top PC
```
# xrandr --output HDMI-1 --auto --primary --output VGA-1 --auto --right-of HDMI-1
# xrandr
Screen 0: minimum 320 x 200, current 3841 x 1080, maximum 8192 x 8192
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 16mm x 9mm
   1920x1080i    60.00*+  50.00    59.94  
...
VGA-1 connected 1920x1080+1921+0 (normal left inverted right x axis y axis) 477mm x 268mm
   1920x1080     60.00*+
...
```


## Test The Marquee Screen
Check that we can get an image to display on the marquee screen:
```sh
cd /recalbox/share/dynquee
mpv --screen=2 --alpha=blend --loop media/system/zxspectrum.logo.png
```

If all goes well you should see the Sinclair ZX Spectrum logo on the marquee screen.
Press Q to exit `mpv`.


## Set Screen Layout At Startup

Edit the file `/etc/X11/xinit/xinitrc`; find the line 
`/usr/bin/externalscreen.sh`
and insert your `xrandr` command immediately after it so that it looks similar to:
```sh
/usr/bin/externalscreen.sh
xrandr --output ... --auto --primary --output ... --auto --right-of ...
```


## Configure *dynquee*
Edit the *dynquee* config file `dynquee.ini` and change the settings as follows:
```ini
viewer = /usr/bin/mpv
viewer_opts = --screen=2 --alpha=blend --loop {file}
terminate_viewer = yes

clear_cmd =
clear_cmd_opts =

video_player = /usr/bin/mpv
video_player_opts = --screen=2 {file}
```


## Configure Openbox
With default settings, `mpv` grabs the focus when it is launched,
so that keypresses are sent to `mpv` rather than [Emulation Station][emulationstation] or an emulator.

To prevent this, edit the [Openbox][openbox] config file `/etc/openbox/rc.xml` and add the following lines after the line which reads `<applications>`:


```xml
<application class="EmulationStation">
    <focus>yes</focus>
</application>
<application class="mpv">
    <focus>no</focus>
</application>
```
This tells Openbox to give Emulation Station the focus when it launches, but not to give `mpv` the focus.


## Run *dynquee* At Startup
I've tested various methods of auto-starting *dynquee*, but this is the only method I could find that works.

Edit the file `/etc/X11/xinit/xinitrc` and find the line that reads:
`openbox --config-file /etc/openbox/rc.xml --startup "emulationstation --windowed"`

Change that line to read:
`openbox --config-file /etc/openbox/rc.xml --startup "bash /recalbox/share/dynquee/startup_pc.sh"`


Create a new file `/recalbox/share/dynquee/startup_pc.sh` with this content:
```bash
#!/usr/bin/env bash

emulationstation --windowed &
cd /recalbox/share/dynquee
python3 dynquee.py >/dev/null 2>&1 &
```


## Final Check
Do a final check that *dynquee* starts when Emulation Station starts:
```sh
es stop
es start
```

Once it's working as expected, reboot your Recalbox and give everything a test.

Now you can move on to [configuring your marquee and adding media][config-guide].


<!-- LINKS & IMAGES -->
[config-guide]: doc/config.md
[different-device]: Running_on_separate_device.md
[emulationstation]: https://wiki.recalbox.com/en/basic-usage/getting-started/emulationstation
[manual-install]: manual_install.md
[openbox]: http://openbox.org/
[project-image]: ../dynquee.png
[quick-install]: ../README.md#quick-installation
[recalbox-ssh]: https://wiki.recalbox.com/en/tutorials/system/access/root-access-terminal-cli
