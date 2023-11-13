import os
import sys
import shutil
import logging
import bcrypt
import datetime
import sqlite3
import socket

from DICOM_Networking import MoveSCP, StorageSCU, verifyEcho, validEntry, pingTest
from Autocontour import Autocontour
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.uic import loadUi


# Directory paths
PARENT_DIRECTORY = os.path.abspath((os.path.join(os.getcwd(), "..")))
UI_DIRECTORY = os.path.join(PARENT_DIRECTORY, "ui_files")
RESOURCES_DIRECTORY = os.path.join(PARENT_DIRECTORY, "resources")
LOGS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "logs")
TEMP_DIRECTORY = os.path.join(PARENT_DIRECTORY, "Temp")

# Get the IP address of this device
HOSTIP = socket.gethostbyname(socket.gethostname())
scpAET = None
scpPort = None

# Set global variables
current_user = None
user_type = None
selected_server = None
setup_screen = None
config_screen = None

current_dicom = None

# Set the log formatter
LOG_FORMATTER = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s:%(lineno)d")

# Initialize the Logger files
pynet_logger = logging.getLogger("network")
pynet_logger.setLevel(logging.DEBUG)
mrpac_logger = logging.getLogger("mrpac")
mrpac_logger.setLevel(logging.DEBUG)
autocontour_logger = logging.getLogger("autocontour")
autocontour_logger.setLevel(logging.DEBUG)
database_logger = logging.getLogger("database")
database_logger.setLevel(logging.DEBUG)
file_handler_pynet = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "network.log"))
file_handler_pynet.setFormatter(LOG_FORMATTER)
file_handler_mrpac = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "mrpac.log"))
file_handler_mrpac.setFormatter(LOG_FORMATTER)
file_handler_autocontour = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "autocontour.log"))
file_handler_autocontour.setFormatter(LOG_FORMATTER)
file_handler_database = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "database.log"))
file_handler_database.setFormatter(LOG_FORMATTER)
pynet_logger.addHandler(file_handler_pynet)
mrpac_logger.addHandler(file_handler_mrpac)
autocontour_logger.addHandler(file_handler_autocontour)
database_logger.addHandler(file_handler_database)


# Initiate the database connection
try:
    db_path = os.path.join(RESOURCES_DIRECTORY, "entries.db")
    con = sqlite3.connect(db_path, check_same_thread=False)
    cur = con.cursor()

except Exception as e:
    database_logger.error(e)
    database_logger.debug(e, exc_info=True)


def databaseSetup():
    """Sets up the database and creates neccesary tables if they are not created already."""

    createHostTable = 'CREATE TABLE "host" \
                        ("id" INTEGER, \
                         "hostAET" TEXT, \
                         "hostIP" TEXT, \
                         "hostPort" TEXT, \
                         PRIMARY KEY("id" AUTOINCREMENT))'
    createServersTable = 'CREATE TABLE "servers" \
                          ("id" INTEGER, \
                           "serverAET" TEXT, \
                           "serverIP" TEXT, \
                           "serverPort" TEXT, \
                           PRIMARY KEY("id" AUTOINCREMENT))'
    createUsersTable = 'CREATE TABLE "users" \
                        ("id" INTEGER, \
                         "userName" TEXT, \
                         "passPhrase" TEXT, \
                         "userType" TEXT, \
                         PRIMARY KEY("id" AUTOINCREMENT))'
    createHistoryTable = 'CREATE TABLE "history" \
                          ("id" INTEGER, \
                           "patientName" TEXT, \
                           "patientID" TEXT, \
                           "time" TEXT, \
                           "status" TEXT, \
                           "errors", \
                           PRIMARY KEY("id" AUTOINCREMENT))'

    try:
        cur.execute(createHostTable)
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute(createServersTable)
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute(createUsersTable)
        con.commit()
        query = "INSERT INTO users (userName, passPhrase, userType) VALUES (?, ?, ?)"
        passPhrase = bcrypt.hashpw(b"mrpac", bcrypt.gensalt()).decode()
        cur.execute(query, ("Admin", passPhrase, "Administrator"))
        con.commit()

    except sqlite3.OperationalError:
        pass

    try:
        cur.execute(createHistoryTable)
        con.commit()
    except sqlite3.OperationalError:
        pass


