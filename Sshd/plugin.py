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

#TODO:
# key gen
# pretty logging from within plugin
#docstrings

# Supybot imports
import supybot.log as log
import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.schedule as schedule
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.registry as registry
import supybot.callbacks as callbacks

# Twisted imports
import twisted.cred.error as error
import twisted.cred.portal as portal
# twisted-conch is often a separate package
import twisted.conch.avatar as avatar
import twisted.conch.ssh.keys as keys
import twisted.internet.defer as defer
import twisted.internet.error as terror
import twisted.cred.checkers as checkers
import twisted.python.failure as failure
import twisted.conch.ssh.common as common
import twisted.internet.reactor as reactor
import twisted.conch.ssh.channel as channel
import twisted.conch.ssh.factory as factory
import twisted.conch.ssh.session as session
import twisted.internet.protocol as protocol
import twisted.conch.ssh.userauth as userauth
import twisted.conch.checkers as conchcheckers
import twisted.cred.credentials as credentials
import twisted.conch.ssh.connection as connection

# Standard library imports
import os
import md5
import sys
import code
import time
import base64
import binascii

# Only needed if you want to generate keys.
try:
    import Crypto.PublicKey.RSA as RSA
except ImportError:
    RSA = None

DATAROOT = conf.supybot.directories.data.dirize('Sshd')

## Twisted Logs
# These components allow debugging Twisted to Supybot's logs.
#
# ** This should be commented out
# If things are appearing not to work, it may be useful to uncomment it.
##

#from twisted.python import log as tlog
#
#class TwistedSupyLog(object):
#
#    def write(self, data):
#        log.debug(data)
#
#    def flush(self):
#        pass
#
#    def close(self):
#        pass
#
#        
#tlog.startLogging(TwistedSupyLog())

## Converters
#
# Check specific capability to connect to the Sshd
def sshdCapable(irc, msg, args, state):
    """Converter to check that the command was issued from an Sshd capable user.

    It checks the user's capability against the value from the registry. On
    failure a No Capability error is raised.
    """
    capability = state.cb.registryValue('capability')
    if not ircdb.checkCapability(msg.prefix, capability):
        irc.errorNoCapability(capability, Raise=True)

# Converter to check source.
def sshdSource(irc, msg, args, state):
    con = msg.fromSshd
    if con:
        state.args.append(con)
    else:
        irc.error('This command may only be called from Sshd connections',
                    Raise = True)

# Add the converters
addConverter('sshdSource', sshdSource)
addConverter('sshdCapable', sshdCapable)

## The Plugin
class Sshd(callbacks.Plugin):
    """
    The Sshd plugin provides methods of connecting to Supybot using the SSH
    protocol with standard SSH clients such as OpenSSH.

    If you are the owner of this bot, please read the associated README.txt
   
    @version: 0.2.0

    @author: Ali Afshar U{mailto:aafshar@gmail.com}
    """
    def __init__(self, irc):
        callbacks.Privmsg.__init__(self, irc)
        self.available = {}
        self.datapaths = {}
        self.irc = irc
        try:
            self._createDirectories()
            self._importProtocols()
            self._autoStart()
        except Exception as e:
            import traceback
            traceback.print_exc(e)
        self.loggers = []

        
        def hel(self, irc, msg, args):
            irc.reply('hello %s %s' % (dir(self), self.cbs))
        hel = wrap(hel, [])

        def doPrivmsg(self, irc, msg):
            self.log.critical('privmasg')

    def outFilter(self, irc, msg):
        """Filter and redirect messages leaving the bot for Sshd replies.

        Checks all messages leaving the bot as to whether they are replies
        to messages sent via Sshd. It performs this by checking for the
        presence of:
            1. the inReplyTo tag (a Message object)
            2. the inReplyTo's fromSshd tag (an SshUser object)
        
        If both tags are present, it uses the B{fromSshd} tag (which is an
        instance of the SshUser class or subclass) to direct the reply to
        that user's connection.

        @return: Will return the passed in Message object if the Message
        is not a reply to an Sshd message. Otherwise will return None. The
        returning of None will be logged at DEBUG log level.
        """
        if msg.inReplyTo:
            if msg.inReplyTo.fromSshd:
                con = msg.inReplyTo.fromSshd
                con.sendReply(msg.args[1],
                    inreply=msg.inReplyTo.args[1],
                    source='outfilter',
                    msg=msg)
                return None
            else:
                return msg
        else:
            return msg
    
    def die(self):
        """Called on unload, or reload. Shut down all the servers."""
        for p in self.available:
            self.available[p].stop()
       
    def getPluginHelp(self):
        return """The Sshd plugin provides methods of connecting to Supybot using the SSH
                    protocol with standard SSH clients such as OpenSSH."""

    def logout(self, irc, msg, args, con):
        """takes no arguments

        Log out of a Sshd session. May only be called from Sshd, not Irc.
        """
        con.sendReply('logging out', source='status', inreply='logout')
        con.close()
    logout = wrap(logout, ['sshdSource'])
    
    def wall(self, irc, msg, args, opts, text):
        """[--user username] <text>

        Say <text> to all users connected to the Sshd. If the
        optional [--user] argument is given, it should be a registered user
        name and will specify a single user that the message will be sent
        to.
        """
        targets = []
        if len(opts):
            for t in opts:
                if t[0] == 'user':
                    targets.append(t[1])
                    break
        nick = self._getMsgNick(msg)
        found = False
        for p in self.available:
            pr = self.available[p]
            if pr.port:
                for c in pr.connections:
                    if len(targets):
                        if c.user in targets:
                            c.sendReply(text, inreply=nick, source='wall')
                            found = True
                    else:
                        c.sendReply(text, inreply=nick, source='wall')
                        found = True
        if found:
            irc.replySuccess()
        else:
            irc.reply('User not found')
    wall = wrap(wall, ['sshdCapable', getopts({'user': 'otherUser'}), 'text'])
    
    def protocols(self, irc, msg, args):
        """takes no arguments

        Displays a list of available protocols.
        """
        L = [s.NAME for s in self.available.values()]
        irc.reply(format('%L', L))
    available = wrap(protocols, ['sshdCapable'])

    def running(self, irc, msg, args):
        """takes no arguments

        Returns a list of running server, and the ports they are
        listening on.
        """
        L = ['%s on %s' % (s.NAME,
                    s.port) for s in self.available.values() if s.port]
        if len(L):
            irc.reply(format('%L', L))
        else:
            irc.reply(format('%s', 'There are no running gateways.'))
    running = wrap(running, ['sshdCapable'])
        
    def start(self, irc, msg, args, protocol, port):
        """<protocol> [port]

        Start the server named by <protocol>. If the optional [port]
        parameter is provided, the server is started listening on that port.
        Otherwise the autoStart registry value for that protocol is used.
        """
        # needs changing
        p = protocol
        if p in self.available:
            if not self.available[p].port:
                if not port:
                    port = \
                    self.registryValue('%s.defaultPort' % p)
                self.available[p].start(port)
                irc.replySuccess()
            else:
                irc.reply('Error: Already running')
    start = wrap(start, ['owner', 'something', optional('int')])

    def stop(self, irc, msg, args, protocol):
        """<protocol>

        Stop the server named by <protocol>.
        """
        for p in self.available:
            if p == protocol:
                self.available[p].stop()
                irc.replySuccess()
    stop = wrap(stop, ['owner', 'something'])

    def users(self, irc, msg, args):
        """
        takes no arguments

        Returns a list of users connected via the Sshd plugin.
        """
        rl = []
        for p in self.available:
            pr = self.available[p]
            #running servers have the port attribute set
            if pr.port:
                nc = len(pr.connections)
                hml = []
                for i in pr.connections:
                    hml.append(i.user.name)
                if nc:
                    rl.append('%s %s (%s)' % (p, nc, format('%L', hml)))
        if len(rl):
            irc.reply(format('Users connected to the gateway: %L.', rl))
        else:
            irc.reply('There are no users connected to the gateway.')
    users = wrap(users, ['sshdCapable'])
   
    def receivedCommand(self, cmd, con):
        """Handle a single command by creating a custom Message and feeding it
        to the irc object.
        
        @param command: The command received from Ssh.
        @type command: str
        
        @param user: The user object which will be tagged and used to reply.
        @type user: SshUser"""
        cmd = cmd.strip()
        self.log.debug('Received command %s from %s.',
                        cmd,
                        con.hostmask)
        to = self.getNick()
        m =  ircmsgs.privmsg(self.getNick(), cmd, con.hostmask)
        # tag it with the connection so we can pick up the reply
        m.tag('fromSshd', con)
        # feed the message
        world.ircs[0].feedMsg(m)

    def getUser(self, **kw):
        """ will return a user object tagged with a hostmask for use or False
        """
        if 'protocol' not in kw:
            raise KeyError, 'Need a protocol name'
        else:
            user = None
            if 'username' not in kw:
                raise KeyError, 'Need a username'
            try:
                user = ircdb.users.getUser(kw['username'])
            except KeyError:
                self.log.debug('Denying %s. Unregistered user.', kw['username'])
                return False
            cap = self.registryValue('capability')
            pcap = self.registryValue('%s.capability' % kw['protocol'])
            if cap:
                if not ircdb.checkCapability(kw['username'], cap):
                    self.log.debug('Denying %s. Uncapable user.', kw['username'])
                    return False
            if pcap:
                if not ircdb.checkCapability(kw['username'], pcap):
                    self.log.debug('Denying %s. Uncapable protocol for user.', kw['username'])
                    return False
            if 'password' in kw:
                if not user.checkPassword(kw['password']):
                    self.log.debug('Denying %s. Bad password.', kw['username'])
                    return False
            elif 'blob' in kw:
                if not self._checkKey(kw['username'], kw['blob']):
                    self.log.debug('Denying %s. Bad key.', kw['username'])
                    return False
            else:
                return False
            user.gwhm = self._buildHostmask(kw['username'], kw['protocol'],
                    kw['peer'])
            user.addAuth(user.gwhm)
            return user
    
    def getNick(self):
        """Return any (the first) bot nick it can."""
        return world.ircs[0].nick
           
    def _checkKey(self, un, blob):
        self.debug('Checking key for %s.' % un)
        keypath = '%s%s%s' % \
            (self.datapaths['authorized'],
                os.sep, un)
        if not os.access(keypath, os.F_OK):
            return False
        else:
            f = open(keypath)
            for line in f:
                l = line.split()
                if len(l) > 2:
                    try:
                        if base64.decodestring(l[1]) == blob:
                            return True
                    except binascii.Error:
                        pass
            return False
           
    def _buildHostmask(self, un, protocol, peer):
        """ build a new partly random hostmask and return it """
        return '%s%s!%s@%s' % (protocol, utils.mktemp()[:9], un, peer)
          
    def _createDirectories(self):
        #TODO make this registry
        self.datapaths['root'] = DATAROOT
        self._createIfNotExistingDir(self.datapaths['root'])
        self.datapaths['keys'] = '%s%s%s' % (self.datapaths['root'], os.sep, 'keys')
        self._createIfNotExistingDir(self.datapaths['keys'])
        self.datapaths['authorized'] = '%s%s%s' % (self.datapaths['keys'], os.sep,
                            self.registryValue('keys.rsaAuthorizedDir'))
        self._createIfNotExistingDir(self.datapaths['authorized'])

    def _createIfNotExistingDir(self, path):
        if not os.access(path, os.F_OK):
            os.mkdir(path)
    
    def _getMsgNick(self, msg):
        con = msg.fromGateway
        nick = ''
        if con:
            nick = con.user.name
        else:
            nick = msg.nick
        return nick

    def _importProtocols(self):
        for c in [SshServer, PyServer, UiServer, PlainServer]:
            s = c.NAME
            self.available[s] = c(self)
    
    def _autoStart(self):
        for p in self.available:
            if self.registryValue('%s.autoStart' % p):
                port = self.registryValue('%s.defaultPort' % p)
                self.available[p].start(port)

    debug = lambda self, s, *args: self.log.debug('Sshd: [Plugin] %s' % s, *args)

