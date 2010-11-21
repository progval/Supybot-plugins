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
"<h1>%s</h1><p>%s</p>"

def get(useSkeleton, channel, db):
    channel = '#' + channel
    items = db.getChanGlobalData(channel)
    output = content % (_("Stats about %s channel"), _("There were %n, %n, %n, %n, %n, and %n."))
    output = utils.str.format(output, channel, (items[0], 'line'), (items[1], 'word'),
                                       (items[2], 'char'), (items[3], 'join'),
                                       (items[4], 'part'), (items[5], 'quit'))
    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
