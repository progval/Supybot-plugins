###
# Copyright (c) 2011, Valentin Lorentz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import os

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3 # for python2.4

_ = PluginInternationalization('Variables')

class VariableDoesNotExist(Exception):
    pass

@internationalizeDocstring
class Variables(callbacks.Plugin):
    """Add the help for "@plugin help Variables" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        callbacks.Plugin.__init__(self, irc)
        self._filename = os.path.join(conf.supybot.directories.data(),
                'Variables.db')
        self._load()

    def _load(self):
        if hasattr(self, '_connection'):
            self._connection.close()
        createDatabase = not os.path.exists(self._filename)
        self._connection = sqlite3.connect(self._filename)
        self._connection.text_factory = str
        if createDatabase:
            self._makeDb()

    def _makeDb(self):
        cursor = self._connection.cursor()
        cursor.execute("""CREATE TABLE variables (
                          domainType TEXT,
                          domainName TEXT,
                          variableName TEXT,
                          value TEXT,
                          sticky BOOLEAN
                          )""")
        self._connection.commit()

    def _getDomain(self, irc, msg, opts):
        opts = dict(opts)
        if 'domain' not in opts:
            domainType = 'global'
        else:
            domainType = opts['domain']
        if 'name' not in opts:
            if domainType == 'global':
                domainName = 'default'
            elif domainType == 'channel':
                domainName = msg.args[0]
            elif domainType == 'network':
                domainName = irc.network
        else:
            domainName = opts['name']
        return domainType, domainName

    def _getVariable(self, domainType, domainName, variableName):
        cursor = self._connection.cursor()
        cursor.execute("""SELECT value FROM variables WHERE
                          domainType=? AND domainName=? AND variableName=?""",
                          (domainType, domainName, variableName))
        row = cursor.fetchone()
        if row is None:
            raise VariableDoesNotExist()
        else:
            return row[0]

    @internationalizeDocstring
    def set(self, irc, msg, args, opts, name, value):
        """[--domain <domaintype>] [--name <domainname>] <name> <value>

        Sets a variable called <name> to be <value>, in the domain matching
        the <domaintype> and the <domainname>.
        If <domainname> is not given, it defaults to the current domain
        matching the <domaintype>.
        If <domaintype> is not given, it defaults to the global domain.
        Valid domain types are 'global', 'channel', and 'network'.
        Note that channel domains are channel-specific, but are cross-network.
        """
        domainType, domainName = self._getDomain(irc, msg, opts)
        cursor = self._connection.cursor()
        try:
            self._getVariable(domainType, domainName, name)
            cursor.execute("""DELETE FROM variables WHERE
                              domainType=? AND domainName=? AND
                              variableName=?""",
                          (domainType, domainName, name))
        except VariableDoesNotExist:
            pass
        cursor.execute("""INSERT INTO variables VALUES (?,?,?,?,?)""",
                          (domainType, domainName, name, value, True))
        self._connection.commit()
        irc.replySuccess()
    set = wrap(set, [getopts({'domain': ('literal', ('global', 'network', 'channel')),
                              'name': 'something'}),
                     'something', 'text'])

    @internationalizeDocstring
    def get(self, irc, msg, args, opts, name):
        """[--domain <domaintype>] [--name <domainname>] <name>

        Get the value of the variable called <name>, in the domain matching
        the <domaintype> and the <domainname>.
        If <domainname> is not given, it defaults to the current domain
        matching the <domaintype>.
        If <domaintype> is not given, it defaults to the global domain.
        Valid domain types are 'global', 'channel', and 'network'.
        Note that channel domains are channel-specific, but are cross-network.
        """
        domainType, domainName = self._getDomain(irc, msg, opts)
        try:
            irc.reply(self._getVariable(domainType, domainName, name))
        except VariableDoesNotExist:
            irc.error(_('Variable does not exist.'))

    get = wrap(get, [getopts({'domain': ('literal', ('global', 'network', 'channel')),
                              'name': 'something'}),
                     'something'])


Class = Variables


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
