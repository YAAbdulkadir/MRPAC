from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from .ui_verify import Ui_Verification


class VerifyWindow(qtw.QWidget, Ui_Verification):
    """The window with status of the verification requests."""

    def __init__(self, pingResult: str, echoResult: str) -> None:
        """Initialize the verify window.

        Parameters
        ----------
        pingResult : str
            The result of the ping test.
        echoResult : str
            The result of the DICOM C-Echo test.
        """

        super().__init__()
        self.setupUi(self)
        self.setFixedHeight(100)
        self.setFixedWidth(200)
        if pingResult == "Success":
            self.pingStatus.setText(pingResult)
            self.pingStatus.setStyleSheet("color: rgb(100, 255, 100);font: 10pt MS Shell Dlg 2")
        else:
            self.pingStatus.setText(pingResult)
            self.pingStatus.setStyleSheet("color: rgb(232, 35, 17);font: 10pt MS Shell Dlg 2")

        if echoResult == "0000":
            self.echoStatus.setText("Success")
            self.echoStatus.setStyleSheet("color: rgb(100, 255, 100);font: 10pt MS Shell Dlg 2")
        else:
            self.echoStatus.setText("Failed")
            self.echoStatus.setStyleSheet("color: rgb(232, 35, 17);font: 10pt MS Shell Dlg 2")

        self.show()
