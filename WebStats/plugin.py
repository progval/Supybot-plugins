# -*- coding: utf8 -*-
###
# Copyright (c) 2010-2011, Valentin Lorentz
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
import time
import random
import datetime
import supybot.conf as conf
import supybot.world as world
import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.irclib as irclib
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3 # for python2.4

try:
    from supybot.i18n import _PluginInternationalization
    class WebStatsInternationalization(_PluginInternationalization):
        def __init__(self):
            self.name = 'WebStats'
            try:
                self.loadLocale(conf.supybot.language())
            except:
                pass
    _ = WebStatsInternationalization()
except ImportError:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

DEBUG = False

world.webStatsCacheLinks = {}
testing = world.testing

def getTemplate(name):
    if 'WebStats.templates.skeleton' in sys.modules:
        reload(sys.modules['WebStats.templates.skeleton'])
    if 'WebStats.templates.%s' % name in sys.modules:
        reload(sys.modules['WebStats.templates.%s' % name])
    module = __import__('WebStats.templates.%s' % name)
    return getattr(getattr(module, 'templates'), name)

class FooException(Exception):
    pass

class WebStatsServerCallback(httpserver.SupyHTTPServerCallback):
    name = 'WebStats'
    def doGet(self, handler, path):
        output = ''
        splittedPath = path.split('/')
        try:
            if path == '/design.css':
                response = 200
                content_type = 'text/css'
                output = getTemplate('design').get(not testing)
            elif path == '/':
                response = 200
                content_type = 'text/html'
                output = getTemplate('index').get(not testing,
                                                 self.db.getChannels())
            elif path == '/%s/' % _('about'):
                response = 200
                content_type = 'text/html'
                output = getTemplate('about').get(not testing)
            elif path == '/global/':
                response = 404
                content_type = 'text/html'
                output = """<p style="font-size: 20em">BAM!</p>
                <p>You played with the URL, you lost.</p>"""
            elif splittedPath[1] in ('nicks', 'global', 'links') \
                    and path[-1]=='/'\
                    or splittedPath[1] == 'nicks' and \
                    path.endswith('.htm'):
                response = 200
                content_type = 'text/html'
                if splittedPath[1] == 'links':
                    try:
                        import pygraphviz
                        content_type = 'image/png'
                    except ImportError:
                        content_type = 'text/plain'
                        response = 501
                        self.send_response(response)
                        self.send_header('Content-type', content_type)
                        self.end_headers()
                        self.wfile.write('Links cannot be displayed; ask '
                                'the bot owner to install python-pygraphviz.')
                        self.wfile.close()
                        return
                assert len(splittedPath) > 2
                chanName = splittedPath[2].replace('%20', '#')
                getTemplate('listingcommons') # Reload
                page = splittedPath[-1][0:-len('.htm')]
                if page == '':
                    page = '0'
                if len(splittedPath) == 3:
                    _.loadLocale(self.plugin._getLanguage(chanName))
                    output = getTemplate(splittedPath[1]).get(not testing,
                                                           chanName,
                                                           self.db,
                                                           len(splittedPath),
                                                           page)
                else:
                    assert len(splittedPath) > 3
                    _.loadLocale(self.plugin._getLanguage(chanName))
                    subdir = splittedPath[3]
                    output = getTemplate(splittedPath[1]).get(not testing,
                                                           chanName,
                                                           self.db,
                                                           len(splittedPath),
                                                           page,
                                                           subdir.lower())
            else:
                response = 404
                content_type = 'text/html'
                output = getTemplate('error404').get(not testing)
        except FooException as  e:
            response = 500
            content_type = 'text/html'
            if output == '':
                output = '<h1>Internal server error</h1>'
                if DEBUG:
                    output += '<p>The server raised this exception: %s</p>' % \
                    repr(e)
        finally:
            self.send_response(response)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(output.encode())

