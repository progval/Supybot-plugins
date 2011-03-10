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
import sys
import json
import tarfile
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Packages')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

if not hasattr(world, 'features'):
    world.features = {}
world.features.update({'package-installer': '0.2'})

BIGGER = 1
EQUAL = 0
LOWER = -1

def compareVersions(v1, v2):
    """Returns -1, 0, or 1, depending on the newest version."""
    def split(version):
        splitted = version.split('+')
        patches = splitted[1:]
        numbers = splitted[0].split('.')
        return numbers.extend(patches)
    for index in range(0, min(len(v1), len(v2))):
        if v1[index] < v2[index]:
            return LOWER
        elif v1[index] > v2[index]:
            return BIGGER
    if len(v1) < len(v2):
        return LOWER
    if len(v1) > len(v2):
        return BIGGER
    return EQUAL

def getDirectory(file_):
    """Tries to find the directory where plugin files are. Returns None
    if it is not found or if any file is missing."""
    directory = None
    names = []
    for name in file_.getnames():
        assert not name.startswith('/')
        assert not name.startswith('../')
        assert ':' not in name # Prevents Windows drives and bad formed names
        if directory is not None and not name.startswith(directory + '/'):
            # No more than one directory at root
            return False
        elif directory is None:
            directory = name.split('/')[0]
        if '/' in name:
            assert name.startswith(directory + '/')
        else:
            assert name == directory
        names.append(name[len(directory)+1:])
    if directory is None:
        return None
    if not all([x in names for x in ('__init__.py', 'config.py',
                                     'plugin.py', 'packaging.py',
                                     'test.py')]):
        # I know, test.py is not necessary. But people who don't write
        # test case suck. More over, supybot-plugin-create automatically
        # creates this file for a long time, so it should be there.
        return None
    return directory

def getWritableDirectoryFromList(directories):
    for directory in directories:
        if os.access(directory, os.W_OK):
            return directory
    return None


