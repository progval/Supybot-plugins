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

def fillTable(items, orderby=None):
    output = ''
    max_ = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    for index in items:
        for index_ in range(0, len(max_)):
            max_[index_] = max(max_[index_], items[index][index_])
    rowsList = []
    if orderby is not None:
        while len(items) > 0:
            maximumIndex = None
            highScore = -1
            for index in items:
                if items[index][orderby] > highScore:
                    maximumIndex = index
                    highScore = items[index][orderby]
            rowsList.append((maximumIndex, items.pop(maximumIndex)))
    else:
        for index in items.keys():
            rowsList.append((index, items.pop(index)))
    for row in rowsList[0:20]:
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
    return output

headers = (_('Lines'), _('Words'), _('Joins'), _('Parts'),
           _('Quits'), _('Nick changes'), _('Kicks'), _('Kicked'))
tableHeaders = '<table><tr><th><a href="%s">%s</a></th>'
for header in headers:
    tableHeaders += '<th style="width: 100px;"><a href="%%s%s">%s</a></th>' %\
                    (header, header)

nameToColumnIndex = {'lines':0,'words':1,'chars':2,'joins':3,'parts':4,
                     'quits':5,'nicks':6,'kickers':7,'kickeds':8,'kicks':7}
def getTable(firstColumn, items, channel, orderby):
    percentParameter = tuple()
    for foo in range(1, len(tableHeaders.split('%s'))-1):
        percentParameter += ('/%s/%s/' % (_('channels'), channel[1:]),)
        if len(percentParameter) == 1:
            percentParameter += (firstColumn,)
    output = tableHeaders % percentParameter
    if orderby is not None:
        orderby = orderby.split('%20')[0]
        if not orderby.endswith('s'):
            orderby += 's'
        try:
            index = nameToColumnIndex[orderby]
            output += fillTable(items, index)
        except KeyError:
            orderby = None
    if orderby is None:
        output += fillTable(items)
    output += '</table>'
    return output

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
    output += getTable(_('Hour'), items, channel, orderby)

    output += '<br />'

    items = db.getChanNickGlobalData(channel, 20)
    output += getTable(_('Nick'), items, channel, orderby)

    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
