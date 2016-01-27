#!/usr/bin/env python
# -*- Encoding: utf-8 -*-
###
# Copyright (c) 2006-2007 Dennis Kaarsemaker
# Copyright (c) 2008-2010 Terence Simpson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
###

import sys
import warnings
warnings.filterwarnings("ignore", "apt API not stable yet", FutureWarning)
import subprocess, os, apt

if sys.version_info[0] >= 3:
    from email import feedparser
    urlquote = urllib.parse.quote
else:
    from email import feedparser as FeedParser
    urlquote = urllib.quote

def component(arg):
    if '/' in arg: return arg[:arg.find('/')]
    return 'main'

def description(pkg):
    if not pkg:
        return None
    if 'Description-en' in pkg:
        return pkg['Description-en'].split('\n')[0]
    elif 'Description' in pkg:
        return pkg['Description'].split('\n')[0]
    return None

def apt_cache(aptdir, distro, extra):
    return subprocess.check_output(['apt-cache',
             '-oDir::State::Lists=%s/%s' % (aptdir, distro),
             '-oDir::etc::sourcelist=%s/%s.list' % (aptdir, distro),
             '-oDir::etc::SourceParts=%s/%s.list.d' % (aptdir, distro),
             '-oDir::State::status=%s/%s.status' % (aptdir, distro),
             '-oDir::Cache=%s/cache' % aptdir,
             '-oAPT::Architecture=i386'] +
             extra).decode('utf8')

def apt_file(aptdir, distro, pkg):
    return subprocess.check_output(['apt-file',
            '-s', '%s/%s.list' % (aptdir, distro),
            '-c', '%s/apt-file/%s' % (aptdir, distro),
            '-l', '-a', 'i386',
            'search', pkg]).decode('utf8')

