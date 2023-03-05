# Restoring *dynquee* After A Recalbox Upgrade

When performing an upgrade, Recalbox generally leaves `/recalbox/share/` untouched.
However, the contents of `/etc/init.d/` are usually overwritten which will prevent *dynquee* launching at startup.

To fix this, log in to Recalbox [via ssh][recalbox-ssh] or at the console and restore the init script
by entering the following:

```sh
cd /recalbox/share/dynquee
mount -o rw,remount /
cp -vf install/S32dynquee /etc/init.d/
chmod -v +x /etc/init.d/S32dynquee
mount -o ro,remount /
```

[recalbox-ssh]: https://wiki.recalbox.com/en/tutorials/system/access/root-access-terminal-cli