def send_c_store(recAET, recIP, recPort, struct_path):
    """Start a StorageSCU AE and send the given DICOM file.

    Arguments:
        recAET -- The called AE title.
        recIP -- The called IP address.
        recPort -- The called port number.
        struct_path -- The path to the DICOM file to be sent.
    """
    try:
        storagescu = StorageSCU(recAET, recIP, recPort)
    except Exception as e:
        pynet_logger.error(e)
        pynet_logger.debug(e, exc_info=True)

    try:
        storagescu.c_store(struct_path + "\\MRPAutoContour.dcm")
    except Exception as e:
        pynet_logger.error(e)
        pynet_logger.debug(e, exc_info=True)


def handle_open(event):
    """
    Log the remote's (host, port) when connected.
    """

    msg = "Connected with remote at {}".format(event.address)
    pynet_logger.info(msg)


def handle_close(event):
    """
    Handle processes when closing the Move AE.

    When the association is closed after receiving the DICOM image,
    it runs the Autocontour program to generate segmentations for the DICOM image.
    The Autocontour program saves the segmentations as RTstruct. The RTstruct
    is then sent to the DICOM location selected at the Setup window.
    """

    global selected_server
    global current_dicom
    global setup_screen
    msg = "Disconnected from remote at {}".format(event.address)
    pynet_logger.info(msg)
    try:
        setup_screen.contourStatus.setText("")
    except Exception as e:
        mrpac_logger.error(e)
        mrpac_logger.debug(e, exc_info=True)

    if MoveSCP.slices_path != "":
        slices_path = os.path.abspath(MoveSCP.slices_path)
        MoveSCP.slices_path = ""
        parPath = os.path.abspath(os.path.join(slices_path, os.pardir))
        struct_path = os.path.join(parPath, "RTstruct")
        status = "Success"
        error = ""
        try:
            if selected_server:
                serverAET = selected_server[1]
                serverIP = selected_server[2]
                serverPort = selected_server[3]
                serverPort = int(serverPort)

                try:
                    setup_screen.contouringStatus.setText(
                        f"Autocontouring MR for {str(current_dicom['patientName'])}"
                    )
                    try:
                        try:
                            with open("uid_file", "r") as uid:
                                uid_prefix = uid.readline()
                        except FileNotFoundError:
                            uid_prefix = None
                        autocontour_pelvis = Autocontour(
                            slices_path, struct_path, uid_prefix, autocontour_logger
                        )
                        autocontour_pelvis.run()
                    except Exception as e:
                        mrpac_logger.error(e)
                        mrpac_logger.debug(e, exc_info=True)
                    try:
                        setup_screen.contouringStatus.setText(
                            f"Transferring RTSTRUCT to {serverAET}"
                        )
                        send_c_store(serverAET, serverIP, serverPort, struct_path)
                    except Exception as e:
                        status = "Failed"
                        error = str(e)
                        pynet_logger.error(
                            str(current_dicom["patientName"])
                            + " "
                            + str(current_dicom["patientID"])
                            + ":"
                            + str(e)
                            + ":"
                            + str(sys.exc_info()[2])
                        )
                        pynet_logger.debug(e, exc_info=True)
                except Exception as e:
                    status = "Failed"
                    error = e
                    mrpac_logger.error(
                        str(current_dicom["patientName"])
                        + " "
                        + str(current_dicom["patientID"])
                        + ":"
                        + str(e)
                        + ":"
                        + str(sys.exc_info()[2])
                    )
                    mrpac_logger.debug(e, exc_info=True)
                shutil.rmtree(slices_path)
                shutil.rmtree(struct_path)
            else:
                status = "Failed"
                error = "No SCU selected"
                shutil.rmtree(slices_path)
                pynet_logger.error(
                    str(current_dicom["patientName"])
                    + " "
                    + str(current_dicom["patientID"])
                    + ":"
                    + "No SCU selected"
                    + ":"
                    + str(sys.exc_info()[2])
                )
            pynet_logger.info(
                str(current_dicom["patientName"])
                + " "
                + str(current_dicom["patientID"])
                + ":"
                + "Success"
                + ":"
                + str(sys.exc_info()[2])
            )
        except Exception as e:
            status = "Failed"
            error = e
            pynet_logger.error(
                str(current_dicom["patientName"])
                + " "
                + str(current_dicom["patientID"])
                + ":"
                + str(e)
                + ":"
                + str(sys.exc_info()[2])
            )
            pynet_logger.debug(e, exc_info=True)

        try:
            query = "INSERT INTO history \
                (patientName, patientID, time, status, error) \
                    VALUES (?, ?, ?, ?, ?)"
            cur.execute(
                query,
                (
                    str(current_dicom["patientName"]),
                    str(current_dicom["patientID"]),
                    str(current_dicom["time"]),
                    status,
                    error,
                ),
            )
            con.commit()
        except Exception as e:
            database_logger.error(
                str(current_dicom["patientName"])
                + str(current_dicom["patientID"])
                + ":"
                + str(e)
                + ":"
                + str(sys.exc_info()[2])
            )
            database_logger.debug(e, exc_info=True)

        setup_screen.contouringStatus.setText("")


