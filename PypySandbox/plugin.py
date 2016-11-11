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

import os
import io
import sys
import signal
import tempfile
import subprocess

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PypySandbox')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

if not hasattr(subprocess, 'TimeoutExpired'):
    raise callbacks.Error('Python >= 3.3 is required.')
if not hasattr(tempfile, 'TemporaryDirectory'):
    # You have some weird setup...
    raise callbacks.Error('Python >= 3.2 is required.')

class TimeoutException(Exception):
    pass

SOURCE_PREFIX = """
try:
    """

SOURCE_SUFFIX = """
except Exception as e:
    import sys
    import traceback
    traceback.print_exc(file=sys.stdout)
"""

def run(code, heapsize, timeout):
    with tempfile.TemporaryDirectory() as dirname:
        command = ['pypy-sandbox',
                '--tmp', dirname,
                '--heapsize', str(heapsize),
                '--timeout', str(timeout),
                '/tmp/source.py',
                ]
        source = open(os.path.join(dirname, 'source.py'), 'w+')
        try:
            source.write(SOURCE_PREFIX)
            source.write(code)
            source.write(SOURCE_SUFFIX)
            source.seek(0)
            source.seek(0)
            proc = subprocess.Popen(command,
                    universal_newlines=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    # http://stackoverflow.com/a/4791612/539465
                    preexec_fn=os.setsid,
                    )
            (outs, errs) = proc.communicate(None, timeout=timeout)
            if errs:
                outs += errs
        except subprocess.TimeoutExpired:
            # --timeout is ignored in Debian 8.0, so we have to kill
            # the child process of pypy-sandbox ourselves.
            # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=785559
            os.killpg(proc.pid, signal.SIGTERM)
            proc.kill()
            raise TimeoutException()
        except subprocess.CalledProcessError:
            raise
        finally:
            source.close()
    if outs.startswith("'import site' failed"):
        outs = outs[len("'import site' failed"):]
    outs = outs.strip()
    return outs

class PypySandbox(callbacks.Plugin):
    """Interprets arbitrary Python code from IRC, using Pypy's sandbox."""
    threaded = True
    @wrap(['text'])
    def sandbox(self, irc, msg, args, code):
        """<code>

        Runs Python code safely thanks to Pypy's sandbox."""
        heapsize = self.registryValue('heapsize')
        timeout = self.registryValue('timeout')
        try:
            output = run(code, heapsize, timeout)
        except TimeoutException:
            irc.error(_('Timeout.'))
        else:
            irc.replies(output.split('\n'))


Class = PypySandbox


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
