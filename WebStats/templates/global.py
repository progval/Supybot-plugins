from listingcommons import *
from listingcommons import _

def get(useSkeleton, channel, db, urlLevel, page, orderby=None):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    bound = db.getChanRecordingTimeBoundaries(channel)
    output = '<h1>%s</h1>' % _('Stats about %s channel')
    output %= channel
    output += '<p><a href="/webstats/nicks/%s/">%s</a></p>' % \
            (channel[1:].replace('#', ' '), _('View nick-by-nick stats'))
    output += '<p><a href="/webstats/links/%s/">%s</a></p>' % \
            (channel[1:].replace('#', ' '), ('View links'))
    output += '<p>%s</p>' % _('There were %n, %n, %n, %n, %n, %n, %n, '
                              'and %n.')
    output = utils.str.format(output, (items[0], _('line')), (items[1], _('word')),
                                       (items[2], _('char')), (items[3], _('join')),
                                       (items[4], _('part')), (items[5], _('quit')),
                                       (items[6], _('nick change')),
                                       (items[8], _('kick')))
    items = db.getChanXXlyData(channel, 'hour')
    html, nbDisplayed = getTable(_('Hour'), items, channel, urlLevel, page, orderby)
    output += html

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