# Implement the handler for evt.EVT_C_STORE
def handle_store(event):
    """
    Handle a C-STORE request event.
    """

    global TEMP_DIRECTORY
    global current_dicom
    global setup_screen
    current_dicom = {}

    ds = event.dataset
    ds.file_meta = event.file_meta

    current_dicom["patientName"] = ds.PatientName
    current_dicom["patientID"] = ds.PatientID
    current_dicom["time"] = str(datetime.datetime.now())

    try:
        os.makedirs(TEMP_DIRECTORY)
    except OSError:
        pass

    path = os.path.join(TEMP_DIRECTORY, ds.PatientID)
    MoveSCP.slices_path = os.path.join(path, ds.Modality)
    try:
        os.makedirs(MoveSCP.slices_path)
    except OSError:
        pass

    # Save the dataset using the SOP Instance UID as the filename
    outfile = os.path.join(MoveSCP.slices_path, ds.SOPInstanceUID + ".dcm")
    ds.save_as(outfile, write_like_original=False)

    try:
        setup_screen.contouringStatus.setText(
            f"Receiving {str(ds.Modality)} for {str(ds.PatientName)} {str(ds.PatientID)}"
        )
    except Exception as e:
        mrpac_logger.error(e)
        mrpac_logger.debug(e, exc_info=True)
    # Return a 'Success' status
    return 0x0000


