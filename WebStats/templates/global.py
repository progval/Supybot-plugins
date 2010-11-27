from listingcommons import *
from listingcommons import _

def get(useSkeleton, channel, db, urlLevel, page, orderby=None):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    bound = db.getChanRecordingTimeBoundaries(channel)
    output = '<h1>%s</h1>' % _('Stats about %s channel')
    output %= channel
    output += '<p><a href="/nicks/%s/">View nick-by-nick stats</a></p>' % \
                                                                channel[1:]
    output += '<p>%s</p>' % _('There were %n, %n, %n, %n, %n, %n, %n, '
                              'and %n.')
    output = utils.str.format(output, (items[0], 'line'), (items[1], 'word'),
                                       (items[2], 'char'), (items[3], 'join'),
                                       (items[4], 'part'), (items[5], 'quit'),
                                       (items[6], 'nick change'),
                                       (items[8], 'kick'))
    items = db.getChanXXlyData(channel, 'hour')
    output += getTable(_('Hour'), items, channel, urlLevel, int(page), orderby)

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
