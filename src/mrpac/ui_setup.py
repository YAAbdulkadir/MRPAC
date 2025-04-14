# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Setup.ui'
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
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QWidget,
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 400)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.setupWidget = QWidget(self.centralwidget)
        self.setupWidget.setObjectName("setupWidget")
        self.setupWidget.setGeometry(QRect(0, 0, 600, 400))
        self.setupWidget.setStyleSheet(
            "QWidget#setupWidget{\n" "background-color: rgb(50, 51, 99);}"
        )
        self.setupButton = QToolButton(self.setupWidget)
        self.setupButton.setObjectName("setupButton")
        self.setupButton.setGeometry(QRect(0, 0, 61, 21))
        self.runButton = QToolButton(self.setupWidget)
        self.runButton.setObjectName("runButton")
        self.runButton.setGeometry(QRect(60, 0, 61, 21))
        self.usersButton = QToolButton(self.setupWidget)
        self.usersButton.setObjectName("usersButton")
        self.usersButton.setGeometry(QRect(120, 0, 61, 21))
        self.scpDetails = QGroupBox(self.setupWidget)
        self.scpDetails.setObjectName("scpDetails")
        self.scpDetails.setGeometry(QRect(10, 30, 281, 241))
        self.scpDetails.setStyleSheet(
            "QWidget#scpDetails{\n"
            "border:1px solid rgba(255, 255, 255,80);\n"
            "border-radius:10px;\n"
            "color:rgba(255, 255, 255,255);\n"
            "}"
        )
        self.scpAETLabel = QLabel(self.scpDetails)
        self.scpAETLabel.setObjectName("scpAETLabel")
        self.scpAETLabel.setGeometry(QRect(20, 50, 71, 21))
        self.scpAETLabel.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.scpAETEntry = QLineEdit(self.scpDetails)
        self.scpAETEntry.setObjectName("scpAETEntry")
        self.scpAETEntry.setGeometry(QRect(100, 50, 160, 20))
        self.scpAETEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.scpPortLabel = QLabel(self.scpDetails)
        self.scpPortLabel.setObjectName("scpPortLabel")
        self.scpPortLabel.setGeometry(QRect(20, 90, 61, 21))
        self.scpPortLabel.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.scpPortEntry = QLineEdit(self.scpDetails)
        self.scpPortEntry.setObjectName("scpPortEntry")
        self.scpPortEntry.setGeometry(QRect(100, 90, 160, 20))
        self.scpPortEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.saveButton = QPushButton(self.scpDetails)
        self.saveButton.setObjectName("saveButton")
        self.saveButton.setGeometry(QRect(180, 130, 80, 20))
        self.saveButton.setStyleSheet(
            "color: rgb(255,255,255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )
        self.startSCPButton = QPushButton(self.scpDetails)
        self.startSCPButton.setObjectName("startSCPButton")
        self.startSCPButton.setGeometry(QRect(20, 210, 80, 20))
        font = QFont()
        font.setBold(False)
        self.startSCPButton.setFont(font)
        self.startSCPButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color:#388e3c;\n" "border-radius:6px;"
        )
        self.stopSCPButton = QPushButton(self.scpDetails)
        self.stopSCPButton.setObjectName("stopSCPButton")
        self.stopSCPButton.setGeometry(QRect(180, 210, 80, 20))
        self.stopSCPButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color:#e57373;\n" "border-radius:6px;"
        )
        self.invalidLabel = QLabel(self.scpDetails)
        self.invalidLabel.setObjectName("invalidLabel")
        self.invalidLabel.setGeometry(QRect(70, 170, 191, 20))
        self.invalidLabel.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(232, 35, 17);"
        )
        self.scpStatus = QGroupBox(self.setupWidget)
        self.scpStatus.setObjectName("scpStatus")
        self.scpStatus.setGeometry(QRect(10, 290, 281, 101))
        self.scpStatus.setStyleSheet(
            "QWidget#scpStatus{\n"
            "border:1px solid rgba(255, 255, 255,80);\n"
            "border-radius:10px;\n"
            "color:rgba(255, 255, 255,255);\n"
            "}"
        )
        self.saveButton_2 = QPushButton(self.scpStatus)
        self.saveButton_2.setObjectName("saveButton_2")
        self.saveButton_2.setGeometry(QRect(196, 140, 75, 23))
        self.saveButton_2.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: rgb(88, 88, 88);"
        )
        self.startSCPButton_2 = QPushButton(self.scpStatus)
        self.startSCPButton_2.setObjectName("startSCPButton_2")
        self.startSCPButton_2.setGeometry(QRect(30, 210, 75, 23))
        self.startSCPButton_2.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: rgb(88, 88, 88);"
        )
        self.stopSCPButton_2 = QPushButton(self.scpStatus)
        self.stopSCPButton_2.setObjectName("stopSCPButton_2")
        self.stopSCPButton_2.setGeometry(QRect(180, 210, 75, 23))
        self.stopSCPButton_2.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: rgb(88, 88, 88);"
        )
        self.invalidLabel_3 = QLabel(self.scpStatus)
        self.invalidLabel_3.setObjectName("invalidLabel_3")
        self.invalidLabel_3.setGeometry(QRect(70, 180, 191, 20))
        self.invalidLabel_3.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(232, 35, 17);"
        )
        self.cstoreAETLabel = QLabel(self.scpStatus)
        self.cstoreAETLabel.setObjectName("cstoreAETLabel")
        self.cstoreAETLabel.setGeometry(QRect(30, 20, 111, 21))
        self.cstoreAETLabel.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.cstorePortLabel = QLabel(self.scpStatus)
        self.cstorePortLabel.setObjectName("cstorePortLabel")
        self.cstorePortLabel.setGeometry(QRect(30, 40, 111, 21))
        self.cstorePortLabel.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.cstoreAETEntry = QLabel(self.scpStatus)
        self.cstoreAETEntry.setObjectName("cstoreAETEntry")
        self.cstoreAETEntry.setGeometry(QRect(170, 20, 111, 21))
        self.cstoreAETEntry.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.cstorePortEntry = QLabel(self.scpStatus)
        self.cstorePortEntry.setObjectName("cstorePortEntry")
        self.cstorePortEntry.setGeometry(QRect(170, 40, 111, 21))
        self.cstorePortEntry.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.statusLabel = QLabel(self.scpStatus)
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setGeometry(QRect(100, 0, 47, 13))
        self.statusLabel.setStyleSheet(
            "color: rgb(255, 255, 255);\n" 'font: 10pt "MS Shell Dlg 2";'
        )
        self.serverDetails = QGroupBox(self.setupWidget)
        self.serverDetails.setObjectName("serverDetails")
        self.serverDetails.setGeometry(QRect(309, 30, 281, 241))
        self.serverDetails.setStyleSheet(
            "QWidget#serverDetails{\n"
            "border:1px solid rgba(255, 255, 255,80);\n"
            "border-radius:10px;\n"
            "color:rgba(255, 255, 255,255);\n"
            "}"
        )
        self.serverAETLabel = QLabel(self.serverDetails)
        self.serverAETLabel.setObjectName("serverAETLabel")
        self.serverAETLabel.setGeometry(QRect(30, 50, 41, 21))
        self.serverAETLabel.setStyleSheet(
            'font: 11pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.serverIPLabel = QLabel(self.serverDetails)
        self.serverIPLabel.setObjectName("serverIPLabel")
        self.serverIPLabel.setGeometry(QRect(30, 90, 31, 21))
        self.serverIPLabel.setStyleSheet(
            'font: 11pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.serverPortLabel = QLabel(self.serverDetails)
        self.serverPortLabel.setObjectName("serverPortLabel")
        self.serverPortLabel.setGeometry(QRect(30, 130, 51, 21))
        self.serverPortLabel.setStyleSheet(
            'font: 11pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.configButton = QPushButton(self.serverDetails)
        self.configButton.setObjectName("configButton")
        self.configButton.setGeometry(QRect(190, 170, 80, 20))
        self.configButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )
        self.currentServerAET = QLabel(self.serverDetails)
        self.currentServerAET.setObjectName("currentServerAET")
        self.currentServerAET.setGeometry(QRect(110, 50, 160, 20))
        self.currentServerAET.setStyleSheet(
            'font: 12pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.currentServerIP = QLabel(self.serverDetails)
        self.currentServerIP.setObjectName("currentServerIP")
        self.currentServerIP.setGeometry(QRect(110, 90, 160, 20))
        self.currentServerIP.setStyleSheet(
            'font: 12pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.currentServerPort = QLabel(self.serverDetails)
        self.currentServerPort.setObjectName("currentServerPort")
        self.currentServerPort.setGeometry(QRect(110, 130, 160, 20))
        self.currentServerPort.setStyleSheet(
            'font: 12pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.verifyConButton = QPushButton(self.serverDetails)
        self.verifyConButton.setObjectName("verifyConButton")
        self.verifyConButton.setGeometry(QRect(90, 210, 111, 23))
        self.verifyConButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: #648dae;\n" "border-radius:6px;"
        )
        self.contouringStatus = QLabel(self.setupWidget)
        self.contouringStatus.setObjectName("contouringStatus")
        self.contouringStatus.setGeometry(QRect(320, 330, 261, 20))
        self.contouringStatus.setStyleSheet(
            'font: 10pt "Times New Roman";\n' "color: rgb(255,255,255);"
        )
        self.contouringStatus.setAlignment(Qt.AlignCenter)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MRPAC", None))
        self.setupButton.setText(QCoreApplication.translate("MainWindow", "Setup", None))
        self.runButton.setText(QCoreApplication.translate("MainWindow", "Run", None))
        self.usersButton.setText(QCoreApplication.translate("MainWindow", "Users", None))
        self.scpDetails.setTitle(QCoreApplication.translate("MainWindow", "SCP Details", None))
        self.scpAETLabel.setText(QCoreApplication.translate("MainWindow", "SCP AET :", None))
        self.scpPortLabel.setText(QCoreApplication.translate("MainWindow", "PORT :", None))
        self.saveButton.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.startSCPButton.setText(QCoreApplication.translate("MainWindow", "Start SCP", None))
        self.stopSCPButton.setText(QCoreApplication.translate("MainWindow", "Stop SCP", None))
        self.invalidLabel.setText("")
        self.scpStatus.setTitle(QCoreApplication.translate("MainWindow", "SCP Status", None))
        self.saveButton_2.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.startSCPButton_2.setText(QCoreApplication.translate("MainWindow", "Start SCP", None))
        self.stopSCPButton_2.setText(QCoreApplication.translate("MainWindow", "Stop SCP", None))
        self.invalidLabel_3.setText("")
        self.cstoreAETLabel.setText("")
        self.cstorePortLabel.setText("")
        self.cstoreAETEntry.setText("")
        self.cstorePortEntry.setText("")
        self.statusLabel.setText(QCoreApplication.translate("MainWindow", "Inactive", None))
        self.serverDetails.setTitle(
            QCoreApplication.translate("MainWindow", "Server Details", None)
        )
        self.serverAETLabel.setText(QCoreApplication.translate("MainWindow", "AET :", None))
        self.serverIPLabel.setText(QCoreApplication.translate("MainWindow", "IP :", None))
        self.serverPortLabel.setText(QCoreApplication.translate("MainWindow", "PORT :", None))
        self.configButton.setText(QCoreApplication.translate("MainWindow", "Config...", None))
        self.currentServerAET.setText("")
        self.currentServerIP.setText("")
        self.currentServerPort.setText("")
        self.verifyConButton.setText(
            QCoreApplication.translate("MainWindow", "Verify connection", None)
        )
        self.contouringStatus.setText("")

    # retranslateUi