class WebStatsDB:
    def __init__(self):
        filename = conf.supybot.directories.data.dirize('WebStats.db')
        alreadyExists = os.path.exists(filename)
        if alreadyExists and testing:
            os.remove(filename)
            alreadyExists = False
        self._conn = sqlite3.connect(filename, check_same_thread = False)
        self._conn.text_factory = str
        if not alreadyExists:
            self.makeDb()

    def makeDb(self):
        """Create the tables in the database"""
        cursor = self._conn.cursor()
        cursor.execute("""CREATE TABLE messages (
                          chan VARCHAR(128),
                          nick VARCHAR(128),
                          time TIMESTAMP,
                          content TEXT
                          )""")
        cursor.execute("""CREATE TABLE moves (
                          chan VARCHAR(128),
                          nick VARCHAR(128),
                          time TIMESTAMP,
                          type VARCHAR(16),
                          content TEXT
                          )""")
        cursor.execute("""CREATE TABLE links_cache (
                          chan VARCHAR(128),
                          `from` VARCHAR(128),
                          `to` VARCHAR(128),
                          `count` VARCHAR(128))""")
        cacheTableCreator = """CREATE TABLE %s_cache (
                          chan VARCHAR(128),
                          %s
                          year INT,
                          month TINYINT,
                          day TINYINT,
                          dayofweek TINYINT,
                          hour TINYINT,
                          lines INTEGER,
                          words INTEGER,
                          chars INTEGER,
                          joins INTEGER,
                          parts INTEGER,
                          quits INTEGER,
                          nicks INTEGER,
                          kickers INTEGER,
                          kickeds INTEGER
                          )"""
        cursor.execute(cacheTableCreator % ('chans', ''))
        cursor.execute(cacheTableCreator % ('nicks', 'nick VARCHAR(128),'))
        self._conn.commit()
        cursor.close()

    def getChannels(self):
        """Get a list of channels in the database"""
        cursor = self._conn.cursor()
        cursor.execute("""SELECT DISTINCT(chan) FROM chans_cache""")
        results = []
        for row in cursor:
            results.append(row[0])
        cursor.close()
        return results

    def recordMessage(self, chan, nick, message):
        """Called by doPrivmsg or onNotice.

        Stores the message in the database"""
        cursor = self._conn.cursor()
        cursor.execute("""INSERT INTO messages VALUES (?,?,?,?)""",
                       (chan, nick, time.time(), message))
        self._conn.commit()
        cursor.close()
        if DEBUG or random.randint(0,50) == 10:
            self.refreshCache()

    def recordMove(self, chan, nick, type_, message=''):
        """Called by doJoin, doPart, or doQuit.

        Stores the 'move' in the database"""
        cursor = self._conn.cursor()
        cursor.execute("""INSERT INTO moves VALUES (?,?,?,?,?)""",
                       (chan, nick, time.time(), type_, message))
        self._conn.commit()
        cursor.close()
        if DEBUG or random.randint(0,50) == 10:
            self.refreshCache()

    _regexpAddressedTo = re.compile('^(?P<nick>[^a-zA-Z0-9]+):')
    def refreshCache(self):
        """Clears the cache tables, and populate them"""
        self._truncateCache()
        tmp_chans_cache = {}
        tmp_nicks_cache = {}
        tmp_links_cache = {}
        cursor = self._conn.cursor()
        cursor.execute("""SELECT * FROM messages""")
        for row in cursor:
            chan, nick, timestamp, content = row
            chanindex, nickindex = self._getIndexes(chan, nick, timestamp)
            self._incrementTmpCache(tmp_chans_cache, chanindex, content)
            self._incrementTmpCache(tmp_nicks_cache, nickindex, content)

            matched = self._regexpAddressedTo.match(content)
            if matched is not None:
                to = matched.group('nick')
                if chan not in tmp_links_cache:
                    tmp_links_cache.update({chan: {}})
                if nick not in tmp_links_cache[chan]:
                    tmp_links_cache[chan].update({nick: {}})
                if to not in tmp_links_cache[chan][nick]:
                    tmp_links_cache[chan][nick].update({to: 0})
                tmp_links_cache[chan][nick][to] += 1
        for chan, nicks in tmp_links_cache.items():
            for nick, tos in nicks.items(): # Yes, tos is the plural for to
                for to, count in tos.items():
                    if to not in nicks:
                        continue
                    cursor.execute('INSERT INTO links_cache VALUES(?,?,?,?)',
                                   (chan, nick, to, count))
        cursor.close()
        cursor = self._conn.cursor()
        cursor.execute("""SELECT * FROM moves""")
        for row in cursor:
            chan, nick, timestamp, type_, content = row
            chanindex, nickindex = self._getIndexes(chan, nick, timestamp)
            self._addKeyInTmpCacheIfDoesNotExist(tmp_chans_cache, chanindex)
            self._addKeyInTmpCacheIfDoesNotExist(tmp_nicks_cache, nickindex)
            id = {'join':3,'part':4,'quit':5,'nick':6,'kicker':7,'kicked':8}
            id = id[type_]
            tmp_chans_cache[chanindex][id] += 1
            tmp_nicks_cache[nickindex][id] += 1
        cursor.close()
        self._writeTmpCacheToCache(tmp_chans_cache, 'chan')
        self._writeTmpCacheToCache(tmp_nicks_cache, 'nick')
        self._conn.commit()

    def _addKeyInTmpCacheIfDoesNotExist(self, tmpCache, key):
        """Takes a temporary cache list and key.

        If the key is not in the list, add it in the list with value list
        filled with zeros."""
        if not tmpCache.has_key(key):
            tmpCache.update({key: [0, 0, 0, 0, 0, 0, 0, 0, 0]})

    def _truncateCache(self):
        """Clears the cache tables"""
        cursor = self._conn.cursor()
        cursor.execute("""DELETE FROM chans_cache""")
        cursor.execute("""DELETE FROM nicks_cache""")
        cursor.execute("""DELETE FROM links_cache""")
        cursor.close()

    def _incrementTmpCache(self, tmpCache, index, content):
        """Takes a temporary cache list, the index it'll increment, and the
        message content.

        Updates the temporary cache to count the content."""
        self._addKeyInTmpCacheIfDoesNotExist(tmpCache, index)
        tmpCache[index][0] += 1
        tmpCache[index][1] += len(content.split(' '))
        tmpCache[index][2] += len(content)

    def _getIndexes(self, chan, nick, timestamp):
        """Takes a chan name, a nick, and a timestamp, and returns two index,
        to crawl the temporary chans and nicks caches."""
        dt = datetime.datetime.today()
        dt = dt.fromtimestamp(timestamp)
        chanindex = (chan,dt.year,dt.month,dt.day,dt.weekday(),dt.hour)
        nickindex = (chan,nick,dt.year,dt.month,dt.day,dt.weekday(),dt.hour)
        return chanindex, nickindex

    def _writeTmpCacheToCache(self, tmpCache, type_):
        """Takes a temporary cache list, its type, and write it in the cache
        database."""
        cursor = self._conn.cursor()
        for index in tmpCache:
            data = tmpCache[index]
            values = index + tuple(data)
            cursor.execute("""INSERT INTO %ss_cache
                    VALUES(%s)""" % (type_, ('?,'*len(values))[0:-1]), values)
        cursor.close()


    def getChanGlobalData(self, chanName):
        """Returns a tuple, containing the channel stats, on all the recording
        period."""
        cursor = self._conn.cursor()
        cursor.execute("""SELECT SUM(lines), SUM(words), SUM(chars),
                                 SUM(joins), SUM(parts), SUM(quits),
                                 SUM(nicks), SUM(kickers), SUM(kickeds)
                          FROM chans_cache WHERE chan=?""", (chanName,))
        row = cursor.fetchone()
        if None in row:
            oldrow = row
            row = None
            for item in oldrow:
                if row is None:
                    row = (0,)
                else:
                    row += (0,)
        assert None not in row
        return row

    def getChanRecordingTimeBoundaries(self, chanName):
        """Returns two tuples, containing the min and max values of each
        year/month/day/dayofweek/hour field.

        Note that this data comes from the cache, so they might be a bit
        outdated if DEBUG is False."""
        cursor = self._conn.cursor()
        cursor.execute("""SELECT MIN(year), MIN(month), MIN(day),
                                 MIN(dayofweek), MIN(hour)
                          FROM chans_cache WHERE chan=?""", (chanName,))
        min_ = cursor.fetchone()

        cursor = self._conn.cursor()
        cursor.execute("""SELECT MAX(year), MAX(month), MAX(day),
                                 MAX(dayofweek), MAX(hour)
                          FROM chans_cache WHERE chan=?""", (chanName,))
        max_ = cursor.fetchone()

        if None in min_:
            min_ = tuple([int('0') for x in max_])
        if None in max_:
            max_ = tuple([int('0') for x in max_])
        assert None not in min_
        assert None not in max_
        return min_, max_

    def getChanXXlyData(self, chanName, type_):
        """Same as getChanGlobalData, but for the given
        year/month/day/dayofweek/hour.

        For example, getChanXXlyData('#test', 'hour') returns a list of 24
        getChanGlobalData-like tuples."""
        sampleQuery = """SELECT SUM(lines), SUM(words), SUM(chars),
                         SUM(joins), SUM(parts), SUM(quits),
                         SUM(nicks), SUM(kickers), SUM(kickeds)
                         FROM chans_cache WHERE chan=? and %s=?"""
        min_, max_ = self.getChanRecordingTimeBoundaries(chanName)
        typeToIndex = {"year":0, "month":1, "day":2, "dayofweek":3, "hour":4}
        if type_ not in typeToIndex:
            raise ValueError("Invalid type")
        min_ = min_[typeToIndex[type_]]
        max_ = max_[typeToIndex[type_]]
        results = {}
        for index in range(min_, max_+1):
            query = sampleQuery % (type_)
            cursor = self._conn.cursor()
            cursor.execute(query, (chanName, index))
            try:
                row = cursor.fetchone()
                assert row is not None
                if None in row:
                    row=tuple([0 for x in range(0,len(row))])
                results.update({index: row})
            except:
                self._addKeyInTmpCacheIfDoesNotExist(results, index)
            cursor.close()
        assert None not in results
        return results

    def getChanNickGlobalData(self, chanName, nick):
        """Same as getChanGlobalData, but only for one nick."""
        cursor = self._conn.cursor()
        cursor.execute("""SELECT nick, lines, words, chars, joins, parts,
                                 quits, nicks, kickers, kickeds
                          FROM nicks_cache WHERE chan=?""", (chanName,))
        results = {}
        for row in cursor:
            if not results.has_key(row[0]):
                results.update({row[0]: row[1:]})
            else:
                results.update({row[0]: tuple(sum(i)
                    for i in zip(row[1:], results[row[0]]))})
        return results

    def getChanLinks(self, chanName):
        cursor = self._conn.cursor()
        cursor.execute("""SELECT `from`, `to`, `count` FROM links_cache
                          WHERE chan=?""", (chanName,))
        return cursor

    def clearChannel(self, channel):
        cursor = self._conn.cursor()
        for table in ('messages', 'moves', 'links_cache', 'chans_cache',
                'nicks_cache'):
            cursor.execute('DELETE FROM %s WHERE chan=?' % table, (channel,))

