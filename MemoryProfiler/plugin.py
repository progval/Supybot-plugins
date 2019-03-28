###
# Copyright (c) 2015, Valentin Lorentz
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

from __future__ import print_function

import gc
import sys
import collections

import supybot.utils as utils
from supybot.commands import *
import supybot.irclib as irclib
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('MemoryProfiler')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from sys import getsizeof, stderr
from itertools import chain
from collections import deque
try:
    from reprlib import repr
except ImportError:
    pass


def list_attrs(obj):
    for attr_name in dir(obj):
        if attr_name.startswith('__'):
            # Magic method, don't touch that
            continue
        if hasattr(type(obj), attr_name):
            # Probably class attribute, skip it
            continue
        yield attr_name
        try:
            yield getattr(obj, attr_name, None)
        except Exception:
            pass

# from https://code.activestate.com/recipes/577504/
def total_size(objects, handlers={}, verbose=False, object_filter=None):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(list(d.items()))
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                    str: None,
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                if handler:
                    try:
                        s += sum(map(sizeof, handler(o)))
                    except RuntimeError:
                        pass
                break
        else:
            if not object_filter or object_filter(o):
                try:
                    s += sum(map(sizeof, list_attrs(o)))
                except RuntimeError:
                    pass
        return s

    return sum(map(sizeof, objects))

class MemoryProfiler(callbacks.Plugin):
    """Collects informations about memory usage."""
    threaded = True

    def plugins(self, irc, msg, args):
        """takes no arguments

        Collects informations about memory usage of plugins and shows it."""
        data = []
        for callback in irc.callbacks:
            module_filter=lambda m:callback.name() in m.__name__.split('.')
            module_handler = lambda m: (list_attrs(m)
                                        if module_filter(m) else [])
            size = total_size([callback], handlers={
                type(sys): module_handler,
                irclib.Irc: None,
                })
            data.append((size, callback.name()))
        data.sort(reverse=True)
        irc.replies([format('%s: %S', x[1], x[0]) for x in data])

    def modules(self, irc, msg, args):
        """takes no arguments

        Collects informations about memory usage of structures defined in each
        module and shows it."""
        module_sizes = collections.defaultdict(lambda: 0)
        gc.collect()
        for obj in gc.get_objects():
            if not hasattr(obj, '__module__'):
                continue
            module = obj.__module__
            module_sizes[module] += total_size([obj],
                    object_filter=lambda o:o is module or
                    (hasattr(o, '__module__') and o.__module__ is module))
        data = []
        for (name, size) in module_sizes.items():
            data.append((size, name))
        data.sort(reverse=True)
        irc.replies([format('%s: %S', x[1], x[0]) for x in data])



Class = MemoryProfiler


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