class SupybotPortal(portal.Portal):
    def __init__(self, realm):
        portal.Portal.__init__(self, realm)
        realm.setCallbacks(self)
        pwc = self.PasswordChecker()
        pkc = self.PublicKeyChecker()
        for c in [pwc, pkc]:
            self.setCallbacks(c)
            self.registerChecker(c)
        self.debug('Portal initialised.')

    def login(self, c, mind, userclass):
        self.debug('Authenticating user %s with %s credentials',
            c.username, c.__class__.__name__)
        return portal.Portal.login(self, c, mind, userclass)
        

    class PasswordChecker(object):
        """ SSH Username and Password Credential checker """
        # this implements line tells the portal that we can handle un/pw
        __implements__ = (checkers.ICredentialsChecker,)
        credentialInterfaces = (credentials.IUsernamePassword,)

        def requestAvatarId(self, cr):
            self.cbPlugin.log.debug('twisted checker checking %s',
            cr.username)
            """ Return an avatar id or return an error """
            a = self.cbPlugin.getUser(protocol=self.cbServer.NAME,
                username=cr.username,
                password=cr.password,
                peer=cr.peer)
            if a:
                return a
            else:
                return failure.Failure(error.UnauthorizedLogin())

    class PublicKeyChecker(object):
        """ Public key checker """
        __implements__ = (checkers.ICredentialsChecker,)
        credentialInterfaces = (credentials.ISSHPrivateKey,)

        def requestAvatarId(self, cr):
            a = self.cbPlugin.getUser(protocol=self.cbServer.NAME,
                            username=cr.username,
                            blob=cr.blob,
                            peer=cr.peer)
            
            if a:
                return a
            else:
                return failure.Failure(error.UnauthorizedLogin())

class SshAuthServer(userauth.SSHUserAuthServer):
    def auth_password(self, packet):
        password = userauth.getNS(packet[1:])[0]
        c = userauth.credentials.UsernamePassword(self.user, password)
        return self.auth_all(c, packet)

    def auth_publickey(self, packet):
        NS = userauth.NS
        hasSig = ord(packet[0])
        algName, blob, rest = userauth.getNS(packet[1:], 2)
        pubKey = userauth.keys.getPublicKeyObject(data = blob)
        b = NS(self.transport.sessionID) + chr(userauth.MSG_USERAUTH_REQUEST) + \
            NS(self.user) + NS(self.nextService) + NS('publickey') + \
            chr(hasSig) +  NS(keys.objectType(pubKey)) + NS(blob)
        signature = hasSig and userauth.getNS(rest)[0] or None
        c = userauth.credentials.SSHPrivateKey(self.user, blob, b, signature)
        return self.auth_all(c, packet)
    
    def auth_all(self, c, packet):
        #hack for fbsd twisted version
        try:
            c.peer = self.transport.transport.getPeer().host
        except:
            c.peer = self.transport.transport.getPeer()[0]
            
        return self.portal.login(c, None, self.User).addErrback(
                                                    self._ebCheckKey,
                                                    packet[1:])
              
