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

def get(useSkeleton, channel, db):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    bound = db.getChanRecordingTimeBoundaries(channel)
    output = '<h1>%s</h1>' % _('Stats about %s channel')
    output %= channel
    output += '<p>%s</p>' % _('There were %n, %n, %n, %n, %n, and %n.')
    output = utils.str.format(output, (items[0], 'line'), (items[1], 'word'),
                                       (items[2], 'char'), (items[3], 'join'),
                                       (items[4], 'part'), (items[5], 'quit'))
    output += '<table><tr><th>%s</th><th style="width: 100px;">%s</th></tr>'
    output %= (_('Hour'), _('Lines'))
    items = db.getChanXXlyData(channel, 'hour')
    max_ = 0
    for hour in items:
        max_ = max(max_, items[hour][0])
    for hour in items:
        output += """<tr>
                        <td>%s</td>
                        <td class="progressbar">
                            <div class="text">%i</div>
                            <div style="width: %ipx" class="color"></div>
                        </td>
                    </tr>""" % \
                 (hour, items[hour][0], round(float(items[hour][0])/float(max_)*100))
    output += '</table>'
    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
