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
import cgi
import time
import urllib

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.irclib as irclib
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('WebLogs')

page_template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" >
    <head>
        <title>%(title)s - WebLogs</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
            h1 {
                display: inline;
            }
            .line .timestamp {
                display: none;
            }
            .line:hover .timestamp, .line:focus .timestamp {
                display: inline;
                float: right;
            }
            .command-PART { color: maroon; }
            .command-QUIT { color: maroon; }
            .command-JOIN { color: green; }
            .command-MODE { color: olive; }
            .command-KICK { color: red; }
        </style>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js">
        </script>
        <script>
            $(document).ready(function() {
                $("div.day div").hide();
                $("div.day input.hide").hide();
                $("input.reveal").click(function() {
                        $(this).hide();
                        $(this).parents("div").children("div.day input.hide").fadeIn(600);
                        $(this).parents("div").children("div.day div").fadeIn(600);
                });
                $("input.hide").click(function() {
                        $(this).hide();
                        $(this).parents("div").children("div.day input.reveal").fadeIn(600);
                        $(this).parents("div").children("div.day div").fadeOut(600);
                });
            });
        </script>
    </head>
    <body>
        %(body)s
    </body>
</html>"""

# From http://stackoverflow.com/questions/1071191/detect-urls-in-a-string
URL_REGEXP = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')

def format_logs(logs):
    def format_nick(nick):
        template = '<span style="color: %(color)s;">%(nick)s</span>'
        colors = ['red', 'orange', 'blue', 'lime', 'grey', 'green', 'purple',
                'black', 'olive']
        hash_ = sum([ord(x) for x in nick]) % len(colors)
        return template % {'color': colors[hash_], 'nick': nick}
    html_logs = '<div>' # Will be closed by the first "Changed day"
    old_gmtime_day = None
    for line in logs.split('\n'):
        words = line.split(' ')
        if len(words) < 2:
            continue
        timestamp = words[0]
        command = words[1]
        new_line = None
        if command == 'PRIVMSG' or command == 'NOTICE':
            if command == 'PRIVMSG':
                nick_delimiters = ('&lt;', '&gt;')
            else:
                nick_delimiters = ('*', '*')
            formatted_nick = nick_delimiters[0] + format_nick(words[2]) + \
                    nick_delimiters[1]
            new_line = _('%(formatted_nick)s %(message)s') % {
                    'formatted_nick': formatted_nick,
                    'message': cgi.escape(' '.join(words[3:]))}
        elif command == 'PRIVMSG-ACTION':
            new_line = _('* %(nick)s %(message)s') % {
                    'nick': format_nick(words[2]),
                    'message': cgi.escape(' '.join(words[3:]))}
        elif command == 'PART':
            new_line = _('<-- %(nick)s has left the channel (%(reason)s)') % \
                    {'nick': format_nick(words[2]),
                    'reason': cgi.escape(' '.join(words[3:]))}
        elif command == 'QUIT':
            new_line = _('<-- %(nick)s has quit the network (%(reason)s)') % \
                    {'nick': format_nick(words[2]),
                    'reason': cgi.escape(' '.join(words[3:]))}
        elif command == 'JOIN':
            new_line = _('--> %(nick)s has joined the channel') % \
                    {'nick': format_nick(words[2])}
        elif command == 'MODE':
            new_line = _('*/* %(nick)s has set mode %(modes)s') % \
                    {'nick': format_nick(words[2]),
                    'modes': ' '.join(words[3:])}
        elif command == 'KICK':
            new_line = _('<-- %(kicked)s has been kicked by %(kicker)s (%(reason)s)') % \
                    {'kicked': format_nick(words[3]),
                    'kicker': format_nick(words[2]),
                    'reason': cgi.escape(' '.join(words[4:]))}
        if new_line is not None:
            template = """
                <div class="line command-%(command)s">
                    <span class="timestamp">%(timestamp)s</span>
                    %(line)s
                </div>"""
            new_line = URL_REGEXP.sub(r'<a href="\1">\1</a>', new_line)

            # Timestamp handling
            gmtime = time.gmtime(int(words[0]))
            gmtime_day = (gmtime.tm_mday, gmtime.tm_mon, gmtime.tm_year)
            if old_gmtime_day != gmtime_day:
                html_logs += '</div><div class="day">'
                html_logs += """
                    <input type="button" value="reveal" class="reveal" />
                    <input type="button" value="hide" class="hide" />
                    """
                html_logs += '<h1>%i/%i/%i</h1>' % \
                        gmtime_day
                old_gmtime_day = gmtime_day
            timestamp = time.strftime('%H:%M:%S', gmtime)


            html_logs += template % {'line': new_line,
                    'timestamp': timestamp, 'command': command}
    return html_logs


class WebLogsMiddleware(object):
    """Class for reading and parsing WebLogs data."""
    __shared_states = {}
    def __init__(self, channel):
        if channel in self.__shared_states:
            self.__dict__ = self.__shared_states[channel]
        else:
            self._channel = channel
            path = conf.supybot.directories.data.dirize('WebLogs_%s.log' %
                    channel)
            self.fd = open(path, 'a+')
            self.__shared_states.update({channel: self.__dict__})

    @classmethod
    def get_channel_list(cls):
        channels = [x[len('WebLogs_'):-len('.log')]
                for x in os.listdir(conf.supybot.directories.data())
                if x.endswith('.log')]
        return [x for x in channels
                if cls._plugin.registryValue('enabled', x)]

    def get_logs(self):
        self.fd.seek(0)
        return self.fd.read()

    def write(self, *args):
        self.fd.read()
        self.fd.write('%i %s\n' % (time.time(), ' '.join(args)))

class WebLogsServerCallback(httpserver.SupyHTTPServerCallback):
    name = 'WebLogs'

    def doGet(self, handler, path):
        if path == '':
            self.send_response(301)
            self.send_header('Location', '/weblogs/')
            self.end_headers()
            return
        elif path == '/':
            splitted_path = []
        else:
            splitted_path = path[1:].split('/')
        if len(splitted_path) == 0:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            page_body = """Here is a list of available logs:<ul>"""
            for channel in WebLogsMiddleware.get_channel_list():
                page_body += '<li><a href="./html/%s/">%s</a></li>' % (
                        utils.web.urlquote(channel), channel)
            page_body += '</ul>'
            self.wfile.write(page_template %
                    {'title': 'Index', 'body': page_body})
            return
        elif len(splitted_path) == 3:
            mode, channel, page = splitted_path
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Bad URL.')
            return
        assert mode in ('html', 'json')
        channel = utils.web.urlunquote(channel)
        if channel not in WebLogsMiddleware.get_channel_list():
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('This channel is not logged.')
            return

        middleware = WebLogsMiddleware(channel)
        if page == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(page_template % {
                'title': channel,
                'body': format_logs(middleware.get_logs())})

def check_enabled(f):
    def newf(self, irc, msg):
        channel = msg.args[0]
        if irc.isChannel(channel) and self.registryValue('enabled', channel):
            return f(self, irc, msg, WebLogsMiddleware(channel))
        return msg
    return newf

@internationalizeDocstring
class WebLogs(callbacks.Plugin):
    """Add the help for "@plugin help WebLogs" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        # Some stuff needed by Supybot
        self.__parent = super(WebLogs, self)
        callbacks.Plugin.__init__(self, irc)

        self.lastStates = {}
        WebLogsMiddleware._plugin = self

        # registering the callback
        callback = WebLogsServerCallback() # create an instance of the callback
        httpserver.hook('weblogs', callback)

    @check_enabled
    def doPrivmsg(self, irc, msg, middleware):
        if ircmsgs.isAction(msg):
            middleware.write('PRIVMSG-ACTION', msg.nick,
                    ircmsgs.unAction(msg))
        else:
            middleware.write('PRIVMSG', msg.nick, msg.args[1])

    @check_enabled
    def outFilter(self, irc, msg, middleware):
        if msg.command == 'PRIVMSG':
            middleware.write('PRIVMSG', irc.nick, msg.args[1])
        elif msg.command == 'NOTICE':
            middleware.write('NOTICE', irc.nick, msg.args[1])
        return msg

    @check_enabled
    def doNotice(self, irc, msg, middleware):
        middleware.write('NOTICE', msg.nick, msg.args[1])

    @check_enabled
    def doPart(self, irc, msg, middleware):
        if len(msg.args) == 1:
            reason = ''
        else:
            reason = msg.args[1]
        middleware.write('PART', msg.nick, reason)

    @check_enabled
    def doJoin(self, irc, msg, middleware):
        middleware.write('JOIN', msg.nick)

    @check_enabled
    def doMode(self, irc, msg, middleware):
        middleware.write('MODE', msg.nick, msg.args[1], ' '.join(msg.args[2:]))

    @check_enabled
    def doKick(self, irc, msg, middleware):
        middleware.write('KICK', msg.nick, ' '.join(msg.args[1:]))

    def __call__(self, irc, msg):
        self.__parent.__call__(irc, msg)
        self.lastStates[irc] = irc.state.copy()
    def doQuit(self, irc, msg):
        if len(msg.args) == 0:
            reason = ''
        else:
            reason = msg.args[0]

        if not isinstance(irc, irclib.Irc):
            irc = irc.getRealIrc()
        for (channel, chan) in self.lastStates[irc].channels.iteritems():
            if msg.nick in chan.users:
                if self.registryValue('enabled', channel):
                    middleware = WebLogsMiddleware(channel)
                    middleware.write('QUIT', msg.nick, reason)

    def die(self):
        # unregister the callback
        httpserver.unhook('weblogs')

        # Stuff for Supybot
        self.__parent.die()

Class = WebLogs


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
