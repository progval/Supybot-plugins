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
import sys
import time
import datetime
import threading
import BaseHTTPServer
import supybot.conf as conf
import supybot.world as world
import supybot.log as log
import supybot.utils as utils
from supybot.commands import *
import supybot.irclib as irclib
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3 # for python2.4

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('WebStats')
except:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

DEBUG = True

testing = world.testing

def getTemplate(name):
    if sys.modules.has_key('WebStats.templates.skeleton'):
        reload(sys.modules['WebStats.templates.skeleton'])
    if sys.modules.has_key('WebStats.templates.%s' % name):
        reload(sys.modules['WebStats.templates.%s' % name])
    module = __import__('WebStats.templates.%s' % name)
    return getattr(getattr(module, 'templates'), name)

class FooException(Exception):
    pass

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def log_request(self, code=None, size=None):
        # By default, it logs the request to stderr
        pass
    def do_GET(self):
        output = ''
        try:
            if self.path == '/design.css':
                response = 200
                content_type = 'text/css'
                output = getTemplate('design').get(not testing)
            elif self.path == '/':
                response = 200
                content_type = 'text/html'
                output = getTemplate('index').get(not testing,
                                                 self.server.db.getChannels())
            elif self.path == '/about/':
                response = 200
                content_type = 'text/html'
                self.end_headers()
                output = getTemplate('about').get(not testing)
            elif self.path == '/%s/' % _('channels'):
                response = 404
                content_type = 'text/html'
                output = """<p style="font-size: 20em">BAM!</p>
                <p>You played with the URL, you losed.</p>"""
            elif self.path.startswith('/%s/' % _('channels')):
                response = 200
                content_type = 'text/html'
                chanName = self.path[len(_('channels'))+2:].split('/')[0]
                output = getTemplate('chan_index').get(not testing, chanName,
                                                       self.server.db)
            else:
                response = 404
                content_type = 'text/html'
                output = getTemplate('error404').get(not testing)
        except FooException as e:
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
            self.wfile.write(output)

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
                          type CHAR(4),
                          content TEXT
                          )""")
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
                          quits INTEGER
                          )"""
        cursor.execute(cacheTableCreator % ('chans', ''))
        cursor.execute(cacheTableCreator % ('nicks', 'nick VARCHAR(128)'))
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
        if DEBUG:
            self.refreshCache()

    def recordMove(self, chan, nick, type_, message=''):
        """Called by doJoin, doPart, or doQuit.

        Stores the 'move' in the database"""
        cursor = self._conn.cursor()
        cursor.execute("""INSERT INTO moves VALUES (?,?,?,?,?)""",
                       (chan, nick, time.time(), type_, message))
        self._conn.commit()
        cursor.close()
        if DEBUG:
            self.refreshCache()

    def refreshCache(self):
        """Clears the cache tables, and populate them"""
        self._truncateCache()
        tmp_chans_cache = {}
        tmp_nicks_cache = {}
        cursor = self._conn.cursor()
        cursor.execute("""SELECT * FROM messages""")
        for row in cursor:
            chan, nick, timestamp, content = row
            chanindex, nickindex = self._getIndexes(chan, nick, timestamp)
            self._incrementTmpCache(tmp_chans_cache, chanindex, content)
            self._incrementTmpCache(tmp_nicks_cache, nickindex, content)
        cursor.close()
        cursor = self._conn.cursor()
        cursor.execute("""SELECT * FROM moves""")
        for row in cursor:
            chan, nick, timestamp, type_, content = row
            chanindex, nickindex = self._getIndexes(chan, nick, timestamp)
            self._addKeyInTmpCacheIfDoesNotExist(tmp_chans_cache, chanindex)
            self._addKeyInTmpCacheIfDoesNotExist(tmp_nicks_cache, nickindex)
            id = {'join': 3, 'part': 4, 'quit': 5}[type_]
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
            tmpCache.update({key: [0, 0, 0, 0, 0, 0]})

    def _truncateCache(self):
        """Clears the cache tables"""
        cursor = self._conn.cursor()
        cursor.execute("""DELETE FROM chans_cache""")
        cursor.execute("""DELETE FROM nicks_cache""")
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
        chanindex = (chan, dt.year, dt.month, dt.day, dt.weekday(), dt.hour)
        nickindex = (nick, dt.year, dt.month, dt.day, dt.weekday(), dt.hour)
        return chanindex, nickindex

    def _writeTmpCacheToCache(self, tmpCache, type_):
        """Takes a temporary cache list, its type, and write it in the cache
        database."""
        cursor = self._conn.cursor()
        for index in tmpCache:
            data = tmpCache[index]
            cursor.execute("""INSERT INTO %ss_cache
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""" % type_,
                    (index[0], index[1], index[2], index[3], index[4], index[5],
                    data[0], data[1], data[2], data[3], data[4], data[5]))
        cursor.close()


    def getChanGlobalData(self, chanName):
        """Returns a tuple, containing the channel stats, on all the recording
        period."""
        cursor = self._conn.cursor()
        cursor.execute("""SELECT SUM(lines), SUM(words), SUM(chars),
                                 SUM(joins), SUM(parts), SUM(quits)
                          FROM chans_cache WHERE chan=?""", (chanName,))
        row = cursor.fetchone()
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

        return min_, max_

    def getChanXXlyData(self, chanName, type_):
        """Same as getChanGlobalData, but for the given
        year/month/day/dayofweek/hour.

        For example, getChanXXlyData('#test', 'hour') returns a list of 24
        getChanGlobalData-like tuples."""
        sampleQuery = """SELECT lines, words, chars, joins, parts, quits
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
                if row is None:
                    raise Exception()
                results.update({index: row})
            except:
                self._addKeyInTmpCacheIfDoesNotExist(results, index)
            cursor.close()
        return results

class WebStatsHTTPServer(BaseHTTPServer.HTTPServer):
    """A simple class that set a smaller timeout to the socket"""
    timeout = 0.1

class Server:
    """The WebStats HTTP server handler."""
    def __init__(self, plugin):
        self.serve = True
        self._plugin = plugin
    def run(self):
        serverAddress = (self._plugin.registryValue('server.host'),
                          self._plugin.registryValue('server.port'))
        done = False
        while not done:
            time.sleep(1)
            try:
                httpd = WebStatsHTTPServer(serverAddress, HTTPHandler)
                done = True
            except:
                pass
        log.info('WebStats web server launched')
        httpd.db = self._plugin.db
        while self.serve:
            httpd.handle_request()
        httpd.server_close()
        time.sleep(1) # Let the socket be really closed


class WebStats(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(WebStats, self)
        callbacks.Plugin.__init__(self, irc)
        self.lastmsg = {}
        self.ircstates = {}
        self.db = WebStatsDB()
        self._server = Server(self)
        if not world.testing:
            threading.Thread(target=self._server.run,
                             name="WebStats HTTP Server").start()

    def die(self):
        self._server.serve = False
        self.__parent.die()

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if channel == 'AUTH':
            return
        if not self.registryValue('channel.enable', channel):
            return
        content = msg.args[1]
        nick = msg.prefix.split('!')[0]
        self.db.recordMessage(channel, nick, content)
    doNotice = doPrivmsg

    def doJoin(self, irc, msg):
        channel = msg.args[0]
        if not self.registryValue('channel.enable', channel):
            return
        nick = msg.prefix.split('!')[0]
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
        self.db.recordMove(channel, nick, 'part', message)

    def doQuit(self, irc, msg):
        nick = msg.prefix.split('!')[0]
        if len(msg.args) > 1:
            message = msg.args[1]
        else:
            message = ''
        for channel in self.ircstates[irc].channels:
            if self.registryValue('channel.enable', channel):
                self.db.recordMove(channel, nick, 'quit', message)

    # The two fellowing functions comes from the Relay plugin, provided
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
