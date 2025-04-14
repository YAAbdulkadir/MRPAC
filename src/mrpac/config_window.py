import logging
import sqlite3


from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ._globals import Globals
from .ui_config import Ui_ConfigWindow
from .add_window import AddWindow
from .edit_window import EditWindow

mrpac_logger = logging.getLogger("mrpac")
database_logger = logging.getLogger("database")
pynet_logger = logging.getLogger("network")


class ConfigWindow(qtw.QWidget, Ui_ConfigWindow):
    """The configuration window."""

    def __init__(self):
        """Initialize the configuration window."""
        super().__init__()

        self.setupUi(self)
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

        conn, cursor = Globals.get_db_connection()
        try:
            all_servers = cursor.execute(query).fetchall()
            indx = 1
            for server in all_servers:
                self.listWidget.addItem(f"{indx} {server[1]}")
                self.serversCode[str(indx)] = server[0]
                indx += 1

        except Exception as e:
            mrpac_logger.error(e)
            mrpac_logger.debug(e, exc_info=True)

        finally:
            Globals.close_db_connection()

    def addFunc(self):
        """Start the Add window."""
        self.add_ = AddWindow()

    def removeFunc(self):
        """Remove a selected DICOM location from database."""
        if not self.selectedItem:
            self.invalidLabel.setText("No server selected")
            return

        try:
            idx_ = self.selectedItem[0]

            if idx_ not in self.serversCode:
                self.invalidLabel.setText("Invalid selection")
                return

            id_ = self.serversCode[idx_]
            query = "DELETE FROM servers WHERE id = ?"

            conn, cursor = Globals.get_db_connection()

            try:
                cursor.execute(query, (id_,))
                conn.commit()
                self.startUp()
                msg = f"CONFIG: Removed server ID {id_}"
                database_logger.info(msg)
                Globals.log_to_db("database", "INFO", msg, None)

            except sqlite3.Error as e:
                error = f"CONFIG: Database error while removing server: {e}"
                self.invalidLabel.setText("Failed to remove server")
                database_logger.error(error)
                Globals.log_to_db("database", "ERROR", msg, None)
        except Exception as e:
            self.invalidLabel.setText("An error occurred")
            error = f"CONFIG: Unexpected error in removeFunc: {e}"
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()

    def itemClicked_event(self, item):
        """Get the info of the DICOM location that is clicked on.

        Parameters
        ----------
        item : `QListWidgetItem`
            The selected DICOM location.
        """
        self.selectedItem = item.text()
        self.selectedItem = self.selectedItem.split(" ")

    def itemActivated_event(self, item):
        """Activates the selected DICOM location and updates SetupScreen."""

        if not item:
            msg = "CONFIG: No item selected in itemActivated_event"
            database_logger.warning(msg)
            Globals.log_to_db("database", "WARNING", msg, None)
            return

        self.selectedItem = item.text().split(" ", maxsplit=1)  # Split only once
        if not self.selectedItem or len(self.selectedItem) < 2:
            msg = "CONFIG: Invalid item format in itemActivated_event"
            database_logger.warning(msg)
            Globals.log_to_db("database", "WARNING", msg, None)
            return

        idx_ = self.selectedItem[0]

        if idx_ not in self.serversCode:
            self.invalidLabel.setText("Invalid selection")
            return

        id_ = self.serversCode[idx_]
        query = "SELECT * FROM servers WHERE id = ?"

        conn, cursor = Globals.get_db_connection()

        try:
            cursor.execute(query, (id_,))
            Globals.selected_server = cursor.fetchone()

            if Globals.selected_server:
                Globals.setup_screen.serverSelected()
                self.close()
                msg = f"CONFIG: Activated server ID {id_}"
                database_logger.info(msg)
                Globals.log_to_db("database", "INFO", msg, None)
            else:
                self.invalidLabel.setText("Server not found")
                msg = f"CONFIG: Server ID {id_} not found"
                database_logger.warning(msg)
                Globals.log_to_db("database", "WARNING", msg, None)

        except sqlite3.Error as e:
            error = f"CONFIG: Database error in itemActivated_event: {e}"
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()

    def editFunc(self):
        """Edit the details of the selected DICOM location."""

        if not self.selectedItem:
            msg = "CONFIG: No server selected for editing"
            database_logger.warning(msg)
            Globals.log_to_db("database", "WARNING", msg, None)
            self.invalidLabel.setText("No server selected")
            return

        idx_ = self.selectedItem[0]

        if idx_ not in self.serversCode:
            self.invalidLabel.setText("Invalid selection")
            msg = "CONFIG: Invalid selection in editFunc"
            database_logger.warning(msg)
            Globals.log_to_db("database", "WARNING", msg, None)
            return

        id_ = self.serversCode[idx_]
        query = "SELECT * FROM servers WHERE id = ?"

        conn, cursor = Globals.get_db_connection()

        try:
            cursor.execute(query, (id_,))
            Globals.selected_server = cursor.fetchone()

            if Globals.selected_server:
                self.edit = EditWindow()
                msg = f"CONFIG: Editing server ID {id_}"
                database_logger.info(msg)
                Globals.log_to_db("database", "INFO", msg, None)
            else:
                self.invalidLabel.setText("Server not found")
                msg = f"CONFIG: Server ID {id_} not found for editing"
                database_logger.warning(msg)
                Globals.log_to_db("database", "WARNING", msg, None)

        except sqlite3.Error as e:
            error = f"CONFIG: Database error in editFunc: {e}"
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()

    def selectFunc(self):
        """Activate the selected DICOM location."""

        if not self.selectedItem:
            msg = "CONFIG: No server selected for activation"
            database_logger.warning(msg)
            Globals.log_to_db("database", "WARNING", msg, None)
            self.invalidLabel.setText("No server selected")
            return

        idx_ = self.selectedItem[0]

        if idx_ not in self.serversCode:
            self.invalidLabel.setText("Invalid selection")
            msg = "CONFIG: Invalid selection in selectFunc"
            database_logger.warning(msg)
            Globals.log_to_db("database", "WARNING", msg, None)
            return

        id_ = self.serversCode[idx_]
        query = "SELECT * FROM servers WHERE id = ?"

        conn, cursor = Globals.get_db_connection()

        try:
            cursor.execute(query, (id_,))
            Globals.selected_server = cursor.fetchone()

            if Globals.selected_server:
                self.close()
                Globals.setup_screen.serverSelected()
                msg = f"CONFIG: Selected server ID {id_}"
                database_logger.info(msg)
                Globals.log_to_db("database", "INFO", msg, None)
            else:
                self.invalidLabel.setText("Server not found")
                msg = f"CONFIG: Server ID {id_} not found for selection"
                database_logger.warning(msg)
                Globals.log_to_db("database", "WARNING", msg, None)

        except sqlite3.Error as e:
            error = f"CONFIG: Database error in selectFunc: {e}"
            database_logger.error(error)
            Globals.log_to_db("database", "ERROR", error, None)

        finally:
            Globals.close_db_connection()