class SshServerFactory(factory.SSHFactory):
    services = {
        'ssh-userauth': None,
        'ssh-connection': connection.SSHConnection
    }

    def startFactory(self):
        # disable coredumps
        if factory.resource:
            factory.resource.setrlimit(factory.resource.RLIMIT_CORE, (0,0))
        else:
            self.cb.log.debug('SSH: INSECURE: unable to disable core dumps.')
        if not hasattr(self,'publicKeys'):
            self.publicKeys = self.getPublicKeys()
        if not hasattr(self,'privateKeys'):
            self.privateKeys = self.getPrivateKeys()
        if not self.publicKeys or not self.privateKeys:
            raise error.ConchError('no host keys, failing')
        if not hasattr(self,'primes'):
            self.primes = self.getPrimes()
            #if not self.primes:
            #    log.msg('disabling diffie-hellman-group-exchange because we cannot find moduli file')
            #    transport.SSHServerTransport.supportedKeyExchanges.remove('diffie-hellman-group-exchange-sha1')
            if self.primes:
                self.primesKeys = self.primes.keys()

    def getDHPrime(self, bits):
        """
        Return a tuple of (g, p) for a Diffe-Hellman process, with p being as
        close to bits bits as possible.

        @type bits: C{int}
        @rtype:     C{tuple}
        """
        self.primesKeys.sort(lambda x,y,b=bits:cmp(abs(x-b), abs(x-b)))
        realBits = self.primesKeys[0]
        return random.choice(self.primes[realBits])
   
    def buildProtocol(self, addr):
        t = factory.transport.SSHServerTransport()
        t.supportedPublicKeys = self.privateKeys.keys()
        if not self.primes:
            ske = t.supportedKeyExchanges[:]
            ske.remove('diffie-hellman-group-exchange-sha1')
            t.supportedKeyExchanges = ske
        t.factory = self
        return t

class SshProtocolWrapper(object):
    """ class representing each connected SSH client """
    def __init__(self, avatar):
        # the point at which we stop calling it an avatar and start
        # calling it a user
        self.shell = None
        self.user = avatar
        self.user.setCallbacks(self)

    def getPty(self, term, windowSize, attrs):
        self.initialWindowSize = windowSize

    def windowChanged(self, windowSize):
        self.shell.updateSize(*windowSize[:2])

    def closed(self):
        self.debug('closed')
        #self.shell.loseConnection()
    
    def execCommand(self, proto, cmd):
        pass
    
    def openShell(self, trans):
        """ called back on a successful connection """
        if self.shell:
            return
        shellProtocol = self.Protocol(self.user)
        self.setCallbacks(shellProtocol)
        self.shell = shellProtocol
        self.windowChanged(self.initialWindowSize)
        shellProtocol.makeConnection(trans)
        trans.makeConnection(session.wrapProtocol(shellProtocol))

class SshSession(session.SSHSession):
    name = 'session'
    def __init__(self, *args, **kw):
        channel.SSHChannel.__init__(self, *args, **kw)
        self.buf = ''
        self.session = self.ProtocolWrapper(self.avatar)

class SshRealm(object):
    __implements__ = portal.IRealm
    
    def __init__(self, userClass):
        self.User = userClass
            
    def requestAvatar(self, avatarId, mind, *interfaces):
        self.debug('Requesting avatar type %s for %s', self.User,
            avatarId.gwhm)
        av = self.User(avatarId)
        self.setCallbacks(av)
        return interfaces[0], av, lambda: None

class SshProtocol(protocol.Protocol):
    def __init__(self, user):
        self.user = user
        user.con = self
        self.lineBuf = []
        self.oncloseCallbacks = []
        self.doBeforeConnect()

    def doBeforeConnect(self):
        pass
        
    def connectionMade(self):
        self.cbServer.authorised(self.user)
        
    def receivedLine(self):
        line = ''.join(self.lineBuf)
        self.receivedCommand(line)
        self.lineBuf = []
        return line
    
    def connectionLost(self, reason):
        """ Called on loss of connection. """
        #if self.user in self.cbServer.connections:
        self.debug('Connection lost. Reason: %s', reason.getTraceback())

    def loseConnection(self):
        self._loseConnection()
    
    def _loseConnection(self):
        self.user.conn.transport.transport.loseConnection()
        self.user.user.clearAuth()
        try:
            self.cbServer.connections.remove(self.user)
        except ValueError:
            self.debug('Connection already removed. Somehow!')

    def dataReceived(self, data):
        for c in data:
            if c == chr(13):
                self.receivedLine()
            else:
                self.lineBuf.append(c)
    
    def receivedCommand(self, cmd):
        """ receives a line, and returns a prompt """
        self.debug('Received command %s from %s',
            cmd, self.user.hostmask)
        self.cbPlugin.receivedCommand(cmd, self.user)

    def updateSize(self, y, x):
        pass

    def write(self, data):
        reactor.callLater(0, self.transport.write, data)
        
    def writeReply(self, reply, **kw):
        assert('source' in kw)
        if kw['source'] != 'status':
            self.write(reply)

