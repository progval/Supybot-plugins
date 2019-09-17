import re
import os.path

import requests
from pyquery import PyQuery as pq

TARGET_FILE = os.path.join(os.path.dirname(__file__), 'config.py')

html = requests.get('https://developer.github.com/v3/activity/events/types/').content

with open(TARGET_FILE, 'r') as fd:
    old_content = fd.read()

matches = re.finditer('''<a id="webhook-event-name-[0-9]+" class="anchor" href="#webhook-event-name-[0-9]+" aria-hidden="true"><span aria-hidden="true" class="octicon octicon-link"></span></a>Webhook event name</h3>

<p><code>(?P<event_type>[a-z_]*)</code></p>''', html.decode(), flags=re.MULTILINE)

event_types = []
for match in matches:
    event_type = match.group('event_type')
    if "GitHub.format, '%s'" % event_type not in old_content:
        event_types.append(event_type)


s = '\n'.join("    '%s'," % event_type for event_type in event_types)

s = '''# BEGIN AUTOGEN
EVENT_TYPES = (
%s
)
# END AUTOGEN
''' % s

new_content = re.sub(r'# BEGIN AUTOGEN.*\n# END AUTOGEN', s, old_content, flags=re.DOTALL)

with open(TARGET_FILE, 'w') as fd:
    fd.write(new_content)
