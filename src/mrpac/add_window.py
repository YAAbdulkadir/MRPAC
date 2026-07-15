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


class ConnectionVerificationWorker(qtc.QObject):
    """Run ping and DICOM C-ECHO without blocking the Qt interface."""

    finished = qtc.Signal(str, str)

    def __init__(
        self,
        scp_aet: str,
        server_aet: str,
        server_ip: str,
        server_port: int,
    ) -> None:
        super().__init__()
        self.scp_aet = scp_aet
        self.server_aet = server_aet
        self.server_ip = server_ip
        self.server_port = server_port

    def _log_failure(self, message: str) -> None:
        """Log a verification failure without stopping the worker."""

        pynet_logger.error(message)
        pynet_logger.debug(message, exc_info=True)

        try:
            Globals.log_to_db("network", "ERROR", message, None)
        except Exception:
            pynet_logger.debug(
                "Could not write verification failure to the database.",
                exc_info=True,
            )

    @qtc.Slot()
    def run(self) -> None:
        """Perform the blocking network checks in a background thread."""

        ping_result = "Failed"
        echo_result = "Failed"

        try:
            ping_result = pingTest(self.server_ip)
        except Exception as error:
            msg = f"ADD--Ping Test Error: {error}"
            self._log_failure(msg)

        try:
            echo_result = verifyEcho(
                self.scp_aet,
                self.server_aet,
                self.server_ip,
                self.server_port,
            )
        except Exception as error:
            msg = f"ADD--C-Echo Test Error: {error}"
            self._log_failure(msg)

        self.finished.emit(ping_result, echo_result)


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

        self._verify_thread = None
        self._verify_worker = None
        self._verify_button_text = self.verifyConButton.text()

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
        """Verify ping and DICOM connectivity without blocking the UI."""

        if self._verify_thread is not None and self._verify_thread.isRunning():
            return

        server_aet = self.serverAETEntry.text().strip()
        server_ip = self.serverIPEntry.text().strip()
        server_port_text = self.serverPortEntry.text().strip()

        if not server_aet or not server_ip or not server_port_text:
            self.invalidLabel.setText("Fields cannot be empty.")
            msg = "ADD--Server Details: Fields cannot be empty."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(server_aet, "AET"):
            self.invalidLabel.setText("Invalid AET")
            msg = "ADD--Server Details: Invalid AE Title."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(server_ip, "IP"):
            self.invalidLabel.setText("Invalid IP")
            msg = "ADD--Server Details: Invalid IP address."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        if not validEntry(server_port_text, "Port"):
            self.invalidLabel.setText("Invalid port")
            msg = "ADD--Server Details: Invalid port number."
            mrpac_logger.error(msg)
            Globals.log_to_db("database", "ERROR", msg, None)
            return

        try:
            server_port = int(server_port_text)
        except ValueError:
            self.invalidLabel.setText("Invalid port")
            return

        scp_aet = getattr(Globals, "scpAET", "") or "MRPAC"

        self.invalidLabel.setText("")
        self.verifyConButton.setEnabled(False)
        self.verifyConButton.setText("Verifying...")

        self._verify_thread = qtc.QThread(self)
        self._verify_worker = ConnectionVerificationWorker(
            scp_aet,
            server_aet,
            server_ip,
            server_port,
        )
        self._verify_worker.moveToThread(self._verify_thread)

        self._verify_thread.started.connect(self._verify_worker.run)
        self._verify_worker.finished.connect(self._verificationFinished)
        self._verify_worker.finished.connect(self._verify_thread.quit)
        self._verify_worker.finished.connect(self._verify_worker.deleteLater)
        self._verify_thread.finished.connect(self._verificationThreadFinished)
        self._verify_thread.finished.connect(self._verify_thread.deleteLater)

        self._verify_thread.start()

    @qtc.Slot(str, str)
    def _verificationFinished(
        self,
        ping_result: str,
        echo_result: str,
    ) -> None:
        """Display the verification results."""

        try:
            self.verify = VerifyWindow(ping_result, echo_result)
        finally:
            self.verifyConButton.setEnabled(True)
            self.verifyConButton.setText(self._verify_button_text)

    @qtc.Slot()
    def _verificationThreadFinished(self) -> None:
        """Release references to a completed verification thread."""

        self._verify_worker = None
        self._verify_thread = None
