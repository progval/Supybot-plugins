###
# Copyright (c) 2011, Valentin Lorentz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import time
import random
import supybot.world as world
from listingcommons import *
from listingcommons import _
import pygraphviz
from cStringIO import StringIO

if not hasattr(world, 'webStatsCacheLinks'):
    world.webStatsCacheLinks = {}

colors = ['green', 'red', 'orange', 'blue', 'black', 'gray50', 'indigo']

def chooseColor(nick):
    global colors
    return random.choice(colors)

def get(useSkeleton, channel, db, urlLevel, page, orderBy=None):
    cache = world.webStatsCacheLinks # The template is often reloaded
    channel = '#' + channel
    items = db.getChanLinks(channel)
    output = ''
    if channel in cache and cache[channel][0] > time.time() - 3600:
        output = cache[channel][1]
    else:
        graph = pygraphviz.AGraph(strict=False, directed=True,
                                  start='regular', smoothing='spring',
                                  size='40') # /!\ Size is in inches /!\
        items = [(x,y,float(z)) for x,y,z in items]
        if not items:
            graph.add_node('No links for the moment.')
            buffer_ = StringIO()
            graph.draw(buffer_, prog='circo', format='png')
            buffer_.seek(0)
            output = buffer_.read()
            return output
        graph.add_node('#root#', style='invisible')
        insertedNicks = {}
        divideBy = max([z for x,y,z in items])/10
        for item in items:
            for i in (0, 1):
                if item[i] not in insertedNicks:
                    try:
                        insertedNicks.update({item[i]: chooseColor(item[i])})
                        graph.add_node(item[i], color=insertedNicks[item[i]],
                                       fontcolor=insertedNicks[item[i]])
                        graph.add_edge(item[i], '#root#', style='invisible',
                                       arrowsize=0, color='white')
                    except: # Probably unicode issue
                        pass
            graph.add_edge(item[0], item[1], arrowhead='vee',
                           color=insertedNicks[item[1]],
                           penwidth=item[2]/divideBy,
                           arrowsize=item[2]/divideBy/2+1)
        buffer_ = StringIO()
        graph.draw(buffer_, prog='circo', format='png')
        buffer_.seek(0)
        output = buffer_.read()
        cache.update({channel: (time.time(), output)})

    #if useSkeleton:
    #    output = ''.join([skeleton.start, output, skeleton.end])
    return output
