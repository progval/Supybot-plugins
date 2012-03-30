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

import re
import os
import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.registry as registry
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Sudo')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x
try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3 # for python2.4

class DuplicatedName(Exception):
    pass
class NonExistantName(Exception):
    pass

class SudoRule:
    def __init__(self, priority, mode, hostmask, regexp):
        self.priority = int(priority)
        self.mode = mode
        self.hostmask = hostmask
        self.regexp = regexp

    def __repr__(self):
        return '\n'.join([str(self.priority), self.mode, self.hostmask,
                          self.regexp])

class SudoDB:
    def __init__(self):
        self.rules = {}

    def add(self, name, rule):
        """Add a rule with the given ID."""
        if name in self.rules:
            raise DuplicatedName()
        self.rules.update({name: rule})

    def remove(self, name):
        """Remove the rule associated with the name, and returns it."""
        if name not in self.rules:
            raise NonExistantName()
        return self.rules.pop(name)

    def getRuleMatching(self, command):
        currentName = None
        currentRule = None
        for name, rule in self.rules.items():
            if not re.match(rule.regexp, command):
                continue
            if currentRule is None or currentRule.priority < rule.priority:
                currentName = name
                currentRule = rule
        if currentRule is None or currentRule.mode == 'deny':
            return None, None
        return currentName, currentRule

    def save(self, file_):
        file_.write(repr(self))

    def load(self, file_):
        currentName = None
        currentArgs = []
        for line in file_:
            if line != '\n' and currentName is None:
                currentName = line[0:-1]
            elif currentName is not None and len(currentArgs) != 4:
                currentArgs.append(line[0:-1])
            elif currentName is not None:
                self.rules.update({currentName: SudoRule(*currentArgs)})
                currentName = None
                currentArgs = []
        if currentName is not None:
            assert currentArgs != []
            self.rules.update({currentName: SudoRule(*currentArgs)})


    def __repr__(self):
        return '\n\n'.join(['%s\n%s' % (x,repr(y))
                            for x,y in self.rules.items()]) + '\n'





@internationalizeDocstring
class Sudo(callbacks.Plugin):
    """Plugin that allows to run commands as someone else"""
    def __init__(self, irc):
        callbacks.Plugin.__init__(self, irc)
        self.db = SudoDB()
        self._path = os.path.join(conf.supybot.directories.data(), 'sudo.db')
        if not world.testing and os.path.isfile(self._path):
            self.db.load(open(self._path, 'ru'))

    @internationalizeDocstring
    def add(self, irc, msg, args, priority, name, mode, hostmask, regexp):
        """[<priority>] <name> {allow,deny} [<hostmask>] <regexp>

        Sets a new Sudo rule, called <name> with the given <priority>
        (greatest numbers have precedence),
        allowing or denying to run commands matching the pattern <regexp>,
        from users to run commands as wearing the <hostmask>.
        The <priority> must be a relative integer.
        If <priority> is not given, it defaults to 0.
        The <hostmask> defaults to your hostmask.
        The <hostmask> is only needed if you set an 'allow' rule.
        """
        try:
            if mode == 'deny' and hostmask is not None:
                irc.error(_('You don\'t have to give a hostmask when setting '
                            'a "deny" rule.'))
                return
            if hostmask is None:
                hostmask = msg.prefix
            if priority is None:
                priority = 0
            self.db.add(name, SudoRule(priority, mode, hostmask, regexp))
        except DuplicatedName:
            irc.error(_('This name already exists'))
            return
        irc.replySuccess()
    add = wrap(add, ['owner', optional('int'), 'something',
                     ('literal', ('allow', 'deny')), optional('hostmask'),
                     'text'])

    @internationalizeDocstring
    def remove(self, irc, msg, args, name):
        """<id>

        Remove a Sudo rule."""
        try:
            self.db.remove(name)
        except NonExistantId:
            irc.error(_('This name does not exist.'))
            return
        irc.replySuccess()
    remove = wrap(remove, ['owner', 'something'])

    @internationalizeDocstring
    def sudo(self, irc, msg, args, command):
        """<command> [<arg1> [<arg2> ...]]

        Runs the command following the Sudo rules."""
        name, rule = self.db.getRuleMatching(command)
        bannedChars = conf.supybot.commands.nested.brackets()
        if name is None:
            log.warning('Sudo not granted to "%s"' % msg.prefix)
            irc.error(_('Sudo not granted.'))
        else:
            assert rule is not None
            log.info('Sudo granted to "%s" with rule %s' % (msg.prefix, name))
            msg.prefix = rule.hostmask
            tokens = callbacks.tokenize(command)
            msg.nick = msg.prefix.split('!')[0]
            self.Proxy(irc.irc, msg, tokens)
    sudo = wrap(sudo, ['text'])

    @internationalizeDocstring
    def fakehostmask(self, irc, msg, args, hostmask, command):
        """<hostmask> <command>

        Runs <command> as if you were wearing the <hostmask>. Of course, usage
        of the command is restricted to the owner."""
        log.info('fakehostmask used to run "%s" as %s' % (command, hostmask))
        msg.prefix = hostmask
        tokens = callbacks.tokenize(command)
        self.Proxy(irc.irc, msg, tokens)
    fakehostmask = wrap(fakehostmask, ['owner', 'hostmask', 'text'])

    def die(self):
        if not world.testing:
            try:
                os.unlink(self._path)
            except OSError:
                pass
            self.db.save(open(self._path, 'au'))
        callbacks.Plugin.die(self)


Class = Sudo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
