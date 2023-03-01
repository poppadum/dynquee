![dynquee: dynamic marquee for Recalbox][project-image]  
Running *dynquee* on a different device to Recalbox
===

While *dynquee* was originally intended to run on same computer as Recalbox, it can run on a separate machine and communicate with Recalbox via the network.


## Contents
- [Requirements](#requirements)
- [Quick Installation](#quick-installation)
- [Manual Installation](#manual-installation)
    - [Install Packages](#install-packages)
    - [Network Setup](#network-setup)
    - [Download](#download)
    - [Configure](#configure)
    - [Test](#test)
    - [Run At Startup](#run-at-startup)
- [Help](#help)
- [Using Other Media Players](#using-other-media-players)

---


## Requirements
*dynquee* requires the following to be installed:

- Python v3.7 or later

- Python package [paho.mqtt.client][py-paho-mqtt]

- Software to show images and play video files. \
    By default *dynquee* uses [`fbi`][fbi] for still images and [`ffmpeg`][ffmpeg] for videos, but if you want to use something else you can configure it via the [config file](#configure).

    **TODO**: Is fbi still available for bullseye? 

    **Note**: because `fbi` and `ffmpeg` write direct to the framebuffer device, dynquee needs to run as `root` (or possibly a member of the `video` group)

- a Recalbox machine running on the local network with the [Recalbox Manager][recalbox-manager] web interface left enabled

If you are using a Raspberry Pi to run your marquee I recommend installing the *Lite* version of [Raspberry Pi OS][raspi-os] as it's much more lightweight than the desktop version.

---

## Quick Installation

Follow these steps to install *dynquee* using the install script:

1. Log in to your marquee computer either at the console or via `ssh`

1. Fetch and run the installer: copy and paste this command and press enter:
    ```sh
    sudo bash -c "$(wget -qO - https://github.com/poppadum/dynquee/raw/main/install/install-remote.sh)"
    ```
    
    **TODO**: test this

1. When prompted, type the hostname or IP address of your Recalbox (default hostname: `recalbox`)  
    **Note**: if you supply an IP address, make sure that IP address won't change
    because *dynquee* will try to connect to that IP address every time it starts.

---

## Manual Installation
If you prefer to install everything manually, follow these instructions. 
They assume you are installing *dynquee* on a Raspberry Pi running Raspberry Pi OS, but should apply to any debian-like OS.

<details>
<summary>Click to expand full instructions:</summary>

### Install Packages
Install the required packages with:  
```sh
sudo apt install python3 python3-paho-mqtt fbi ffmpeg
```

### Network Setup
1. Make sure the marquee computer is connected to the same local network as Recalbox

1. Optional: give Recalbox a static IP, either by [editing the Recalbox config file][recalbox-static-ip] or adding a reservation in your DHCP server

1. Test connectivity by pinging Recalbox by hostname or IP address from your marquee machine:  
    ```sh
    $ ping -c 5 recalbox
    PING recalbox (10.0.0.70) 56(84) bytes of data.
    64 bytes from recalbox (10.0.0.70): icmp_seq=1 ttl=64 time=5.93 ms
    64 bytes from recalbox (10.0.0.70): icmp_seq=2 ttl=64 time=6.35 ms
    64 bytes from recalbox (10.0.0.70): icmp_seq=3 ttl=64 time=5.43 ms
    64 bytes from recalbox (10.0.0.70): icmp_seq=4 ttl=64 time=5.55 ms
    64 bytes from recalbox (10.0.0.70): icmp_seq=5 ttl=64 time=6.81 ms

    --- recalbox ping statistics ---
    5 packets transmitted, 5 received, 0% packet loss, time 9ms
    rtt min/avg/max/mdev = 5.426/6.011/6.808/0.520 ms

    ```
    If ping fails to get a reply, double-check the hostname / IP address of your Recalbox and that it's connected to your local network.

    Once ping is working, make a note of the hostname or IP address of your Recalbox.


### Download
1. Decide where to locate *dynquee*: the default is `/opt/dynquee`

1. Create the directory:  
    ```
    sudo mkdir -p /opt/dynquee
    ```

1. Change to that directory:  
    ```
    cd /opt/dynquee
    ```

1. Download the *dynquee* release and unzip it:  
     ```sh
     sudo wget https://github.com/poppadum/dynquee/releases/latest/download/dynquee.zip
     sudo unzip dynquee.zip
     ```


### Configure

1. Copy the config file for remote running:
    ```sh
    sudo cp install/dynquee-remote.ini ./dynquee.ini
    ```


1. Optional: make the `media/` directory world-writeable so you can copy files to it without `sudo`:  
    ```sh
    chmod -R a+w ./media/
    ```


1. Edit the config file `dynquee.ini` as follows:

    - in the `[global]` section, change `dynquee_path` if you installed dynquee somewhere other than `/opt/dynquee`

    - in the `[recalbox]` section, change `host` to the hostname or IP address of your Recalbox you noted earlier


### Test
Try running the command `sudo ./dynquee.py`. If all goes well, you should see the startup image on your marquee display. Check that it responds to Recalbox actions by selecting a game system: the marquee should change to the logo or console image of that system.

Press Ctrl+C to stop the program.

If it doesn't work as expected, check the log files in the `logs/` directory:  
- `logs/dynquee.log` contains the summary log
- `logs/dynquee.debug.log` contains the full debug log

If you've checked the logs and still can't see what's wrong, see the [help section](#help).


### Run At Startup

There are various ways to get dynquee to run when the machine starts. \
Recent releases of Raspberry Pi OS use [systemd][systemd] so that's what I recommend.

1. Copy the `systemd` unit file to the systemd directory, and enable it:
    ```sh
    sudo cp install/dynquee.service /etc/systemd/system/
    ```

1. If you installed *dynquee* somewhere other than `/opt/dynquee`, edit the file
   `/etc/systemd/system/dynquee.service` and update the `WorkingDirectory` and `ExecStart` lines.

1. Enable the service:
    ```sh
    sudo systemctl daemon-reload
    sudo systemctl enable dynquee.service
    ```

1. Start the service: 
    ```sh
    sudo systemctl start dynquee.service
    ```

If you don't want to use `systemd`, you could add the startup command to `root`'s crontab e.g.  
`@reboot /opt/dynquee/dynquee.py`  
or  add it to `/etc/rc.local`

To test, reboot your marquee machine and check that *dynquee* starts automatically.

</details>

---


## Help
If you've checked the log files and still can't get it working,
post on the Recalbox forum **TODO: link needed** or discuss on github?

Please paste your config file and debug log file on [pastebin][pastebin] and provide a link when reporting issues.

---


## Using Other Media Players
If you don't want to use [`fbi`][fbi] or [`ffmpeg`][ffmpeg], look in the config file `dynquee.ini` at the `[slideshow]` section, in particular the settings:  
- `viewer`
- `viewer_opts`
- `terminate_viewer`
- `video_player`
- `video_player_opts`

Below are a couple of examples of other possible configs.

### Using [vlc][vlc]:
```ini
viewer = /usr/bin/cvlc
viewer_opts = --no-audio --no-video-title-show --loop --quiet
terminate_viewer = yes

video_player = /usr/bin/cvlc
video_player_opts = --no-audio --no-video-title-show --play-and-exit --quiet

```

### Using [omxplayer][omxplayer]:
```ini
video_player = /usr/bin/omxplayer
video_player_opts = --no-osd --no-keys
```


<!-- LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[fbi]: https://git.kraxel.org/cgit/fbida/
[ffmpeg]: https://ffmpeg.org
[omxplayer]: https://github.com/popcornmix/omxplayer/blob/master/README.md
[pastebin]: https://pastebin.com/
[project-image]: ../dynquee.png
[py-paho-mqtt]: https://pypi.org/project/paho-mqtt/
[raspi-os]: https://www.raspberrypi.com/software/
[recalbox-manager]: https://wiki.recalbox.com/en/tutorials/system/access/recalbox-manager-web-interface
[recalbox-static-ip]: https://wiki.recalbox.com/en/tutorials/network/ip/static-manual-ip
[systemd]: https://systemd.io/
[vlc]: https://www.videolan.org/vlc/
