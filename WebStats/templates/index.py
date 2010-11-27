import skeleton
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('WebStats')
except:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

content = """
<h1>%s</h1>
"""

def get(useSkeleton, channels):
    output = content
    if len(channels) == 0:
        output %= _('Stats available for no channels')
    elif len(channels) == 1:
        output %= _('Stats available for a channel:')
    elif len(channels):
        output %= _('Stats available for channels:')
    output += '<ul class="chanslist">'
    for channel in channels:
        output += '<li><a href="/global/%s/" title="%s">%s</a></li>' % (
                  channel[1:], # Strip the #
                  _('View the stats for the %s channel') % channel,
                  channel)
    output += '</ul>'
    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
