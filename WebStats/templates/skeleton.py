import time
from WebStats.plugin import _

start = \
"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" >
    <head>
        <title>Supybot WebStats</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <link rel="stylesheet" media="screen" type="text/css" title="Design" href="/webstats/design.css" />
    </head>
    <body>
        <p id="header">
            WebStats
        </p>
        <ul id="menu">
            <li><a href="/webstats/" title="%s">%s</a></li>
            <li><a href="/webstats/%s/" title="%s">%s</a></li>
        </ul>
""" % (_('Come back to the root page'), _('Home'),
       _('about'), _('Get more informations about this website'), _('About'))

end = \
"""
        <p id="footer">
            <a href="http://supybot.com">Supybot</a> and
            <a href="https://github.com/ProgVal/Supybot-plugins/tree/master/WebStats/">WebStats</a> powered.<br />
            Libre software available under BSD licence.<br />
            Page generated at %s.
        </p>
    </body>
</html>""" % (time.strftime('%H:%M:%S'))
