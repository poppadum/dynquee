![dynquee: dynamic marquee for Recalbox][project-image]  
Manual Installation of *dynquee* on Recalbox PC
===

If you prefer to install *dynquee* manually, follow these steps. 

## Notes
1. These instructions are for installing *dynquee* on Recalbox PC.  
If you're installing on Recalbox on Raspberry Pi, see [the Raspberry Pi manual install guide][manual-install-rpi].  
If you're installing on a separate machine, see [the guide for running on a separate device][different-device].

1. These steps involve editing config files which probably means you need to be comfortable using the linux command-line and editing files with either `nano` or `vi`.

   If you edit config files on Windows and transfer them to your Recalbox, please remember to transfer the files in TEXT mode.
   
   Stray Windows CRLF line-endings can cause problems that are hard to diagnose.


## Contents
- [Download *dynquee*](#download-dynquee)
- [Identify Video Outputs](#identify-video-outputs)
- [Set Up Screen Layout](#set-up-screen-layout)
- [Test The Marquee Screen](#test-the-marquee-screen)
- [Set Screen Layout At Startup](#set-screen-layout-at-startup)
- [Run *dynquee* At Startup](#run-dynquee-at-startup)
- [Install The PC Startup Script](#install-the-pc-startup-script)
- [Install The PC Config File](#install-the-pc-config-file)
- [Configure Openbox](#configure-openbox)
- [Final Check](#final-check)
- [Help](#help)

---


## Download *dynquee*
1. Log in to recalbox as user `root` either [via ssh][recalbox-ssh] or via the console.

1. Create the *dynquee* directory:  
    ```sh
    mkdir -p /recalbox/share/dynquee
    ```

1. Change to that directory:  
    ```sh
    cd /recalbox/share/dynquee
    ```

1. Download the latest *dynquee* release, unzip it and tidy up:  
     ```sh
     wget -O dynquee.zip https://github.com/poppadum/dynquee/releases/latest/download/dynquee.zip
     unzip dynquee.zip
     rm dynquee.zip
     ```

## Identify Video Outputs
If you don't want to do the next step manually, run `install/find_marquee_output.sh`
which will walk you through the process and generate the `xrandr` command for you.
Then skip on to the [next section](#set-up-screen-layout).

Otherwise, type `xrandr` to get a list of available video outputs.
Look at the list and identify which output you want to be the primary for Recalbox,
and which output you want to use for your marquee.

### Example 1: Samsung NP305VC laptop
This laptop has a built-in display and both HDMI and VGA outputs.
I connected my marquee display via HDMI:
```
# xrandr
Screen 0: minimum 320 x 200, current 1366 x 768, maximum 16384 x 16384
LVDS-1 connected primary 1366x768+0+0 (normal left inverted right x axis y axis) 344mm x 193mm
   1366x768      60.06*+
…
VGA-1 disconnected (normal left inverted right x axis y axis)
HDMI-1 connected (normal left inverted right x axis y axis)
   1920x1080i    60.00 +  50.00    59.94  
…
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
…
VGA-1 connected (normal left inverted right x axis y axis)
   1920x1080     60.00 +
…
```
In this case `HDMI-1` is the primary (Recalbox) display and `VGA-1` is the marquee.



## Set Up Screen Layout

If you used the `find_marquee_output.sh` script to generate your `xrandr` command, enter that command now (copy & paste is easiest).

Otherwise, test your screen layout by entering:
```sh
xrandr --output $PRIMARY --auto --primary --output $MARQUEE --auto --right-of $PRIMARY
```
replacing `$PRIMARY` and `$MARQUEE` above with the names of
your primary and marquee displays that you just discovered.

Your marquee display should turn on and show a blank screen.

Double-check by entering `xrandr` again (with no arguments this time).
The output should show the marquee display's resolution and offset,
for example: `HDMI-1 connected 1920x1080+1366+0 …`

Make a note of your `xrandr` command for later.
The install script records this command in the file `xrandr_cmd.txt`, so I suggest doing the same.
It will be useful if a later Recalbox upgrade removes your startup script.

**TODO**: get script to write `xrandr_cmd.txt` file and execute command?


### Example 1: Samsung NP305VC laptop

```
# xrandr --output LDVS-1 --auto --primary --output HDMI-1 --auto --right-of LVDS-1
# xrandr
Screen 0: minimum 320 x 200, current 1920 x 1848, maximum 16384 x 16384
LVDS-1 connected primary 1366x768+0+0 (normal left inverted right x axis y axis) 344mm x 193mm
   1366x768      60.06*+
…
HDMI-1 connected 1920x1080+1366+0 (normal left inverted right x axis y axis) 16mm x 9mm
   1920x1080i    60.00*+  50.00    59.94
…
```

### Example 2: Intel Atom net-top PC
```
# xrandr --output HDMI-1 --auto --primary --output VGA-1 --auto --right-of HDMI-1
# xrandr
Screen 0: minimum 320 x 200, current 3841 x 1080, maximum 8192 x 8192
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 16mm x 9mm
   1920x1080i    60.00*+  50.00    59.94  
…
VGA-1 connected 1920x1080+1921+0 (normal left inverted right x axis y axis) 477mm x 268mm
   1920x1080     60.00*+
…
```



## Test The Marquee Screen
Check that we can get an image to display on the marquee screen:
```sh
mpv --screen=2 --alpha=blend --loop media/system/zxspectrum.logo.png
```

You should see the Sinclair ZX Spectrum logo on the marquee screen.
Press Q to exit `mpv`.


## Set Screen Layout At Startup

First, remount the root filesystem read/write:
```sh
mount -o rw,remount /
```

Now edit the file `/etc/X11/xinit/xinitrc`; find the line 
`/usr/bin/externalscreen.sh`
and insert the `xrandr` command you noted earlier immediately after it so that it looks similar to:
```sh
/usr/bin/externalscreen.sh
xrandr --output … --auto --primary --output … --auto --right-of …
```
Again, copy & paste is easiest.

## Run *dynquee* At Startup
I tested various methods of auto-starting *dynquee* on PC, but this is the only method I could find that works.

While you're editing the file `/etc/X11/xinit/xinitrc`, find the line that reads:  
`openbox --config-file /etc/openbox/rc.xml --startup "emulationstation --windowed"`  
 (probably the last line of the file).

Change that line to read:  
`openbox --config-file /etc/openbox/rc.xml --startup "bash /recalbox/share/dynquee/startup_pc.sh"`


## Install The PC Startup Script
Copy the PC startup script to the program directory:
```sh
cp -vf install/startup_pc.sh ./
```

## Install The PC Config File
Copy the PC version of the *dynquee* config file to the program directory:
```sh
cp -vf install/dynquee-pc.ini ./dynquee.ini
```

Optional: if you have a video card that supports hardware acceleration, you could add the [`mpv --hwdec` option][mpv--hwdec] to the `video_player_opts` setting
e.g. `--hwdec nvdec` for nVidia GPUs or `--hwdec vaapi` for AMD or Intel GPUs.
This may take some load off the CPU if you are using video marquees.


## Configure Openbox
With default settings, `mpv` grabs the application focus when it is launched,
so that keypresses are sent to `mpv` rather than [Emulation Station][emulationstation] or a game emulator.

To prevent this, edit the [Openbox][openbox] config file `/etc/openbox/rc.xml`
and add the following lines after the line which reads `</application>` (indentation is not important):


```xml
<application class="EmulationStation">
    <focus>yes</focus>
</application>
<application class="mpv">
    <focus>no</focus>
</application>
```
This tells Openbox to give Emulation Station the focus when it launches, but never to give `mpv` (which displays the marquee images and videos) the focus.


## Final Check
Do a final check that *dynquee* starts when Emulation Station starts:
```sh
es stop
es start
```

Once it's working as expected, reboot your Recalbox and test everything.

Then you can move on to [configuring your marquee and adding media][config-guide].


## Help
Please see the [help section in the README](../README.md#help).


<!-- LINKS & IMAGES -->
[config-guide]: config.md
[different-device]: Running_on_separate_device.md
[emulationstation]: https://wiki.recalbox.com/en/basic-usage/getting-started/emulationstation
[manual-install-rpi]: manual_install_rpi.md
[mpv--hwdec]: https://mpv.io/manual/master/#options-hwdec
[openbox]: http://openbox.org/
[project-image]: ../dynquee.png
[recalbox-ssh]: https://wiki.recalbox.com/en/tutorials/system/access/root-access-terminal-cli
