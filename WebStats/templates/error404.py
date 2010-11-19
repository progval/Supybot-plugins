import skeleton

content = \
"""
<p>
    Requested page is not found. Sorry.
</p>
"""

content = '%s%s%s' % (skeleton.start, content, skeleton.end)

print 'toto'

def get():
    global content
    return content