class ShellProtocol(SshProtocol):
    S_DATA = 0
    S_ESCAPED = 1
    S_BRACEKETED = 2
    S_TILDED = 3

    def doBeforeConnect(self):
        self.linePos = 0
        self.insertMode = True
        self.state = self.S_DATA
        self.term = SshTerminal(self)
        self.hist = SshHistory(self)

    def characterReceived(self, c):
        if self.state == self.S_DATA:
            self.receivedDataChar(c)
        elif self.state == self.S_ESCAPED:
            if c == chr(91):
                self.state = self.S_BRACEKETED
            else:
                self.receivedShortEscapeChar(c)
                self.state = self.S_DATA
           
        elif self.state == self.S_BRACEKETED:
            if ord(c) in [50, 51, 52, 53]:
                self.state = self.S_TILDED
                self.tild = c
            else:
                self.receivedEscapeChar(c)
                self.state = self.S_DATA
        
        elif self.state == self.S_TILDED:
            self.receivedTildEscapeChar(self.tild)
            self.state = self.S_DATA
        else:
            self.debug('Somehow %s is in an illegal state.', self)
            self.state = self.S_DATA


    def dataReceived(self, data):
        for c in data:
            self.characterReceived(c)
            
    def receivedCommand(self, cmd):
        SshProtocol.receivedCommand(self, cmd)
        self.writeNewline()
        if len(cmd):
            self.hist.append(cmd)

    def ps1(self):
        fs = '%s ' % self.cbPlugin.registryValue('shell.ps1')
        return fs % {'username': self.user.user.name,
                    'nick': self.cbPlugin.getNick()}

    def receivedDataChar(self, c):
        fname = 'character_%s' % ord(c)
        if hasattr(self, fname):
            getattr(self, fname)()
        elif ord(c) > 31:
            self.receivedPrintableChar(c)
        else:
            self.debug('Unprinted character (%s)',
                ord(c))
            
    def receivedPrintableChar(self, c):
        if self.insertMode:
            remainder =  ''.join(self.lineBuf[self.linePos:])
            self.lineBuf.insert(self.linePos, c)
            self.term.insertChar(c, remainder)
            self.linePos = self.linePos + 1
        else:
            self.lineBuf[self.linePos] = c
            self.term.write(c)
            self.linePos += 1

    def receivedEscapeChar(self, c):
        fname = 'escape_%s' % ord(c)
        if hasattr(self, fname):
            getattr(self, fname)()
        else:
            self.cbPlugin.log.debug('Unhandled escape character %s %s',
                c, ord(c))
     
    def receivedTildEscapeChar(self, c):
        fname = 'tildescape_%s' % ord(c)
        if hasattr(self, fname):
            getattr(self, fname)()
        else:
            self.cbPlugin.log.debug('Unhandled tilda character %s %s',
                c, ord(c))
        
    def receivedShortEscapeChar(self, c):
        fname = 'shescape_%s' % ord(c)
        if hasattr(self, fname):
            getattr(self, fname)()
        else:
            self.cbPlugin.log.debug('Unhandled short escape character (%s)',
            ord(c))

    def character_3(self):
        self.writeNewline()

    def character_4(self):
        self.cbPlugin.receivedCommand('logout', self.user)

    def character_8(self):
        # ^H
        self.receivedBackspace()

    def character_27(self):
        self.state = self.S_ESCAPED
    
    def character_13(self):
        self.receivedLine()

    def character_127(self):
        self.receivedBackspace()
       
    def tildescape_51(self):
        self.receivedDelete()

    def tildescape_50(self):
        """Insert key handler"""
        self.insertMode = not self.insertMode
        msg = (self.insertMode and 'Insert Mode') or 'Overwrite Mode'
        self.term.blinkMessage(msg)

    def escape_65(self):
        prev = self.hist.getPrevious(''.join(self.lineBuf))
        self.updateLineBuffer(prev)

    def escape_66(self):
        next = self.hist.getNext(''.join(self.lineBuf))
        self.updateLineBuffer(next)

    def escape_67(self):
        if self.linePos < len(self.lineBuf):
            self.term.cursorRight()
            self.linePos += 1
            
    def escape_68(self):
        if self.linePos > 0:
            self.term.cursorLeft()
            self.linePos -= 1

    def receivedDelete(self):
        if self.linePos < len(self.lineBuf):
            self.lineBuf.pop(self.linePos)
            self.term.insertChar('', ''.join(self.lineBuf[self.linePos:]))
            #self.linePos += 1
            #self.term.cursorRight()

    def receivedBackspace(self):
        if self.linePos > 0:
            self.linePos -= 1
            self.lineBuf.pop(self.linePos)
            self.term.cursorLeft()
            self.term.insertChar('', ''.join(self.lineBuf[self.linePos:]))

    def ps(self):
        return self.ps1()

    def writeReplaceline(self, s=''):
        self.term.replaceLine('%s%s' % (self.ps(), s))

    def updateLineBuffer(self, s):
        self.lineBuf = [l for l in s]
        self.linePos = len(self.lineBuf)
        self.writeReplaceline(s)
    
    def writeNewlineChars(self):
        self.write('\r\n')
        
    def writeNewline(self):
        self.writeNewlineChars()
        self.updateLineBuffer('')
        
    def writePrompt(self, ps):
        self.write(ps)

    def writeReply(self, reply, **kw):
        r = ('[%(source)s] <%(inreply)s> %%s' % kw) % reply
        self.write(r)
        if kw['inreply'] == 'motd':
            self.writeNewlineChars()
        else:
            self.writeNewline()
        
   
    def historyFeedback(self, position, total):
        pass
  
    def updateSize(self, y, x):
        self.term.updateSize(y, x)
  
class SshTerminal(object):
    def __init__(self, connection):
        self.con = connection
        self.width = 0
        self.height = 0

    def updateSize(self, height, width):
        self.width = width
        self.height = height

    def sendEscape(self, s):
        self.write('\x1B%s' % s)

    def reset(self):
        self.sendEscape('c')

    def eraseScreen(self):
        self.sendEscape('[2J')

    def cursorDown(self, i=''):
        self.sendEscape('[%sB' % i)

    def cursorLeft(self, i=''):
        self.sendEscape('[%sD' % i)

    def cursorRight(self, i=''):
        self.sendEscape('[%sC' % i)

    def cursorHome(self):
        self.sendEscape('[H')

    def cursorTo(self, y, x):
        self.sendEscape('[%s;%sH' % (y, x))

    def cursorSave(self):
        self.sendEscape('7')

    def cursorUnsave(self):
        self.sendEscape('8')

    def eraseLineEnd(self):
        self.sendEscape('[K')

    def eraseLine(self):
        self.sendEscape('[2K')

    def setScrollRows(self, start, end):
        self.sendEscape('[%s;%sr' % (start, end))
    
    def setScrollEntire(self):
        self.sendEscape('[r')
    
    def scrollUp(self):
        self.cursorSave()
        self.sendEscape('M')
        self.cursorUnsave()

    #go
    def attrReset(self):
        self.sendEscape('[0m')

    #go
    def attrColors(self, *args):
        self.sendEscape('[%sm' % ';'.join(args))

    #go
    def attrReverse(self):
        self.sendEscape('[7m')

    def replaceLine(self, s):
        self.eraseLine()
        self.write(chr(13))
        self.write(s)

    def insertChar(self, c, remainder):
        if len(remainder) or not len(c):
            self.eraseLineEnd()
        if len(c):
            self.write(c)
        if len(remainder):
            self.write(remainder)
            self.cursorLeft(len(remainder))

    #go
    def fillLine(self, bg):
       self.eraseLine()

    #go
    def getColoredText(self, text, fg, bg):
        return '\x1B[%s;%sm%s\x1B[0m' % (fg, bg, text)
       
    #go
    def writeReverse(self, s):
        self.attrReverse()
        self.write(s)
        self.attrReset()

    def write(self, s):
        self.con.write(s)

class SshHistory(object):
    MAX = 20
    def __init__(self, proto):
        self.history = []
        self.position = -1
        self.lineBuf = ''
        self.feedBack = lambda: proto.historyFeedback(self.position + 1, len(self.history))
        #self.clearBack = proto.term.clearMessage

    def append(self, item):
        self.history.insert(0, item)
        if len(self.history) > self.MAX:
            self.history.pop()
        self.position = -1
    
    def getPrevious(self, buf):
        if self.position == -1:
            self.lineBuf = buf
        if len(self.history):
            if self.position < (len(self.history) - 1):
                self.position = self.position + 1
            self.feedBack()
            return self.history[self.position]
        else:
            return buf
    
    def getNext(self, buf):
        if self.position == 0:
            self.position = -1 
            #self.clearBack()
            return self.lineBuf
        elif self.position > 0:
            self.position = self.position - 1 
            self.feedBack()
            return self.history[self.position]
        else:
            return buf

class SshUser(avatar.ConchUser):
    def __init__(self, user):
        avatar.ConchUser.__init__(self)
        self.user = user
        self.hostmask = user.gwhm
        #self.channelLookup.update({'session':session.SSHSession})

    def lookupChannel(self, channelType, windowSize, maxPacket, data):
        return self.Session(remoteWindow = windowSize,
                            remoteMaxPacket = maxPacket,
                            data=data, avatar=self)

    def sendReply(self, reply, **kw):
        self.con.writeReply(reply, **kw)
        #self.con.write_reply('\r\n[%s] %s' % (inreply, reply), **kw)

    def close(self):
        self.con.loseConnection()

