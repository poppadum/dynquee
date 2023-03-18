# install/ directory

Contains install scripts and helper files.

- `install.sh` installs *dynquee* on Recalbox
- `dynquee-pc.ini`: config file for Recalbox PC
- `S32dynquee`: init script for Recalbox RasPi
- `startup_pc.sh`: startup script for Recalbox PC

- `install-remote.sh` installs *dynquee* on a non-Recalbox machine
- `dynquee-remote.ini`: config file for non-Recalbox machines
- `dynquee.service`: systemd unit file for non-Recalbox machines

- `find_marquee_output.sh`: helps user discover video outputs on Recalbox PC
- `after_recalbox_upgrade.sh`: run this after a Recalbox upgrade to restore dynquee
- `install_common.sh`: library functions for install/upgrade scripts
