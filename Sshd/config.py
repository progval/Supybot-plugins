###
# Copyright (c) 2005, Ali Afshar
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

import supybot.conf as conf
import supybot.registry as registry
import os

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Sshd', True)

# The root configuration group
Sshd = conf.registerPlugin('Sshd')

conf.registerGlobalValue(Sshd, 'capability',
    registry.String('owner',
    """The default capability to connect to the Ssh server and to use the
    Ssh commands."""))

conf.registerGlobalValue(Sshd, 'motd',
    registry.String('Welcome to the Supybot SSH Server',
    """This is the message returned to clients on successful
    authorization."""))

#Group containing key information
conf.registerGroup(Sshd, 'keys')

#Filename information
conf.registerGlobalValue(Sshd.keys, 'rsaPrivateFile',
    registry.String('id_rsa',
	"""Filename of RSA private key file for use with Ssh. Unless a complete
    path is given, the location of the file is assumed to be inside the
    data%sGateway%skeys directory""" % (os.sep, os.sep)))

conf.registerGlobalValue(Sshd.keys, 'rsaPublicFile',
    registry.String('id_rsa.pub',
	"""Filename of RSA public key file for use with Ssh. Unless a complete
    path is given, the location of the file is assumed to be inside the
    data%sGateway%skeys directory""" % (os.sep, os.sep)))

conf.registerGlobalValue(Sshd.keys, 'rsaAuthorizedDir',
    registry.String('authorized_rsa',
	"""Name of the directory containing the authorized RSA public key files
    for use with Ssh. Unless a complete path is given, the location of the
    file is assumed to be inside the data%sGateway%skeys directory""" % \
    (os.sep, os.sep)))

shellGroup = conf.registerGroup(Sshd, 'shell')

conf.registerGlobalValue(shellGroup, 'defaultPort',
    registry.Integer(9022,
    """The port that the Sshd Shell server will start on if started
    automatically, or without port argument."""))

conf.registerGlobalValue(shellGroup, 'autoStart',
    registry.Boolean(True,
    """Determines whether the Sshd Shell server will start automatically when
    the Sshd plugin is loaded."""))

conf.registerGlobalValue(shellGroup, 'capability',
	registry.String('',
	"""Determines what capability users will require to connect to the protocol.
	If this value is an empty string, no capability will be checked."""))

conf.registerGlobalValue(shellGroup, 'ps1',
    registry.String('%(username)s@%(nick)s: @',
	"""The prompt format. Bug me to improve this."""))
    
pyGroup = conf.registerGroup(Sshd, 'pyshell')

conf.registerGlobalValue(pyGroup, 'defaultPort',
    registry.Integer(9044,
    """The port that the Python Shell server will start on if started
    automatically, or without port argument."""))

conf.registerGlobalValue(pyGroup, 'autoStart',
    registry.Boolean(False,
    """Determines whether the Python Shell server will start automatically when
    the Sshd plugin is loaded."""))

conf.registerGlobalValue(pyGroup, 'capability',
	registry.String('owner',
	"""Determines what capability users will require to connect to the
    protocol. If this value is an empty string, no capability will be checked."""))

uiGroup = conf.registerGroup(Sshd, 'ui')

conf.registerGlobalValue(uiGroup, 'defaultPort',
    registry.Integer(9066,
    """The port that the User Interface Shell server will start on if
    started automatically, or without port argument."""))

conf.registerGlobalValue(uiGroup, 'autoStart',
    registry.Boolean(False,
    """Determines whether the User Interface Shell server will start
    automatically when the Sshd plugin is loaded."""))

conf.registerGlobalValue(uiGroup, 'capability',
	registry.String('owner',
	"""Determines what capability users will require to connect to the protocol.
	If this value is an empty string, no capability will be checked."""))

plGroup = conf.registerGroup(Sshd, 'plain')

conf.registerGlobalValue(plGroup, 'defaultPort',
    registry.Integer(9088,
    """The port that the Plain server will start on if started
    automatically, or without port argument."""))

conf.registerGlobalValue(plGroup, 'autoStart',
    registry.Boolean(False,
    """Determines whether the Plain server will start automatically when
    the Sshd plugin is loaded."""))

conf.registerGlobalValue(plGroup, 'capability',
	registry.String('owner',
	"""Determines what capability users will require to connect to the protocol.
	If this value is an empty string, no capability will be checked."""))

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
