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
import copy
import operator
import fractions
import functools
import collections

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Scheme')

NUMBER_TYPES = (
        ('integer', int),
        ('rational', fractions.Fraction),
        ('real', float),
        ('complex', complex),
        ('number', str),
        )

class SchemeException(Exception):
    pass

def no_edge_effect(f):
    def newf(tree, env):
        return f(tree, env.copy())
    return newf

def eval_argument(arg, env):
    if isinstance(arg, list):
        return eval_scheme(arg, env)
    elif isinstance(arg, str):
        if arg in env:
            return eval_argument(env[arg], {})
        else:
            for name, parser in NUMBER_TYPES:
                try:
                    return parser(arg)
                except ValueError:
                    pass
            # You shall not pass
            raise SchemeException(_('Unbound variable: %s') % arg)
    else:
        return arg

def py2scheme(tree):
    if isinstance(tree, list):
        return '(%s)' % (' '.join(map(py2scheme, tree)))
    else:
        return str(tree)

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
    newf.__name__ = 'schemified_%s' % f.__name__
    return newf

ARGUMENTS_ERROR = _('%s takes %s %i arguments not %i (in (%s))')
@no_edge_effect
def scm_lambda(tree, env):
    try:
        self, args, expr = tree
    except ValueError:
        raise SchemeException(ARGUMENTS_ERROR %
            ('lambda', _('exactly'), 2, len(tree)-1, py2scheme(tree)))
    if not isinstance(args, list):
        args = ['.', args]
    try:
        if args.index('.') != len(args)-2:
            raise SchemeException(_('Invalid arguments list: %s') %
                py2scheme(args))
        rest = args[-1]
        args = args[0:-2]
    except ValueError: # No rest
        rest = None
    @no_edge_effect
    def f(tree2, env2):
        self2, args2 = tree2[0], tree2[1:]
        arguments_error = ARGUMENTS_ERROR % \
                    (self2, '%s', len(args), len(args2), tree2)
        env3 = env2.copy()
        if len(args2) < len(args):
            raise SchemeException(arguments_error %
                _('at least') if rest else _('exactly'))
        elif not rest and len(args2) > len(args):
            raise SchemeException(arguments_error % _('exactly'))
        else:
            env3.update(dict(zip(args, args2)))
            if rest:
                env3.update({rest: args2[len(args):]})
        return eval_scheme(expr, env3)
    f.__name__ = 'scheme_%s' % py2scheme(tree)
    return f

def scm_begin(tree, env):
    for arg in tree[1:-1]:
        eval_scheme(arg)
    return eval_scheme(tree[-1])

def scm_set(tree, env):
    try:
        self, name, value = tree
    except ValueError:
        raise SchemeException(ARGUMENTS_ERROR %
            ('set!', _('exactly'), 2, len(tree)-1, py2scheme(tree)))
    env[name] = value

DEFAULT_ENV = [
    ('lambda', scm_lambda),
    ('begin', scm_begin),
    ('set!', scm_set),
    ]
# Add some math operators
DEFAULT_ENV += map(lambda x:(x[0], schemify_math(x[1])), (
    ('+', operator.add),
    ('-', operator.sub),
    ('*', operator.mul),
    ('/', operator.truediv),
    ))

DEFAULT_ENV = dict(DEFAULT_ENV)


def parse_scheme(code, start=0, end=None, unpack=False):
    if end is None:
        end = len(code)-1
    while code[start] == ' ':
        start += 1
    while code[end] == ' ':
        end -= 1
    if code[start] == '(' and code[end] == ')':
        return parse_scheme(code, start+1, end-1, unpack=False)
    level = 0
    in_string = False
    escaped = False
    tokens = []
    token_start = start
    for i in xrange(start, end+1):
        if code[i] == '"' and not escaped:
            in_string = not in_string
        elif in_string:
            pass
        elif code[i] == '\'':
            escaped = not escaped
        elif code[i] == '(':
            level += 1
        elif code[i] == ')':
            level -=1
            if level == -1:
                raise SchemeException(_('At index %i, unexpected `)\' near %s')
                        % (end, code[max(0, end-10):end+10]))
            elif level == 0:
                tokens.append(parse_scheme(code, token_start, i))
                token_start = i+1
        elif level == 0 and code[i] == ' ' and token_start != i:
            tokens.append(parse_scheme(code, token_start, i))
            token_start = i+1
        else:
            continue # Nothing to do
    if level != 0:
        raise SchemeException(_('Unclosed parenthesis in: %s') %
                code[start:end+1])
    if start == token_start:
        return code[start:end+1]
    elif start < end:
        tokens.append(parse_scheme(code, token_start, end))
    tokens = filter(bool, tokens)
    if unpack:
        assert len(tokens) == 1, tokens
        tokens = tokens[0]
    return tokens

def eval_scheme(tree, env=DEFAULT_ENV):
    if isinstance(tree, str):
        if tree in env:
            return env[tree]
        else:
            print(repr(env))
            raise SchemeException(_('Undefined keyword %s.') % tree)
    first = eval_scheme(tree[0])
    if callable(first):
        return first(tree, env)
    else:
        return tree

def eval_scheme_result(tree):
    if isinstance(tree, list):
        return '(%s)' % ' '.join(map(eval_scheme_result, tree))
    else:
        return str(eval_argument(tree, []))

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
            tree = parse_scheme(code)
        except SchemeException as e:
            irc.error('Syntax error: ' + e.args[0], Raise=True)
        try:
            result = eval_scheme(tree)
        except SchemeException as e:
            irc.error('Runtime error: ' + e.args[0], Raise=True)
        irc.reply(eval_scheme_result(result))
    scheme = wrap(scheme, ['text'])

Class = Scheme


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
