"""The main module for MRPAC."""

import logging
import os
import sqlite3
import sys
import traceback
import bcrypt
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from .login import LoginWindow
from ._globals import Globals

# Initialize the Logger files
if not os.path.exists(Globals.LOGS_DIRECTORY):
    os.makedirs(Globals.LOGS_DIRECTORY)

# Initialize Logger files
pynet_logger = logging.getLogger("network")
mrpac_logger = logging.getLogger("mrpac")
autocontour_logger = logging.getLogger("autocontour")
database_logger = logging.getLogger("database")
loggers = {
    "network": ["network.log", pynet_logger],
    "mrpac": ["mrpac.log", mrpac_logger],
    "autocontour": ["autocontour.log", autocontour_logger],
    "database": ["database.log", database_logger],
}

for logger_name, (log_file, logger) in loggers.items():
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(os.path.join(Globals.LOGS_DIRECTORY, log_file))
    file_handler.setFormatter(Globals.LOG_FORMATTER)
    logger.addHandler(file_handler)


def databaseSetup() -> None:
    """Sets up the database and creates neccesary tables if they are not created already."""

    tables = {
        "host": """
            CREATE TABLE IF NOT EXISTS "host" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "hostAET" TEXT,
                "hostIP" TEXT,
                "hostPort" TEXT
            )
        """,
        "servers": """
            CREATE TABLE IF NOT EXISTS "servers" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "serverAET" TEXT,
                "serverIP" TEXT,
                "serverPort" TEXT
            )
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS "users" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "userName" TEXT,
                "passPhrase" TEXT,
                "userType" TEXT
            )
        """,
        "history": """
            CREATE TABLE IF NOT EXISTS "history" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "patientName" TEXT,
                "patientID" TEXT,
                "time" TEXT,
                "status" TEXT,
                "errors" TEXT
            )
        """,
    }

    conn, cursor = Globals.get_db_connection()

    # Execute each table creation SQL statement
    for table_sql in tables.values():
        try:
            cursor.execute(table_sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE userName = ?", ("Admin",))
        admin_exists = cursor.fetchone()[0]  # Get count result

        if admin_exists == 0:  # If no Admin exists, insert one
            query = "INSERT INTO users (userName, passPhrase, userType) VALUES (?, ?, ?)"
            passPhrase = bcrypt.hashpw(b"mrpac", bcrypt.gensalt()).decode()
            cursor.execute(query, ("Admin", passPhrase, "Administrator"))
            conn.commit()

    except sqlite3.Error as e:
        print(f"Database error while ensuring Admin user exists: {e}")


def logger_db_setup(db_path):
    # SQL statements to create the tables
    table_creations = {
        "mrpac_log": """
            CREATE TABLE IF NOT EXISTS mrpac_log (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp DATETIME,
                LogLevel TEXT,
                Message TEXT,
                LineNumber INTEGER,
                StackTrace TEXT
            );
        """,
        "autocontour_log": """
            CREATE TABLE IF NOT EXISTS autocontour_log (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp DATETIME,
                LogLevel TEXT,
                Message TEXT,
                LineNumber INTEGER,
                StackTrace TEXT
            );
        """,
        "database_log": """
            CREATE TABLE IF NOT EXISTS database_log (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp DATETIME,
                LogLevel TEXT,
                Message TEXT,
                LineNumber INTEGER,
                StackTrace TEXT
            );
        """,
        "network_log": """
            CREATE TABLE IF NOT EXISTS network_log (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp DATETIME,
                LogLevel TEXT,
                Message TEXT,
                LineNumber INTEGER,
                StackTrace TEXT
            );
        """,
    }

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # Execute each table creation SQL statement
    for table_sql in table_creations.values():
        cursor.execute(table_sql)

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def start():
    """"""
    try:
        # Initiate the Logging System
        logger_db_setup(Globals.log_db_path)
        Globals.start_logging()

        # Initiate the Database Connection
        if not os.path.exists(Globals.RESOURCES_DIRECTORY):
            os.makedirs(Globals.RESOURCES_DIRECTORY)

        # Establish Database connection (Main Thread)
        conn, cursor = Globals.get_db_connection()

        databaseSetup()

        # Start the Application
        mrpac_logger.info("Starting MRPAC ...")
        Globals.log_to_db("mrpac", "INFO", "Starting MRPAC ...", None)

        APP = qtw.QApplication(sys.argv)
        login = LoginWindow()

        try:
            sys.exit(APP.exec())
        except Exception as e:
            stack_trace = traceback.format_exc()
            Globals.log_to_db("mrpac", "ERROR", str(e), None)
            Globals.log_to_db("mrpac", "DEBUG", str(e), stack_trace)
            print(e)

    finally:
        shutdown()


def shutdown():
    """Cleans up resources when MRPAC exits."""
    logging.getLogger("mrpac").info("Shutting down MRPAC ...")
    Globals.log_to_db("mrpac", "INFO", "Shutting down MRPAC ...", None)

    # Stop logging thread
    Globals.stop_logging_func()

    # Close SQLite Connection
    Globals.close_db_connection()

    sys.exit(0)


if __name__ == "__main__":

    start()
