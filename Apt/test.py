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
import time

from supybot.test import *
import supybot.conf as conf

from .plugin import Apt

SOURCES_LIST = '''
deb [allow-insecure=yes] http://archive.ubuntu.com/ubuntu bionic main universe
deb-src [allow-insecure=yes] http://archive.ubuntu.com/ubuntu bionic main universe
deb [allow-insecure=yes arch=amd64,armel] http://deb.debian.org/debian buster main
deb-src [allow-insecure=yes] http://deb.debian.org/debian buster main
deb [allow-insecure=yes] http://deb.debian.org/debian stretch-backports main
deb-src [allow-insecure=yes] http://deb.debian.org/debian stretch-backports main
'''


# Save the cache between tests so it doesn't have to be re-opened every time,
# it makes tests twice as fast.
_cache = None


class AptTestCase(PluginTestCase):
    plugins = ('Apt', 'Misc')
    cleanDataDir = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        rootdir = conf.supybot.directories.data.dirize('aptdir')
        os.makedirs(rootdir + '/etc/apt', exist_ok=True)
        with open(rootdir + '/etc/apt/sources.list', 'w') as fd:
            fd.write(SOURCES_LIST)

        # Doing this in the setUp because commands would timeout
        Apt(None)._get_cache()

    def setUp(self):
        super().setUp()
        if _cache is not None:
            # Don't re-open the cache for each test case
            plugin = self.irc.getCallback('Apt')
            plugin._cache = _cache
            plugin._cache_last_update = time.time()

    def tearDown(self):
        global _cache
        plugin = self.irc.getCallback('Apt')
        _cache = plugin._cache  # save the cache
        plugin._cache = None  # prevent the plugin from closing it
        super().tearDown()

    def testHelp(self):
        self.assertRegexp(
            'help package depends',
            '^' +
            re.escape('(\x02package depends '
                      '[--archs <arch>,<arch>,...] '
                      '[--distribs <distrib>,<distrib>,...] '
                      '[--releases <release>,<release>,...] '
                      '[--types <type>,<type>,...] '
                      '<package>\x02) -- Lists'))

    def testUpdate(self):
        self.assertResponse('apt update', 'The operation succeeded.')

    def testFilePackages(self):
        self.assertRegexp(
            'file packages plugins/Owner/plugin.py',
            '(limnoria and supybot|supybot and limnoria)')
        self.assertRegexp(
            'file packages badblocks',
            'e2fsprogs')
        self.assertResponse(
            'file packages sbin/badblocks',
            'e2fsprogs')

    def testFilePackagesFilterArchs(self):
        self.assertResponse(
            'file packages doc/linux-image-amd64/changelog',
            'linux-image-amd64')
        self.assertResponse(
            'file packages --archs armel doc/linux-image-amd64/changelog',
            'Error: No package found.')
        self.assertResponse(
            'file packages --archs all doc/linux-image-amd64/changelog',
            'linux-image-amd64')

    def testPackageDepends(self):
        self.assertResponse(
            'package depends limnoria',
            'limnoria=2019.02.23-1: python3:any')
        self.assertResponse(
            'package depends --types Breaks,Replaces,Conflicts limnoria',
            'limnoria=2019.02.23-1: supybot')
        self.assertResponse(
            'package depends --types breaks,replaces,conflicts limnoria',
            'limnoria=2019.02.23-1: supybot')

    def testPackageDependsTranslation(self):
        with conf.supybot.language.context('fr'):
            self.assertResponse(
                'package depends limnoria',
                'limnoria=2019.02.23-1 : python3:any')
            self.assertResponse(
                'package depends --types Casse,Remplace,Conflicte limnoria',
                'limnoria=2019.02.23-1 : supybot')
            self.assertResponse(
                'package depends --types casse,remplace,conflicte limnoria',
                'limnoria=2019.02.23-1 : supybot')

    def testPackageInfo(self):
        self.assertResponse(
            'package info limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2019.02.23-1 package is 558KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')

    def testPackageInfoTranslation(self):
        with conf.supybot.language.context('fr'):
            self.assertResponse(
                'package info limnoria',
                'limnoria (source : limnoria) est optionnel et est dans la '
                'section "net". '
                'Le paquet de la version 2019.02.23-1 fait 558KB et prend '
                '4MB après installation. '
                'Description : robust and user-friendly Python IRC bot')

    def testPackageInfoFilterDistributions(self):
        self.assertResponse(
            'package info --distribs debian,ubuntu limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2019.02.23-1 package is 558KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')
        self.assertResponse(
            'package info --distribs ubuntu limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2018.01.25-1 package is 555KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')

        # archive (note: this test may break when buster becomes oldstable)
        self.assertResponse(
            'package info --distribs "Debian Backports" limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2019.02.23-1~bpo9+1 package is 560KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')

    def testPackageInfoFilterArchs(self):
        self.assertResponse(
            'package info --releases buster --archs all limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2019.02.23-1 package is 558KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')

        self.assertResponse(
            'package info --releases buster --archs amd64 limnoria',
            'Error: Package exists, but no version is found.')

        self.assertRegexp(
            'package info --releases buster --archs amd64 firefox-esr',
            'firefox-esr.*~deb10')

        self.assertResponse(
            'package info --releases buster --archs armel firefox-esr',
            'Error: Package exists, but no version is found.')

    def testPackageInfoFilterReleases(self):
        # codenames
        self.assertResponse(
            'package info --releases bionic,buster limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2019.02.23-1 package is 558KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')
        self.assertResponse(
            'package info --releases bionic limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2018.01.25-1 package is 555KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')

        # archive (note: this test will break when buster becomes oldstable)
        self.assertResponse(
            'package info --releases stable limnoria',
            'limnoria (source: limnoria) is optional and in section "net". '
            'Version 2019.02.23-1 package is 558KB and takes 4MB when '
            'installed. '
            'Description: robust and user-friendly Python IRC bot')

    def testPackageInfoConfiguredFilter(self):
        with conf.supybot.plugins.Apt.defaults.distribs.context(['Debian Backports']):
            # The configured default, "Debian Backports" should be used as
            # --distribs is not given
            self.assertResponse(
                'package info limnoria',
                'limnoria (source: limnoria) is optional and in section "net". '
                'Version 2019.02.23-1~bpo9+1 package is 560KB and takes 4MB when '
                'installed. '
                'Description: robust and user-friendly Python IRC bot')

            # Config is overridden by the command caller
            self.assertResponse(
                'package info --distribs ubuntu limnoria',
                'limnoria (source: limnoria) is optional and in section "net". '
                'Version 2018.01.25-1 package is 555KB and takes 4MB when '
                'installed. '
                'Description: robust and user-friendly Python IRC bot')

    def testPackageInfoNotFound(self):
        # Package doesn't exist
        self.assertResponse(
            'package info this-package-does-not-exist',
            'Error: Package not found.')

        # Debian has no release 'bionic', so filters can't find a matching
        # version.
        self.assertResponse(
            'package info --distribs debian --releases bionic limnoria',
            'Error: Package exists, but no version is found.')

    def testPackageDescription(self):
        self.assertRegexp(
            'package description limnoria',
            '^limnoria 2019.02.23-1: A robust, full-featured Python IRC bot '
            'with a clean and flexible plugin API. Equipped with')

    def testPackageSearch(self):
        self.assertResponse(
            'package search limnoria',
            'limnoria')

        self.assertResponse(
            'package search --archs amd64 limnoria',
            'Error: Package exists, but no version is found.')

        self.assertResponse(
            'package search limnori',
            'Error: No package found.')

        self.assertResponse(
            'package search limnori*',
            'limnoria')

        self.assertRegexp(
            'package search --description *upybot*',
            '(supybot and limnoria|limnoria and supybot)')

        self.assertResponse(
            'package search e2fsprogs*',
            'e2fsprogs and e2fsprogs-l10n')

    def testPackageSearchTooMany(self):
        self.assertResponse(
            'package search *',
            'Error: Too many packages match this search.')

    def testPackageSearchWithVersion(self):
        self.assertResponse(
            'package search --with-version limnoria',
            'limnoria 2019.02.23-1 (in buster), '
            'limnoria 2019.02.23-1~bpo9+1 (in stretch-backports), '
            'and limnoria 2018.01.25-1 (in bionic)')

        self.assertResponse(
            'package search --archs amd64 --with-version limnoria',
            'Error: Package exists, but no version is found.')

        self.assertResponse(
            'package search --with-version limnori',
            'Error: No package found.')

        self.assertResponse(
            'package search --with-version limnori*',
            'limnoria 2019.02.23-1 (in buster), '
            'limnoria 2019.02.23-1~bpo9+1 (in stretch-backports), '
            'and limnoria 2018.01.25-1 (in bionic)')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
