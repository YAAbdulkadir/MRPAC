import logging

import bcrypt

from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ._globals import Globals
from .DICOM_Networking import validEntry
from .ui_login import Ui_Login
from .setup_window import SetupWindow

mrpac_logger = logging.getLogger("mrpac")
database_logger = logging.getLogger("database")


class LoginWindow(qtw.QWidget, Ui_Login):
    """The login window configuration."""

    def __init__(self):
        """Initialize the login window."""
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Login")
        self.setFixedHeight(220)
        self.setFixedWidth(400)
        self.loginButton.clicked.connect(self.loginFunc)

        self.show()

    def loginFunc(self):
        """Log in the user when the button is clicked."""
        username_entered = self.usernameEntry.text().strip()
        passphrase_entered = self.passwordEntry.text().strip()

        if not username_entered or not passphrase_entered:
            self.invalidLabel.setText("Invalid username or password")
            mrpac_logger.warning("LOGIN: Empty username or password entered.")
            Globals.log_to_db(
                "mrpac", "WARNING", "LOGIN: Empty username or password entered.", None
            )
            return

        if not validEntry(username_entered, "AET") or not validEntry(passphrase_entered, "AET"):
            self.invalidLabel.setText("Invalid username or password")
            mrpac_logger.warning("LOGIN: Invalid username or password format.")
            Globals.log_to_db("mrpac", "WARNING", "LOGIN: Invalid username or password format.")
            return

        # Get a thread-safe database connection
        conn, cursor = Globals.get_db_connection()

        query = "SELECT * FROM users WHERE userName = ?"
        try:
            cursor.execute(query, (username_entered,))
            usr_info = cursor.fetchone()

            if usr_info is None:
                self.invalidLabel.setText("Invalid username or password")
                mrpac_logger.warning("LOGIN: Failed login attempt.")
                Globals.log_to_db("mrpac", "WARNING", "LOGIN: Failed login attempt.", None)
                return

            stored_passPhrase = usr_info[2]

            if bcrypt.checkpw(
                passphrase_entered.encode("utf-8"), stored_passPhrase.encode("utf-8")
            ):
                Globals.user_type = usr_info[3]
                Globals.setup_screen = SetupWindow()
                self.close()

            else:
                self.invalidLabel.setText("Invalid username or password")
                mrpac_logger.warning("LOGIN: Failed login attempt.")

        except Exception as e:
            self.invalidLabel.setText("An error occured. Please try again.")
            database_logger.error(f"LOGIN: Database error - {str(e)}")
            Globals.log_to_db("mrpac", "ERROR", f"LOGIN: Error occured - {e}", None)

        finally:
            # Close the thread-local connection after use
            Globals.close_db_connection()
