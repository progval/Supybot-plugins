###
# Copyright (c) 2019, Valentin Lorentz
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
import glob
import time
import itertools
import threading

import apt
import apt_pkg
try:
    import lz4.frame
except ImportError:
    lz4 = None

from supybot import callbacks, utils
from supybot.commands import wrap, commalist, getopts
from supybot.i18n import PluginInternationalization
import supybot.conf as conf


_ = PluginInternationalization('Apt')


def get_dependency_translations():
    return utils.InsensitivePreservingDict({
        'Breaks': _('Breaks'),
        'Conflicts': _('Conflicts'),
        'Depends': _('Depends'),
        'Enhances': _('Enhances'),
        'PreDepends': _('PreDepends'),
        'Recommends': _('Recommends'),
        'Replaces': _('Replaces'),
        'Suggests': _('Suggests'),
    })


def get_dependency_reverse_translations():
    return utils.InsensitivePreservingDict(
        {v: k for (k, v) in get_dependency_translations().items()})


def get_priority_translations():
    return {
        'required': _('required'),
        'important': _('important'),
        'standard': _('standard'),
        'optional': _('optional'),
        'extra': _('extra'),
    }


def get_file_opener(extension):
    if extension == 'lz4':
        try:
            return lz4.frame.open
        except AttributeError:
            raise callbacks.Error(
                _('Cannot open lz4 file, python3-lz4 0.23.1 or higher '
                  'is required.'))
    else:
        raise ValueError(
            'Cannot open .%s files, unknown extension' % extension)


def read_chunk(fd, remainder):
    new_data = fd.read(1024*1024)
    chunk = remainder + new_data
    if new_data:
        (chunk, remainder) = chunk.rsplit(b'\n', 1)
    else:
        remainder = b''
    return (chunk, remainder, bool(new_data))


def search_lines(pattern, fd):
    """Reads the fd un chunks of lines, and runs pattern.finditer on each of
    the chunks."""
    remainder = b''
    while True:
        (chunk, remainder, new_data) = read_chunk(fd, remainder)
        yield from pattern.findall(chunk)
        if not new_data:
            break


_packages_lists_filename_re = re.compile(
    r'(?P<beginning>.*)_binary-(?P<arch>[^_-]+)_Packages')


def list_content_lists(plugin, irc, channel, filters, rootdir):
    """Returns a list of '/var/lib/apt/lists/*_Content-*' and functions
    suitable to open them"""
    archs = get_filter_config(plugin, irc, channel, filters, 'archs')
    if archs:
        archs = [arch.lower() for arch in archs]

    distribs = get_filter_config(plugin, irc, channel, filters, 'distribs')
    if distribs:
        distribs = [distrib.lower() for distrib in distribs]

    releases = get_filter_config(plugin, irc, channel, filters, 'releases')
    if releases:
        releases = [release.lower() for release in releases]

    list_filenames = []
    for file in plugin._get_cache()._cache.file_list:
        # TODO: add support for 'all' arch; which would check that the file is
        # indeed available in all architecture.
        if archs and file.architecture not in archs:
            continue

        if distribs and file.label not in distribs:
            continue

        if releases \
                and file.archive.lower() not in releases \
                and file.codename not in releases:
            continue

        match = _packages_lists_filename_re.match(file.filename)
        if not match:
            continue

        list_filenames.extend(glob.glob(
            '%(beginning)s_Contents-%(arch)s*' % match.groupdict()))

    for list_filename in list_filenames:
        (_, extension) = os.path.splitext(list_filename)
        file_opener = get_file_opener(extension.strip('.'))
        yield (list_filename, file_opener)