class LoginScreen(QWidget):
    """The login window configuration."""

    def __init__(self):
        """Initialize the login window."""
        super(LoginScreen, self).__init__()
        ui_file = os.path.join(UI_DIRECTORY, "Login.ui")
        loadUi(ui_file, self)
        self.setWindowTitle("Login")
        self.setFixedHeight(220)
        self.setFixedWidth(400)
        self.loginButton.clicked.connect(self.loginFunc)

        self.show()

    def loginFunc(self):
        """Log in the user when the button is clicked."""

        global user_type
        global setup_screen
        if self.usernameEntry.text() == "" or self.passwordEntry.text() == "":
            pass
        else:
            username_entered = self.usernameEntry.text()
            passphrase_entered = self.passwordEntry.text()
            if not validEntry(username_entered, "AET") or not validEntry(
                passphrase_entered, "AET"
            ):
                self.invalidLabel.setText("Invalid username or password")
                mrpac_logger.error("LOGIN: Invalid username or password.")
            else:
                query = 'SELECT * FROM users WHERE userName ="' + username_entered + '"'
                try:
                    cur.execute(query)
                    usr_info = cur.fetchone()
                    stored_passPhrase = usr_info[2]
                    user_type = usr_info[3]
                    if bcrypt.checkpw(
                        passphrase_entered.encode("utf-8"),
                        stored_passPhrase.encode("utf-8"),
                    ):
                        setup_screen = SetupScreen()
                        self.close()

                    else:
                        self.invalidLabel.setText("Invalid username or password")
                        mrpac_logger.error("LOGIN: Invalid username or password.")
                except Exception as e:
                    self.invalidLabel.setText("Invalid username or password")
                    mrpac_logger.error(e)
                    mrpac_logger.debug(e, exc_info=True)