class Apt:
    def __init__(self, plugin):
        self.aptdir = plugin.registryValue('aptdir')
        self.distros = []
        self.plugin = plugin
        self.log = plugin.log
        os.environ["LANG"] = "C"
        if self.aptdir:
            self.distros = [x[:-5] for x in os.listdir(self.aptdir) if x.endswith('.list')]
            self.distros.sort()

    def find(self, pkg, chkdistro, filelookup=True):
        _pkg = ''.join([x for x in pkg.strip().split(None,1)[0] if x.isalnum() or x in '.-_+/'])
        distro = ''
        if len(pkg.strip().split()) > 1:
            distro = ''.join([x for x in pkg.strip().split(None,2)[1] if x.isalnum() or x in '.-_+'])
        if not distro:
            distro = chkdistro
        if distro not in self.distros:
            return "%s is not a valid distribution: %s" % (distro, ", ".join(self.distros))
        pkg = _pkg

        try:
            data = apt_cache(self.aptdir, distro, ['search', '-n', pkg])
        except subprocess.CalledProcessError as e:
            data = e.output
        if not data:
            if filelookup:
                try:
                    data = apt_file(self.aptdir, distro, pkg).split()
                except subprocess.CalledProcessError as e:
                    data = e.output
                if data:
                    if data[0] == 'sh:': # apt-file isn't installed
                      self.log.error("PackageInfo/packages: apt-file is not installed")
                      return "Please use http://packages.ubuntu.com/ to search for files"
                    if data[0] == 'E:': # No files in the cache dir
                      self.log.error("PackageInfo/packages: Please run the 'update_apt_file' script")
                      return "Cache out of date, please contact the administrator"
                    if data[0] == "Use" and data[1] == "of":
                        url = "http://packages.ubuntu.com/search?searchon=contents&keywords=%s&mode=&suite=%s&arch=any" % (urlquote(pkg), distro)
                        return url
                    if len(data) > 10:
                        return "File %s found in %s (and %d others) http://packages.ubuntu.com/search?searchon=contents&keywords=%s&mode=&suite=%s&arch=any" % (pkg, ', '.join(data[:10]), len(data)-10, urlquote(pkg), distro)
                    return "File %s found in %s" % (pkg, ', '.join(data))
                return 'Package/file %s does not exist in %s' % (pkg, distro)
            return "No packages matching '%s' could be found" % pkg
        pkgs = [x.split()[0] for x in data.split('\n') if x.split()]
        if len(pkgs) > 10:
            return "Found: %s (and %d others) http://packages.ubuntu.com/search?keywords=%s&searchon=names&suite=%s&section=all" % (', '.join(pkgs[:10]), len(pkgs)-10, urlquote(pkg), distro)
        else:
            return "Found: %s" % ', '.join(pkgs[:5])

    def raw_info(self, pkg, chkdistro):
        if not pkg.strip():
            return ''
        _pkg = ''.join([x for x in pkg.strip().split(None,1)[0] if x.isalnum() or x in '.-_+'])
        distro = chkdistro
        if len(pkg.strip().split()) > 1:
            distro = ''.join([x for x in pkg.strip().split(None,2)[1] if x.isalnum() or x in '-._+'])
        if distro not in self.distros:
            return "%r is not a valid distribution: %s" % (distro, ", ".join(self.distros))

        pkg = _pkg

        try:
            data = apt_cache(self.aptdir, distro, ['show', pkg])
        except subprocess.CalledProcessError as e:
            data = e.output
        try:
            data2 = apt_cache(self.aptdir, distro, ['showsrc', pkg])
        except subprocess.CalledProcessError as e:
            data2 = e.output
        if not data or 'E: No packages found' in data:
            return 'Package %s does not exist in %s' % (pkg, distro)
        maxp = {'Version': '0~'}
        packages = [x.strip() for x in data.split('\n\n')]
        for p in packages:
            if not p.strip():
                continue
            parser = feedparser.FeedParser()
            parser.feed(p)
            p = parser.close()
            if type(p) == type(""):
                self.log.error("PackageInfo/packages: apt returned an error, do you have the deb-src URLs in %s.list?" % distro)
                return "Package lookup faild"
            if not p.get("Version", None):
                continue
            if apt.apt_pkg.version_compare(maxp['Version'], p['Version']) <= 0:
                maxp = p
            del parser
        maxp2 = {'Version': '0~'}
        packages2 = [x.strip() for x in data2.split('\n\n')]
        for p in packages2:
            if not p.strip():
                continue
            parser = feedparser.FeedParser()
            parser.feed(p)
            p = parser.close()
            if type(p) == type(""):
                self.log.error("PackageInfo/packages: apt returned an error, do you have the deb-src URLs in %s.list?" % distro)
                return "Package lookup faild"
            if not p['Version']:
                continue
            if apt.apt_pkg.version_compare(maxp2['Version'], p['Version']) <= 0:
                maxp2 = p
            del parser
        archs = ''
        if 'Architecture' in maxp2:
            archs = [_.strip() for _ in maxp2['Architecture'].split() if _.strip()]
            for arch in archs:
                if arch not in ('any', 'all'):
                    continue
                else:
                    archs = ''
                    break

            if archs:
                archs = ' (Only available for %s)' % '; '.join(archs)

        maxp["Distribution"] = distro
        maxp["Architectures"] = archs
        return maxp

    def info(self, pkg, chkdistro):
        maxp = self.raw_info(pkg, chkdistro)
        if isinstance(maxp, str):
            return maxp
        return("%s (source: %s): %s. In component %s, is %s. Version %s (%s), package size %s kB, installed size %s kB%s" %
               (maxp['Package'], maxp['Source'] or maxp['Package'], description(maxp), component(maxp['Section']),
                maxp['Priority'], maxp['Version'], maxp["Distribution"], int(maxp['Size'])/1024, maxp['Installed-Size'], maxp["Architectures"]))

    def depends(self, pkg, chkdistro):
        maxp = self.raw_info(pkg, chkdistro)
        if isinstance(maxp, str):
            return maxp
        return("%s (version %s in %s) depends on: %s" %
                (maxp['Package'], maxp["Version"], maxp["Distribution"], maxp["Depends"]))
                       
# Simple test
if __name__ == "__main__":
    import sys
    argv = sys.argv
    argc = len(argv)
    if argc == 1:
        print("Need at least one arg")
        sys.exit(1)
    if argc > 3:
        print("Only takes 2 args")
        sys.exit(1)
    class FakePlugin:
        class FakeLog:
            def error(*args, **kwargs):
                pass
        def __init__(self):
            self.log = self.FakeLog()
        def registryValue(self, *args, **kwargs):
            return "/home/bot/aptdir"

    command = argv[1].split(None, 1)[0]
    try:
        lookup = argv[1].split(None, 1)[1]
    except:
        print("Need something to lookup")
        sys.exit(1)
    dists = "hardy"
    if argc == 3:
        dists = argv[2]
    plugin = FakePlugin()
    aptlookup = Apt(plugin)
    if command == "find":
        print(aptlookup.find(lookup, dists))
    else:
        print(aptlookup.info(lookup, dists))

