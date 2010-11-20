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
    items = db.getChanMainData(channel)
    output = content % (_("Stats about %s channel"), _("There were %n, %n, %n, %n, %n, and %n."))
    output = utils.str.format(output, channel, (items[1], 'line'), (items[2], 'word'),
                                       (items[3], 'char'), (items[4], 'join'),
                                       (items[5], 'part'), (items[6], 'quit'))
    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
