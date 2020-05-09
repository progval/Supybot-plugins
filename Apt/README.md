Provides read access to APT repositories.

This plugin is a rewrite of PackageInfo using the `python-apt` library instead
of parsing `apt-cache`'s console output.

## Usage

To use it, you must set `$DATADIR/aptdir/etc/apt/sources.list` (where $DATADIR is
configured with `supybot.directories.data`, which defaults to $BOTDIR/data`)
to the list of sources you want to use. See `man sources.list` for supported
format.

You should also either allow insecure sources, or add keys to the trusted
store yourself.

Example:

```
deb [trusted=yes] http://archive.ubuntu.com/ubuntu bionic main universe
deb-src [trusted=yes] http://archive.ubuntu.com/ubuntu bionic main universe
deb [trusted=yes] http://deb.debian.org/debian buster main
deb-src [trusted=yes] http://deb.debian.org/debian buster main
deb [trusted=yes] http://deb.debian.org/debian stretch-backports main
deb-src [trusted=yes] http://deb.debian.org/debian stretch-backports main
```

The bot will then take care of updating these sources, based on the value of
`supybot.plugins.Apt.cache.updateInterval`.


## Foreign architectures

By default, APT only considers packages on the native architecture (the one
the bot is running on, usually amd64 on PC or arm64/armhf/armel on SBCs).

This is usually not a big deal, as the distributions you configure in
`sources.list` usually support your native architecture, and almost all
packages are available for your native architectures.
There are however two cases where you care about this:

1. The distribution doesn't support your native architecture at all
   (eg. your bot is running on a PC but the distribution is Armbian;
   or you're running your bot on a Raspberry Pi and the distribution
   doesn't support ARM).
2. You want to see specific information about packages on foreign
   architectures, using the `--arch` option.

There are [many ways to enable foreign architecture](https://wiki.debian.org/Multiarch/HOWTO),
but the easiest for you is probably just to add them to `sources.list`.
For example:

```
deb [trusted=yes arch=amd64,arm64,armhf] http://deb.debian.org/debian buster main
deb-src [trusted=yes] http://deb.debian.org/debian buster main
```
