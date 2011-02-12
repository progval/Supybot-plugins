# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'connection.ui'
#
# Created: Sat Feb 12 14:04:00 2011
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_connection(object):
    def setupUi(self, connection):
        connection.setObjectName("connection")
        connection.resize(400, 153)
        self.formLayout = QtGui.QFormLayout(connection)
        self.formLayout.setObjectName("formLayout")
        self.buttonBox = QtGui.QDialogButtonBox(connection)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.buttonBox)
        self.editServer = QtGui.QLineEdit(connection)
        self.editServer.setObjectName("editServer")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.editServer)
        self.labelServer = QtGui.QLabel(connection)
        self.labelServer.setObjectName("labelServer")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.labelServer)
        self.editUsername = QtGui.QLineEdit(connection)
        self.editUsername.setObjectName("editUsername")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.editUsername)
        self.labelUsername = QtGui.QLabel(connection)
        self.labelUsername.setObjectName("labelUsername")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.labelUsername)
        self.labelPassword = QtGui.QLabel(connection)
        self.labelPassword.setObjectName("labelPassword")
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.labelPassword)
        self.labelState = QtGui.QLabel(connection)
        self.labelState.setObjectName("labelState")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.labelState)
        self.state = QtGui.QLabel(connection)
        self.state.setObjectName("state")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.state)
        self.editPassword = QtGui.QLineEdit(connection)
        self.editPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.editPassword.setObjectName("editPassword")
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.editPassword)

        self.retranslateUi(connection)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), connection.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), connection.reject)
        QtCore.QMetaObject.connectSlotsByName(connection)

    def retranslateUi(self, connection):
        connection.setWindowTitle(QtGui.QApplication.translate("connection", "Connection", None, QtGui.QApplication.UnicodeUTF8))
        self.editServer.setText(QtGui.QApplication.translate("connection", "localhost:14789", None, QtGui.QApplication.UnicodeUTF8))
        self.labelServer.setText(QtGui.QApplication.translate("connection", "Server:port", None, QtGui.QApplication.UnicodeUTF8))
        self.labelUsername.setText(QtGui.QApplication.translate("connection", "Username", None, QtGui.QApplication.UnicodeUTF8))
        self.labelPassword.setText(QtGui.QApplication.translate("connection", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.labelState.setText(QtGui.QApplication.translate("connection", "State", None, QtGui.QApplication.UnicodeUTF8))
        self.state.setText(QtGui.QApplication.translate("connection", "Not connected", None, QtGui.QApplication.UnicodeUTF8))

