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
import urllib
import random
import datetime
if sys.version_info[0] >= 3:
    from io import BytesIO
else:
    from cStringIO import StringIO as BytesIO

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
            super().__init__()
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

testing = world.testing
world.webStatsCacheLinks = {}

#####################################################################
# Utilities
#####################################################################

class FooException(Exception):
    pass

class CacheDict(utils.InsensitivePreservingDict):
    """Subclass of dict to make key comparison IRC-case insensitive."""
    def key(self, k):
        if isinstance(k, str):
            k = ircutils.toLower(k)
        elif isinstance(k, tuple):
            k = tuple([(ircutils.toLower(x) if isinstance(x, str) else x)
                       for x in k])
        else:
            assert False
        return k

if not hasattr(world, 'webStatsCacheLinks'):
    world.webStatsCacheLinks = {}

colors = ['green', 'red', 'orange', 'blue', 'black', 'gray50', 'indigo']

def chooseColor(nick):
    global colors
    return random.choice(colors)

def progressbar(item, max_):
    template = """<td class="progressbar">
                      <div class="text">%i</div>
                      <div style="width: %i%%; background-color: %s"
                      class="color"></div>
                  </td>"""
    try:
        percent = round(float(item)/float(max_)*100)
        color = round((100-percent)/10)*3+59
        template %= (item, percent, '#ef%i%i' % (color, color))
    except ZeroDivisionError:
        template %= (item, 0, 'orange')
    return template

def fillTable(items, page, orderby=None):
    output = ''
    nbDisplayed = 0
    max_ = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    for index in items:
        for index_ in range(0, len(max_)):
            max_[index_] = max(max_[index_], items[index][index_])
    rowsList = []
    while len(items) > 0:
        maximumIndex = max(items.keys())
        highScore = -1
        for index in items:
            if orderby is not None and items[index][orderby] > highScore:
                maximumIndex = index
                highScore = items[index][orderby]
        item = items.pop(maximumIndex)
        try:
            int(index)
            indexIsInt = True
        except:
            indexIsInt = False
        if sum(item[0:1] + item[3:]) > 5 or indexIsInt:
            rowsList.append((maximumIndex, item))
            nbDisplayed += 1
    for row in rowsList[int(page):int(page)+25]:
        index, row = row
        output += '<tr><td>%s</td>' % index
        for cell in (progressbar(row[0], max_[0]),
                     progressbar(row[1], max_[1]),
                     progressbar(row[3], max_[3]),
                     progressbar(row[4], max_[4]),
                     progressbar(row[5], max_[5]),
                     progressbar(row[6], max_[6]),
                     progressbar(row[7], max_[7]),
                     progressbar(row[8], max_[8])
                     ):
            output += cell
        output += '</tr>'
    return output, nbDisplayed

headers = (_('Lines'), _('Words'), _('Joins'), _('Parts'),
           _('Quits'), _('Nick changes'), _('Kicks'), _('Kicked'))
tableHeaders = '<table><tr><th><a href="%s">%s</a></th>'
for header in headers:
    tableHeaders += '<th style="width: 150px;"><a href="%%s%s/">%s</a></th>' %\
                    (header, header)
tableHeaders += '</tr>'

nameToColumnIndex = {_('lines'):0,_('words'):1,_('chars'):2,_('joins'):3,
                     _('parts'):4,_('quits'):5,_('nick changes'):6,_('kickers'):7,
                     _('kicked'):8,_('kicks'):7}
def getTable(firstColumn, items, channel, urlLevel, page, orderby):
    percentParameter = tuple()
    for foo in range(1, len(tableHeaders.split('%s'))-1):
        percentParameter += ('./' + '../'*(urlLevel-4),)
        if len(percentParameter) == 1:
            percentParameter += (firstColumn,)
    output = tableHeaders % percentParameter
    if orderby is not None:
        if sys.version_info[0] >= 3:
            orderby = urllib.parse.unquote(orderby)
        else:
            orderby = urllib.unquote(orderby)
        try:
            index = nameToColumnIndex[orderby]
            html, nbDisplayed = fillTable(items, page, index)
        except KeyError:
            orderby = None
    if orderby is None:
        html, nbDisplayed = fillTable(items, page)
    output += html
    output += '</table>'
    return output, nbDisplayed

