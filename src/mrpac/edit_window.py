import logging

from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ._globals import Globals
from .DICOM_Networking import (
    pingTest,
    validEntry,
    verifyEcho,
)
from .ui_edit import Ui_Edit
from .verify_window import VerifyWindow

mrpac_logger = logging.getLogger("mrpac")
database_logger = logging.getLogger("database")
pynet_logger = logging.getLogger("network")


class EditWindow(qtw.QWidget, Ui_Edit):
    """The Edit window to modify DICOM location info."""

    def __init__(self):
        """Initialize the Edit window."""

        super().__init__()
        self.setupUi(self)
        self.setFixedHeight(300)
        self.setFixedWidth(400)
        self.updateButton.clicked.connect(self.updateFunc)
        self.cancelButton.clicked.connect(self.cancelFunc)
        self.verifyConButton.clicked.connect(self.verifyConFunc)

        self.startUp()

        self.show()

    def startUp(self):
        """Start the Edit window and show details of the DICOM location to be edited."""
        try:
            self.serverAETEntry.setText(Globals.selected_server[1])
            self.serverIPEntry.setText(Globals.selected_server[2])
            self.serverPortEntry.setText(Globals.selected_server[3])
        except Exception as e:
            msg = f"EDIT: Failed to populate EditWindow fields: {e}"
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)

    def updateFunc(self):
        """Update the DICOM location details with the new info."""

        serverAET = self.serverAETEntry.text()
        serverIP = self.serverIPEntry.text()
        serverPort = self.serverPortEntry.text()

        if not serverAET or not serverIP or not serverPort:
            msg = "EDIT--Server Details: Fields cannot be empty."
            self.invalidLabel.setText("Fields cannot be empty.")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverAET, "AET"):
            msg = "EDIT--Server Details: Invalid AE Title."
            self.invalidLabel.setText("Invalid AET")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverIP, "IP"):
            msg = "EDIT--Server Details: Invalid IP address."
            self.invalidLabel.setText("Invalid IP")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverPort, "Port"):
            msg = "EDIT--Server Details: Invalid port number."
            self.invalidLabel.setText("Invalid Port")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        conn, cursor = Globals.get_db_connection()
        try:
            query = "UPDATE servers SET serverAET = ?, serverIP = ?, serverPort = ? WHERE id = ?"
            cursor.execute(query, (serverAET, serverIP, serverPort, Globals.selected_server[0]))
            conn.commit()

            msg = f"EDIT--Server ID {Globals.selected_server[0]} updated successfully."
            mrpac_logger.info(msg)
            Globals.log_to_db("database", "INFO", msg, None)

            Globals.config_screen.startUp()
            self.close()

        except Exception as e:
            msg = f"EDIT--Database Error: {e}"
            self.invalidLabel.setText("Could not update server")
            database_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)

        finally:
            Globals.close_db_connection()

    def cancelFunc(self):
        """Close the Edit window."""

        self.close()

    def verifyConFunc(self):
        """Verify the DICOM connection using ping and C-Echo."""
        serverAET = self.serverAETEntry.text().strip()
        serverIP = self.serverIPEntry.text().strip()
        serverPort = self.serverPortEntry.text().strip()
        pingResult = None
        echoResult = None

        if not serverAET or not serverIP or not serverPort:
            msg = "VERIFY: Fields cannot be empty."
            self.invalidLabel.setText("Fields cannot be empty.")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverAET, "AET"):
            msg = "VERIFY: Invalid AE Title."
            self.invalidLabel.setText("Invalid AET")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverIP, "IP"):
            msg = "VERIFY: Invalid IP address."
            self.invalidLabel.setText("Invalid IP")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(serverPort, "Port"):
            msg = "VERIFY: Invalid port number."
            self.invalidLabel.setText("Invalid port")
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        try:
            pingResult = pingTest(serverIP)
        except Exception as e:
            pingResult = "Failed"
            error = f"VERIFY: Ping test failed: {e}"
            mrpac_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        try:
            echoResult = verifyEcho(Globals.scpAET, serverAET, serverIP, int(serverPort))
        except Exception as e:
            echoResult = "Failed"
            error = f"VERIFY: C-Echo failed: {e}"
            mrpac_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        self.verify = VerifyWindow(pingResult, echoResult)