class SetupScreen(QMainWindow):
    """The setup window configuration."""

    def __init__(self):
        """Initialize the setup window when login is successful."""

        super(SetupScreen, self).__init__()
        ui_file = os.path.join(UI_DIRECTORY, "Setup.ui")
        loadUi(ui_file, self)
        self.setFixedHeight(400)
        self.setFixedWidth(600)
        self.show()

        self.startSCPButton.clicked.connect(self.startSCPFunc)
        self.stopSCPButton.clicked.connect(self.stopSCPFunc)
        self.saveButton.clicked.connect(self.saveFunc)
        self.configButton.clicked.connect(self.configFunc)
        self.verifyConButton.clicked.connect(self.verifyConFunc)

        self.startUp()

    def startUp(self):
        """Populates the SCP details if saved before."""
        query = "SELECT * FROM host"
        cur.execute(query)
        host_info = cur.fetchone()
        if host_info:
            self.scpAETEntry.setText(host_info[1])
            self.scpPortEntry.setText(host_info[3])

    def startSCPFunc(self):
        """Start the DICOM SCP server to accept C-Move requests."""
        global HOSTIP
        global scpAET
        global scpPort
        scpAET = self.scpAETEntry.text()
        scpPort = self.scpPortEntry.text()
        if scpAET == "" or scpPort == "":
            self.invalidLabel.setText("Fields cannot be empty")
            mrpac_logger.error("SETUP--SCP Details: The AE title and port fields cannot be empty.")
        elif not validEntry(scpAET, "AET"):
            self.invalidLabel.setText("Invalid AE Title")
            mrpac_logger.error("SETUP--SCP Details: Invalid AE Title.")
        elif not validEntry(scpPort, "Port"):
            self.invalidLabel.setText("Invalid port number")
            mrpac_logger.error("SETUP--SCP Details: Invalid port number.")
        else:
            try:
                scpPort = int(scpPort)
                self.new_scp = MoveSCP(scpAET, HOSTIP, int(scpPort))
                self.new_scp.set_handlers(
                    handle_open=handle_open,
                    handle_close=handle_close,
                    handle_store=handle_store,
                )
                self.new_scp.start()
                self.invalidLabel.setText("")
                self.statusLabel.setText("Active")
                self.statusLabel.setStyleSheet(
                    "color: rgb(100, 255, 100);font: 10pt MS Shell Dlg 2"
                )
                self.cstoreAETLabel.setText("DICOM Store AET:")
                self.cstoreAETEntry.setText(scpAET)
                self.cstorePortLabel.setText("Port:")
                self.cstorePortEntry.setText(str(scpPort))
            except ValueError:
                self.invalidLabel.setText("Invalid port number")
                mrpac_logger.e("SETUP--SCP Details: Invalid port number.")
            except Exception as e:
                mrpac_logger.error(e)
                mrpac_logger.debug(e, exc_info=True)

    def stopSCPFunc(self):
        """Stop the DICOM SCP server if it was running."""

        try:
            self.new_scp.stop()
            self.statusLabel.setText("Inactive")
            self.statusLabel.setStyleSheet("color: rgb(255, 255, 255);font: 10pt MS Shell Dlg 2")
            self.cstoreAETLabel.setText("")
            self.cstoreAETEntry.setText("")
            self.cstorePortLabel.setText("")
            self.cstorePortEntry.setText("")

        except AttributeError:
            self.invalidLabel.setText("SCP is inactive")
            mrpac_logger.error("SETUP--SCP Status: SCP is inactive.")
        except ValueError:
            self.invalidLabel.setText("SCP is inactive")
            mrpac_logger.error("SETUP--SCP Status: SCP is inactive")

    def saveFunc(self):
        """Save the SCP Details."""

        global HOSTIP
        global scpAET
        global scpPort
        scpAET = self.scpAETEntry.text()
        scpPort = self.scpPortEntry.text()
        if scpAET == "" or scpPort == "":
            self.invalidLabel.setText("Fields cannot be empty")
            mrpac_logger.error("SETUP--SCP Details: AE title and port fields cannot be empty.")
        elif not validEntry(scpAET, "AET"):
            self.invalidLabel.setText("Invalid AE Title")
            mrpac_logger.error("SETUP--SCP Details: Invalid AE Title.")
        elif not validEntry(scpPort, "Port"):
            self.invalidLabel.setText("Invalid port number")
            mrpac_logger.error("SETUP--SCP Detials: Invalid port number.")
        else:
            try:
                scpPort = int(scpPort)
                try:
                    query = "SELECT * FROM host"
                    savedEntry = cur.execute(query).fetchone()
                    if savedEntry is None:
                        query = "INSERT INTO host (hostAET, hostIP, hostPort) VALUES (?, ?, ?)"
                        cur.execute(query, (scpAET, HOSTIP, scpPort))
                        con.commit()
                    else:
                        query = (
                            "UPDATE host set hostAET = ?, hostIP = ?, hostPort = ? WHERE id = 1"
                        )
                        cur.execute(query, (scpAET, HOSTIP, scpPort))
                except Exception as e:
                    database_logger.debug(e)
                    database_logger.debug(e, exc_info=True)

            except ValueError:
                self.invalidLabel.setText("Invalid port number")
                mrpac_logger.error("SETUP--SCP Details: Invalid port number.")

    def configFunc(self):
        """Start the configuration window."""
        global config_screen
        config_screen = ConfigScreen()

    def verifyConFunc(self):
        """Verify the DICOM connection using ping and C-Echo."""
        global scpAET
        serverAET = self.currentServerAET.text()
        serverIP = self.currentServerIP.text()
        serverPort = self.currentServerPort.text()
        pingResult = None
        echoResult = None

        if serverAET != "" and serverIP != "" and serverPort != "":
            try:
                pingResult = pingTest(serverIP)
            except Exception as e:
                pingResult = "Failed"
                pynet_logger.debug(e)
                pynet_logger.debug(e, exc_info=True)

            try:
                echoResult = verifyEcho(scpAET, serverAET, serverIP, int(serverPort))
            except Exception as e:
                pynet_logger.debug(e)
                pynet_logger.debug(e, exc_info=True)
                echoResult = "Failed"

        self.verify = VerifyScreen(pingResult, echoResult)

    def serverSelected(self):
        """Select a DICOM location to send RTstruct file."""
        global selected_server
        serverAET = selected_server[1]
        serverIP = selected_server[2]
        serverPort = selected_server[3]
        try:
            self.currentServerAET.setText(serverAET)
            self.currentServerIP.setText(serverIP)
            self.currentServerPort.setText(serverPort)
        except Exception as e:
            mrpac_logger.error(e)
            mrpac_logger.debug(e, exc_info=True)