#####################################################################
# Templates
#####################################################################

PAGE_SKELETON = """\
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
        <title>Supybot WebStats</title>
        <link rel="stylesheet" media="screen" type="text/css" title="Design" href="/default.css" />
        <link rel="stylesheet" media="screen" type="text/css" title="Design" href="/webstats/design.css" />
    </head>
    <body %s>
%s
        <p id="footer">
            <a href="https://github.com/ProgVal/Limnoria">Limnoria</a> and
            <a href="https://github.com/ProgVal/Supybot-plugins/tree/master/WebStats/">WebStats</a> powered.<br />
            Libre software available under BSD licence.<br />
            Page generated at %%(date)s.
        </p>
    </body>
</html>
"""

DEFAULT_TEMPLATES = {
        'webstats/design.css': """\
body, html {
    text-align: center;
}

li {
    list-style-type: none;
}

#footer {
    width: 100%;
    font-size: 0.6em;
    text-align: right;
}

.chanslist li a:visited {
    color: blue;
}

table {
    margin-left: auto;
    margin-right: auto;
}
.progressbar {
    border: orange 1px solid;
    height: 20px;
}
.progressbar .color {
    background-color: orange;
    height: 20px;
    text-align: center;
    -moz-border-radius: 10px;
    -webkit-border-radius: 10px;
}
.progressbar .text {
    position: absolute;
    width: 150px;
    text-align: center;
    margin-top: auto;
    margin-bottom: auto;
}""",
        'webstats/index.html': PAGE_SKELETON % ('class="purelisting"', """\
<h1>%(title)s</h1>

<ul class="chanslist">
%(channels)s
</ul>"""),
        'webstats/global.html': PAGE_SKELETON % ('', """\
<h1>Stats about %(channel)s channel</h1>

<p><a href="/webstats/nicks/%(escaped_channel)s/">View nick-by-nick stats</a></p>
<p><a href="/webstats/links/%(escaped_channel)s/">View links</a></p>

<p>There were %(quick_stats)s</p>

%(table)s"""),
        'webstats/nicks.html': PAGE_SKELETON % ('', """\
<h1>Stats about %(channel)s channel</h1>

<p><a href="/webstats/global/%(escaped_channel)s/">View global stats</a></p>
<p><a href="/webstats/links/%(escaped_channel)s/">View links</a></p>

%(table)s

<p>%(pagination)s</p>
"""),
}

httpserver.set_default_templates(DEFAULT_TEMPLATES)

#####################################################################
# Controller
#####################################################################

