import skeleton

content = \
"""
<p>
    Requested page is not found. Sorry.
</p>
"""

def get(useSkeleton=True):
    global content
    if useSkeleton:
        content = '%s%s%s' % (skeleton.start, content, skeleton.end)
    return content
