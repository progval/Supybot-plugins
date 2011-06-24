from listingcommons import *
from listingcommons import _

def get(useSkeleton, channel, db, urlLevel, page, orderby=None):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    bound = db.getChanRecordingTimeBoundaries(channel)
    output = '<h1>%s</h1>' % _('Stats about %s channel users')
    output %= channel
    output += '<p><a href="/webstats/global/%s/">%s</a></p>' % \
            (channel[1:].replace('#', ' '), _('View global stats'))
    output += '<p><a href="/webstats/links/%s/">%s</a></p>' % \
            (channel[1:].replace('#', ' '),  _('View links'))
    items = db.getChanNickGlobalData(channel, 20)
    html, nbDisplayed = getTable(_('Nick'),items,channel,urlLevel,page,orderby)
    output += html
    nbItems = nbDisplayed

    page = int(page)
    output += '<p>'
    if nbItems >= 25:
        if page == 0:
            output += '1 '
        else:
            output += '<a href="0.htm">1</a> '
        if page > 100:
            output += '... '
        for i in range(int(max(1,page/25-3)),int(min(nbItems/25-1,page/25+3))):
            if page != i*25-1:
                output += '<a href="%i.htm">%i</a> ' % (i*25-1, i*25)
            else:
                output += '%i ' % (i*25)
        if nbItems - page > 100:
            output += '... '
        if page == nbItems-24-1:
            output += '%i' % (nbItems-24)
        else:
            output += '<a href="%i.htm">%i</a>' % (nbItems-24-1, nbItems-24)
        output += '</p>'

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
