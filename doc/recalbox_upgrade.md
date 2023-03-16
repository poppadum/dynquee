# Restoring *dynquee* After A Recalbox Upgrade

When performing an upgrade, Recalbox generally leaves everything in `/recalbox/share/` untouched.
But changes made elsewhere (such as to init or startup scripts) will usually be overwritten by a Recalbox upgrade

To fix this, log in to Recalbox [via ssh][recalbox-ssh] or at the console and restore the changes
by entering the following:

```sh
cd /recalbox/share/dynquee
install/after_recalbox_upgrade.sh
```

<!-- Links -->
[recalbox-ssh]: https://wiki.recalbox.com/en/tutorials/system/access/root-access-terminal-cli