class SshServer:
    NAME = 'shell'
    User = SshUser
    Auth = SshAuthServer
    Sess = SshSession
    Real = SshRealm
    Prot = ShellProtocol
    Fact = SshServerFactory
    Wrap = SshProtocolWrapper
    
    PROTOCOL = SshProtocol

    def __init__(self, cb):
        self.connections = []
        self.listener = None
        self.cbPlugin = cb
        self.setCallbacks(self)
        #self.getUser = self.cb.getUser
        self.port = None
        self.preinit()
        self.factory = self.Fact()
        self.setCallbacks(self.factory)
    
    def setCallbacks(self, obj):
        obj.cbPlugin = self.cbPlugin
        obj.cbServer = self
        obj.debug = lambda s, *a: \
            self.cbPlugin.log.debug('Sshd: [%s] %s' % \
                (obj.__class__.__name__, s), *a)
        obj.info = lambda s, *a: \
            self.cbPlugin.log.info('Sshd: [%s] %s' % \
                (obj.__class__.__name__, s), *a)
        obj.setCallbacks = self.setCallbacks
    
    def preinit(self):
        self.portalise()
        self.loadKeys()
        self.User.Session = self.Sess
        self.Auth.User = self.User
        self.Fact.services['ssh-userauth'] = self.Auth
        self.Sess.ProtocolWrapper = self.Wrap
        self.Wrap.Protocol = self.Prot

    def start(self, port):
        self.info('Starting %s server on port %s', self.NAME, port)
        reactor.callLater(0, self.startListening, port)

    def stop(self):
        self.info('Stopping %s server', self.NAME)
        self.stopListening()

    def startListening(self, port):
        if not self.port:
            try:
                self.listener = reactor.listenTCP(port, self.factory)
            except terror.CannotListenError:
                self.start(port)
            self.port = int(port)
        
    def portalise(self):
        realm = self.Real(self.User)
        self.setCallbacks(realm)
        self.portal = SupybotPortal(realm)
        self.Fact.portal = self.portal
        self.debug('Initialised Twisted portal.')
        
    def authorised(self, user):
        self.info('New gateway connection on %s for %s',
            user.hostmask, self.NAME)
        self.connections.append(user)
        user.sendReply(self.cbPlugin.registryValue('motd'),
            inreply='motd',
            source='status')
        user.sendReply(user.hostmask,
            inreply='hostmask',
            source='status')
        
    def stopListening(self):
        for c in self.connections:
            c.close()
        if self.listener:
            self.listener.stopListening()
            self.port = None
            
    def loadKeys(self):
        sshdir = self.cbPlugin.datapaths['keys']
        privpath = '%s%s%s' % (sshdir, os.sep,
            self.cbPlugin.registryValue('keys.rsaPrivateFile'))
        if not os.path.exists(privpath):
            raise Exception, 'The SSH private key is missing %s' % privpath
        pubpath = '%s%s%s' % (sshdir, os.sep,
            self.cbPlugin.registryValue('keys.rsaPublicFile'))
        if not os.path.exists(pubpath):
            raise Exception, 'The SSH public key is missing'
        self.debug('Loading RSA keys')
        self.Fact.publicKeys = \
            {'ssh-rsa':keys.getPublicKeyString(filename=pubpath)}
        self.Fact.privateKeys = \
            {'ssh-rsa':keys.getPrivateKeyObject(filename=privpath)}

class PyUser(SshUser):
    def sendReply(self, reply, **kw):
        if reply != '\n':
            self.con.writeReply('\n%s' %  reply, **kw)

class PyProtocol(ShellProtocol):
    def connectionMade(self):
        self.more = False
        SshProtocol.connectionMade(self)
        self.interpreter = self.Interpreter(self.user,
            {'hostmask': self.user.hostmask,
                'irc': world.ircs[0],
                'feedCommand': lambda s: \
                    self.cbPlugin.receivedCommand(s, self.user)})

    def ps1(self, *a):
        return '>>> '

    def ps2(self, *a):
        return '... '

    def receivedCommand(self, cmd):
        self.debug('Received command %s from %s',
            cmd, self.user.hostmask)
        self.more = self.interpreter.push(cmd)
        self.writeNewline()
        if len(cmd):
            self.hist.append(cmd)
  
    def ps(self):
        return (self.more and self.ps2()) or self.ps1()
  
    def writeReply(self, reply, **kw):
        self.write(reply.replace('\n', '\r\n'))
        if kw['source'] != 'interpreter':
            if 'inreply' in kw and kw['inreply'] != 'motd':
                self.writeNewline()
   
    
    class Interpreter(code.InteractiveInterpreter):
        def __init__(self, handler, _locals=None):
            code.InteractiveInterpreter.__init__(self, _locals)
            self.handler = handler
            self.resetBuffer()

        def push(self, cmd):
            self.rbuf.append(cmd)
            c = '\n'.join(self.rbuf)
            o = sys.stdout
            sys.stdout = self.FileWrapper(self.handler)
            more = self.runsource(c, '<console>')
            sys.stdout = o
            if not more:
                self.resetBuffer()
            return more

        def write(self, msg):
            self.handler.sendReply(msg.rstrip('\n'), source='traceback')
   
        def resetBuffer(self):
            self.rbuf = []

        class FileWrapper:
            softspace = 0
            state = 'normal'

            def __init__(self, o):
                self.o = o

            def flush(self):
                pass

            def write(self, data):
                self.o.sendReply(data, source='interpreter')

            def writelines(self, lines):
                self.write(''.join(lines))

class PyServer(SshServer):
    NAME='pyshell'
    User = PyUser
    Prot = PyProtocol
    Auth = type('PyAuthServer', (SshAuthServer, object), {})
    Sess = type('PySession', (SshSession, object), {})
    Real = type('PyRealm', (SshRealm,), {})
    Fact = type('PyServerFactory', (SshServerFactory, object), {})
    Wrap = type('PyProtocolWrapper', (SshProtocolWrapper,), {})

class UiUser(SshUser):
    def sendReply(self, reply, **kw):
        self.con.write_reply(reply, **kw)

    def close(self):
        self.con.term.setScrollEntire()
        # bizarre bug, this following print returns differently at different
        # times
        #print 'isinst', isinstance(self, SshUser)
        #SshUser.close(self)
        self.con.loseConnection()

# Terminal character options
TSETTINGS = {
            'weight':{
                'default':22,
                'bold':1,
                'dim':2
                },
            'underline':{
                'default':24,
                True:4
                },
            'fg':{
                'black':30,
                'red':31,
                'green':32,
                'yellow':33,
                'blue':34,
                'magenta':35,
                'cyan':36,
                'white':37,
                'default':39},
            'bg':{
                'black':40,
                'red':41,
                'green':42,
                'yellow':43,
                'blue':44,
                'magenta':45,
                'cyan':46,
                'white':47,
                'default':49}}
ESC_O = '\x1B['
ESC_C = 'm'
ESC_T = '%s%%s%s' % (ESC_O, ESC_C)
ESC_R = ESC_T % '0'

# Default terminal character settings
TDEFAULTS = []
for k in TSETTINGS:
    TDEFAULTS.append(TSETTINGS[k]['default'])


class TChar(object):
    def __init__(self, c, **kw):
        self.c = c
        self.settings = {}
        for k in TSETTINGS:
            if k in kw:
                v = kw[k]
            else:
                v = 'default'
            self.settings[k] = v
    
    def getDifference(self, c):
        if not c:
            return [self.getValue(k, self.settings[k]) for k in TSETTINGS]
        settings = []
        if self.settings == c.settings:
            return settings
        for k in TSETTINGS:
            if self.settings[k] != c.settings[k]:
                settings.append(self.getValue(k, self.settings[k]))
        return settings

    def getValue(self, setting, name):
        return TSETTINGS[setting][name]

    def render(self, prev):
        diff = self.getDifference(prev)
        esc = None
        if len(diff):
            if diff == TDEFAULTS:
                diff = ['0']
            esc = ESC_T % ';'.join(map(str, diff))
        return (esc and (''.join([esc, self.c]))) or self.c

