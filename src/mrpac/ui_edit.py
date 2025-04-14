# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Edit.ui'
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
    QPushButton,
    QSizePolicy,
    QWidget,
)


class Ui_Edit(object):
    def setupUi(self, Edit):
        if not Edit.objectName():
            Edit.setObjectName("Edit")
        Edit.resize(400, 300)
        self.editWidget = QWidget(Edit)
        self.editWidget.setObjectName("editWidget")
        self.editWidget.setGeometry(QRect(0, 0, 400, 300))
        self.editWidget.setStyleSheet(
            "QWidget#editWidget{\n" "background-color: rgb(50, 51, 99);}"
        )
        self.serverDetails = QGroupBox(self.editWidget)
        self.serverDetails.setObjectName("serverDetails")
        self.serverDetails.setGeometry(QRect(60, 20, 280, 260))
        self.serverDetails.setStyleSheet(
            "QWidget#serverDetails{\n"
            "border:1px solid rgba(255, 255, 255,80);\n"
            "border-radius:10px;\n"
            "color:rgba(255, 255, 255,255);}"
        )
        self.serverAETLabel = QLabel(self.serverDetails)
        self.serverAETLabel.setObjectName("serverAETLabel")
        self.serverAETLabel.setGeometry(QRect(30, 50, 91, 21))
        self.serverAETLabel.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.serverIPLabel = QLabel(self.serverDetails)
        self.serverIPLabel.setObjectName("serverIPLabel")
        self.serverIPLabel.setGeometry(QRect(30, 90, 91, 21))
        self.serverIPLabel.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.serverPortLabel = QLabel(self.serverDetails)
        self.serverPortLabel.setObjectName("serverPortLabel")
        self.serverPortLabel.setGeometry(QRect(30, 130, 91, 21))
        self.serverPortLabel.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(255, 255, 255);"
        )
        self.cancelButton = QPushButton(self.serverDetails)
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setGeometry(QRect(186, 230, 75, 20))
        self.cancelButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color:#e57373;\n" "border-radius:6px;"
        )
        self.serverAETEntry = QLineEdit(self.serverDetails)
        self.serverAETEntry.setObjectName("serverAETEntry")
        self.serverAETEntry.setGeometry(QRect(110, 50, 151, 20))
        self.serverAETEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.serverIPEntry = QLineEdit(self.serverDetails)
        self.serverIPEntry.setObjectName("serverIPEntry")
        self.serverIPEntry.setGeometry(QRect(110, 90, 151, 20))
        self.serverIPEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.serverPortEntry = QLineEdit(self.serverDetails)
        self.serverPortEntry.setObjectName("serverPortEntry")
        self.serverPortEntry.setGeometry(QRect(110, 130, 151, 20))
        self.serverPortEntry.setStyleSheet(
            'font: 10pt "MS Shell Dlg 2";\n'
            "color: rgb(255, 255, 255);\n"
            "background-color: rgba(255, 255, 255,30);\n"
            "border: 1px;\n"
            "border-radius:6px;"
        )
        self.updateButton = QPushButton(self.serverDetails)
        self.updateButton.setObjectName("updateButton")
        self.updateButton.setGeometry(QRect(90, 230, 75, 20))
        self.updateButton.setStyleSheet(
            "color: rgb(255,255,255);\n"
            "background-color: rgb(96, 99, 255);\n"
            "border-radius:6px;"
        )
        self.verifyConButton = QPushButton(self.serverDetails)
        self.verifyConButton.setObjectName("verifyConButton")
        self.verifyConButton.setGeometry(QRect(160, 160, 101, 23))
        self.verifyConButton.setStyleSheet(
            "color: rgb(255, 255, 255);\n" "background-color: #648dae;\n" "border-radius:6px;"
        )
        self.invalidLabel = QLabel(self.serverDetails)
        self.invalidLabel.setObjectName("invalidLabel")
        self.invalidLabel.setGeometry(QRect(80, 190, 191, 20))
        self.invalidLabel.setStyleSheet(
            'font: 12pt "Times New Roman";\n' "color: rgb(232, 35, 17);"
        )

        self.retranslateUi(Edit)

        QMetaObject.connectSlotsByName(Edit)

    # setupUi

    def retranslateUi(self, Edit):
        Edit.setWindowTitle(QCoreApplication.translate("Edit", "Edit", None))
        self.serverDetails.setTitle(QCoreApplication.translate("Edit", "Server Details", None))
        self.serverAETLabel.setText(QCoreApplication.translate("Edit", "AET :", None))
        self.serverIPLabel.setText(QCoreApplication.translate("Edit", "IP :", None))
        self.serverPortLabel.setText(QCoreApplication.translate("Edit", "PORT :", None))
        self.cancelButton.setText(QCoreApplication.translate("Edit", "Cancel", None))
        self.updateButton.setText(QCoreApplication.translate("Edit", "Update", None))
        self.verifyConButton.setText(QCoreApplication.translate("Edit", "Verify connection", None))
        self.invalidLabel.setText("")

    # retranslateUi