def get_filter_config(plugin, irc, channel, filters, filter_name):
    # First get the filter from the command
    filter_ = filters.get(filter_name)
    if filter_:
        if '*' in filter_:
            # If the command caller used '*' as filter, then it disables
            # the configured filter, ie. there is no filter.
            return None
        else:
            # If the command caller provided filters, and it's not '*', return it
            filter_ = filters[filter_name]

    else:
        # The command caller didn't provide the filter, fall back to the
        # configured filter if any.
        filter_ = plugin.registryValue(
            'defaults.%s' % filter_name, channel, irc.network)

        if filter_ is None:
            return None

    # Remove trailing whitespaces, empty values. Also fixes a glitch in
    # CommaSeparatedListOfStrings that causes '' to be deserialized as [''].
    return [x.strip() for x in filter_ if x.strip()]


FILTERS_SYNTAX = ''' [--archs <arch>,<arch>,...] \
[--distribs <distrib>,<distrib>,...] \
[--releases <release>,<release>,...]'''
FILTERS_DOC = '''<distrib>s are name of distributions (Debian, Ubuntu, "Debian
Backports", ...) to look in, and <release> are release names (buster, bionic,
stretch-backports) to look in. <arch>s are names of CPU architectures
(arm64, amd64, i386, ...).'''


def add_filters_doc(f):
    f.__doc__ %= (FILTERS_SYNTAX, FILTERS_DOC)
    return f


FILTERS_OPTLIST = {
    'archs': commalist('something'),
    'distribs': commalist('something'),
    'releases': commalist('something'),
}


def filter_versions(plugin, irc, channel, filters, versions):
    """Takes a list of apt.Version objects, and returns another list, by
    running filters on it.
    Filters choosen based on the channel's config (see config.py) and the
    command's optlist (which overrides the config)."""

    archs = get_filter_config(plugin, irc, channel, filters, 'archs')
    if archs:
        archs = [arch.lower() for arch in archs]
        versions = [version for version in versions
                    if version.architecture in archs]

    # Spare round-trips to the C code to build the origin list:
    versions = [(version, version.origins) for version in versions]

    def filter_on_origins(pred):
        nonlocal versions
        versions = [
            (version, origins) for (version, origins) in versions
            if any(map(pred, origins))]

    distribs = get_filter_config(plugin, irc, channel, filters, 'distribs')
    if distribs:
        distribs = [distrib.lower() for distrib in distribs]
        filter_on_origins(lambda origin: origin.label.lower() in distribs)

    releases = get_filter_config(plugin, irc, channel, filters, 'releases')
    if releases:
        releases = [release.lower() for release in releases]
        # Examples:
        # * in Debian, origin.archive='stable' and origin.codename='buster'
        # * in Ubuntu, origin.archive='bionic' and origin.codename='bionic'
        # So checking both allows supporting both version names and
        # stable/testing/...
        filter_on_origins(lambda origin: (
            origin.archive.lower() in releases
            or origin.codename.lower() in releases))

    if not versions:
        irc.error(_('Package exists, but no version is found.'),
                  Raise=True)

    return [version for (version, origins) in versions]