class WebStats(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(WebStats, self)
        callbacks.Plugin.__init__(self, irc)
        self.lastmsg = {}
        self.ircstates = {}
        self.db = WebStatsDB()

        callback = WebStatsServerCallback()
        callback.plugin = self
        callback.db = self.db
        httpserver.hook('webstats', callback)

    def die(self):
        httpserver.unhook('webstats')
        self.__parent.die()

    def clear(self, irc, msg, args, channel, optlist):
        """[<channel>]

        Clear database for the <channel>. If <channel> is not given,
        it defaults to the current channel."""
        capability = ircdb.makeChannelCapability(channel, 'op')
        if not ircdb.checkCapability(msg.prefix, capability):
            irc.errorNoCapability(capability, Raise=True)
        if not optlist:
            irc.reply(_('Running this command will wipe all webstats data '
                'for the channel. If you are sure you want to do this, '
                'add the --confirm switch.'))
            return
        self.db.clearChannel(channel)
        irc.replySuccess()
    clear = wrap(clear, ['channel', getopts({'confirm': ''})])

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if not channel.startswith('#'):
            return
        if channel == 'AUTH':
            return
        if not self.registryValue('channel.enable', channel):
            return
        content = msg.args[1]
        nick = msg.prefix.split('!')[0]
        if nick in self.registryValue('channel.excludenicks', channel) \
                .split(' '):
            return
        self.db.recordMessage(channel, nick, content)
    doNotice = doPrivmsg

    def doJoin(self, irc, msg):
        channel = msg.args[0]
        if not self.registryValue('channel.enable', channel):
            return
        nick = msg.prefix.split('!')[0]
        if nick in self.registryValue('channel.excludenicks', channel) \
                .split(' '):
            return
        self.db.recordMove(channel, nick, 'join')

    def doPart(self, irc, msg):
        channel = msg.args[0]
        if not self.registryValue('channel.enable', channel):
            return
        if len(msg.args) > 1:
            message = msg.args[1]
        else:
            message = ''
        nick = msg.prefix.split('!')[0]
        if nick in self.registryValue('channel.excludenicks', channel) \
                .split(' '):
            return
        self.db.recordMove(channel, nick, 'part', message)

    def doQuit(self, irc, msg):
        nick = msg.prefix.split('!')[0]
        if len(msg.args) > 1:
            message = msg.args[1]
        else:
            message = ''
        for channel in self.ircstates[irc].channels:
            if nick in self.registryValue('channel.excludenicks', channel) \
                    .split(' '):
                continue
            if self.registryValue('channel.enable', channel) and \
                msg.nick in self.ircstates[irc].channels[channel].users:
                self.db.recordMove(channel, nick, 'quit', message)
    def doNick(self, irc, msg):
        nick = msg.prefix.split('!')[0]
        if len(msg.args) > 1:
            message = msg.args[1]
        else:
            message = ''
        for channel in self.ircstates[irc].channels:
            if nick in self.registryValue('channel.excludenicks', channel) \
                    .split(' '):
                continue
            if self.registryValue('channel.enable', channel) and \
                msg.nick in self.ircstates[irc].channels[channel].users:
                self.db.recordMove(channel, nick, 'nick', message)
    def doKick(self, irc, msg):
        nick = msg.prefix.split('!')[0]
        if len(msg.args) > 1:
            message = msg.args[1]
        else:
            message = ''
        for channel in self.ircstates[irc].channels:
            if nick in self.registryValue('channel.excludenicks', channel) \
                    .split(' '):
                continue
            if self.registryValue('channel.enable', channel) and \
                msg.nick in self.ircstates[irc].channels[channel].users:
                self.db.recordMove(channel, nick, 'kicker', message)
                self.db.recordMove(channel, msg.args[1], 'kicked', message)

    def _getLanguage(self, channel):
        return self.registryValue('channel.language', '#' + channel)

    # The fellowing functions comes from the Relay plugin, provided
    # with Supybot
    def __call__(self, irc, msg):
        try:
            irc = self._getRealIrc(irc)
            if irc not in self.ircstates:
                self._addIrc(irc)
            self.ircstates[irc].addMsg(irc, self.lastmsg[irc])
        finally:
            self.lastmsg[irc] = msg
        self.__parent.__call__(irc, msg)
    def _addIrc(self, irc):
        # Let's just be extra-special-careful here.
        if irc not in self.ircstates:
            self.ircstates[irc] = irclib.IrcState()
        if irc not in self.lastmsg:
            self.lastmsg[irc] = ircmsgs.ping('this is just a fake message')
        if irc.afterConnect:
            # We've probably been reloaded.  Let's send some messages to get
            # our IrcState objects up to current.
            for channel in irc.state.channels:
                irc.queueMsg(ircmsgs.who(channel))
                irc.queueMsg(ircmsgs.names(channel))
    def _getRealIrc(self, irc):
        if isinstance(irc, irclib.Irc):
            return irc
        else:
            return irc.getRealIrc()

Class = WebStats


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
