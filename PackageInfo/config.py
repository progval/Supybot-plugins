# -*- Encoding: utf-8 -*-
###
# Copyright (c) 2008-2010 Terence Simpson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    def makeSource(release):
        return """deb http://archive.ubuntu.com/ubuntu/ %s main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu/ %s main restricted universe multiverse
""" % (release, release)
#"""

    from supybot.questions import output, expect, something, yn
    import subprocess
    import os

    def anything(prompt, default=None):
        """Because supybot is pure fail"""
        from supybot.questions import expect
        return expect(prompt, [], default=default)

    PackageInfo = conf.registerPlugin('PackageInfo', True)

    enabled = yn("Enable this plugin in all channels?", default=True)

    if enabled and advanced:
        prefixchar = something("Which prefix character should be bot respond to?", default=PackageInfo.prefixchar._default)
        defaultRelease = something("What should be the default distrobution when not specified?", default=PackageInfo.defaultRelease._default)
        aptdir = something("Which directory should be used for the apt cache when looking up packages?", default=PackageInfo.aptdir._default)

        # People tend to thing this should be /var/cache/apt
        while aptdir.startswith('/var'): #NOTE: This is not a good hack. Maybe just blacklist /var/cache/apt (or use apt to report back the cache dir)
            output("NO! Do not use your systems apt directory")
            aptdir = something("Which directory should be used for the apt cache when looking up packages?", default=PackageInfo.aptdir._default)

    else:
        prefixchar = PackageInfo.prefixchar._default
        defaultRelease = PackageInfo.defaultRelease._default
        aptdir = PackageInfo.aptdir._default


    PackageInfo.enabled.setValue(enabled)
    PackageInfo.aptdir.setValue(aptdir)
    PackageInfo.prefixchar.setValue(prefixchar)
    PackageInfo.defaultRelease.setValue(defaultRelease)

    default_dists = set(['dapper', 'hardy', 'lucid', 'maveric', 'natty', 'oneiric'])
    pluginDir = os.path.abspath(os.path.dirname(__file__))
    update_apt = os.path.join(pluginDir, 'update_apt')
    update_apt_file = os.path.join(pluginDir, 'update_apt_file')

    default_dists.add(defaultRelease)

    ## Create the aptdir
    try:
        os.makedirs(aptdir)
    except OSError: # The error number would be OS dependant (17 on Linux 2.6, ?? on others). So just pass on this
        pass

    for release in default_dists:
        filename = os.path.join(aptdir, "%s.list" % release)
        try:
            output("Creating %s" % filename)
            fd = open(filename, 'wb')
            fd.write("# Apt sources list for Ubuntu %s\n" % release)
            fd.write(makeSource(release))
            fd.write(makeSource(release + '-security'))
            fd.write(makeSource(release + '-updates'))
            fd.close()

            for sub in ('backports', 'proposed'):
                sub_release = "%s-%s" % (release, sub)
                filename = os.path.join(aptdir, "%s.list" % sub_release)
                output("Creating %s" % filename)
                fd = open(filename, 'wb')
                fd.write("# Apt sources list for Ubuntu %s\n" % release)
                fd.write(makeSource(sub_release))
                fd.close()
        except Exception as e:
            output("Error writing to %r: %r (%s)" % (filename, str(e), type(e)))

    if yn("In order for the plugin to use these sources, you must run the 'update_apt' script, do you want to do this now?", default=True):
        os.environ['DIR'] = aptdir # the update_apt script checks if DIR is set and uses it if it is
        if subprocess.getstatus(update_apt) != 0:
            output("There was an error running update_apt, please run '%s -v' to get more information" % update_apt)

    if subprocess.getstatusoutput('which apt-file') != 0:
        output("You need to install apt-file in order to use the !find command of this plugin")
    else:
        if yn("In order for the !find command to work, you must run the 'update_apt_file' script, do you want to do this now?", default=True):
            os.environ['DIR'] = aptdir # the update_apt_file script checks if DIR is set and uses it if it is
            if subprocess.getstatusoutput(update_apt_file) != 0:
                output("There was an error running update_apt_file, please run '%s -v' to get more information" % update_apt_file)

PackageInfo = conf.registerPlugin('PackageInfo')
conf.registerChannelValue(PackageInfo, 'enabled',
    registry.Boolean(True, "Enable package lookup"))
conf.registerChannelValue(PackageInfo, 'prefixchar',
    conf.ValidPrefixChars('!', "Character the bot will respond to"))
conf.registerChannelValue(PackageInfo, 'defaultRelease',
    registry.String('natty', "Default release to use when none is specified"))
conf.registerGlobalValue(PackageInfo, 'aptdir',
    conf.Directory(conf.supybot.directories.data.dirize('aptdir'), "Path to the apt directory", private=True))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
