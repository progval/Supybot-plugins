###
# Copyright (c) 2010, Valentin Lorentz
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
import urllib
import urllib2
import tarfile
import supybot
import supybot.conf as conf
from xml.dom import minidom
import supybot.utils as utils
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

# Exceptions tree:
# PackageException
#   |- PackageFormatException
#   |   |- TarFormatException
#   |   |- MetadataException
#   |   |   |- MissingMetadataFileException
#   |   |   |- XmlMetadataFormatException
#   |   |   |- MissingMetadataDataException
#   |   |   `- DuplicatedMetadataDataException
#   |   |       `- DuplicatedAuthorException
#   `- PackageCompatibilityException
#       `- VersionNotCompatibleException
#           |- CurrentVersionIsTooOldException
#           `- CurrentVersionIsTooNewException


class PackageException(Exception):
    pass
class PackageFormatException(PackageException):
    pass
class TarFormatException(PackageFormatException):
    pass
class MetadataException(PackageFormatException):
    pass
class MissingMetadataFileException(MetadataException):
    pass
class XmlMetadataFormatException(MetadataException):
    pass
class MissingMetadataDataException(MetadataException):
    pass
class PackageCompatibilityException(PackageException):
    pass
class VersionNotCompatibleException(PackageCompatibilityException):
    pass
class CurrentVersionIsTooOldException(VersionNotCompatibleException):
    pass
class CurrentVersionIsTooNewException(VersionNotCompatibleException):
    pass

def getWhetherIsOlderThan(version):
    """Checks if the current version is older than the given version"""
    def split(version):
        splitted = version.split('+')
        patches = splitted[1:]
        numbers = splitted[0].split('.')
        return numbers.extend(patches)
    givenVersion = split(version)
    currentVersion = split(conf.version)
    for index in range(0, min(len(givenVersion), len(currentVersion))):
        if currentVersion[index] < givenVersion[index]:
            return True
        elif currentVersion[index] > givenVersion[index]:
            return False
    if len(givenVersion) < len(currentVersion):
        return True
    if len(givenVersion) >= len(currentVersion):
        return True

class Package:
    """Class that stands for a package"""
    def __init__(self, file):
        self.extractData(file)
        self.parseMetadata(self.metadata)
        self._file = file
    
    def extractData(self, file):
        """Extracts data from the given file object, and fill the object
        attributes with it"""
        try:
            file = tarfile.open(fileobj=file, mode='r:')
        except tarfile.ReadError:
            raise TarFormatException()
        self.filesToExtract = []
        self.metadata == '', '', ''
        for name in file.getnames():
            if name.startswith('plugin/'):
                self.filesToExtract.append(name)
            elif name == 'data/info.xml':
                self._metadata = file.extractfile(name)
        if self._metadata == '':
            raise MissingMetadataFileException()

    def parseMetadata(self):
        """Parses the string in self._metadata"""
        metadata = minidom.parseString(self._metadata)
        for childNode in metadata:
            if childNode.nodeName == 'compatibility':
                self._extractCompatibilityData(childNode)
            elif childNode.nodeName == 'authoring':
                self._extractAuthoringData(childNode)
            elif childNode.nodeName == 'plugin':
                self._extractPluginData(childNode)

    def _extractCompatibilityData(self, node):
        """Takes the <compatibility> node of the metadata file, parse it, and
        extracts data"""
        for childNode in node.childNodes:
            if childNode.nodeName == 'version':
                for grandChildNode in childNode.childNodes:
                    if grandChildNode.nodeName == 'oldest' and \
                    getWhetherIsOlderThan(grandChildNode.value):
                        raise CurrentVersionIsTooOldException()
                    if grandChildNode.nodeName == 'newest' and \
                    not getWhetherIsOlderThan(grandChildNode.value):
                        raise CurrentVersionIsTooNewException()
                    #TODO add <isnot> managment

    def _extractAuthoringData(self, node):
        """Takes the <authoring> node of the metadata file, parses it, and
        extracts data"""
        for childNode in node:
            if childNode.nodeName == 'author':
                if hasattr(self, 'author'):
                    raise DuplicatedAuthorException()
                self.author = self._getAuthorFromNode(childNode)
            if childNode.nodeName == 'contributor':
                self.contributors.append(self._getAuthorFromNode(childNode))

    def _getAuthorFromNode(self, node):
        """Takes a <author> or a <contributor> node from the metadatafile,
        parses it, and returns an Author object"""
        for childNode in node.childNodes:
            if childNode.nodeName == 'realname':
                realname = childNode.value
            elif childNode.nodeName == 'nickname':
                nickname = childNode.value
            elif childNode.nodeName == 'email':
                email = childNode.value
        try:
            author = supybot.Author(realname, nickname, email)
        except:
            author = supybot.authors.unknown
        return author

    def _extractPluginData(self, node):
        """Takes the <plugin> node of the metadata file, parse it, and
        extracts data"""
        for childNode in node.childNodes:
            if childNode.nodeName == 'name':
                self.name = childNode.value
            elif childNode.nodeName == 'version':
                self.version = childNode.value
    
    def extractToFilesystem(self, plugindir):
        """Extracts the files from the package in the given plugin directory"""
        for filename in self.filesToExtract:
            file.extract(filename, '%s/%s/' % (plugindir, self.name))

lineParser = re.compile('.*<a href="(?P<URL>.+\.tar)">'
                            '(?P<plugin_name>\w+)\.tar'
                        '</a>.*')
class PackagesServer:
    def __init__(self, url):
        if not url.endswith('/'):
            url += '/'
        self._url = url
        self.packages = {}
        self.fetch()

    def fetch(self):
        response = self.getPage(self._url)
        for line in response:
            parsed = lineParser.match(line)
            if parsed is None:
                continue
            print repr(self.getPage(self._url + parsed.group('URL')))
            self.packages.update({parsed.group('plugin_name'):
                       Package(self.getPage(self._url + parsed.group('URL')))})

    def getPage(self, url):
        """Returns the content of the URL"""
        print url
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url += 'protocol=supybot&version=0.1'
        return urllib2.urlopen(urllib2.Request(url))

class Packages(callbacks.Plugin):
    """This plugins allows to download packages for Supybot."""
    threaded = True
    
    def fetch(self, irc, msg, args):
        pluginsSource = self.registryValue('sources.plugins')
        self._packagesServer = PackagesServer(pluginsSource)
        irc.replySuccess()
    fetch = wrap(fetch, ['owner'])
    
    def getlist(self, irc, msg, args):
        if not hasattr(self, '_packagesServer'):
            irc.error(_('The plugins list is not yet downloaded.'))
            return
        irc.reply(format('%L', self._packagesServer.packages.keys()))
        
    
Packages = internationalizeDocstring(Package)

Class = Packages


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