@internationalizeDocstring
class Packages(callbacks.Plugin):
    """Add the help for "@plugin help Packages" here
    This should describe *how* to use this plugin."""
    threaded = True

    @internationalizeDocstring
    def install(self, irc, msg, args, filename, optlist):
        """<filename> [--force]

        Installs the package. If the package has been downloaded with Package,
        just give the package name; otherwise, give the full path (including
        the extension).
        If given, --force disables sanity checks (usage is deprecated)."""
        filename = os.path.expanduser(filename)
        if os.path.sep not in filename:
            filename = os.path.join(conf.supybot.directories.data(), filename)
            filename += '.tar'
        try:
            file_ = tarfile.open(name=filename, mode='r:*')
        except:
            irc.error(_('Cannot open the package. Are you sure it is '
                        'readable, it is a tarball and it is not '
                        'corrupted?'))
            return
        directory = getDirectory(file_)
        if not directory:
            irc.error(_('The file is not a valid package.'))
            return
        class packaging:
            """Namespace for runned code"""
            exec(file_.extractfile('%s/packaging.py' % directory).read())
        if not ('force', True) in optlist:
            failures = []
            for feature, version in packaging.requires.items():
                if feature not in world.features:
                    failures.append(_('%s (missing)') % feature)
                elif compareVersions(world.features[feature], version) == LOWER:
                    failures.append(_('%s (>=%s needed, but %s available)') %
                            (feature, version, world.features[feature]))
            if failures != []:
                irc.error(_('Missing dependency(ies) : ') +
                          ', '.join(failures))
                return
        directories = conf.supybot.directories.plugins()
        directory = getWritableDirectoryFromList(directories)
        if directory is None:
            irc.error(_('No writable plugin directory found.'))
            return
        file_.extractall(directory)
        irc.replySuccess()
        if hasattr(packaging, 'additionalReply'):
            irc.reply('The plugin provides this additional information: %s' %
                      packaging.additionalReply)
    install = wrap(install, ['owner', 'filename', getopts({'force': ''})])

    @internationalizeDocstring
    def download(self, irc, msg, args, name, optlist):
        """<package> [--version <version>] [--repo <repository url>]

        Downloads the <package> at the <repository url>.
        <version> defaults to the latest version available.
        <repository url> defaults to http://packages.supybot.fr.cr/"""
        # Parse and check parameters
        version = None
        repo = 'http://packages.supybot.fr.cr/'
        for key, value in optlist:
            if key == 'version': version = value
            elif key == 'repo': repo = value
        if __builtins__['any']([x in repo for x in ('?', '&')]):
            # Supybot rewrites any() in commands.py
            irc.error(_('Bad formed url.'))
            return
        selectedPackage = None

        # Get server's index
        try:
            index = json.load(utils.web.getUrlFd(repo))
        except ValueError:
            irc.error(_('Server\'s JSON is bad formed.'))
            return

        # Crawl the available packages list
        for package in index['packages']:
            if not package['name'] == name:
                continue
            if version is None and (
                    selectedPackage == None or
                    compareVersions(selectedPackage['version'],
                                    package['version']) == BIGGER):
                # If not version given, and [no selected package
                # or selected package is older than this one]
                selectedPackage = package
            elif package['version'] == version:
                selectedPackage = package
        if selectedPackage is None:
            irc.error(_('No packages matches your query.'))
            return

        # Determines the package's real URL
        # TODO: handle relative URL starting with /
        # FIXME: URL ending with /foobar.txt
        packageUrl = selectedPackage['download-url']
        if packageUrl.startswith('./'):
            packageUrl = repo
            if not packageUrl.endswith('/'):
                packageUrl += '/'
            packageUrl += selectedPackage['download-url']

        # Write the package to the disk
        directory = conf.supybot.directories.data()
        assert os.access(directory, os.W_OK)
        path = os.path.join(directory, '%s.tar' % name)
        try:
            os.unlink(path)
        except OSError:
            # Does not exist
            pass
        with open(path, 'ab') as file_:
            try:
                file_.write(utils.web.getUrlFd(packageUrl).read())
            except utils.web.Error as e:
                irc.reply(e.args[0])
                return
        irc.replySuccess()
    download = wrap(download, ['owner', 'something',
                               getopts({'version': 'something',
                                        'repo': 'httpUrl'})])

    @internationalizeDocstring
    def checkupdates(self, irc, msg, args, repo):
        """[<repository url>]

        Checks for updates for loaded plugins at the <repository url>.
        <repository url> defaults to http://packages.supybot.fr.cr/"""
        if repo is None:
            repo = 'http://packages.supybot.fr.cr/'

        # Get server's index
        try:
            index = json.load(utils.web.getUrlFd(repo))
        except ValueError:
            irc.error(_('Server\'s JSON is bad formed.'))
            return

        # Crawl the index
        needUpdate = {}
        for package in index['packages']:
            if package['name'] in sys.modules and (
                    not hasattr(sys.modules[package['name']], '__version__') or
                    compareVersions(sys.modules[package['name']].__version__,
                                    package['version']) == LOWER):
                if package['name'] in needUpdate:
                    if compareVersions(needUpdate[package['name']].__version__,
                                        package['version']) != LOWER:
                        continue
                needUpdate.update({package['name']: package})

        # Display results
        if needUpdate == {}:
            irc.reply(_('All loaded plugins are up to date :)'))
        else:
            irc.reply(', '.join(['%s (%s)' % (y['name'],y['version'])
                                 for x,y in needUpdate.items()]))
    checkupdates = wrap(checkupdates, ['owner', optional('httpUrl')])

    def search(self, irc, msg, args, repo, optlist, description):
        """[<repository url>] [--name <name>] [--version <version>]\
            [--author <author>] [<description>]

        Searches the packages matching the query in the <repository url>.
        <repository url> defaults to http://packages.supybot.fr.cr"""
        # Parse the arguments
        if repo is None:
            repo = 'http://packages.supybot.fr.cr/'
        if description is None:
            description = ''
        if not __builtins__['any'](x in description for x in '*?'):
            description = '*%s*' % description
        optlist.append(('description', description))
        def glob2matcher(glob):
            glob = utils.python.glob2re(glob)
            return re.compile(glob).match
        matchers = {}
        for key, value in optlist:
            if value != None:
                matchers.update({key: glob2matcher(value)})

        # Get server's index
        try:
            index = json.load(utils.web.getUrlFd(repo))
        except ValueError:
            irc.error(_('Server\'s JSON is bad formed.'))
            return

        # Crawl packages index
        results = []
        for package in index['packages']:
            ok = True
            for key, matcher in matchers.items():
                if key in package and not matcher(str(package[key])):
                    # If the packages index doesn't have this key, we consider
                    # the key matched.
                    ok = False
                    break
            if ok:
                results.append(package)

        # Display results
        reply = ['%s (%s)' % (x['name'],x['version']) for x in results]
        reply.sort()
        irc.reply(', '.join(reply))
    options = ['name', 'version', 'author']
    search = wrap(search, [optional('httpUrl'),
                           getopts(dict([(x,'anything') for x in options])),
                           optional('text')])

    def info(self, irc, msg, args, repo, name, version, optlist):
        """[<repository url>] <package> [<version>] [--author-full]

        Displays informations about the <package>, at the given <version>.
        <repository url> defaults to http://packages.supybot.fr.cr/ and
        <version> defaults to the latest available."""
        # Parse the arguments
        if repo is None:
            repo = 'http://packages.supybot.fr.cr/'
        if version == '--author-full': # Bug in wrap()
            version = None
            optlist.append(('--author-full', True))

        # Get server's index
        try:
            index = json.load(utils.web.getUrlFd(repo))
        except ValueError:
            irc.error(_('Server\'s JSON is bad formed.'))
            return

        # Crawl the index
        selectedPackage = None
        for package in index['packages']:
            if package['name'] == name:
                if version is not None and package['version'] != version:
                    continue
                if version is None and selectedPackage is not None and \
                        compareVersions(selectedPackage['version'],
                                        package['version']) != LOWER:
                    continue
                selectedPackage = package

        # Display result
        if selectedPackage is None:
            irc.error('No such package/version.')
            return
        selectedPackage['author-name'] = selectedPackage['author'][0]
        selectedPackage['author-nick'] = selectedPackage['author'][1]
        selectedPackage['author-email'] = selectedPackage['author'][2]
        if ('author-full', True) in optlist:
            selectedPackage['author-string'] = '%s "%s" <%s>' % \
                                               tuple(selectedPackage['author'])
        else:
            selectedPackage['author-string'] = selectedPackage['author-name']
        for key in ('requires', 'suggests', 'provides'):
            selectedPackage[key] = ', '.join('%s (%s)' % x for x in
                                             selectedPackage[key].items())
        irc.reply(('%(name)s (version %(version)s) has been written by '
                   '%(author-string)s and requires the fellowing flags: '
                   '%(requires)s') % selectedPackage)
    info = wrap(info, [optional('httpUrl'), 'something',
                       optional('something'), getopts({'author-full': ''})])




Class = Packages


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
