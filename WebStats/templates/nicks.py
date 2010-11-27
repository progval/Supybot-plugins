from listingcommons import *
from listingcommons import _

def get(useSkeleton, channel, db, urlLevel, orderby=None):
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
    output += getTable(_('Nick'), items, channel, urlLevel, orderby)

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
