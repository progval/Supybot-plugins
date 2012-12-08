###
# Copyright (c) 2012, Valentin Lorentz
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

import json

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Redmine')

def fetch(site, uri, **kwargs):
    url = site['url'] + uri + '.json'
    if kwargs:
        url += '?' + utils.web.urlencode(kwargs)
    return json.load(utils.web.getUrlFd(url))

class ProjectNotFound(Exception):
    pass

class AmbiguousProject(Exception):
    pass

def get_project(site, project):
    projects = []
    for variable in ('id', 'identifier', 'name'):
        projects = filter(lambda x:x[variable] == project,
                fetch(site, 'projects')['projects'])
        if projects:
            break
    if not projects:
        raise ProjectNotFound()
    elif len(projects) > 1:
        raise AmbiguousProject()
    else:
        return projects[0]

def handle_site_arg(wrap_args):
    """Decorator for handling the <site> argument of all commands, because
    I am lazy."""
    if 'project' in wrap_args:
        assert wrap_args[0] == 'project'
        wrap_args[0] = 'somethingWithoutSpaces'
        project = True
    else:
        project = False
    assert 'project' not in wrap_args
    wrap_args = [optional('somethingWithoutSpaces')] + wrap_args

    def decorator(f):
        def newf(self, irc, msg, args, site_name, *args2):
            if not site_name:
                site_name = self.registryValue('defaultsite', msg.args[0])
                if not site_name:
                    irc.error(_('No default site.'), Raise=True)
            sites = self.registryValue('sites')
            if site_name not in sites:
                irc.error(_('Invalid site name.'), Raise=True)
            site = sites[site_name]

            # Handle project converter
            if project:
                try:
                    args2 = (get_project(site, args2[0]),) + tuple(args[1:])
                except ProjectNotFound:
                    irc.error(_('Project not found.'), Raise=True)
                except AmbiguousProject:
                    irc.error(_('Ambiguous project name.'), Raise=True)

            return f(self, irc, msg, args, site, *args2)
            
        newf.__doc__ = """[<site>] %s
            
            If <site> is not given, it defaults to the default set for this
            channel, if any.
            """ % f.__doc__
        return wrap(newf, wrap_args)
    return decorator

@internationalizeDocstring
class Redmine(callbacks.Plugin):
    """Add the help for "@plugin help Redmine" here
    This should describe *how* to use this plugin."""
    threaded = True

    class site(callbacks.Commands):
        conf = conf.supybot.plugins.Redmine
        @internationalizeDocstring
        def add(self, irc, msg, args, name, url):
            """<name> <base url>

            Add a site to the list of known redmine sites."""
            if not url.endswith('/'):
                url += '/'
            if name == '':
                irc.error(_('Invalid site name.'), Raise=True)
            if name in self.conf.sites():
                irc.error(_('This site name is already registered.'), Raise=True)
            try:
                data = json.load(utils.web.getUrlFd(url + 'projects.json'))
                assert 'total_count' in data
            except:
                irc.error(_('This is not a valid Redmine site.'), Raise=True)
            with self.conf.sites.editable() as sites:
                sites[name] = {'url': url}
            irc.replySuccess()
        add = wrap(add, ['admin', 'somethingWithoutSpaces', 'url'])

        @internationalizeDocstring
        def remove(self, irc, msg, args, name):
            """<name>

            Remove a site form the list of known redmine sites."""
            if name not in self.conf.sites():
                irc.error(_('This site name does not exist.'), Raise=True)
            with self.conf.sites.editable() as sites:
                del sites[name]
            irc.replySuccess()
        remove = wrap(remove, ['admin', 'somethingWithoutSpaces'])

        @internationalizeDocstring
        def list(self, irc, msg, args):
            """takes no arguments

            Return the list of known redmine sites."""
            sites = self.conf.sites().keys()
            if sites:
                irc.reply(format('%L', sites))
            else:
                irc.reply(_('No registered Redmine site.'))
        list = wrap(list, [])

    @internationalizeDocstring
    @handle_site_arg([])
    def projects(self, irc, msg, args, site):
        """

        Return the list of projects of the Redmine <site>."""
        projects = map(lambda x:self.registryValue('format.projects') % x,
                fetch(site, 'projects')['projects'])
        irc.reply(format('%L', projects))

    @internationalizeDocstring
    @handle_site_arg(['project'])
    def issues(self, irc, msg, args, site, project):
        """<project>

        Return the list of issues of the <project> on the Redmine <site>."""
        issues = fetch(site, 'issues', project_id=project['id'],
                sort='updated_on:desc')['issues']
        new_issues = []
        for issue in issues:
            new_issue = {}
            for key, value in issue.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        new_issue['%s__%s' % (key, subkey)] = subvalue
                else:
                    new_issue[key] = value
            new_issues.append(new_issue)
        issues = map(lambda x:self.registryValue('format.issues') % x,
                new_issues)
        irc.reply(format('%L', issues))

Class = Redmine


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