class TString(object):
    def __init__(self, *chars):
        self.chars = list(chars)

    def reverse(self):
        #returns a copy
        return TString(*self.chars[::-1])

    def __len__(self):
        return len(self.chars)

    def add(self, s, **kw):
        s = str(s)
        for c in s:
            self.chars.append(TChar(c, **kw))
        
    def render(self):
        s = ''
        lastChar = None
        for c in self.chars:
            s = ''.join([s, c.render(lastChar)])
            lastChar = c
        return ''.join([s, ESC_R])

    def append(self, *ts):
        self.chars.extend(*[t.chars for t in ts])
              
    def paint(self, **kw):
        for c in self.chars:
            for k in kw:
                if k in c.settings:
                    c.settings[k] = kw[k]
              
    def split(self, spllen, indlen=0):
        splstrings = []
        splchars = []
        for c in self.chars:
            i = len(splchars)
            if i and (i % spllen == 0):
                splstrings.append(TString(*splchars))
                splchars = [TChar(' ') for j in range(indlen)]
            splchars.append(c)
        splstrings.append(TString(*splchars))
        return splstrings

class UiBar(object):
    PREF = TString()
    PREF.add('-', weight='bold', fg='black')
    PREF.add('-', fg='cyan')
    PREF.add('. ', weight='bold', fg='cyan')
    POSTF = PREF.reverse()
    def __init__(self, f):
        self.func = f
    def render(self):
        s = TString()
        for t in self.func():
            s.add(' ')
            s.append(self.PREF)
            s.append(t)
            s.append(self.POSTF)
        s.paint(bg='black')
        return s.render()
 
class UiPane(object):
    BUFMAX = 100
    TIMESTAMP = True
    act = 0 
    def __init__(self, display):
        self.lines = []
        self.visible = False
        self.display = display
        self.title = "Supybot, at http://supybot.com/"

    def writeLine(self, s, append, importance):
        if append:
            self.lines.append(s.render())
        if self.visible:
            self.displayLine(s.render())
        else:
            if importance > self.act:
                self.act = importance
                self.display.drawSbar()

    def displayLine(self, s):
        self.display.term.cursorTo(self.display.term.height - 2, 0)
        self.display.term.write('\r\n%s' % s)
        
    def makeVisible(self):
        self.act = 0
        self.display.term.cursorSave()
        self.display.term.eraseScreen()
        if not self.visible:
            for l in self.lines[-self.display.term.height:]:
                self.displayLine(l)
            self.visible = True
        self.display.term.cursorUnsave()

    def displayBuffer(self, end=-1):
        pass
       
class UiDisplay(object):
    def __init__(self, terminal):
        self.term = terminal
        self.bar = UiBar(self.getSbarData)
        self.panes = {}
        self.windows = []
        self.createPane('status')
        self.currentPane = 'status'
        self.reset()

    def getTbarData(self):
        ts = TString()
        ts.add(self.panes[self.currentPane].title[:self.term.width - 2], bg='black')
        return ' %s' % ts.render()

    def getSbarData(self):
        tss = []
        tstime = TString()
        tstime.add(time.strftime('%H:%M'))
        tss.append(tstime)
        tsnick = TString()
        tsnick.add(self.term.con.user.user.name)
        tsnick.add('@', fg='cyan')
        tsnick.add(self.term.con.cbPlugin.getNick())
        tss.append(tsnick)
        tschan = TString()
        tschan.add(self.windows.index(self.currentPane))
        tschan.add(':')
        tschan.add(self.currentPane)
        tss.append(tschan)
        tsact = TString()
        tsact.add('Act: ')
        acts = []
        for i, p in enumerate(self.windows):
            act = self.panes[p].act
            if act:
                attrs = {}
                if act == 1:
                    attrs = {'fg':'cyan'}
                elif act == 2:
                    attrs = {'weight': 'bold'}
                elif act == 3:
                    attrs = {'fg':'magenta', 'weight':'bold'}
                if len(tsact) > 5:
                    tsact.add(',', fg='cyan')
                tsact.add('%s' % i, **attrs)
        tss.append(tsact)
        return tss
    
    def drawSbar(self):
        self.term.cursorSave()
        self.term.cursorTo(self.term.height - 1, 0)
        self.term.sendEscape('[%sm' % TSETTINGS['bg']['black'])
        self.term.eraseLine()
        self.term.cursorTo(self.term.height - 1, 0)
        self.term.write(self.bar.render())
        self.term.cursorTo(0, 0)
        self.term.sendEscape('[%sm' % TSETTINGS['bg']['black'])
        self.term.eraseLine()
        self.term.cursorTo(0, 0)
        self.term.write(self.getTbarData())
        self.term.cursorUnsave()
        reactor.callLater(45, self.drawSbar)

    def reset(self):
        self.term.setScrollRows(2, self.term.height - 2)
        self.setVisiblePane(self.currentPane)

    def setVisiblePane(self, name):
        for p in self.panes:
            self.panes[p].visible = False
        self.panes[name].makeVisible()
        self.currentPane = name
        self.drawSbar()
      
    def setVisibleWindow(self, number):
        wid = number - 1
        if wid >= 0 and wid < len(self.windows):

            self.setVisiblePane(self.windows[wid])

    def createPane(self, name):
        self.panes[name] = UiPane(self)
        self.windows.append(name)
        return self.panes[name]
    
    def writeReply(self, s, **kw):
        try:
            source =  kw['source']
        except KeyError:
            source = 'default'
            kw['source'] = source
        formatter = 'format_%s' % source
        formatmethod = getattr(self, formatter, False)
        if formatmethod:
            formatted, indent = formatmethod(s, **kw)
        else:
            formatted, indent = self.format_default(s, **kw)
        if not formatted:
            return
        pane = self.getPane(**kw)
        if 'topic' in kw:
            pane.title = kw['topic']
            if self.currentPane == kw['inreply']:
                self.drawSbar()
                
        self.term.cursorSave()
        newts = TString()
        newts.add(time.strftime('%H:%M '))
        indent = indent + len(newts)
        assert isinstance(formatted, TString)
        newts.append(formatted)
        appendtobuf = source not in ['ls', 'completer', 'registry']
        importance = 2
        if source == 'bnc':
            if 'importance' in kw:
                importance = kw['importance']
        for ts in newts.split(self.term.width, indent):
            pane.writeLine(ts, appendtobuf, importance)
        self.term.cursorUnsave()
       
    def getPane(self, **kw):
        self.debug('%s', self.panes)
        source = kw['source']
        if source == 'bnc':
            if 'inreply' in kw:
                try:
                    return self.panes[kw['inreply']]
                except KeyError:
                    return self.createPane(kw['inreply'])
            else:
                source = 'status'
        if source in ['status', 'log']:
            return self.panes[source]
        elif source in ['menu', 'ls']:
            return self.panes[self.currentPane]
        else:
            return self.panes['status']

    def format_bnc(self, s, **kw):
        ts = TString()
        if 'inreply' in kw and kw['inreply'] == self.term.con.cbPlugin.getNick():
            return False, False
        if kw['command'] in ['join', 'part', 'nick', 'quit', 'kick', 'mode',
        'bounce', 'topic']:
            return self.format_bnc_userevent(s, **kw)
        ts.add('<', weight='bold', fg='black')
        ts.add(kw['nick'])
        ts.add('> ', weight='bold', fg='black')
        ind = len(ts)
        ts.add(s)
        return ts, ind
       
    def format_bnc_userevent(self, s, **kw):
        ts = TString()
        ts.add('.', fg='black', weight='bold')
        ts.add(".")
        ts.add('. ', fg='white', weight='bold')
        ts.add(kw['command'], fg='blue')
        ts.add('!', fg='black', weight='bold')
        if not 'evalue' in kw:
            kw['evalue'] = kw['inreply']
        ts.add(kw['evalue'], fg='blue', weight='bold')
        ts.add(' -> ', fg='black', weight='bold')
        ind = len(ts)
        ts.add(s, weight='bold')
        for k in ['hm', 'extra']:
            if k in kw:
                ts.add('(', fg='black', weight='bold')
                ts.add(kw[k], fg='cyan')
                ts.add(') ', fg='black', weight='bold')
        return ts, ind

    def format_status(self, s, **kw):
        ts = TString()
        ts.add('***Status ', fg='green')
        ts.add(s)
        return ts, len('***Status ')

    def format_outfilter(self, s, **kw):
        ts = TString()
        ts.add('>>> ', weight='bold', fg='blue')
        ts.add(s)
        return ts, 4

    def format_completer(self, s, **kw):
        ts = TString()
        ts.add('***Completer ', fg='magenta')
        ts.add(s)
        return ts, len('***Completer ')
    
    def format_registry(self, s, **kw):
        ts = TString()
        ts.add('***Registry ', fg='yellow', weight='dim')
        ts.add('[', fg='yellow', weight='dim')
        ts.add(kw['inreply'])
        ts.add('] ', fg='yellow', weight='dim')
        ts.add(s)

        return ts, len('***Registry ')

    def format_menu(self, s, **kw):
        ts = TString()
        ts.add('[', fg='black', weight='bold')
        ts.add(kw['inreply'], weight='bold', fg='yellow')
        ts.add('] ', fg='black', weight='bold')
        ts.add(s)
        return ts, 4

    def format_default(self, s, **kw):
        ts = TString()
        for k in kw:
            ts.add('<', fg='cyan', weight='dim')
            ts.add('%s=' % k)
            ts.add(kw[k], weight='bold')
            ts.add('> ', fg='cyan', weight='dim')
        ts.add(s)
        return ts, 4

    def format_ls(self, s, **kw):
        kw.setdefault('inreply', '.')
        ts = TString()
        ts.add('[', fg='blue', weight='bold')
        ts.add(kw['inreply'])
        ts.add('] ', fg='blue', weight='bold')

        if isinstance(s, TString):
            ts.append(s)
        else:
            ts.add(s)
        return ts, 4

    def format_command(self, s, **kw):
        ts = TString()
        ts.add('<<< ', fg='green', weight='bold')
        ts.add(s)
        return ts, 4

    def format_help(self, s, **kw):
        ts = TString()
        ts.add('***Help ', fg='blue', weight='dim')
        ts.add(s)
        return ts, 4

    def buildCommand(self, cmd):
        if cmd.startswith('/'):
            return cmd[1:]
        if self.currentPane != 'status':
            if self.currentPane.startswith('#'):
                bcmd = 'msg'
            else:
                bcmd = 'pmsg'
            return '%s %s %s' % (bcmd, self.currentPane, cmd)
        else:
            return cmd

    def ps(self):
        if self.currentPane == 'status':
            return '[(status)] $ '
        else:
            return '[%s] ' % self.currentPane

