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
import socket
import time
import sys

# Third-party modules
from PyQt4 import QtCore, QtGui

# Local modules
import window


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 14789))
sock.settimeout(0.01)

# FIXME: internationalize
_ = lambda x:x

def sendCommand(command):
    sock.send(unicode(command).encode('utf8', 'replace') + '\n')

class GetReplies(QtCore.QObject):
    def __init__(self, commandsHistory):
        self._commandsHistory = commandsHistory
        self._timer = QtCore.QTimer()
        self.connect(self._timer, QtCore.SIGNAL('timeout()'),
                     self.run);
        self._timer.start(100)
    def run(self):
        currentLine = ''
        if not '\n' in currentLine:
            try:
                data = sock.recv(4096)
            except socket.timeout:
                return
        if '\n' in data:
            splitted = (currentLine + data).split('\n')
            nextLines = '\n'.join(splitted[1:])
            self._commandsHistory.appendPlainText('--> ' +
                                                  splitted[0].decode('utf8'))

class Window(QtGui.QTabWidget, window.Ui_window):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)

        self.connect(self.commandSend, QtCore.SIGNAL('returnPressed()'),
                     self.commandSendHandler)
        self.connect(self.commandSend, QtCore.SIGNAL('clicked()'),
                     self.commandSendHandler)

        self._getReplies = GetReplies(self.commandsHistory)

    def commandSendHandler(self):
        command = self.commandEdit.text()
        self.commandEdit.clear()
        sendCommand(command)
        self.commandsHistory.appendPlainText('<-- ' + command)



if __name__ == "__main__":
    running = True

    app = QtGui.QApplication(sys.argv)

    window = Window()
    window.show()

    status = app.exec_()
    running = False
    sys.exit(status)
