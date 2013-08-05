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
import urllib

import supybot.utils as utils
from supybot.commands import *
import supybot.world as world
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('ChannelStatus')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

PAGE_SKELETON = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Channel status</title>
<link rel="stylesheet" href="/default.css" />
</head>
%s
</html>"""

DEFAULT_TEMPLATES = {
        'channelstatus/index.html': PAGE_SKELETON % """\
<body class="purelisting">
    <h1>Channels</h1>
    <ul>
        %(channels)s
    </ul>
</body>""",
        'channelstatus/channel.html': PAGE_SKELETON % """\
<body class="purelisting">
    <h1>%(channel)s@%(network)s</h1>
    <h2>Topic</h2>
    %(topic)s
    <h2>Users</h2>
    %(nicks)s
</body>""",
}

httpserver.set_default_templates(DEFAULT_TEMPLATES)

if sys.version_info[0] >= 3:
    quote = urllib.parse.quote
    unquote = urllib.parse.unquote
else:
    quote = urllib.quote
    unquote = urllib.unquote

class ChannelStatusCallback(httpserver.SupyHTTPServerCallback):
    name = 'Channels status'

    def _invalidChannel(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(httpserver.get_template('generic/error.html')%
            {'title': 'ChannelStatus - not a channel',
             'error': 'This is not a channel'})

    def doGet(self, handler, path):
        parts = path.split('/')[1:]
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            template = httpserver.get_template('channelstatus/index.html')
            channels = set()
            for irc in world.ircs:
                channels |= set(['<li><a href="./%s/">%s@%s</a></li>' %
                    (quote('%s@%s' % (x, irc.network)), x, irc.network)
                    for x in irc.state.channels.keys()
                    if self._plugin.registryValue('listed', x)])
            channels = list(channels)
            channels.sort()
            self._write(template % {'channels': ('\n'.join(channels))})
        elif len(parts) == 2:
            (channel, network) = unquote(parts[0]).split('@')
            if not ircutils.isChannel(channel):
                self._invalidChannel()
                return
            for irc in world.ircs:
                if irc.network == network:
                    break
            if irc.network != network or channel not in irc.state.channels:
                self._invalidChannel()
                return
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            state = irc.state.channels[channel]
            replacements = {'channel': channel, 'network': network,
                    'nicks': _('Private'), 'topic': _('Private')}
            if self._plugin.registryValue('topic', channel):
                replacements['topic'] = state.topic
            if self._plugin.registryValue('nicks', channel):
                replacements['nicks'] = '<ul>' + \
                        '\n'.join(sorted(['<li>%s</li>' % x
                            for x in state.users])) + \
                        '</ul>'
            template = httpserver.get_template('channelstatus/channel.html')
            self._write(template % replacements)
    def _write(self, s):
        if sys.version_info[0] >= 3 and isinstance(s, str):
            s = s.encode()
        self.wfile.write(s)


class ChannelStatus(callbacks.Plugin):
    """Add the help for "@plugin help ChannelStatus" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        callbacks.Plugin.__init__(self, irc)
        self._startHttp()
    def _startHttp(self):
        callback = ChannelStatusCallback()
        callback._plugin = self
        httpserver.hook('channelstatus', callback)
        self._http_running = True
    def _stopHttp(self):
        httpserver.unhook('channelstatus')
        self._http_running = False
    def die(self):
        self._stopHttp()
        super(self.__class__, self).die()


Class = ChannelStatus


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