class Apt(callbacks.Plugin):
    """Provides read access to APT repositories."""
    threaded = True

    _cache = None
    _cache_last_update = 0
    _cache_lock = threading.Lock()

    def die(self):
        if self._cache:
            self._cache.close()

    def _get_cache_dir(self):
        return conf.supybot.directories.data.dirize('aptdir')

    def _should_update(self):
        """Is the cache older than the configured interval?"""
        interval = self.registryValue('cache.updateInterval')
        if not interval:
            return False
        return self._cache_last_update + interval < time.time()

    def _get_cache(self):
        """Get the current cache if any, else open it. Also performs an update
        if the cache is expired (wrt. the updateInterval)."""
        is_open = False
        with self._cache_lock:
            if not self._cache:
                self._cache = apt.Cache(rootdir=self._get_cache_dir())
                is_open = False
            else:
                # The cache is already instantiated, assume it's open.
                is_open = True
            if self._should_update():
                if is_open:
                    self._cache.close()
                    is_open = False
                self._cache.update()
                self._cache_last_update = time.time()
            if not is_open:
                self._cache.open()
            return self._cache

    def _update_cache(self):
        """Equivalent to 'apt-get update'"""
        with self._cache_lock:
            if self._cache:
                self._cache.close()
                self._cache.update()
                self._cache.open()
            else:
                self._cache = apt.Cache(rootdir=self._get_cache_dir())
                self._cache.update()
                self._cache.open()

    @wrap([('checkCapability', 'trusted')])
    def update(self, irc, msg, args):
        """takes no arguments

        Updates the APT cache from repositories."""
        self._update_cache()
        irc.replySuccess()

    class file(callbacks.Commands):
        def plugin(self, irc):
            return irc.getCallback('Apt')

        @wrap([
            getopts({
                **FILTERS_OPTLIST,
            }),
            'something',
        ])
        @add_filters_doc
        def packages(self, irc, msg, args, opts, filename):
            """%s <filename>

            Lists packages that contain the given filename. %s"""
            opts = dict(opts)
            plugin = self.plugin(irc)
            plugin._get_cache()  # open the cache

            filename = filename.encode()
            # You may want to add '^.*' at the beginning of the pattern; but
            # don't do that because the regexp then becomes much slower (6s for
            # a 500MB list, instead of 0.3s).
            # Given that we're matching end of lines, a line can't be matched
            # anyway because matches can't overlap.
            line_entry_re = re.compile(
                rb'%s.*\s+(\S+)/(\S+)$' % re.escape(filename),
                re.MULTILINE)
            results = set()

            # I can't find a way to do this with python-apt, so let's open and
            # parse the files directly
            rootdir = self.plugin(irc)._get_cache_dir()
            lists = list_content_lists(plugin, irc, msg.channel, opts, rootdir)
            for (list_filename, file_opener) in lists:
                with file_opener(list_filename) as fd:
                    for match in search_lines(line_entry_re, fd):
                        results.add(match[1].decode())

            if results:
                irc.reply(format('%L', sorted(results)))
            else:
                irc.error(_('No package found.'))

    class package(callbacks.Commands):
        def plugin(self, irc):
            return irc.getCallback('Apt')

        def _get_package_versions(self, irc, package_name):
            # TODO: add support for selecting the version
            cache = self.plugin(irc)._get_cache()

            versions = []
            try:
                # TODO: when python3-apt is released with support for groups,
                # (probably via a Cache.find_grp method), use that instead
                # of hacking around with apt_pkg
                group = apt_pkg.Group(cache._cache, package_name)
            except KeyError:
                irc.error(_('Package not found.'), Raise=True)

            for pkg in group:
                # get an apt.Package instance, using the data from the
                # apt_pkg.Package instance:
                pkg = apt.Package(cache, pkg)
                versions.extend(pkg.versions)

            return versions

        @wrap([
            getopts({
                **FILTERS_OPTLIST,
                'types': commalist('somethingWithoutSpaces'),
            }),
            'somethingWithoutSpaces',
        ])
        @add_filters_doc
        def depends(self, irc, msg, args, optlist, package_name):
            """%s [--types <type>,<type>,...] <package>

            Lists dependencies of a package. <type>s are types of dependencies
            that will be shown. Valid types are: Breaks, Conflicts, Depends,
            Enhances, PreDepends, Recommends, Replaces, Suggests. %s
            """
            opts = dict(optlist)

            dep_types = opts.get('types', ['Depends', 'PreDepends'])
            dep_types = [dep_type for dep_type in dep_types]
            translations = get_dependency_reverse_translations()
            dep_types = [translations.get(dep_type, dep_type)
                         for dep_type in dep_types]

            # TODO: better version selection
            pkg_versions = self._get_package_versions(irc, package_name)
            pkg_version = filter_versions(
                self.plugin(irc), irc, msg.channel, opts, pkg_versions)[0]

            deps = pkg_version.get_dependencies(*dep_types)
            irc.reply(format(_('%s: %L'),
                             pkg_version,
                             [dep.rawstr for dep in deps]))

        @wrap([
            getopts({
                **FILTERS_OPTLIST,
            }),
            'somethingWithoutSpaces'
        ])
        @add_filters_doc
        def description(self, irc, msg, args, optlist, package_name):
            """%s <package>

            Shows the long description of a package. %s"""
            opts = dict(optlist)

            # TODO: better version selection
            pkg_versions = self._get_package_versions(irc, package_name)
            pkg_version = filter_versions(
                self.plugin(irc), irc, msg.channel, opts, pkg_versions)[0]

            description = utils.str.normalizeWhitespace(
                pkg_version.description)
            irc.reply(format(_('%s %s: %s'),
                             pkg_version.package.shortname,
                             pkg_version.version, description))

        @wrap([
            getopts({
                **FILTERS_OPTLIST,
            }),
            'somethingWithoutSpaces'
        ])
        @add_filters_doc
        def info(self, irc, msg, args, optlist, package_name):
            """%s <package>

            Shows generic information about a package. %s"""
            opts = dict(optlist)

            # TODO: better version selection
            pkg_versions = self._get_package_versions(irc, package_name)
            pkg_version = filter_versions(
                self.plugin(irc), irc, msg.channel, opts, pkg_versions)[0]

            # source_name and priority shouldn't change too often, so I assume
            # it's safe to call it a "generic info" in a UI
            priority = get_priority_translations().get(
                pkg_version.priority, pkg_version.priority)
            generic_info = format(
                _('%s (source: %s) is %s and in section "%s".'),
                pkg_version.package.shortname, pkg_version.source_name,
                priority, pkg_version.package.section)

            version_info = format(
                _('Version %s package is %S and takes %S when installed.'),
                pkg_version.version, pkg_version.size,
                pkg_version.installed_size)

            irc.reply(format(_('%s %s Description: %s'),
                             generic_info, version_info, pkg_version.summary))

        @wrap([
            getopts({
                **FILTERS_OPTLIST,
                'with-version': '',
                'description': '',
            }),
            'somethingWithoutSpaces'
        ])
        @add_filters_doc
        def search(self, irc, msg, args, optlist, package_pattern):
            """%s [--with-version] [--description] <package>

            Shows generic information about a package. --with-version also
            returns matching version numbers. --description searches in package
            description instead of name. %s"""
            opts = dict(optlist)
            search_description = 'description' in opts
            cache = self.plugin(irc)._get_cache()
            pattern = re.compile(utils.python.glob2re(package_pattern),
                    re.DOTALL)


            if search_description:
                packages = iter(cache)
            else:
                # The next line is equivalent to:
                # packages = (pkg for pkg in cache if pattern.match(pkg.shortname))
                # but is much much faster, because Cache.__iter__ takes a lot
                # of time to build Package instances and update its weakref
                # cache dictionary
                packages = (cache[pkgname] for pkgname in cache.keys()
                            if pattern.match(pkgname))

                # Dirty trick to check if the iterator is empty without
                # consuming it entirely
                (packages, peek_packages) = itertools.tee(packages)
                if not next(peek_packages, None):
                    irc.error(_('No package found.'), Raise=True)

            versions = (version
                        for pkg in packages
                        for version in pkg.versions)

            if search_description:
                versions = (version
                            for version in versions
                            if pattern.match(version.description))

            # filter_versions is rather slow, so we're putting this guard
            # before running it.
            versions = list(itertools.islice(versions, 10000))
            if len(versions) >= 10000:
                irc.error(_('Too many packages match this search.'),
                        Raise=True)

            versions = filter_versions(
                self.plugin(irc), irc, msg.channel, opts, versions)

            if not opts.get('with-version'):
                package_names = sorted({version.package.shortname
                                        for version in versions})
                irc.reply(format('%L', package_names))
                return

            items = []
            for version in versions:
                items.append(format('%s %s (in %L)',
                                    version.package.shortname,
                                    version.version,
                                    {origin.codename
                                     for origin in version.origins}))
            irc.reply(format('%L', items))


Class = Apt


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
