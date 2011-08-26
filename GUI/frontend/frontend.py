#!/usr/bin/env python
# -*- coding: utf8 -*-

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

# Standard library
from __future__ import print_function
import threading
import hashlib
import socket
import time
import sys
import re

# Third-party modules
from PyQt4 import QtCore, QtGui

# Local modules
import connection
import window



# FIXME: internationalize
_ = lambda x:x

refreshingTree = threading.Lock()
class ConfigurationTreeRefresh:
    def __init__(self, eventsManager, window):
        if not refreshingTree.acquire(False):
            return
        self._eventsManager = eventsManager

        parentItem = QtGui.QStandardItemModel()
        window.connect(parentItem, QtCore.SIGNAL('itemClicked()'),
                       window.configurationItemActivated)
        window.configurationTree.setModel(parentItem)
        self.items = {'supybot': parentItem}

        hash_ = eventsManager.sendCommand('config search ""')
        eventsManager.hook(hash_, self.slot)

    def slot(self, reply):
        """Slot called when a childs list is got."""
        childs = reply.split(', ')
        for child in childs:
            if '\x02' in child:
                hash_ = self._eventsManager.sendCommand('more')
                self._eventsManager.hook(hash_, self.slot)
                break
            elif ' ' in child:
                refreshingTree.release()
                break
            splitted = child.split('.')
            parent, name = '.'.join(splitted[0:-1]), splitted[-1]
            item = QtGui.QStandardItem(name)
            item.name = QtCore.QString(child)
            self.items[parent].appendRow(item)
            self.items[child] = item



class Connection(QtGui.QTabWidget, connection.Ui_connection):
    """Represents the connection dialog."""
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setupUi(self)

    def accept(self):
        """Signal called when the button 'accept' is clicked."""
        self.state.text = _('Connecting...')
        if not self._connect():
            self.state.text = _('Connection failed.')
            return

        self.state.text = _('Connected. Loading GUI...')

        window = Window(self._eventsManager)
        window.show()
        window.commandEdit.setFocus()

        self._eventsManager.callbackConnectionClosed = window.connectionClosed
        self._eventsManager.defaultCallback = window.replyReceived

        self.hide()

    def _connect(self):
        """Connects to the server, using the filled fields in the GUI.
        Return wheter or not the connection succeed. Note that a successful
        connection with a failed authentication is interpreted as successful.
        """
        server = str(self.editServer.text()).split(':')
        username = str(self.editUsername.text())
        password = str(self.editPassword.text())

        assert len(server) == 2
        assert re.match('[0-9]+', server[1])
        assert ' ' not in username
        assert ' ' not in password

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server[1] = int(server[1])
        try:
            sock.connect(tuple(server))
        except socket.error:
            return False
        sock.settimeout(0.01)

        self._eventsManager = EventsManager(sock)

        self._eventsManager.sendCommand('identify %s %s' %
                                        (username, password))
        return True

    def reject(self):
        """Signal called when the button 'close' is clicked."""
        exit()

class Window(QtGui.QTabWidget, window.Ui_window):
    """Represents the main window."""
    def __init__(self, eventsManager, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self._eventsManager = eventsManager

        self.setupUi(self)
        self.connect(self.commandEdit, QtCore.SIGNAL('returnPressed()'),
                     self.commandSendHandler)
        self.connect(self.commandSend, QtCore.SIGNAL('clicked()'),
                     self.commandSendHandler)

        self.connect(self.refreshConfigurationTree, QtCore.SIGNAL('clicked()'),
                     self._refreshConfigurationTree)

    def commandSendHandler(self):
        """Slot called when the user clicks 'Send' or presses 'Enter' in the
        raw commands tab."""
        command = self.commandEdit.text()
        self.commandEdit.clear()
        try:
            # No hooking, because the callback would be the default callback
            self._eventsManager.sendCommand(command)
            s = _('<-- ') + command
        except socket.error:
            s = _('(not sent) <-- ') + command
        self.commandsHistory.appendPlainText(s)

    def replyReceived(self, reply):
        """Called by the events manager when a reply to a raw command is
        received."""
        self.commandsHistory.appendPlainText(_('--> ') + reply.decode('utf8'))

    def connectionClosed(self):
        """Called by the events manager when a special message has to be
        displayed."""
        self.commandsHistory.appendPlainText(_('* connection closed *'))
        self.commandEdit.readOnly = True
        self._eventsManager.stop()

    def _refreshConfigurationTree(self):
        """Slot called when the user clicks 'Refresh' under the configuration
        tree."""
        ConfigurationTreeRefresh(self._eventsManager, self)

    def configurationItemActivated(self, item):
        print(repr(item))




class EventsManager(QtCore.QObject):
    """This class handles all incoming messages, and call the associated
    callback (using hook() method)"""
    def __init__(self, sock):
        self._sock = sock
        self.defaultCallback = lambda x:x
        self._currentLine = ''
        self._hooks = {} # FIXME: should be cleared every minute

        self._timerGetReplies = QtCore.QTimer()
        self.connect(self._timerGetReplies, QtCore.SIGNAL('timeout()'),
                     self._getReplies);
        self._timerGetReplies.start(100)

        self._timerCleanHooks = QtCore.QTimer()
        self.connect(self._timerCleanHooks, QtCore.SIGNAL('timeout()'),
                     self._cleanHooks);
        self._timerCleanHooks.start(100)

    def _getReplies(self):
        """Called by the QTimer; fetches the messages and calls the hooks."""
        currentLine = self._currentLine
        self.currentLine = ''
        if not '\n' in currentLine:
            try:
                data = self._sock.recv(65536)
                if not data: # Frontend closed connection
                    self.callbackConnectionClosed()
                    return
                currentLine += data
            except socket.timeout:
                return
        if '\n' in currentLine:
            splitted = currentLine.split('\n')
            nextLines = '\n'.join(splitted[1:-1])
            splitted = splitted[0].split(': ')
            hash_, reply = splitted[0], ': '.join(splitted[1:])
            if hash_ in self._hooks:
                self._hooks[hash_][0](reply)
            else:
                self.defaultCallback(reply)
        else:
            nextLines = currentLine
        self._currentLine = nextLines

    def hook(self, hash_, callback, lifeTime=60):
        """Attach a callback to a hash: everytime a reply with this hash is
        received, the callback is called."""
        self._hooks[hash_] = (callback, time.time() + lifeTime)

    def unhook(self, hash_):
        """Undo hook()."""
        return self._hooks.pop(hash_)

    def _cleanHooks(self):
        for hash_, data in self._hooks.items():
            if data[1] < time.time():
                self._hooks.pop(hash_)

    def sendCommand(self, command):
        """Get a command, send it, and returns a unique hash, used to identify
        replies to this command."""
        hash_ = hashlib.sha1(str(time.time()) + command).hexdigest()
        command = '%s: %s\n' % (hash_, unicode(command).encode('utf8', 'replace'))
        self._sock.send(command)
        return hash_

    def stop(self):
        """Stops the loop."""
        self._timer.stop()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    connection = Connection()
    connection.show()


    sys.exit(app.exec_())
