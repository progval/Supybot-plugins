from listingcommons import *
from listingcommons import _

def get(useSkeleton, channel, db, urlLevel, page, orderby=None):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    bound = db.getChanRecordingTimeBoundaries(channel)
    output = '<h1>%s</h1>' % _('Stats about %s channel users')
    output %= channel
    output += '<p><a href="/global/%s/">View global channel stats</a></p>' % \
                                                                    channel[1:]
    output = utils.str.format(output, (items[0], 'line'), (items[1], 'word'),
                                       (items[2], 'char'), (items[3], 'join'),
                                       (items[4], 'part'), (items[5], 'quit'),
                                       (items[6], 'nick change'),
                                       (items[8], 'kick'))
    items = db.getChanNickGlobalData(channel, 20)
    nbItems = len(items)
    output += getTable(_('Nick'), items, channel, urlLevel, page, orderby)
    nbItems -= len(items)

    page = int(page)
    output += '<p>'
    if nbItems >= 25:
        if page == 0:
            output += '1 '
        else:
            output += '<a href="0.htm">1</a> '
        if page > 100:
            output += '... '
        for i in range(int(max(1, page/25-3))+1, int(min(nbItems/25, page/25+3))+2):
            if page != i*25-1:
                output += '<a href="%i.htm">%i</a> ' % (i*25-1, i*25)
            else:
                output += '%i ' % (i*25)
        if nbItems - page > 100:
            output += '... '
        if page == nbItems -1:
            output += '%i' % nbItems
        else:
            output += '<a href="%i.htm">%i</a>' % (nbItems-1, nbItems)
        output += '</p>'

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