class ConfigScreen(QWidget):
    """The configuration window."""

    def __init__(self):
        """Initialize the configuration window."""
        super(ConfigScreen, self).__init__()
        ui_file = os.path.join(UI_DIRECTORY, "Config.ui")
        loadUi(ui_file, self)
        self.setFixedHeight(220)
        self.setFixedWidth(400)
        self.addButton.clicked.connect(self.addFunc)
        self.removeButton.clicked.connect(self.removeFunc)
        self.editButton.clicked.connect(self.editFunc)
        self.selectButton.clicked.connect(self.selectFunc)

        self.startUp()

        self.listWidget.itemClicked.connect(self.itemClicked_event)
        self.listWidget.itemActivated.connect(self.itemActivated_event)
        self.selectedItem = None
        self.show()

    def startUp(self):
        """Populate the configuration screen with saved DICOM locations."""

        self.listWidget.clear()
        query = "SELECT * FROM servers"
        self.serversCode = {}
        try:
            all_servers = cur.execute(query).fetchall()
            indx = 1
            for server in all_servers:
                self.listWidget.addItem(f"{indx} {server[1]}")
                self.serversCode[str(indx)] = server[0]
                indx += 1

        except Exception as e:
            mrpac_logger.error(e)
            mrpac_logger.debug(e, exc_info=True)

    def addFunc(self):
        """Start the Add window."""
        self.add_ = AddScreen()

    def removeFunc(self):
        """Remove a selected DICOM location from database."""
        if self.selectedItem:
            try:
                idx_ = self.selectedItem[0]
                id_ = self.serversCode[idx_]
                query = "DELETE FROM servers WHERE id = ?"
                try:
                    cur.execute(query, (id_,))
                    con.commit()
                    self.startUp()
                except Exception as e:
                    print(e)
            except Exception as e:
                database_logger.error(e)
                database_logger.debug(e, exc_info=True)

    def itemClicked_event(self, item):
        """Get the info of the DICOM location that is clicked on.

        Arguments:
            item -- The selected DICOM location.
        """
        self.selectedItem = item.text()
        self.selectedItem = self.selectedItem.split(" ")

    def itemActivated_event(self, item):
        """Activate the DICOM location selected.

        Activates the DICOM location that is selected in this ConfigScreen and
        shows the details in the "Server Details" section of the Setup window.

        Arguments:
            item -- The DICOM location to activate.
        """
        global selected_server
        global setup_screen
        self.selectedItem = item.text()
        self.selectedItem = self.selectedItem.split(" ")

        try:
            idx_ = self.selectedItem[0]
            id_ = self.serversCode[idx_]
            query = "SELECT * FROM servers WHERE id = ?"
            selected_server = cur.execute(query, (id_,)).fetchone()
            setup_screen.serverSelected()
            self.close()
        except Exception as e:
            mrpac_logger.error(e)
            mrpac_logger.debug(e, exc_info=True)

    def editFunc(self):
        """Edit the details of the selected DICOM location."""

        global selected_server
        if self.selectedItem:
            try:
                idx_ = self.selectedItem[0]
                id_ = self.serversCode[idx_]
                query = "SELECT * FROM servers WHERE id = ?"
                selected_server = cur.execute(query, (id_,)).fetchone()
                self.edit = EditScreen()
            except Exception as e:
                mrpac_logger.error(e)
                mrpac_logger.debug(e, exc_info=True)

    def selectFunc(self):
        """Activate the selected DICOM location."""
        global selected_server
        global setup_screen

        try:
            idx_ = self.selectedItem[0]
            id_ = self.serversCode[idx_]
            query = "SELECT * FROM servers WHERE id = ?"
            selected_server = cur.execute(query, (id_,)).fetchone()
            self.close()
            setup_screen.serverSelected()
        except Exception as e:
            mrpac_logger.error(e)
            mrpac_logger.debug(e, exc_info=True)