class RegistryBrowser(object):
    def __init__(self, display):
        self.root = dict(conf.supybot.getValues(getChildren=True))
        self.display = display
    
    def ps(self):
        if len(self.codes):
            ks = self.codes.keys()
            ks.sort()
            return '(%s) Select ? ' % ''.join(ks)
        else:
            return '(Ctrl-G to cancel) Enter new Value > '

    def resetCurrent(self):
        self.currentVal = None
        self.current = {}
        self.curdirs = []
        self.curvals = []
        self.name = None
        self.sdir = None
        self.codes = {}
        self.keys = {}
        
    def _showGroup(self, name='supybot'):
        self.resetCurrent()
        entry = None
        if name == 'supybot':
            entry = conf.supybot
        elif name in self.root:
            entry = self.root[name]
        else:
            print 'bad regentry %s' % name
            return
        if not hasattr(entry, 'value') or len(entry.getValues()):
            self.selectedDir(name, entry)
        else:
            return self.selectedValue(name, entry)

    def receivedKey(self, key):
        if key in self.codes:
            k = self.codes[key]
            self.display.writeReply(k, source='menu', inreply=key)
            return self._showGroup(k)
        else:
            self.display.writeReply('Unlinked key.', source='menu', inreply=key)
            #self._showGroup(self.name)
   
    def selectedValue(self, name, sval):
        self.currentval = name
        self.display.writeReply(name, source='registry',
            inreply='ed')
        self.display.writeReply(sval.value, source="registry",
            inreply='-')
        return True
   
    def selectedDir(self, name, sdir):
        self.name = name
        self.sdir = sdir
        for k, v in sdir.getValues():
            self.current[k] = v
            s = ''
            if not hasattr(v, 'value') or len(v.getValues()):
                self.curdirs.append(k)
            else:
                self.curvals.append(k)
                s = v.value
        self.curdirs.sort()
        self.curvals.sort()
        self.displayDir(name)
        return False
       
    def displayDir(self, name):
        self.display.writeReply(name, source='registry',
            inreply='ls')
        if name != 'supybot':
            parent='.'.join(name.split('.')[:-1])
            self.codes['.'] = parent
            dot = TString()
            dot.add('.', underline=True, weight='bold')
            self.display.writeReply(dot, source='ls', inreply='+')
        i = 0
        for k in self.curdirs + self.curvals:
            i = i + 1
            n = k.split('.')[-1]
            ds = TString()
            hascode = False
            for l in n:
                if not (hascode or l in self.codes):
                    hascode = True
                    self.codes[l] = k
                    ds.add(l, underline=True, weight='bold')
                else:
                    ds.add(l)
            if not hascode:
                j = 0
                while not hascode:
                    j = j + 1
                    sj = '%s' % j
                    if not sj in self.codes:
                        self.codes[sj] = k
                        hascode = True
                        ds.add(' ')
                        ds.add(sj, underline=True)
            inreply = ''
            textra = TString()
            textra.add(' (')
            if k in self.curdirs:
                textra.add (len(self.current[k].getValues()), fg='cyan',
                    weight='bold')
                inreply = '+'
            else:
                textra.add(self.current[k].value, fg='green', weight='bold')
                inreply = ' '
            textra.add(')')
            
            ds.append(textra)
            #extra = self.display.term.getColoredText('%s' % extra[0], extra[1], 1)
            
            #ds = '%s (%s)' % (ds, extra)
            #code = self.display.term.getColoredText('%s' % i, 4, 33)
            #ds = '%s %s' % (code, ds)
            self.display.writeReply(ds, source='ls', inreply=inreply)
            
