###
# Copyright (c) 2010-2011, Valentin Lorentz
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

# pysandbox were originally writen by haypo (under the BSD license), 
# and fschfsch by Tila (under the WTFPL license).

###

IN_MAXLEN = 1000 # bytes
OUT_MAXLEN = 1000 # bytes
TIMEOUT = 3  # seconds

EVAL_MAXTIMESECONDS = TIMEOUT
EVAL_MAXMEMORYBYTES = 75 * 1024 * 1024 # 10 MiB

try:
    import sandbox as S
except ImportError:
    print('You need pysandbox in order to run SupySandbox plugin '
          '[http://github.com/haypo/pysandbox].')
    raise
import re
import os
import sys
import time
import random
import select
import signal
import contextlib
import resource as R
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from cStringIO import StringIO

class SandboxError(Exception):
    pass

def createSandboxConfig():
    cfg = S.SandboxConfig(
        'stdout',
        'stderr',
        'regex',
        'unicodedata', # flow wants u'\{ATOM SYMBOL}' :-)
        'future',
        #'code',
        'time',
        'datetime',
        'math',
        'itertools',
        'random',
        'encodings',
    )
    cfg.max_memory = EVAL_MAXMEMORYBYTES
    cfg.timeout = EVAL_MAXTIMESECONDS
    cfg.allowModule('sys',
        'version', 'hexversion', 'version_info')
    return cfg

evalPythonInSandbox = r"""
try:
    if "\n" in line:
        raise SyntaxError()
    code = compile(line, "<irc>", "single")
except SyntaxError:
    code = compile(line, "<irc>", "exec")
exec code in namespace, namespace
del code
del namespace
"""

def evalPython(line, locals=None):
    try:
        config = createSandboxConfig()
        sandbox = S.Sandbox(config=config)

        if locals is None:
            locals = {}
        sandbox.execute(
            evalPythonInSandbox,
            locals={'namespace': locals, 'line': line})
    except BaseException as  e:
        print('Error: [%s] %s' % (e.__class__.__name__, str(e)))
    except:
        print('Error: <unknown exception>')
    sys.stdout.flush()

@contextlib.contextmanager
def capture_stdout():
    import sys
    import tempfile
    stdout_fd = sys.stdout.fileno()
    with tempfile.TemporaryFile(mode='w+b') as tmp:
        stdout_copy = os.dup(stdout_fd)
        try:
            os.dup2(tmp.fileno(), stdout_fd)
            yield tmp
        finally:
            os.dup2(stdout_copy, stdout_fd)
            os.close(stdout_copy)

def evalLine(line, locals):
    with capture_stdout() as stdout:
        evalPython(line, locals)
        stdout.seek(0)
        txt = stdout.read()

    print("Output: %r" % txt)

    txts = txt.rstrip().split('\n')
    if len(txts) > 1:
        txt = txts[0].rstrip() + ' [+ %d line(s)]' % (len(txts) - 1)
    else:
        txt = txts[0].rstrip()
    return 'Output: ' + txt

def handle_line(line):
    if IN_MAXLEN < len(line):
        return '(command is too long: %s bytes, the maximum is %s)' % (len(line), IN_MAXLEN)

    print("Process %s" % repr(line))
    result = evalLine(line, {})
    print("=> %s" % repr(result))
    return result

class SupySandbox(callbacks.Plugin):
    """Add the help for "@plugin help SupySandbox" here
    This should describe *how* to use this plugin."""

    _parser = re.compile(r'(.*sandbox)? (?P<code>.*)')
    _parser = re.compile(r'(.?sandbox)? (?P<code>.*)')
    def sandbox(self, irc, msg, args, code):
        """<code>
        
        Runs Python code safely thanks to pysandbox"""
        try:
            irc.reply(handle_line(code.replace(' $$ ', '\n')))
        except SandboxError as  e:
            irc.error('; '.join(e.args))
    sandbox = wrap(sandbox, ['text'])
        
    def runtests(self, irc, msg, args):
        irc.reply(runTests())


Class = SupySandbox


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
