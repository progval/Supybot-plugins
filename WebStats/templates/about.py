import skeleton
import supybot.utils as utils
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('WebStats')
except:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

content = _(
"""<p>This website is powered by three awesome softwares :
<ul>
    <li>
        The well-known <a href="http://python.org">Python</a> programming
        language
    </li>
    <li>
        <a href="http://supybot.com">Supybot</a>, the best Python IRC bot in
        existance
    </li>
    <li>
        <a href="mailto:progval@gmail.com">ProgVal</a>'s
        <a href="http://supybot-fr.tk/WebStats">WebStats plugin for Supybot</a>
    </li>
""")

def get(useSkeleton):
    output = content
    if useSkeleton:
        output = ''.join([skeleton.start, output, skeleton.end])
    return output
