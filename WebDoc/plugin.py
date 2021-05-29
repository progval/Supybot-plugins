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
import html
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WebDoc')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

PAGE_SKELETON = """\
<!DOCTYPE html>
 <html>
    <head>
        <meta charset="UTF-8" />
        <title>Supybot web documentation</title>
        <link rel="stylesheet" media="screen" type="text/css" title="Design" href="/default.css" />
    </head>
    <body class="%s">
%s
    </body>
</html>
"""

DEFAULT_TEMPLATES = {
        'webdoc/index.html': PAGE_SKELETON % ('purelisting', """\
<h1>Loaded plugins</h1>

<ul class="pluginslist">
%(plugins)s
</ul>"""),
        'webdoc/plugin.html': PAGE_SKELETON % ('puretable', """\
<a href="../">Plugin list</a>

<h1>%(plugin)s</h1>

<p>%(description)s</p>

<table>
    <tr>
        <th>Command</th>
        <th>Help</th>
    </tr>
%(table)s
</table>"""),
        }

httpserver.set_default_templates(DEFAULT_TEMPLATES)

class WebDocServerCallback(httpserver.SupyHTTPServerCallback):
    def __init__(self, plugin, irc):
        super(WebDocServerCallback, self).__init__()
        self._irc = irc
        self._plugin = plugin
    name = 'WebDoc'
    def doGet(self, handler, path):
        splitted_path = path.split('/')
        if len(splitted_path) == 2:
            names = filter(lambda x: conf.supybot.plugins.get(x).public(),
                    map(lambda cb:cb.name(), self._irc.callbacks))
            plugins = ''.join(map(lambda x:'<li><a href="%s/">%s</a></li>'%(x,x),
                sorted(names)))
            response = 200
            output = httpserver.get_template('webdoc/index.html') % {
                    'plugins': plugins,
                    }
        elif len(splitted_path) == 3:
            name = splitted_path[1]
            cbs = dict(map(lambda cb:(cb.name(), cb),
                self._irc.callbacks))
            if name not in cbs or \
                    not conf.supybot.plugins.get(name).public():
                response = 404
                output = httpserver.get_template('generic/error.html') % \
                    {'title': 'PluginsDoc',
                     'error': 'Requested plugin is not found. Sorry.'}
            else:
                response = 200
                callback = cbs[name]
                commands = callback.listCommands()
                description = callback.__doc__
                if not description or description.startswith('Add the help for'):
                    description = ''
                if commands:
                    commands.sort()
                def formatter(command):
                    command = list(map(callbacks.canonicalName,
                        command.split(' ')))
                    doc = callback.getCommandMethod(command).__doc__
                    if not doc:
                        return '<tr><td>%s</td><td> </td></tr>' % \
                                ' '.join(command)
                    doclines = doc.splitlines()
                    if self._plugin.registryValue('withFullName'):
                        s = '%s %s %s' % (name, ' '.join(command), doclines.pop(0))
                    else:
                        s = doclines.pop(0)
                    s = html.escape(s)
                    if doclines:
                        help_ = html.escape('\n'.join(doclines))
                        s = '<strong>%s</strong><br />%s' % \
                                (s, help_)
                    return '<tr><td>%s</td><td>%s</td></tr>' % \
                            (' '.join(command), s)

                table = ''.join(map(formatter, commands))
                output = httpserver.get_template('webdoc/plugin.html') % {
                        'plugin': name,
                        'table': table,
                        'description': description
                        }
                
        self.send_response(response)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        if sys.version_info[0] >= 3:
            output = output.encode()
        self.wfile.write(output)
                

class WebDoc(callbacks.Plugin):
    """Add the help for "@plugin help WebDoc" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        self.__parent = super(WebDoc, self)
        callbacks.Plugin.__init__(self, irc)

        callback = WebDocServerCallback(self, irc)
        httpserver.hook('plugindoc', callback)

    def die(self):
        httpserver.unhook('plugindoc')
        self.__parent.die()


Class = WebDoc


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