class WebStatsServerCallback(httpserver.SupyHTTPServerCallback):
    name = 'WebStats'
    def doGet(self, handler, path):
        output = ''
        splittedPath = path.split('/')
        try:
            if path == '/design.css':
                response = 200
                content_type = 'text/css; charset=utf-8'
                output = httpserver.get_template('webstats/design.css')
            elif path == '/':
                response = 200
                content_type = 'text/html; charset=utf-8'
                output = self.get_index()
            elif path == '/global/':
                response = 404
                content_type = 'text/html; charset=utf-8'
                output = """<p style="font-size: 20em">BAM!</p>
                <p>You played with the URL, you lost.</p>"""
            elif splittedPath[1] in ('nicks', 'global', 'links') \
                    and path[-1]=='/'\
                    or splittedPath[1] == 'nicks' and \
                    path.endswith('.htm'):
                response = 200
                content_type = 'text/html; charset=utf-8'
                if splittedPath[1] == 'links':
                    try:
                        import pygraphviz
                        content_type = 'image/png'
                    except ImportError:
                        content_type = 'text/plain; charset=utf-8'
                        response = 501
                        output = 'Links cannot be displayed; ask ' \
                                'the bot owner to install python-pygraphviz.'
                        return
                assert len(splittedPath) > 2
                chanName = splittedPath[2].replace('%20', '#')
                page = splittedPath[-1][0:-len('.htm')]
                if page == '':
                    page = '0'
                if splittedPath[1] == 'nicks':
                    formatter = self.get_nicks
                elif splittedPath[1] == 'global':
                    formatter = self.get_global
                elif splittedPath[1] == 'links':
                    formatter = self.get_links
                else:
                    raise AssertionError(splittedPath[1])
                
                if len(splittedPath) == 3:
                    _.loadLocale(self.plugin._getLanguage(chanName))
                    output = formatter(len(splittedPath), chanName, page)
                else:
                    assert len(splittedPath) > 3
                    _.loadLocale(self.plugin._getLanguage(chanName))
                    subdir = splittedPath[3].lower()
                    output = formatter(len(splittedPath), chanName, page,
                            subdir)
            else:
                response = 404
                content_type = 'text/html; charset=utf-8'
                output = httpserver.get_template('generic/error.html') % \
                    {'title': 'WebStats - not found',
                     'error': 'Requested page is not found. Sorry.',
                     'date': time.strftime('%Y-%m-%d %H:%M:%S%z')}
        except Exception as e:
            response = 500
            content_type = 'text/html; charset=utf-8'
            if output == '':
                error = '<h1>Internal server error</h1>'
                if DEBUG:
                    error = '<p>The server raised this exception: %s</p>' % \
                            repr(e)
                output = httpserver.get_template('generic/error.html') % \
                    {'title': 'Internal server error',
                     'error': error,
                     'date': time.strftime('%Y-%m-%d %H:%M:%S%z')}
            import traceback
            traceback.print_exc()
        finally:
            self.send_response(response)
            self.send_header('Content-type', content_type)
            self.end_headers()
            if sys.version_info[0] >= 3:
                output = output.encode()
            self.wfile.write(output)

    def get_index(self):
        template = httpserver.get_template('webstats/index.html')
        channels = self.db.getChannels()
        if len(channels) == 0:
            title = _('Stats available for no channels')
        elif len(channels) == 1:
            title = _('Stats available for a channel:')
        else:
            title = _('Stats available for channels:')
        channels_html = ''
        for channel in channels:
            channels_html += ('<li><a href="/webstats/global/%s/" title="%s">'
                         '%s</a></li>') % \
                      (channel[1:].replace('#', ' '), # Strip the leading #
                      _('View the stats for the %s channel') % channel,
                      channel)
        return template % {'title': title, 'channels': channels_html,
                           'date': time.strftime('%Y-%m-%d %H:%M:%S%z')}

    def get_global(self, urlLevel, channel, page, orderby=None):
        template = httpserver.get_template('webstats/global.html')
        channel = '#' + channel
        items = self.db.getChanGlobalData(channel)
        bound = self.db.getChanRecordingTimeBoundaries(channel)
        hourly_items = self.db.getChanXXlyData(channel, 'hour')
        replacement = {'channel': channel,
                'escaped_channel': channel[1:].replace('#', ' '),
                'quick_stats': utils.str.format(
                    '%n, %n, %n, %n, %n, %n, %n, and %n.',
                    (items[0], _('line')), (items[1], _('word')),
                    (items[2], _('char')), (items[3], _('join')),
                    (items[4], _('part')), (items[5], _('quit')),
                    (items[6], _('nick change')),
                    (items[8], _('kick'))),
                'table': getTable(_('Hour'), hourly_items, channel, urlLevel,
                    page, orderby)[0],
                'date': time.strftime('%Y-%m-%d %H:%M:%S%z'),
                }
        return template % replacement

    def get_nicks(self, urlLevel, channel, page, orderby=None):
        channel = '#' + channel
        template = httpserver.get_template('webstats/nicks.html')
        items = self.db.getChanGlobalData(channel)
        bound = self.db.getChanRecordingTimeBoundaries(channel)
        nickly_items = self.db.getChanNickGlobalData(channel, 20)
        table, nbItems = getTable(_('Nick'), nickly_items, channel,
                urlLevel, page, orderby)

        page = int(page)
        pagination = ''
        if nbItems >= 25:
            if page == 0:
                pagination += '1 '
            else:
                pagination += '<a href="0.htm">1</a> '
            if page > 100:
                pagination += '... '
            for i in range(int(max(1,page/25-3)),int(min(nbItems/25-1,page/25+3))):
                if page != i*25-1:
                    pagination += '<a href="%i.htm">%i</a> ' % (i*25-1, i*25)
                else:
                    pagination += '%i ' % (i*25)
            if nbItems - page > 100:
                pagination += '... '
            if page == nbItems-24-1:
                pagination += '%i' % (nbItems-24)
            else:
                pagination += '<a href="%i.htm">%i</a>' % (nbItems-24-1, nbItems-24)
        replacement = {
                'channel': channel,
                'escaped_channel': channel[1:].replace('#', ' '),
                'table': table,
                'pagination': pagination,
                'date': time.strftime('%Y-%m-%d %H:%M:%S%z'),
                }
        return template % replacement

    def get_links(self, urlLevel, channel, page, orderby=None):
        import pygraphviz
        cache = world.webStatsCacheLinks
        channel = '#' + channel
        items = self.db.getChanLinks(channel)
        output = ''
        if channel in cache and cache[channel][0] > time.time() - 3600:
            output = cache[channel][1]
        else:
            graph = pygraphviz.AGraph(strict=False, directed=True,
                                      start='regular', smoothing='spring',
                                      size='40') # /!\ Size is in inches /!\
            items = [(x,y,float(z)) for x,y,z in items]
            if not items:
                graph.add_node('No links for the moment.')
                buffer_ = BytesIO()
                graph.draw(buffer_, prog='circo', format='png')
                buffer_.seek(0)
                output = buffer_.read()
                return output
            graph.add_node('#root#', style='invisible')
            insertedNicks = {}
            divideBy = max([z for x,y,z in items])/10
            for item in items:
                for i in (0, 1):
                    if item[i] not in insertedNicks:
                        try:
                            insertedNicks.update({item[i]: chooseColor(item[i])})
                            graph.add_node(item[i], color=insertedNicks[item[i]],
                                           fontcolor=insertedNicks[item[i]])
                            graph.add_edge(item[i], '#root#', style='invisible',
                                           arrowsize=0, color='white')
                        except: # Probably unicode issue
                            pass
                graph.add_edge(item[0], item[1], arrowhead='vee',
                               color=insertedNicks[item[1]],
                               penwidth=item[2]/divideBy,
                               arrowsize=item[2]/divideBy/2+1)
            buffer_ = BytesIO()
            graph.draw(buffer_, prog='circo', format='png')
            buffer_.seek(0)
            output = buffer_.read()
            cache.update({channel: (time.time(), output)})
        return output

