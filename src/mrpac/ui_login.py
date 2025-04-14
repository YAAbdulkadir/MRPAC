# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Login.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QSizePolicy, QWidget


class Ui_Login(object):
    def setupUi(self, Login):
        if not Login.objectName():
            Login.setObjectName("Login")
        Login.resize(400, 220)
        self.loginWidget = QWidget(Login)
        self.loginWidget.setObjectName("loginWidget")
        self.loginWidget.setGeometry(QRect(0, 0, 400, 220))
        self.loginWidget.setStyleSheet(
            "QWidget#loginWidget{\n" "background-color: rgb(50, 51, 99);}"
        )
        self.usernameLabel = QLabel(self.loginWidget)
        self.usernameLabel.setObjectName("usernameLabel")
        self.usernameLabel.setGeometry(QRect(60, 70, 81, 20))
        self.usernameLabel.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n' "color: rgb(255, 255, 255);"
        )
        self.passwordLabel = QLabel(self.loginWidget)
        self.passwordLabel.setObjectName("passwordLabel")
        self.passwordLabel.setGeometry(QRect(60, 110, 81, 20))
        self.passwordLabel.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n' "color: rgb(255, 255, 255);"
        )
        self.usernameEntry = QLineEdit(self.loginWidget)
        self.usernameEntry.setObjectName("usernameEntry")
        self.usernameEntry.setGeometry(QRect(160, 70, 180, 20))
        self.usernameEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;\n"
            "padding:0px 10px;\n"
            ""
        )
        self.passwordEntry = QLineEdit(self.loginWidget)
        self.passwordEntry.setObjectName("passwordEntry")
        self.passwordEntry.setGeometry(QRect(160, 110, 180, 20))
        self.passwordEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;\n"
            "padding:0px 10px;\n"
            "\n"
            ""
        )
        self.passwordEntry.setEchoMode(QLineEdit.Password)
        self.loginButton = QPushButton(self.loginWidget)
        self.loginButton.setObjectName("loginButton")
        self.loginButton.setGeometry(QRect(260, 150, 80, 20))
        self.loginButton.setStyleSheet(
            "color: rgb(255,255,255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )
        self.invalidLabel = QLabel(self.loginWidget)
        self.invalidLabel.setObjectName("invalidLabel")
        self.invalidLabel.setGeometry(QRect(150, 180, 191, 20))
        self.invalidLabel.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(232, 35, 17);"
        )

        self.retranslateUi(Login)

        QMetaObject.connectSlotsByName(Login)

    # setupUi

    def retranslateUi(self, Login):
        Login.setWindowTitle(QCoreApplication.translate("Login", "Log in", None))
        self.usernameLabel.setText(QCoreApplication.translate("Login", "Username :", None))
        self.passwordLabel.setText(QCoreApplication.translate("Login", "Password  :", None))
        self.usernameEntry.setText("")
        self.usernameEntry.setPlaceholderText("")
        self.passwordEntry.setPlaceholderText("")
        self.loginButton.setText(QCoreApplication.translate("Login", "Log in", None))
        self.invalidLabel.setText("")

    # retranslateUi
