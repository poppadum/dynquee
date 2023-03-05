# Manual Installation
If you prefer to install *dynquee* manually, follow these steps. 

**Note**: these instructions are for installing *dynquee* on Recalbox; if you're installing on a separate machine, see [the guide for running on a separate device][different-device]

## Download
1. Log in to recalbox as user `root` either [via ssh][recalbox-ssh] or via the console.

1. Create the *dynquee* directory:  
    ```
    mkdir -p /recalbox/share/dynquee
    ```

1. Change to that directory:  
    ```
    cd /recalbox/share/dynquee
    ```

1. Download the latest *dynquee* release and unzip it:  
     ```sh
     wget https://github.com/poppadum/dynquee/releases/latest/download/dynquee.zip
     unzip dynquee.zip
     ```


## Test
Try running the command `python3 dynquee.py`. If all goes well, you should see the startup image on your marquee display. Check that it responds to Recalbox actions by selecting a game system: the marquee should change to the logo or console image of that system.

Press Ctrl+C to stop the program.

If it doesn't work as expected, check the log files in the `logs/` directory:  
- `logs/dynquee.log` contains the summary log
- `logs/dynquee.debug.log` contains the full debug log

If you've checked the logs and still can't see what's wrong, see the [help section in the README](../README.md#help).


## Run At Startup
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

If all goes well, reboot Recalbox and check that *dynquee* starts automatically.


<!-- LINKS & IMAGES -->
[different-device]: ./Running_on_separate_device.md
[recalbox-ssh]: https://wiki.recalbox.com/en/tutorials/system/access/root-access-terminal-cli
