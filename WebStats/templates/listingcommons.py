import urllib
import skeleton
import supybot.utils as utils
from WebStats.plugin import _

content = \
'<h1>%s</h1><p>%s</p>'

def progressbar(item, max_):
    template = """<td class="progressbar">
                      <div class="text">%i</div>
                      <div style="width: %ipx; background-color: %s"
                      class="color"></div>
                  </td>"""
    try:
        percent = round(float(item)/float(max_)*100)
        color = round((100-percent)/10)*3+59
        template %= (item, percent, '#ef%i%i' % (color, color))
    except ZeroDivisionError:
        template %= (item, 0, 'orange')
    return template

def fillTable(items, page, orderby=None):
    output = ''
    nbDisplayed = 0
    max_ = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    for index in items:
        for index_ in range(0, len(max_)):
            max_[index_] = max(max_[index_], items[index][index_])
    rowsList = []
    while len(items) > 0:
        maximumIndex = (0, 0, 0, 0, 0)
        highScore = -1
        for index in items:
            if orderby is not None and items[index][orderby] > highScore:
                maximumIndex = index
                highScore = items[index][orderby]
            if orderby is None and index < maximumIndex:
                maximumIndex = index
        item = items.pop(maximumIndex)
        try:
            int(index)
            indexIsInt = True
        except:
            indexIsInt = False
        if sum(item[0:1] + item[3:]) > 5 or indexIsInt:
            rowsList.append((maximumIndex, item))
            nbDisplayed += 1
    for row in rowsList[int(page):int(page)+25]:
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
    return output, nbDisplayed

headers = (_('Lines'), _('Words'), _('Joins'), _('Parts'),
           _('Quits'), _('Nick changes'), _('Kicks'), _('Kicked'))
tableHeaders = '<table><tr><th><a href="%s">%s</a></th>'
for header in headers:
    tableHeaders += '<th style="width: 150px;"><a href="%%s%s/">%s</a></th>' %\
                    (header, header)
tableHeaders += '</tr>'

nameToColumnIndex = {_('lines'):0,_('words'):1,_('chars'):2,_('joins'):3,
                     _('parts'):4,_('quits'):5,_('nick changes'):6,_('kickers'):7,
                     _('kicked'):8,_('kicks'):7}
def getTable(firstColumn, items, channel, urlLevel, page, orderby):
    percentParameter = tuple()
    for foo in range(1, len(tableHeaders.split('%s'))-1):
        percentParameter += ('./' + '../'*(urlLevel-4),)
        if len(percentParameter) == 1:
            percentParameter += (firstColumn,)
    output = tableHeaders % percentParameter
    if orderby is not None:
        orderby = urllib.unquote(orderby)
        try:
            index = nameToColumnIndex[orderby]
            html, nbDisplayed = fillTable(items, page, index)
        except KeyError:
            orderby = None
    if orderby is None:
        html, nbDisplayed = fillTable(items, page)
    output += html
    output += '</table>'
    return output, nbDisplayed
