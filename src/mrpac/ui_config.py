# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Config.ui'
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
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class Ui_ConfigWindow(object):
    def setupUi(self, ConfigWindow):
        if not ConfigWindow.objectName():
            ConfigWindow.setObjectName("ConfigWindow")
        ConfigWindow.resize(400, 220)
        self.configWidget = QWidget(ConfigWindow)
        self.configWidget.setObjectName("configWidget")
        self.configWidget.setGeometry(QRect(0, 0, 400, 220))
        self.configWidget.setStyleSheet(
            "QWidget#configWidget{\n" "background-color: rgb(50, 51, 99);}"
        )
        self.selectClient = QGroupBox(self.configWidget)
        self.selectClient.setObjectName("selectClient")
        self.selectClient.setGeometry(QRect(50, 20, 281, 171))
        self.selectClient.setStyleSheet(
            "QWidget#selectClient{\n"
            "border:1px solid rgba(255, 255, 255,80);\n"
            "border-radius:10px;\n"
            "color:rgba(255, 255, 255,255);\n"
            "}"
        )
        self.startSCPButton_2 = QPushButton(self.selectClient)
        self.startSCPButton_2.setObjectName("startSCPButton_2")
        self.startSCPButton_2.setGeometry(QRect(30, 210, 75, 23))
        self.startSCPButton_2.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: rgb(88, 88, 88);"
        )
        self.stopSCPButton_2 = QPushButton(self.selectClient)
        self.stopSCPButton_2.setObjectName("stopSCPButton_2")
        self.stopSCPButton_2.setGeometry(QRect(180, 210, 75, 23))
        self.stopSCPButton_2.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: rgb(88, 88, 88);"
        )
        self.invalidLabel_3 = QLabel(self.selectClient)
        self.invalidLabel_3.setObjectName("invalidLabel_3")
        self.invalidLabel_3.setGeometry(QRect(70, 180, 191, 20))
        self.invalidLabel_3.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(232, 35, 17);"
        )
        self.listWidget = QListWidget(self.selectClient)
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setGeometry(QRect(10, 30, 171, 131))
        self.listWidget.setStyleSheet(
            "background-color: rgba(255, 255, 255,30);\n"
            "color:rgb(255, 255, 255);\n"
            "border-radius:10px;\n"
            "padding:10px 10px;"
        )
        self.addButton = QPushButton(self.selectClient)
        self.addButton.setObjectName("addButton")
        self.addButton.setGeometry(QRect(200, 30, 75, 23))
        self.addButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )
        self.removeButton = QPushButton(self.selectClient)
        self.removeButton.setObjectName("removeButton")
        self.removeButton.setGeometry(QRect(200, 67, 75, 23))
        self.removeButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color:#e57373;\n" "border-radius:6px;"
        )
        self.editButton = QPushButton(self.selectClient)
        self.editButton.setObjectName("editButton")
        self.editButton.setGeometry(QRect(200, 103, 75, 23))
        self.editButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: #648dae;\n" "border-radius:6px;"
        )
        self.selectButton = QPushButton(self.selectClient)
        self.selectButton.setObjectName("selectButton")
        self.selectButton.setGeometry(QRect(200, 138, 75, 23))
        self.selectButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )

        self.retranslateUi(ConfigWindow)

        QMetaObject.connectSlotsByName(ConfigWindow)

    # setupUi

    def retranslateUi(self, ConfigWindow):
        ConfigWindow.setWindowTitle(QCoreApplication.translate("ConfigWindow", "Config...", None))
        self.selectClient.setTitle(
            QCoreApplication.translate("ConfigWindow", "Select Client", None)
        )
        self.startSCPButton_2.setText(
            QCoreApplication.translate("ConfigWindow", "Start SCP", None)
        )
        self.stopSCPButton_2.setText(QCoreApplication.translate("ConfigWindow", "Stop SCP", None))
        self.invalidLabel_3.setText("")
        self.addButton.setText(QCoreApplication.translate("ConfigWindow", "Add", None))
        self.removeButton.setText(QCoreApplication.translate("ConfigWindow", "Remove", None))
        self.editButton.setText(QCoreApplication.translate("ConfigWindow", "Edit", None))
        self.selectButton.setText(QCoreApplication.translate("ConfigWindow", "Select", None))

    # retranslateUi