class AddScreen(QWidget):
    """The window to add new DICOM location."""

    def __init__(self):
        """Initialize the add window."""

        super(AddScreen, self).__init__()
        ui_file = os.path.join(UI_DIRECTORY, "Add.ui")
        loadUi(ui_file, self)
        self.setFixedHeight(300)
        self.setFixedWidth(400)
        self.addButton.clicked.connect(self.addFunc)
        self.cancelButton.clicked.connect(self.cancelFunc)
        self.verifyConButton.clicked.connect(self.verifyConFunc)

        self.show()

    def addFunc(self):
        """Add the new DICOM location when add button is clicked."""

        serverAET = self.serverAETEntry.text()
        serverIP = self.serverIPEntry.text()
        serverPort = self.serverPortEntry.text()
        if serverAET == "" or serverIP == "" or serverPort == "":
            self.invalidLabel.setText("Fields cannot be empty.")
            mrpac_logger.error("ADD--Server Details: Fields cannot be emtpy.")
        elif not validEntry(serverAET, "AET"):
            self.invalidLabel.setText("Invalid AET")
            mrpac_logger.error("ADD--Server Details: Invalid AE Title")
        elif not validEntry(serverIP, "IP"):
            self.invalidLabel.setText("Invalid IP")
            mrpac_logger.error("ADD--Server Details: Invalid IP address.")
        elif not validEntry(serverPort, "Port"):
            self.invalidLabel.setText("Invalid port")
            mrpac_logger.error("ADD--Server Details: Invalid port number.")

        else:
            query = "INSERT INTO servers (serverAET, serverIP, serverPort) VALUES (?, ?, ?)"
            try:
                cur.execute(query, (serverAET, serverIP, serverPort))
                con.commit()
                self.close()
                self.config = ConfigScreen()
            except Exception as e:
                self.invalidLabel.setText("Could not add server")
                database_logger.error(e)
                database_logger.debug(e, exc_info=True)

    def cancelFunc(self):
        """Close the Add window."""

        self.close()

    def verifyConFunc(self):
        """Send a C-Echo to verify DICOM connectivity."""
        global scpAET
        serverAET = self.serverAETEntry.text()
        serverIP = self.serverIPEntry.text()
        serverPort = self.serverPortEntry.text()
        pingResult = None
        echoResult = None
        if serverAET == "" or serverIP == "" or serverPort == "":
            self.invalidLabel.setText("Fields cannot be empty.")
            mrpac_logger.error("ADD--Server Details: Fields cannot be empty.")
        elif not validEntry(serverAET, "AET"):
            self.invalidLabel.setText("Invalid AET")
            mrpac_logger.error("ADD--Server Details: Invalid AE Tile.")
        elif not validEntry(serverIP, "IP"):
            self.invalidLabel.setText("Invalid IP")
            mrpac_logger.error("ADD--Server Details: Invalid IP address.")
        elif not validEntry(serverPort, "Port"):
            self.invalidLabel.setText("Invalid port")
            mrpac_logger.error("ADD--Server Details: Invalid port number.")
        else:
            try:
                pingResult = pingTest(serverIP)
            except Exception as e:
                pingResult = "Failed"
                mrpac_logger.error(e)

            try:
                echoResult = verifyEcho(scpAET, serverAET, serverIP, int(serverPort))
            except Exception as e:
                echoResult = "Failed"
                mrpac_logger.error(e)

        self.verify = VerifyScreen(pingResult, echoResult)


class VerifyScreen(QWidget):
    """The window with status of the verification requests."""

    def __init__(self, pingResult, echoResult):
        """Initialize the verify window.

        Arguments:
            pingResult -- The result of the ping test.
            echoResult -- The result of the DICOM C-Echo test.
        """

        super(VerifyScreen, self).__init__()
        ui_file = os.path.join(UI_DIRECTORY, "Verify.ui")
        loadUi(ui_file, self)
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


