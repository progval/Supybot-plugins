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

from listingcommons import *
from listingcommons import _
import pygraphviz
from cStringIO import StringIO

def get(useSkeleton, channel, db, urlLevel, page, orderBy=None):
    channel = '#' + channel
    items = db.getChanLinks(channel)
    output = ''
    graph = pygraphviz.AGraph(strict=False, directed=True)
    insertedNicks = []
    for item in items:
        if item[0] not in insertedNicks:
            try:
                graph.add_node(item[0])
                insertedNicks.append(item[0])
            except: # Probably unicode issue
                pass
        for foo in range(0, int(item[2])):
            try:
                graph.add_edge(item[0], item[1])
            except:
                pass
    buffer_ = StringIO()
    graph.draw(buffer_, prog='circo', format='png')
    buffer_.seek(0)
    output = buffer_.read()

    #if useSkeleton:
    #    output = ''.join([skeleton.start, output, skeleton.end])
    return output
