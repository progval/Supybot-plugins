###
# Copyright (c) 2012, Dan
# All rights reserved.
#
#
###

from supybot.test import *

class IMDbTestCase(PluginTestCase):
    plugins = ('IMDb', 'Google')

    if network:
        def testSearch(self):
            self.assertResponse('imdb Steven Universe',
                    '\x02\x031,8IMDb\x03 http://www.imdb.com/title/tt3061046/')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
