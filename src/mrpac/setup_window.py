import os
import logging
import threading
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ._globals import Globals
from .DICOM_Networking import (
    StorageSCP,
    pingTest,
    validEntry,
    verifyEcho,
    handle_open,
    handle_store,
    handle_close,
    process_dicom,
)
from .ui_setup import Ui_MainWindow
from .config_window import ConfigWindow
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

    @qtc.Slot()
    def run(self) -> None:
        """Perform the blocking network checks in a background thread."""

        ping_result = "Failed"
        echo_result = "Failed"

        try:
            ping_result = pingTest(self.server_ip)
        except Exception:
            pynet_logger.debug(
                "Ping verification failed for %s",
                self.server_ip,
                exc_info=True,
            )

        try:
            echo_result = verifyEcho(
                self.scp_aet,
                self.server_aet,
                self.server_ip,
                self.server_port,
            )
        except Exception:
            pynet_logger.debug(
                "DICOM verification failed for %s:%s",
                self.server_ip,
                self.server_port,
                exc_info=True,
            )

        self.finished.emit(ping_result, echo_result)


class SetupWindow(qtw.QMainWindow, Ui_MainWindow):
    """The setup window configuration."""

    def __init__(self):
        """Initialize the setup window when login is successful."""

        super().__init__()
        self.setupUi(self)
        self.setFixedHeight(400)
        self.setFixedWidth(600)
        self.show()

        self.startSCPButton.clicked.connect(self.startSCPFunc)
        self.stopSCPButton.clicked.connect(self.stopSCPFunc)
        self.saveButton.clicked.connect(self.saveFunc)
        self.configButton.clicked.connect(self.configFunc)
        self.verifyConButton.clicked.connect(self.verifyConFunc)

        self.scp_server = None
        self.workers = []

        # Background ping/C-ECHO verification objects
        self._verify_thread = None
        self._verify_worker = None
        self._verify_button_text = self.verifyConButton.text()

        self.startUp()

    def startUp(self):
        """Populates the SCP details if saved before."""
        query = "SELECT * FROM host"
        conn, cursor = Globals.get_db_connection()

        try:
            cursor.execute(query)
            host_info = cursor.fetchone()
            if host_info:
                self.scpAETEntry.setText(host_info[1])
                self.scpPortEntry.setText(host_info[3])
        except Exception as e:
            error = f"Error retrieving SCP details: {e}"
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()

    def worker(self):
        """Thread worker function to process DICOMs from the queue."""
        while True:
            event = Globals.dicom_queue.get()
            if event is None:
                break
            process_dicom(event)
            Globals.dicom_queue.task_done()

    def startSCPFunc(self):
        """Start the DICOM SCP server to accept C-Move requests."""

        Globals.scpAET = self.scpAETEntry.text()
        Globals.scpPort = self.scpPortEntry.text()

        if not Globals.scpAET or not Globals.scpPort:
            self.invalidLabel.setText("Fields cannot be empty")
            mrpac_logger.error("SETUP--SCP Details: The AE title and port fields cannot be empty.")
            return
        elif not validEntry(Globals.scpAET, "AET"):
            self.invalidLabel.setText("Invalid AE Title")
            mrpac_logger.error("SETUP--SCP Details: Invalid AE Title.")
            return
        elif not validEntry(Globals.scpPort, "Port"):
            self.invalidLabel.setText("Invalid port number")
            mrpac_logger.error("SETUP--SCP Details: Invalid port number.")
            return

        try:
            Globals.scpPort = int(Globals.scpPort)
        except ValueError:
            self.invalidLabel.setText("Invalid port number")
            mrpac_logger.error("SETUP--SCP Details: Invalid port number.")
            return

        try:
            # Create the SCP server
            self.scp_server = StorageSCP(Globals.scpAET, Globals.HOSTIP, Globals.scpPort)
            self.scp_server.set_handlers(
                handle_open=handle_open,
                handle_close=handle_close,
                handle_store=handle_store,
            )

            # Start worker threads
            num_workers = os.cpu_count()
            for _ in range(num_workers):
                t = threading.Thread(target=self.worker, daemon=True)
                t.start()
                self.workers.append(t)

            # Start the server
            self.scp_server.start()

            # Update UI to reflect active status
            self.invalidLabel.setText("")
            self.statusLabel.setText("Active")
            self.statusLabel.setStyleSheet("color: rgb(100, 255, 100);font: 10pt MS Shell Dlg 2")
            self.cstoreAETLabel.setText("DICOM Store AET:")
            self.cstoreAETEntry.setText(Globals.scpAET)
            self.cstorePortLabel.setText("Port:")
            self.cstorePortEntry.setText(str(Globals.scpPort))

        except Exception as e:
            mrpac_logger.error(f"Error starting SCP: {e}")
            mrpac_logger.debug(f"Error starting SCP: {e}", exc_info=True)

    def stopSCPFunc(self):
        """Stop the DICOM SCP server if it was running."""

        if self.scp_server:
            self.scp_server.stop()
            self.scp_server = None

            # Update UI to reflect inactive status
            self.statusLabel.setText("Inactive")
            self.statusLabel.setStyleSheet("color: rgb(255, 255, 255);font: 10pt MS Shell Dlg 2")
            self.cstoreAETLabel.setText("")
            self.cstoreAETEntry.setText("")
            self.cstorePortLabel.setText("")
            self.cstorePortEntry.setText("")

            # Gracefully stop worker threads
            for _ in range(len(self.workers)):  # Send termination signals
                Globals.dicom_queue.put(None)

            for t in self.workers:
                t.join()

        else:
            self.invalidLabel.setText("SCP is already inactive")
            mrpac_logger.error("SCP is inactive")

    def saveFunc(self):
        """Save the SCP Details."""

        scpAET = self.scpAETEntry.text()
        scpPort = self.scpPortEntry.text()

        if not scpAET or not scpPort:
            error = "SETUP--SCP Details: AE title and port fields cannot be empty."
            self.invalidLabel.setText("Fields cannot be empty")
            mrpac_logger.error(error)
            Globals.log_to_db("mrpac", "ERROR", error, None)
            return

        if not validEntry(scpAET, "AET"):
            error = "SETUP--SCP Details: Invalid AE Title."
            self.invalidLabel.setText("Invalid AE Title")
            mrpac_logger.error(error)
            Globals.log_to_db("mrpac", "ERROR", error, None)
            return

        if not validEntry(scpPort, "Port"):
            error = "SETUP--SCP Details: Invalid port number"
            mrpac_logger.error(error)
            Globals.log_to_db("mrpac", "ERROR", error, None)
            return

        try:
            scpPort = int(scpPort)
        except ValueError:
            error = "SETUP--SCP Details: Port must be a number."
            self.invalidLabel.setText("Invalid port number")
            mrpac_logger.error(error)
            Globals.log_to_db("mrpac", "ERROR", error, None)
            return

        conn, cursor = Globals.get_db_connection()

        try:
            query = "SELECT * FROM host"
            cursor.execute(query)
            savedEntry = cursor.fetchone()

            if savedEntry is None:
                query = "INSERT INTO host (hostAET, hostIP, hostPort) VALUES (?, ?, ?)"
                cursor.execute(query, (scpAET, Globals.HOSTIP or "127.0.0.1", scpPort))
                conn.commit()
            else:
                query = "UPDATE host SET hostAET = ?, hostIP = ?, hostPort = ? WHERE id = 1"
                cursor.execute(query, (scpAET, Globals.HOSTIP or "127.0.0.1", scpPort))
                conn.commit()

            msg = "SETUP--SCP Details: Successfully saved."
            self.invalidLabel.setText("SCP Details saved successfully")
            mrpac_logger.info(msg)
            Globals.log_to_db("mrpac", "INFO", msg, None)

        except Exception as e:
            error = f"SETUP--SCP Database Error: {e}"
            self.invalidLabel.setText("Failed to save SCP details")
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()

    def configFunc(self):
        """Start the configuration window."""
        Globals.config_screen = ConfigWindow()

    def verifyConFunc(self):
        """Verify ping and DICOM connectivity without blocking the UI."""

        # Prevent multiple simultaneous verification threads
        if self._verify_thread is not None and self._verify_thread.isRunning():
            return

        server_aet = self.currentServerAET.text().strip()
        server_ip = self.currentServerIP.text().strip()
        server_port_text = self.currentServerPort.text().strip()

        if not server_aet or not server_ip or not server_port_text:
            self.invalidLabel.setText("Server fields cannot be empty")
            return

        try:
            server_port = int(server_port_text)
        except ValueError:
            self.invalidLabel.setText("Invalid server port")
            return

        # Use the active SCP AET when available. Otherwise, use the entry field.
        scp_aet = getattr(Globals, "scpAET", "") or self.scpAETEntry.text().strip() or "MRPAC"

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
        """Display results after the background checks complete."""

        self.verify = VerifyWindow(ping_result, echo_result)

        self.verifyConButton.setEnabled(True)
        self.verifyConButton.setText(self._verify_button_text)

    @qtc.Slot()
    def _verificationThreadFinished(self) -> None:
        """Release references to the completed verification thread."""

        self._verify_worker = None
        self._verify_thread = None

    def serverSelected(self):
        """Select a DICOM location to send RTstruct file."""

        serverAET = Globals.selected_server[1]
        serverIP = Globals.selected_server[2]
        serverPort = Globals.selected_server[3]
        try:
            self.currentServerAET.setText(serverAET)
            self.currentServerIP.setText(serverIP)
            self.currentServerPort.setText(serverPort)
        except Exception as e:
            mrpac_logger.error(e)
            mrpac_logger.debug(e, exc_info=True)

    def closeEvent(self, event):
        """Log when window closes.

        Args:
            event (_type_): _description_
        """

        mrpac_logger.info("Closing MRPAC.")
        event.accept()