class EditScreen(QWidget):
    """The Edit window to modify DICOM location info."""

    def __init__(self):
        """Initialize the Edit window."""

        super(EditScreen, self).__init__()
        ui_file = os.path.join(UI_DIRECTORY, "Edit.ui")
        loadUi(ui_file, self)
        self.setFixedHeight(300)
        self.setFixedWidth(400)
        self.updateButton.clicked.connect(self.updateFunc)
        self.cancelButton.clicked.connect(self.cancelFunc)
        self.verifyConButton.clicked.connect(self.verifyConFunc)

        self.startUp()

        self.show()

    def startUp(self):
        """Start the Edit window and show details of the DICOM location to be edited."""

        global selected_server
        self.serverAETEntry.setText(selected_server[1])
        self.serverIPEntry.setText(selected_server[2])
        self.serverPortEntry.setText(selected_server[3])

    def updateFunc(self):
        """Update the DICOM location details with the new info."""

        global config_screen
        global selected_server
        serverAET = self.serverAETEntry.text()
        serverIP = self.serverIPEntry.text()
        serverPort = self.serverPortEntry.text()
        if serverAET == "" or serverIP == "" or serverPort == "":
            self.invalidLabel.setText("Fields cannot be empty.")
            mrpac_logger.error("EDIT--Server Details: Fields cannot be empty.")
        elif not validEntry(serverAET, "AET"):
            self.invalidLabel.setText("Invalid AET")
            mrpac_logger.error("EDIT--Server Details: Invalit AE Title.")
        elif not validEntry(serverIP, "IP"):
            self.invalidLabel.setText("Invalid IP")
            mrpac_logger.error("EDIT--Server Details: Invalid IP address.")
        elif not validEntry(serverPort, "Port"):
            self.invalidLabel.setText("Invalid Port")
            mrpac_logger.error("EDIT--Server Details: Invalid port number.")
        else:
            query = "UPDATE servers set serverAET = ?, serverIP = ?, serverPort = ? WHERE id = ?"
            try:
                cur.execute(query, (serverAET, serverIP, serverPort, selected_server[0]))
                con.commit()
                config_screen.startUp()
                self.close()
            except Exception as e:
                self.invalidLabel.setText("Could not update server")
                database_logger.error(e)
                database_logger.debug(e, exc_info=True)

    def cancelFunc(self):
        """Close the Edit window."""

        self.close()

    def verifyConFunc(self):
        """Verify the DICOM connection using ping and C-Echo."""
        global scpAET
        serverAET = self.serverAETEntry.text()
        serverIP = self.serverIPEntry.text()
        serverPort = self.serverPortEntry.text()
        pingResult = None
        echoResult = None
        if serverAET == "" or serverIP == "" or serverPort == "":
            self.invalidLabel.setText("Fields cannot be empty.")
            mrpac_logger.error("VERIFY: Fields cannot be empty.")
        elif not validEntry(serverAET, "AET"):
            self.invalidLabel.setText("Invalid AET")
            mrpac_logger.error("VERIFY: Invalid AE Title.")
        elif not validEntry(serverIP, "IP"):
            self.invalidLabel.setText("Invalid IP")
            mrpac_logger.error("VERIFY: Invalid IP address.")
        elif not validEntry(serverPort, "Port"):
            self.invalidLabel.setText("Invalid port")
            mrpac_logger.error("VERIFY: Invalid port number.")
        else:
            try:
                pingResult = pingTest(serverIP)
            except Exception as e:
                pingResult = "Failed"
                mrpac_logger.error(e)

            try:
                echoResult = verifyEcho(scpAET, serverAET, serverIP, int(serverPort))
            except Exception as e:
                echoResult = "Failed"
                mrpac_logger.error(e)

        self.verify = VerifyScreen(pingResult, echoResult)


def main():
    databaseSetup()
    APP = QApplication(sys.argv)
    login = LoginScreen()  # noqa

    try:
        sys.exit(APP.exec_())
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
