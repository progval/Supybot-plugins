###
# Copyright (c) 2013, Valentin Lorentz
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

import sys
import json
import logging

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('StdoutCapture')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class StdoutBuffer:
    _buffer = utils.structures.RingBuffer(100)
    def __init__(self, stdout):
        self._real = stdout
    def write(self, data):
        self._real.write(data)
        if data == '\n':
            self._buffer[-1] += '\n'
        else:
            self._buffer.append(data)
    def __getattr_(self, name):
        sys.stderr.write(repr(name))

class StdoutCapture(callbacks.Plugin):
    """Add the help for "@plugin help StdoutCapture" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        super(StdoutCapture, self).__init__(irc)
        self.StdoutBuffer = StdoutBuffer
        sys.stdout = self.StdoutBuffer(sys.stdout)
        sys.stderr = self.StdoutBuffer(sys.stderr)
        # I'm being a bit evil here.
        for logger in logging._handlerList:
            logger = logger() # That's a weakref
            if logger.stream is sys.stdout._real:
                logger.stream = sys.stderr
            elif logger.stream is sys.stderr._real:
                logger.stream = sys.stderr
    def die(self):
        super(self.__class__, self).die()
        assert isinstance(sys.stdout, self.StdoutBuffer)
        assert isinstance(sys.stdout, self.StdoutBuffer)
        for logger in logging._handlerList:
            logger = logger()
            if not hasattr(logger, 'stream'):
                continue
            if logger.stream is sys.stdout:
                logger.stream = sys.stderr._real
            elif logger.stream is sys.stderr:
                logger.stream = sys.stderr._real
        sys.stdout = sys.stdout._real
        sys.stderr = sys.stderr._real

    def history(self, irc, msg, args, number):
        """<number>

        Return the last lines displayed in the console."""
        irc.replies(StdoutBuffer._buffer[-number:])
    history = wrap(history, ['positiveInt', 'owner'])

    def pastebin(self, irc, msg, args, number, url=None):
        """<number> [<pastebin url>]

        Paste the last lines displayed in the console on a pastebin and
        returns the URL.
        The pastebin has to support the LodgeIt API."""
        base = url or self.registryValue('pastebin', msg.args[0])
        if base.endswith('/'):
            base = base[0:-1]
        fd = utils.web.getUrlFd(base+'/json/?method=pastes.newPaste',
                data=json.dumps({
                    'language': 'text',
                    'code': ''.join(StdoutBuffer._buffer[-number:]),
                    }),
                headers={'Content-Type': 'application/json'})
        irc.reply('%s/show/%s' % (base, json.load(fd)['data']))

    pastebin = wrap(pastebin, ['owner', 'positiveInt', optional('text')])


Class = StdoutCapture


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
