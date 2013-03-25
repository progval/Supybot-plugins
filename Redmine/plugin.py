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

import sys
import json
import time

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Redmine')

class ResourceNotFound(Exception):
    pass

class AmbiguousResource(Exception):
    pass

class AccessDenied(Exception):
    pass

def fetch(site, uri, **kwargs):
    url = site['url'] + uri + '.json'
    if kwargs:
        url += '?' + utils.web.urlencode(kwargs).decode()
    try:
        data = utils.web.getUrl(url)
        if sys.version_info[0] >= 3:
            data = data.decode('utf8')
        return json.loads(data)
    except utils.web.Error:
        raise ResourceNotFound()

def flatten_subdicts(dicts):
    """Change dict of dicts into a dict of strings/integers. Useful for
    using in string formatting."""
    flat = {}
    for key, value in dicts.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                flat['%s__%s' % (key, subkey)] = subvalue
        else:
            flat[key] = value
    return flat

def get_project(site, project):
    projects = []
    for variable in ('id', 'identifier', 'name'):
        projects = list(filter(lambda x:x[variable] == project,
                fetch(site, 'projects')['projects']))
        if projects:
            break
    projects = list(projects)
    if not projects:
        raise ResourceNotFound()
    elif len(projects) > 1:
        raise AmbiguousResource()
    else:
        return projects[0]

def get_project_or_error(irc, site, project):
    try:
        return get_project(site, project)
    except ResourceNotFound:
        irc.error(_('Project not found.'), Raise=True)
    except AmbiguousResource:
        irc.error(_('Ambiguous project name.'), Raise=True)

def get_user(site, user):
    if user.isdigit():
        return fetch(site, 'users/%s' % user)
    else:
        # TODO: Find a way to get user data from their name...
        # (authenticating as admin seems the only way)
        raise AccessDenied()

def get_user_or_error(irc, site, user):
    try:
        return get_user(site, user)
    except ResourceNotFound:
        irc.error(_('User not found.'), Raise=True)
    except AmbiguousResource:
        irc.error(_('Ambiguous user name.'), Raise=True)
    except AccessDenied:
        irc.error(_('Cannot get a user id from their name.'), Raise=True)

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

    _last_fetch = {} # {site: (time, data)}
    def __call__(self, irc, msg):
        super(Redmine, self).__call__(irc, msg)
        with self.registryValue('sites', value=False).editable() as sites:
            assert isinstance(sites, dict), repr(sites)
            for site_name, site in sites.items():
                if 'interval' not in site:
                    site['interval'] = 60
                if site_name in self._last_fetch:
                    last_time, last_data = self._last_fetch[site_name]
                    if last_time>time.time()-site['interval']:
                        continue
                data = fetch(site, 'issues', sort='updated_on:desc')
                self._last_fetch[site_name] = (time.time(), data)
                if 'last_time' not in locals():
                    continue
                try:
                    last_update = last_data['issues'][0]['updated_on']
                except IndexError:
                    # There was no issue submitted before
                    last_update = ''

                announces = []
                for issue in data['issues']:
                    if issue['updated_on'] <= last_update:
                        break
                    announces.append(issue)
                for channel in irc.state.channels:
                    if site_name in self.registryValue('announce.sites',
                            channel):
                        format_ = self.registryValue('format.announces.issue',
                                channel)
                        for issue in announces:
                            s = format_ % flatten_subdicts(issue)
                            if sys.version_info[0] < 3:
                                s = s.encode('utf8', errors='replace')
                            msg = ircmsgs.privmsg(channel, s)
                            irc.sendMsg(msg)



    class site(callbacks.Commands):
        conf = conf.supybot.plugins.Redmine
        @internationalizeDocstring
        def add(self, irc, msg, args, name, url):
            """<name> <base url>

            Add a site to the list of known redmine sites."""
            if not url.endswith('/'):
                url += '/'
            if not name:
                irc.error(_('Invalid site name.'), Raise=True)
            if name in self.conf.sites():
                irc.error(_('This site name is already registered.'), Raise=True)
            data = utils.web.getUrl(url + 'projects.json')
            if sys.version_info[0] >= 3:
                data = data.decode('utf8')
            data = json.loads(data)
            assert 'total_count' in data
            #try:
            #    data = json.load(utils.web.getUrlFd(url + 'projects.json'))
            #    assert 'total_count' in data
            #except:
            #    irc.error(_('This is not a valid Redmine site.'), Raise=True)
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
                irc.reply(format('%L', list(sites)))
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
    @handle_site_arg([getopts({'project': 'something',
                               'author': 'something',
                               'assignee': 'something',
                              })])
    def issues(self, irc, msg, args, site, optlist):
        """[--project <project>] [--author <username>] \
        [--assignee <username>]

        Return a list of issues on the Redmine <site>, filtered with
        given parameters."""
        fetch_args = {}
        for (key, value) in optlist:
            if key == 'project':
                fetch_args['project_id'] = get_project_or_error(irc, site, value)['id']
            elif key == 'author':
                fetch_args['author_id'] = get_user_or_error(irc, site, value)['user']['id']
            elif key == 'assignee':
                fetch_args['assigned_to_id'] = get_user_or_error(irc, site, value)['user']['id']
            else:
                raise AssertionError((key, value))
        issues = fetch(site, 'issues', sort='updated_on:desc', **fetch_args)
        issues = issues['issues']
        new_issues = []
        for issue in issues:
            new_issues.append(flatten_subdicts(issue))
        issues = map(lambda x:self.registryValue('format.issues') % x,
                new_issues)
        irc.reply(format('%L', issues))

    @internationalizeDocstring
    @handle_site_arg(['positiveInt'])
    def issue(self, irc, msg, args, site, issueid):
        """<issue id>

        Return informations on an issue."""
        try:
            issue = fetch(site, 'issues/%i' % issueid)['issue']
            issue = flatten_subdicts(issue)
            irc.reply(self.registryValue('format.issue') % issue)
        except ResourceNotFound:
            irc.error(_('Issue not found.'), Raise=True)
        except KeyError as e:
            irc.error(_('Bad format in plugins.Redmine.format.issue: '
                '%r is an unknown key.') % e.args[0])


Class = Redmine


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
