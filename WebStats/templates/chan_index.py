import skeleton
import supybot.utils as utils
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('WebStats')
except:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

content = \
'<h1>%s</h1><p>%s</p>'


def progressbar(item, max_):
    template = """<td class="progressbar">
                      <div class="text">%i</div>
                      <div style="width: %ipx" class="color"></div>
                  </td>"""
    try:
        template %= (item, round(float(item)/float(max_)*100))
    except ZeroDivisionError:
        template %= (item, 0)
    return template

headers = (_('Hour'), _('Lines'), _('Words'), _('Joins'), _('Parts'),
           _('Quits'), _('Nick changes'), _('Kicks'))
tableHeaders = '<table><tr>'
for header in headers:
    tableHeaders += '<th style="width: 100px;">%s</th>' % header
def get(useSkeleton, channel, db):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    bound = db.getChanRecordingTimeBoundaries(channel)
    output = '<h1>%s</h1>' % _('Stats about %s channel')
    output %= channel
    output += '<p>%s</p>' % _('There were %n, %n, %n, %n, %n, %n, %n, '
                              'and %n.')
    output = utils.str.format(output, (items[0], 'line'), (items[1], 'word'),
                                       (items[2], 'char'), (items[3], 'join'),
                                       (items[4], 'part'), (items[5], 'quit'),
                                       (items[6], 'nick change'),
                                       (items[8], 'kick'))
    output += tableHeaders
    items = db.getChanXXlyData(channel, 'hour')
    max_ = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    min_hour = 24
    max_hour = 0
    for item in items:
        min_hour = min(min_hour, item)
        max_hour = max(max_hour, item)
    for hour in range(min_hour, max_hour+1):
        for index in range(0, len(max_)):
            max_[index] = max(max_[index], items[hour][index])
    for hour in range(min_hour, max_hour+1):
        output += '<tr><td>%s</td>' % hour
        for cell in (progressbar(items[hour][0], max_[0]),
                     progressbar(items[hour][1], max_[1]),
                     progressbar(items[hour][3], max_[3]),
                     progressbar(items[hour][4], max_[4]),
                     progressbar(items[hour][5], max_[5]),
                     progressbar(items[hour][6], max_[6]),
                     progressbar(items[hour][8], max_[8])
                     ):
            output += cell
        output += '</tr>'
    output += '</table>'
    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
