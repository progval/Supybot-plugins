###
# Copyright (c) 2003-2005, James Vega
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
import re
import time
import urllib
import fnmatch

import bs4 as BeautifulSoup

import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.utils.iter import all

class Debian(callbacks.Plugin):
    threaded = True

    _debreflags = re.DOTALL | re.MULTILINE
    _deblistreFileExact = re.compile(r'<a href="/[^/>]+/[^/>]+">([^<]+)</a>',
                                     _debreflags)
    def file(self, irc, msg, args, optlist, filename):
        """[--exact] \
        [--mode {path,filename,exactfilename}] \
        [--branch {oldstable,stable,testing,unstable,experimental}] \
        [--section {main,contrib,non-free}] <file name>

        Returns the package(s) containing the <file name>.
        --mode defaults to path, and defines how to search.
        --branch defaults to stable, and defines in what branch to search."""
        url = 'http://packages.debian.org/search?searchon=contents' + \
              '&keywords=%(keywords)s&mode=%(mode)s&suite=%(suite)s' + \
              '&arch=%(arch)s'
        args = {'keywords': None, 'mode': 'path', 'suite': 'stable',
                'arch': 'any'}
        exact = ('exact', True) in optlist
        for (key, value) in optlist:
            if key == 'branch':
                args['suite'] = value
            elif key == 'arch':
                args['arch'] = value
            elif key == 'mode':
                args['mode'] = value
        responses = []
        if '*' in filename:
            irc.error('Wildcard characters can not be specified.', Raise=True)
        args['keywords'] = utils.web.urlquote(filename, '')
        url %= args
        try:
            html = utils.web.getUrl(url).decode()
        except utils.web.Error as e:
            irc.error(format('I couldn\'t reach the search page (%s).', e),
                      Raise=True)
        if 'is down at the moment' in html:
            irc.error('Packages.debian.org is down at the moment.  '
                      'Please try again later.', Raise=True)
        step = 0
        pkgs = []
        for line in html.split('\n'):
            if '<span class="keyword">' in line:
                step += 1
            elif step == 1 or (step >= 1 and not exact):
                pkgs.extend(self._deblistreFileExact.findall(line))
        if pkgs == []:
            irc.reply(format('No filename found for %s (%s)',
                      utils.web.urlunquote(filename), args['suite']))
        else:
            # Filter duplicated
            pkgs = dict(map(lambda x:(x, None), pkgs)).keys()
            irc.reply(format('%i matches found: %s (%s)',
                          len(pkgs), '; '.join(pkgs), args['suite']))
    file = wrap(file, [getopts({'exact': '',
                                'branch': ('literal', ('oldstable',
                                                       'stable',
                                                       'testing',
                                                       'unstable',
                                                       'experimental')),
                                'mode': ('literal', ('path',
                                                     'exactfilename',
                                                     'filename')),
                                'arch': ('literal', ('main',
                                                     'contrib',
                                                     'non-free'))}),
                                'text'])

    _debreflags = re.DOTALL | re.IGNORECASE
    _deblistreVersion = re.compile(r'<h3>Package ([^<]+)</h3>(.*?)</ul>', _debreflags)
    def version(self, irc, msg, args, optlist, package):
        """[--exact] \
        [--searchon {names,all,sourcenames}] \
        [--branch {oldstable,stable,testing,unstable,experimental}] \
        [--section {main,contrib,non-free}] <package name>

        Returns the current version(s) of the Debian package <package name>.
        --exact, if given, means you want only the <package name>, and not
        package names containing this name.
        --searchon defaults to names, and defines where to search.
        --branch defaults to all, and defines in what branch to search.
        --section defaults to all, and defines in what section to search."""
        url = 'http://packages.debian.org/search?keywords=%(keywords)s' + \
              '&searchon=%(searchon)s&suite=%(suite)s&section=%(section)s'
        args = {'keywords': None, 'searchon': 'names', 'suite': 'all',
                'section': 'all'}
        for (key, value) in optlist:
            if key == 'exact':
                url += '&exact=1'
            elif key == 'branch':
                args['suite'] = value
            elif key == 'section':
                args['section'] = value
            elif key == 'searchon':
                args['searchon'] = value
        responses = []
        if '*' in package:
            irc.error('Wildcard characters can not be specified.', Raise=True)
        args['keywords'] = utils.web.urlquote(package)
        url %= args
        try:
            html = utils.web.getUrl(url).decode()
        except utils.web.Error as e:
            irc.error(format('I couldn\'t reach the search page (%s).', e),
                      Raise=True)
        if 'is down at the moment' in html:
            irc.error('Packages.debian.org is down at the moment.  '
                      'Please try again later.', Raise=True)
        pkgs = self._deblistreVersion.findall(html)
        if not pkgs:
            irc.reply(format('No package found for %s (%s)',
                      utils.web.urlunquote(package), args['suite']))
        else:
            for pkg in pkgs:
                pkgMatch = pkg[0]
                soup = BeautifulSoup.BeautifulSoup(pkg[1])
                liBranches = soup.find_all('li')
                branches = []
                versions = []
                def branchVers(br):
                    vers = [b.next.string.strip() for b in br]
                    return [utils.str.rsplit(v, ':', 1)[0] for v in vers]
                for li in liBranches:
                    branches.append(li.a.string)
                    versions.append(branchVers(li.find_all('br')))
                if branches and versions:
                    for pairs in  zip(branches, versions):
                        branch = pairs[0]
                        ver = ', '.join(pairs[1])
                        s = format('%s (%s)', pkgMatch,
                                   ': '.join([branch, ver]))
                        responses.append(s)
            resp = format('%i matches found: %s',
                          len(responses), '; '.join(responses))
            irc.reply(resp)
    version = wrap(version, [getopts({'exact': '',
                                      'searchon': ('literal', ('names',
                                                               'all',
                                                               'sourcenames')),
                                      'branch': ('literal', ('oldstable',
                                                             'stable',
                                                             'testing',
                                                             'unstable',
                                                             'experimental')),
                                      'arch': ('literal', ('main',
                                                           'contrib',
                                                           'non-free'))}),
                                      'text'])

    _incomingRe = re.compile(r'<a href="(.*?\.deb)">', re.I)
    def incoming(self, irc, msg, args, optlist, globs):
        """[--{regexp,arch} <value>] [<glob> ...]

        Checks debian incoming for a matching package name.  The arch
        parameter defaults to i386; --regexp returns only those package names
        that match a given regexp, and normal matches use standard *nix
        globbing.
        """
        predicates = []
        archPredicate = lambda s: ('_i386.' in s)
        for (option, arg) in optlist:
            if option == 'regexp':
                predicates.append(r.search)
            elif option == 'arch':
                arg = '_%s.' % arg
                archPredicate = lambda s, arg=arg: (arg in s)
        predicates.append(archPredicate)
        for glob in globs:
            glob = fnmatch.translate(glob)
            predicates.append(re.compile(glob).search)
        packages = []
        try:
            fd = utils.web.getUrlFd('http://incoming.debian.org/')
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)
        for line in fd:
            m = self._incomingRe.search(line.decode())
            if m:
                name = m.group(1)
                if all(None, map(lambda p: p(name), predicates)):
                    realname = utils.str.rsplit(name, '_', 1)[0]
                    packages.append(realname)
        if len(packages) == 0:
            irc.error('No packages matched that search.')
        else:
            irc.reply(format('%L', packages))
    incoming = thread(wrap(incoming,
                           [getopts({'regexp': 'regexpMatcher',
                                     'arch': 'something'}),
                            any('glob')]))

    def bold(self, s):
        if self.registryValue('bold', dynamic.channel):
            return ircutils.bold(s)
        return s

    _update = re.compile(r' : ([^<]+)</body')
    _bugsCategoryTitle = re.compile(r'<dt id="bugs_.." title="([^>]+)">')
    _latestVersion = re.compile(r'<span id="latest_version">(.+)</span>')
    _maintainer = re.compile(r'<a href=".*login=(?P<email>[^<]+)">.*'
                             '<span class="name" title="maintainer">'
                             '(?P<name>[^<]+)</span>', re.S)
    def stats(self, irc, msg, args, pkg):
        """<source package>

        Reports various statistics (from http://packages.qa.debian.org/) about
        <source package>.
        """
        pkg = pkg.lower()
        try:
            text = utils.web.getUrl('http://packages.qa.debian.org/%s/%s.html' %
                                    (pkg[0], pkg)).decode('utf8')
        except utils.web.Error:
            irc.errorInvalid('source package name')
        for line in text.split('\n'):
            match = self._latestVersion.search(text)
            if match is not None:
                break
        assert match is not None
        version = '%s: %s' % (self.bold('Last version'),
                              match.group(1))
        updated = None
        m = self._update.search(text)
        if m:
            updated = m.group(1)
        soup = BeautifulSoup.BeautifulSoup(text)
        pairs = zip(soup.find_all('dt'),
                    soup.find_all('dd'))
        for (label, content) in pairs:
            try:
                title = self._bugsCategoryTitle.search(str(label)).group(1)
            except AttributeError: # Didn't match
                if str(label).startswith('<dt id="bugs_all">'):
                    title = 'All bugs'
                elif str(label) == '<dt title="Maintainer and Uploaders">' + \
                                   'maint</dt>':
                    title = 'Maintainer and Uploaders'
                else:
                    continue
            if title == 'Maintainer and Uploaders':
                match = self._maintainer.search(str(content))
                name, email = match.group('name'), match.group('email')
                maintainer = format('%s: %s %u', self.bold('Maintainer'),
                                    name, utils.web.mungeEmail(email))
            elif title == 'All bugs':
                bugsAll = format('%i Total', content.span.string)
            elif title == 'Release Critical':
                bugsRC = format('%i RC', content.span.string)
            elif title == 'Important and Normal':
                bugs = format('%i Important/Normal',
                              content.span.string)
            elif title == 'Minor and Wishlist':
                bugsMinor = format('%i Minor/Wishlist',
                                   content.span.string)
            elif title == 'Fixed and Pending':
                bugsFixed = format('%i Fixed/Pending',
                                   content.span.string)
        bugL = (bugsAll, bugsRC, bugs, bugsMinor, bugsFixed)
        s = '.  '.join((version, maintainer,
                        '%s: %s' % (self.bold('Bugs'), '; '.join(bugL))))
        if updated:
            s = 'As of %s, %s' % (updated, s)
        irc.reply(s)
    stats = wrap(stats, ['somethingWithoutSpaces'])

    _newpkgre = re.compile(r'<li><a href[^>/]+>([^<]+)</a>')
    def new(self, irc, msg, args, section, version, glob):
        """[{main,contrib,non-free}] [<version>] [<glob>]

        Checks for packages that have been added to Debian's unstable branch
        in the past week.  If no glob is specified, returns a list of all
        packages.  If no section is specified, defaults to main.
        """
        if version is None:
            version = 'unstable'
        try:
            fd = utils.web.getUrlFd('http://packages.debian.org/%s/%s/newpkg' %
                    (version, section))
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)
        packages = []
        for line in fd:
            m = self._newpkgre.search(line.decode())
            if m:
                m = m.group(1)
                if fnmatch.fnmatch(m, glob):
                    packages.append(m)
        fd.close()
        if packages:
            irc.reply(format('%L', packages))
        else:
            irc.error('No packages matched that search.')
    new = wrap(new, [optional(('literal', ('main', 'contrib', 'non-free')),
                              'main'),
                     optional('something'),
                     additional('glob', '*')])

    _severity = re.compile(r'<p>Severity: ([^<]+)</p>', re.I)
    _package = re.compile(r'<pre class="message">Package: ([^<\n]+)\n',
                          re.I | re.S)
    _reporter = re.compile(r'Reported by: <[^>]+>([^<]+)<', re.I | re.S)
    _subject = re.compile(r'<span class="headerfield">Subject:</span> [^:]+: ([^<]+)</div>', re.I | re.S)
    _date = re.compile(r'<span class="headerfield">Date:</span> ([^\n]+)\n</div>', re.I | re.S)
    _tags = re.compile(r'<p>Tags: ([^<]+)</p>', re.I)
    _searches = (_package, _subject, _reporter, _date)
    def bug(self, irc, msg, args, bug):
        """<num>

        Returns a description of the bug with bug id <num>.
        """
        url = 'http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=%s' % bug
        try:
            text = utils.web.getUrl(url).decode()
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)
        if "There is no record of Bug" in text:
            irc.error('I could not find a bug report matching that number.',
                      Raise=True)
        searches = list(map(lambda p: p.search(text), self._searches))
        sev = self._severity.search(text)
        tags = self._tags.search(text)
        # This section should be cleaned up to ease future modifications
        if all(None, searches):
            L = map(self.bold, ('Package', 'Subject', 'Reported'))
            resp = format('%s: %%s; %s: %%s; %s: by %%s on %%s', *L)
            L = map(utils.web.htmlToText, map(lambda p: p.group(1), searches))
            resp = format(resp, *L)
            if sev:
                sev = filter(None, sev.groups())
                if sev:
                    sev = utils.web.htmlToText(sev[0])
                    resp += format('; %s: %s', self.bold('Severity'), sev)
            if tags:
                resp += format('; %s: %s', self.bold('Tags'), tags.group(1))
            resp += format('; %u', url)
            irc.reply(resp)
        else:
            irc.error('I was unable to properly parse the BTS page.')
    bug = wrap(bug, [('id', 'bug')])

Class = Debian


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
