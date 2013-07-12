#!/usr/bin/python
# CleverBot Supybot Plugin v1.0
# (C) Copyright 2012 Albert H. (alberthrocks)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# This is from the pycleverbot library, found at:
# http://code.google.com/p/pycleverbot/
# 

"""
This library lets you open chat session with cleverbot (www.cleverbot.com)

Example of how to use the bindings:

>>> import cleverbot
>>> cb=cleverbot.Session()
>>> print cb.Ask("Hello there")
'Hello.'

"""

import hashlib
import sys
import re

if sys.version_info[0] >= 3:
    import urllib
    Request = urllib.request.Request
    urlopen = urllib.request.urlopen
    def u(s):
        return s
    def b(s):
        return s.encode('utf-8')
else:
    import urllib2
    from urllib import urlencode, urlopen
    Request = urllib2.Request
    def u(s):
        return unicode(s, "unicode_escape")
    def b(s):
        return s

class ServerFullError(Exception):
    pass

ReplyFlagsRE = re.compile('<INPUT NAME=(.+?) TYPE=(.+?) VALUE="(.*?)">', re.IGNORECASE | re.MULTILINE)

class Session(object):
    keylist=['stimulus','start','sessionid','vText8','vText7','vText6','vText5','vText4','vText3','vText2','icognoid','icognocheck','prevref','emotionaloutput','emotionalhistory','asbotname','ttsvoice','typing','lineref','fno','sub','islearning','cleanslate']
    headers={}
    headers['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0'
    headers['Accept']='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    headers['Accept-Language']='en-us;q=0.8,en;q=0.5'
    headers['X-Moz']='prefetch'
    headers['Accept-Charset']='ISO-8859-1,utf-8;q=0.7,*;q=0.7'
    headers['Referer']='http://www.cleverbot.com'
    headers['Cache-Control']='no-cache, no-cache'
    headers['Pragma']='no-cache'

    def __init__(self):
        self.arglist=['','y','','','','','','','','','wsf','','','','','','','','','0','Say','1','false']
        self.MsgList=[]

    def Send(self):
        data=encode(self.keylist,self.arglist)
        digest_txt=data[9:29]
        hash=hashlib.md5(b(digest_txt)).hexdigest()
        self.arglist[self.keylist.index('icognocheck')]=hash
        data=encode(self.keylist,self.arglist)
        req=Request("http://www.cleverbot.com/webservicemin",b(data),self.headers)
        f=urlopen(req, timeout=9) #Needed to prevent supybot errors
        reply=f.read()
        if sys.version_info[0] >= 3:
            reply = reply.decode()
        return reply

    def Ask(self,q):
        self.arglist[self.keylist.index('stimulus')]=q
        if self.MsgList: self.arglist[self.keylist.index('lineref')]='!0'+str(len(self.MsgList)/2)
        asw=self.Send()
        self.MsgList.append(q)
        answer = parseAnswers(asw)
        for k,v in answer.items():
            try:
                self.arglist[self.keylist.index(k)] = v
            except ValueError:
                pass
        self.arglist[self.keylist.index('emotionaloutput')]=''
        text = answer['ttsText']
        self.MsgList.append(text)
        return text

def parseAnswers(text):
    d = {}
    keys = ["text", "sessionid", "logurl", "vText8", "vText7", "vText6", "vText5", "vText4", "vText3",
            "vText2", "prevref", "foo", "emotionalhistory", "ttsLocMP3", "ttsLocTXT",
            "ttsLocTXT3", "ttsText", "lineRef", "lineURL", "linePOST", "lineChoices",
            "lineChoicesAbbrev", "typingData", "divert"]
    values = text.split("\r")
    i = 0
    for key in keys:
        d[key] = values[i]
        i += 1
    return d

def encode(keylist,arglist):
    text=''
    for i in range(len(keylist)):
        k=keylist[i]; v=quote(arglist[i])
        text+='&'+k+'='+v
    text=text[1:]
    return text

always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789' '_.-')
def quote(s, safe = '/'):   #quote('abc def') -> 'abc%20def'
    safe += always_safe
    safe_map = {}
    for i in range(256):
        c = chr(i)
        safe_map[c] = (c in safe) and c or  ('%%%02X' % i)
    res = map(safe_map.__getitem__, s)
    return ''.join(res)


def main():
    import sys
    cb = Session()

    q = ''
    while q != 'bye':
        try:
            if sys.version_info[0] < 3:
                q = raw_input("> ")
            else:
                q = input("> ")
        except KeyboardInterrupt:
            print()
            sys.exit()
        print(cb.Ask(q))

if __name__ == "__main__":
    main()


