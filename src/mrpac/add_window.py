import logging
import sqlite3

from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ._globals import Globals
from .DICOM_Networking import (
    pingTest,
    validEntry,
    verifyEcho,
)
from .ui_add import Ui_AddWindow
from .verify_window import VerifyWindow

mrpac_logger = logging.getLogger("mrpac")
database_logger = logging.getLogger("database")
pynet_logger = logging.getLogger("network")


class AddWindow(qtw.QWidget, Ui_AddWindow):
    """The window to add new DICOM location."""

    def __init__(self):
        """Initialize the add window."""

        super().__init__()
        self.setupUi(self)
        self.setFixedHeight(300)
        self.setFixedWidth(400)
        self.addButton.clicked.connect(self.addFunc)
        self.cancelButton.clicked.connect(self.cancelFunc)
        self.verifyConButton.clicked.connect(self.verifyConFunc)

        self.show()

    def addFunc(self):
        """Add the new DICOM location when add button is clicked."""

        serverAET = self.serverAETEntry.text().strip()
        serverIP = self.serverIPEntry.text().strip()
        serverPort = self.serverPortEntry.text().strip()

        if not serverAET or not serverIP or not serverPort:
            self.invalidLabel.setText("Fields cannot be empty.")
            msg = "ADD--Server Details: Fields cannot be empty."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverAET, "AET"):
            self.invalidLabel.setText("Invalid AET")
            msg = "ADD--Server Details: Invalid AE Title."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverIP, "IP"):
            self.invalidLabel.setText("Invalid IP")
            msg = "ADD--Server Details: Invalid IP address."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverPort, "Port"):
            self.invalidLabel.setText("Invalid port")
            msg = "ADD--Server Details: Invalid port number."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        # Get a thread-local database connection
        conn, cursor = Globals.get_db_connection()

        try:
            query = "INSERT INTO servers (serverAET, serverIP, serverPort) VALUES (?, ?, ?)"
            cursor.execute(query, (serverAET, serverIP, serverPort))
            conn.commit()

            self.invalidLabel.setText("Server added successfully.")
            msg = f"ADD--Server Added: {serverAET} ({serverIP}:{serverPort})"
            mrpac_logger.info(msg)
            Globals.log_to_db("database", "INFO", msg, None)

            self.close()

        except sqlite3.Error as e:
            self.invalidLabel.setText("Could not add server.")
            error = f"ADD--Database Error: {e}"
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()

    def cancelFunc(self):
        """Close the Add window."""

        self.close()

    def verifyConFunc(self):
        """Send a C-Echo to verify DICOM connectivity."""

        serverAET = self.serverAETEntry.text().strip()
        serverIP = self.serverIPEntry.text().strip()
        serverPort = self.serverPortEntry.text().strip()
        pingResult = None
        echoResult = None

        if not serverAET or not serverIP or not serverPort:
            self.invalidLabel.setText("Fields cannot be empty.")
            msg = "ADD--Server Details: Fields cannot be empty."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverAET, "AET"):
            self.invalidLabel.setText("Invalid AET")
            msg = "ADD--Server Details: Invalid AE Title."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverIP, "IP"):
            self.invalidLabel.setText("Invalid IP")
            msg = "ADD--Server Details: Invalid IP address."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverPort, "Port"):
            self.invalidLabel.setText("Invalid port")
            msg = "ADD--Server Details: Invalid port number."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        try:
            pingResult = pingTest(serverIP)
        except Exception as e:
            pingResult = "Failed"
            error = f"ADD--Ping Test Error: {e}"
            mrpac_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        try:
            echoResult = verifyEcho(Globals.scpAET, serverAET, serverIP, int(serverPort))
        except Exception as e:
            echoResult = "Failed"
            error = f"ADD--C-Echo Test Error: {e}"
            mrpac_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        self.verify = VerifyWindow(pingResult, echoResult)