class Completer(object):
    def __init__(self, *args):
        self.words = args
        self.prevcompletion = None
    
    def complete(self, s):
        results = []
        longest = None
        for word in self.words:
            if word.startswith(s):
                if word not in results:
                    results.append(word)
                    if longest:
                        nl = []
                        for i, l in enumerate(word):
                            if i < len(longest) and longest[i] == l:
                                nl.append(l)
                            else:
                                break                        
                        longest = ''.join(nl)
                    else:
                        if len(s):
                            longest = word
        
        isrepeat = (self.prevcompletion == (longest, results))
        self.prevcompletion = longest, results
        
        return longest, results, isrepeat

class UiProtocol(ShellProtocol):
    M_COMMAND = 1
    M_MENU = 2
    mode = M_COMMAND
   
    def connectionMade(self):
        self.mode = self.M_COMMAND
        self.commandHandler = None
        self.display = UiDisplay(self.term)
        self.setCallbacks(self.display)
        self.regbrowse = RegistryBrowser(self.display)
        self.completer = Completer(*self.generateCompletionStrings())
        self.cbServer.authorised(self.user)
        self.writeNewline()

    def generateCompletionStrings(self):
        L = []
        for c in self.cbPlugin.irc.callbacks:
            L.extend(c.listCommands())
        return L

    def write_reply(self, s, **kw):
        self.display.writeReply(s, **kw)

    def receivedCommand(self, s):
        if self.commandHandler:
            self.display.writeReply(s, source='registry', inreply='+')
            s = 'config %s %s' % (self.regbrowse.currentval, s)
            self.commandHandler = None
        else:
            s = self.display.buildCommand(s)
        self.display.writeReply(s, source='command', inreply='./')
        ShellProtocol.receivedCommand(self, s)
    
    def receivedPrintableChar(self, c):
        if self.mode == self.M_MENU:
            if self.regbrowse.receivedKey(c):
                self.mode = self.M_COMMAND
                self.commandHandler = self.regbrowse
            self.writeReplaceline(''.join(self.lineBuf))
        else:
            ShellProtocol.receivedPrintableChar(self, c)
 
    def ps1(self):
        if self.commandHandler:
            return self.commandHandler.ps()
        else:
            return self.display.ps()

    def ps2(self):
        return self.regbrowse.ps()

    def ps(self):
        return getattr(self, 'ps%s' % self.mode)()
   
    def writeNewlineChars(self):
        self.term.cursorTo(self.term.height, 0)
        
    def updateSize(self, y, x):
        if hasattr(self, 'term'):
            self.term.updateSize(y, x)
            if self.transport:
                self.display.reset()
                self.writeNewlineChars()
                self.writeReplaceline(''.join(self.lineBuf))

    def historyFeedback(self, pos, total):
        #self.display.blinkMessage('History %s of %s' % (pos, total))
        pass

    def character_7(self):
        self.setCommandMode('^G')

    def character_9(self):
        self.doComplete()
    
    def receivedShortEscapeChar(self, c):
        cc = ord(c)
        if cc <= 58 and cc >= 48:
            self.changeScreen(cc - 47)
        else:
            ShellProtocol.receivedShortEscapeChar(self, c)
           
    def shescape_27(self):
        self.setCommandMode('^')

    def shescape_47(self):
        self.displayHelp()

    def changeScreen(self, number):
        self.display.setVisibleWindow(number)
        self.writeNewlineChars()
        self.writeReplaceline(''.join(self.lineBuf))

    def shescape_49(self):
        self.changeScreen('status')

    def shescape_50(self):
        self.changeScreen('#db')

    def displayHelp(self):
        gen = [('<Esc><Esc>',
                """Return to command mode.""")]

        conf = [('<Esc>s',
                """Switch to "supybot" directory in registry mode"""),
                ('<Esc>p',
                """Switch to "supybot.plugins" directory in registry mode"""),
                ('<Esc>n',
                """Switch to "supybot.networks" directory in registry mode"""),
                ('<Esc>d',
                """Switch to "supybot.directories" directory in registry mode"""),
                ('<Esc>r',
                """Switch to "supybot.reply" directory in registry mode""")]
                
        
        self.display.writeReply('Key Press Help',
            source='help', inreply='keys')
            
        for i in gen + conf:
            ts = TString()
            ts.add(i[0], weight='bold')
            ts.add(' ')
            ts.add(i[1])
            self.display.writeReply(ts,
                source='ls', inreply='?')
                
        self.display.writeReply('<Esc> represents the Escape key',
            source='help', inreply='keys')
    
    def shescape_115(self):
        self.setMenuMode('^s', 'supybot')
    
    def shescape_110(self):
        self.setMenuMode('^n', 'supybot.networks')
 
    def shescape_112(self):
        self.setMenuMode('^p', 'supybot.plugins')
   
    def shescape_114(self):
        self.setMenuMode('^r', 'supybot.reply')

    def shescape_100(self):
        self.setMenuMode('^d', 'supybot.directories')
 
    def doComplete(self):
        c, r, ir = self.completer.complete(''.join(self.lineBuf))
        if len(r) == 1:
            c = '%s ' % c
        if c:
            self.updateLineBuffer(c)
            if ir:
                self.display.writeReply('Displaying list for "%s".' % c, source='completer',
                    inreply='ls')
                for res in r:
                    self.display.writeReply(res, source='ls', inreply='.')
 
    def setCommandMode(self, inreply):
        if self.mode == self.M_MENU:
            self.display.writeReply('Entered command mode.', source='menu',
            inreply=inreply)
            self.mode = self.M_COMMAND
        else:
            self.commandHandler = None
            self.display.writeReply('Cancelled Edit.', source='menu',
            inreply=inreply)
        self.writeReplaceline(''.join(self.lineBuf))
  
    def setMenuMode(self, inreply, root='supybot'):
        self.display.writeReply('Entered menu mode.', source='menu',
        inreply=inreply)
        self.mode = self.M_MENU
        self.regbrowse._showGroup(root)
        self.writeReplaceline(''.join(self.lineBuf))

class UiServer(SshServer):
    NAME='ui'
    User = UiUser
    Prot = UiProtocol
    Auth = type('UiAuthServer', (SshAuthServer, object), {})
    Sess = type('UiSession', (SshSession, object), {})
    Real = type('UiRealm', (SshRealm,), {})
    Fact = type('UiServerFactory', (SshServerFactory, object), {})
    Wrap = type('UiProtocolWrapper', (SshProtocolWrapper,), {})

class PlainServer(SshServer):
    NAME='plain'
    User = type('PlainUser', (SshUser, object), {})
    Prot = SshProtocol
    Auth = type('PbAuthServer', (SshAuthServer, object), {})
    Sess = type('PbSession', (SshSession, object), {})
    Real = type('PbRealm', (SshRealm,), {})
    Fact = type('PbServerFactory', (SshServerFactory, object), {})
    Wrap = type('PbProtocolWrapper', (SshProtocolWrapper,), {})

# Left in for posterity. If you don't have OpenSSH, you can use this to generate
# keys.
def keygen(filepath):
    if not RSA:
        return
    key = RSA.generate(1024, common.entropy.get_bytes)
    
    # Create and write the private key file.
    # . Generate the string.
    privk = keys.makePrivateKeyString(key)
    # . Write the file
    privf = open(filepath, 'w')
    privf.write(privk)
    privf.close()
    # . Fix the permissions
    os.chmod(filepath, 33152)
    
    # Create and write the public key file.
    # . Generate the string.
    pubk = keys.makePublicKeyString(key)
    # . Write the file.
    pubf = open('%s.pub' % filepath, 'w')
    pubf.write(pubk)
    pubf.close()

Class = Sshd

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
