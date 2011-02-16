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
    print 'You need pysandbox in order to run SupySandbox plugin ' + \
          '[http://github.com/haypo/pysandbox].'
    raise
import re
import os
import sys
import time
import random
import select
import signal
import resource as R
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from cStringIO import StringIO


class SandboxError(Exception):
    pass

class SandboxInterface(object):
    """This is the base class for interfaces between parent and child."""
    def __init__(self, pipes):
        self._read, self._write = pipes
        self._send('print', 'kikoo')
    def _send(self, command, data):
        assert ' ' not in command
        assert ':' not in command
        os.write(self._write, '%s:%s\n' % (command, data))
    def _get(self):
        lines = []
        rawData = ''
        newData = 'foo'
        while newData != '':
            newData = os.read(self._read, 256)
            rawData += newData
        for line in rawData.split('\n'):
            if line == '':
                continue
            lines.append(line.split(':', 1))
        return lines

class ChildSide(SandboxInterface):
    def __init__(self, pipes):
        super(ChildSide, self).__init__(pipes)
        sys.stdout = sys.stderr = self
    def write(self, data):
        self._send('print', data)
    def flush(self):
        pass
class ParentSide(SandboxInterface):
    def daemon(self):
        """Code that needs to be runned while the child is running"""
        printed = ''
        for command, data in self._get():
            if command == 'print':
                printed += data
        return printed


def createSandboxConfig():
    cfg = S.SandboxConfig(
        'stdout',
        'stderr',
        'regex',
        'unicodedata', # flow wants u'\{ATOM SYMBOL}' :-)
        'future',
        'code',
        'time',
        'datetime',
        'math',
        'itertools',
        'random',
        'encodings',
    )
    cfg.allowModule('sys',
        'version', 'hexversion', 'version_info')
    return cfg

def _evalPython(line, pipes, locals):
    interface = ChildSide(pipes)
    locals_ = dict(locals)
    locals_.update({'interface': interface})
    try:
        if "\n" in line:
            raise SyntaxError()
        code = compile(line, "<irc>", "single")
    except SyntaxError:
        code = compile(line, "<irc>", "exec")
    exec code in locals_

def evalPython(line, pipes, locals=None):
    sandbox = S.Sandbox(config=createSandboxConfig())

    if locals is not None:
        locals = dict(locals)
    else:
        locals = dict()
    try:
        sandbox.call(_evalPython, line, pipes, locals)
    except BaseException, e:
        print 'Error: [%s] %s' % (e.__class__.__name__, str(e))
    except:
        print 'Error: <unknown exception>'
    sys.stdout.flush()

def childProcess(line, pipes, locals):
    # reseed after a fork to avoid generating the same sequence for each child
    random.seed()


    R.setrlimit(R.RLIMIT_CPU, (EVAL_MAXTIMESECONDS, EVAL_MAXTIMESECONDS))
    R.setrlimit(R.RLIMIT_AS, (EVAL_MAXMEMORYBYTES, EVAL_MAXMEMORYBYTES))
    R.setrlimit(R.RLIMIT_NPROC, (0, 0)) # 0 forks

    evalPython(line, pipes, locals)

def handleChild(childpid, pipes):
    txt = ''
    n = 0
    interface = ParentSide(pipes)
    while n < 20:
        pid, status = os.waitpid(childpid, os.WNOHANG)
        if pid:
            break
        time.sleep(.1)
        n += 1
        txt += interface.daemon()
    if not pid:
        os.kill(childpid, signal.SIGKILL)
        raise SandboxError('Timeout')
    elif os.WIFEXITED(status):
        return txt.rstrip()
    elif os.WIFSIGNALED(status):
        raise SandboxError('Killed')

def handle_line(line):
    childToParent = os.pipe()
    parentToChild = os.pipe()
    child = (childToParent[0], parentToChild[1])
    parent = (parentToChild[0], childToParent[1])
    del childToParent, parentToChild
    childpid = os.fork()
    if not childpid:
        pipes = child
        os.close(parent[0])
        os.close(parent[1])
        childProcess(line, pipes, {})
        os._exit(0)
    else:
        pipes = parent
        os.close(child[0])
        os.close(child[1])
        result = handleChild(childpid, pipes)
        return result

class SupySandbox(callbacks.Plugin):
    """Add the help for "@plugin help SupySandbox" here
    This should describe *how* to use this plugin."""

    _parser = re.compile(r'(.?sandbox)? (?P<code>.*)')
    def sandbox(self, irc, msg, args):
        """<code>

        Runs Python code safely thanks to pysandbox"""
        code = self._parser.match(msg.args[1]).group('code')
        try:
            irc.reply(handle_line(code.replace(' $$ ', '\n')))
        except SandboxError, e:
            irc.error('; '.join(e.args))

Class = SupySandbox


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
