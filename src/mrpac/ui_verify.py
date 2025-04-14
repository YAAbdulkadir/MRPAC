# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Verify.ui'
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
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy, QWidget


class Ui_Verification(object):
    def setupUi(self, Verification):
        if not Verification.objectName():
            Verification.setObjectName("Verification")
        Verification.resize(200, 100)
        self.verificationWidget = QWidget(Verification)
        self.verificationWidget.setObjectName("verificationWidget")
        self.verificationWidget.setGeometry(QRect(0, 0, 200, 100))
        self.verificationWidget.setStyleSheet(
            "QWidget#verificationWidget{\n" "background-color: rgb(50, 51, 99);}"
        )
        self.pingLabel = QLabel(self.verificationWidget)
        self.pingLabel.setObjectName("pingLabel")
        self.pingLabel.setGeometry(QRect(40, 30, 41, 20))
        self.pingLabel.setStyleSheet('font: 10pt "MS Shell Dlg 2";\n' "color: rgb(255, 255, 255);")
        self.echoLabel = QLabel(self.verificationWidget)
        self.echoLabel.setObjectName("echoLabel")
        self.echoLabel.setGeometry(QRect(40, 60, 41, 20))
        self.echoLabel.setStyleSheet('font: 10pt "MS Shell Dlg 2";\n' "color: rgb(255, 255, 255);")
        self.loginButton = QPushButton(self.verificationWidget)
        self.loginButton.setObjectName("loginButton")
        self.loginButton.setGeometry(QRect(110, 150, 80, 20))
        self.loginButton.setStyleSheet(
            "color: rgb(255,255,255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )
        self.pingStatus = QLabel(self.verificationWidget)
        self.pingStatus.setObjectName("pingStatus")
        self.pingStatus.setGeometry(QRect(100, 30, 61, 20))
        self.pingStatus.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n' "color: rgb(255, 255, 255);"
        )
        self.echoStatus = QLabel(self.verificationWidget)
        self.echoStatus.setObjectName("echoStatus")
        self.echoStatus.setGeometry(QRect(100, 60, 61, 20))
        self.echoStatus.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n' "color: rgb(255, 255, 255);"
        )

        self.retranslateUi(Verification)

        QMetaObject.connectSlotsByName(Verification)

    # setupUi

    def retranslateUi(self, Verification):
        Verification.setWindowTitle(
            QCoreApplication.translate("Verification", "Network verification", None)
        )
        self.pingLabel.setText(QCoreApplication.translate("Verification", "Ping :", None))
        self.echoLabel.setText(QCoreApplication.translate("Verification", "Echo  :", None))
        self.loginButton.setText(QCoreApplication.translate("Verification", "OK", None))
        self.pingStatus.setText("")
        self.echoStatus.setText("")

    # retranslateUi
