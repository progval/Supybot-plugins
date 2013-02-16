###
# Copyright (c) 2013, Valentin Lorentz
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

import ast
import operator
import functools
import collections

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Scheme')

class SchemeException(Exception):
    pass

def eval_argument(arg, env):
    if isinstance(arg, list):
        return eval_scheme(arg, env)
    else:
        return env[arg] if arg in env else ast.literal_eval(arg)

def schemify_math(f):
    # Makes a two-arguments function an *args function, with correct
    # type parsing.
    def rec(args):
        if args[2:]:
            return f(args[0], rec(args[1:]))
        else:
            return f(args[0], args[1])
    def newf(tree, env):
        return rec(map(functools.partial(eval_argument, env=env), tree[1:]))
    return newf

# Add some math operators
DEFAULT_ENV = map(lambda (x,y):(x, schemify_math(y)), (
    ('+', operator.add),
    ('-', operator.sub),
    ('*', operator.mul),
    ('/', operator.div),
    ))
DEFAULT_ENV = dict(DEFAULT_ENV)


def parse_scheme(code, start=0, end=None, tree=[], wrap=False):
    if wrap:
        wrapper = lambda x:[x]
    else:
        wrapper = lambda x:x
    if end is None:
        end = len(code)-1
    while code[end] == ' ':
        end -= 1
    if code[start] == '(' and code[end] == ')':
        return parse_scheme(code, start+1, end-1, tree, True)
    else:
        level = 0
        in_string = False
        escaped = False
        for i in xrange(start, end):
            if code[i] == '"' and not escaped:
                in_string = not in_string
            elif in_string:
                pass
            elif code[i] == '\'':
                escaped = not escaped
            elif code[i] == '(':
                level += 1
            elif code[i] == ')':
                if level == 0:
                    raise SchemeException(_('At index %i, unexcepted `)\'.')
                            % end)
                level -=1
            elif level == 0 and code[i] == ' ' and start != i:
                return wrapper(parse_scheme(code, start, i,
                        parse_scheme(code, i+1, end)))
            else:
                continue # Nothing to do
        if level != 0:
            raise SchemeException(_('Unclosed parenthesis.'))
        c = code[end]
        return [code[start:end] + (c if c!=' ' else '')] + tree

def eval_scheme(tree, env=DEFAULT_ENV):
    return env[tree[0]](tree, env.copy())

@internationalizeDocstring
class Scheme(callbacks.Plugin):
    """Add the help for "@plugin help Scheme" here
    This should describe *how* to use this plugin."""
    threaded = True

    @internationalizeDocstring
    def scheme(self, irc, msg, args, code):
        """<code>

        Evaluates Scheme."""
        try:
            tree = parse_scheme(code)[0]
        except SchemeException as e:
            irc.error('Syntax error: ' + e.args[0])
        try:
            result = eval_scheme(tree)
        except SchemeException as e:
            irc.error('Runtime error: ' + e.args[0])
        irc.reply(result)
    scheme = wrap(scheme, ['text'])

Class = Scheme


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
