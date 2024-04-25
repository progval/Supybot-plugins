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

"""
Display information on packages using apt-cache and search for files in packages with apt-file.
"""

from importlib import reload
import supybot
import supybot.world as world

__version__ = "0.9.1"
__author__ = supybot.Author("Terence Simpson", "tsimpson", "tsimpson@ubuntu.com")
__contributors__ = {
    supybot.Author("Dennis Kaarsemaker","Seveas","dennis@kaarsemaker.net"): ["Origional concept"]
}
__url__ = 'https://launchpad.net/ubuntu-bots/'

from . import config
reload(config)
from . import plugin
reload(plugin) # In case we're being reloaded.
from . import packages
reload(packages)
# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!

if world.testing:
    from . import test

Class = plugin.Class
configure = config.configure


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