#####################################################################
# Database
#####################################################################

class WebStatsDB:
    def __init__(self):
        filename = conf.supybot.directories.data.dirize('WebStats.db')
        alreadyExists = os.path.exists(filename)
        if alreadyExists and testing:
            os.remove(filename)
            alreadyExists = False
        self._conn = sqlite3.connect(filename, check_same_thread = False)
        if sys.version_info[0] < 3:
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
        results = ircutils.IrcSet()
        for row in cursor:
            results.add(row[0])
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

    _regexpAddressedTo = re.compile('^(?P<nick>[^:, ]+)[:,]')
    def refreshCache(self):
        """Clears the cache tables, and populate them"""
        self._truncateCache()
        tmp_chans_cache = CacheDict()
        tmp_nicks_cache = CacheDict()
        tmp_links_cache = CacheDict()
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
        for chan, nicks in list(tmp_links_cache.items()):
            for nick, tos in list(nicks.items()): # Yes, tos is the plural for to
                for to, count in list(tos.items()):
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
        if key not in tmpCache:
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
        chanName = ircutils.toLower(chanName)
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
        chanName = ircutils.toLower(chanName)
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
        chanName = ircutils.toLower(chanName)
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
        chanName = ircutils.toLower(chanName)
        cursor = self._conn.cursor()
        cursor.execute("""SELECT nick, lines, words, chars, joins, parts,
                                 quits, nicks, kickers, kickeds
                          FROM nicks_cache WHERE chan=?""", (chanName,))
        results = {}
        for row in cursor:
            if row[0] not in results:
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

#####################################################################
# Plugin
#####################################################################

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

    def refresh(self, irc, msg, args):
        """takes no arguments

        Refreshes WebStats cache."""
        self.db.refreshCache()
        irc.replySuccess()
    refresh = wrap(refresh, ['admin'])

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
