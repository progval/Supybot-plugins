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

def fillTable(items, indexes):
    output = ''
    max_ = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    for index in indexes:
        for index_ in range(0, len(max_)):
            max_[index_] = max(max_[index_], items[index][index_])
    for index in indexes:
        output += '<tr><td>%s</td>' % index
        for cell in (progressbar(items[index][0], max_[0]),
                     progressbar(items[index][1], max_[1]),
                     progressbar(items[index][3], max_[3]),
                     progressbar(items[index][4], max_[4]),
                     progressbar(items[index][5], max_[5]),
                     progressbar(items[index][6], max_[6]),
                     progressbar(items[index][8], max_[8])
                     ):
            output += cell
        output += '</tr>'
    return output

headers = (_('Hour'), _('Lines'), _('Words'), _('Joins'), _('Parts'),
           _('Quits'), _('Nick changes'), _('Kicks'))
tableHeaders = '<table><tr>'
for header in headers:
    tableHeaders += '<th style="width: 100px;">%s</th>' % header
def get(useSkeleton, channel, db, orderby=None):
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
    items = db.getChanXXlyData(channel, 'hour')
    min_hour = 24
    max_hour = 0
    for item in items:
        min_hour = min(min_hour, item)
        max_hour = max(max_hour, item)
    output += tableHeaders
    output += fillTable(items, range(min_hour, max_hour+1))
    output += '</table>'

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
