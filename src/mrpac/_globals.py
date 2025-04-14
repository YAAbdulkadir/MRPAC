"""Global variables for MRPAC"""

import logging
import os
import queue
import socket
import inspect
import sqlite3
from datetime import datetime
import threading
from typing import Union


class Globals:
    # Directory paths
    PARENT_DIRECTORY = os.path.join(os.path.dirname(__file__))
    RESOURCES_DIRECTORY = os.path.join(PARENT_DIRECTORY, "resources")
    MODELS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "models")
    LOGS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "logs")
    TEMP_DIRECTORY = os.path.join(PARENT_DIRECTORY, "Temp")
    MODELS_CONFIG_PATH = os.path.join(MODELS_DIRECTORY, "config.json")

    # Set the log formatter
    LOG_FORMATTER = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s:%(lineno)d")

    # Get the UID prefix if present
    try:
        with open(os.path.join(RESOURCES_DIRECTORY, "uid_prefix.txt"), "r") as uid:
            UID_PREFIX: Union[str, None] = uid.readline()
    except FileNotFoundError:
        UID_PREFIX = None

    # Get the IP address of this device
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            HOSTIP = s.getsockname()[0]
    except Exception:
        try:
            HOSTIP = socket.gethostbyname(socket.gethostname())
        except Exception:
            HOSTIP = "127.0.0.1"
    scpAET = None
    scpPort = None

    # Set global variables
    current_user = None
    user_type = None
    selected_server = None
    setup_screen = None
    config_screen = None
    current_dicom = None

    db_path = os.path.join(RESOURCES_DIRECTORY, "entries.db")
    db_thread_local = threading.local()  # Thread-local storage for database connections

    db_cur = None
    db_con = None

    log_db_path = os.path.join(LOGS_DIRECTORY, "log.db")
    log_db_cursor = None
    log_db_conn = None
    log_queue = queue.Queue()
    log_thread = None
    stop_logging = threading.Event()

    # Mapping for tracking stored paths
    stored_paths = {}  # {PatientID: {Modality: {SeriesInstanceUID: path}}}

    # Active session tracking {Address: {"patientID": str, "modality": str, "seriesUIDs": set}}
    active_sessions = {}
    active_sessions_lock = threading.Lock()

    dicom_queue = queue.Queue()

    @staticmethod
    def close_db_connection():
        """Closes the thread-local SQLite connection."""
        if hasattr(Globals.db_thread_local, "db_con"):
            Globals.db_thread_local.db_con.close()
            del Globals.db_thread_local.db_con
            del Globals.db_thread_local.db_cur

    @staticmethod
    def log_to_db(logger_name, log_level, message, stack_trace=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Automatically retrieve the caller's current line number
        frame = inspect.currentframe()
        caller_frame = frame.f_back  # Go back one step in the call stack
        line_number = caller_frame.f_lineno

        # Place the log entry in the queue
        Globals.log_queue.put(
            (logger_name, timestamp, log_level, message, line_number, stack_trace)
        )

    @staticmethod
    def _log_worker():
        """"""
        conn = sqlite3.connect(Globals.log_db_path, check_same_thread=False)
        cursor = conn.cursor()

        while not Globals.stop_logging.is_set() or not Globals.log_queue.empty():
            try:
                logger_name, timestamp, log_level, message, line_number, stack_trace = (
                    Globals.log_queue.get(timeout=1)
                )
                insert_sql = (
                    f"INSERT INTO {logger_name}_log "
                    "(Timestamp, LogLevel, Message, LineNumber, StackTrace) "
                    "VALUES (?, ?, ?, ?, ?)"
                )
                cursor.execute(
                    insert_sql, (timestamp, log_level, message, line_number, stack_trace)
                )
                conn.commit()
                Globals.log_queue.task_done()

            except queue.Empty:
                continue  # If no logs, keep checking

            except sqlite3.Error as e:
                print(f"Database logging error: {e}")

        cursor.close()
        conn.close()

    @staticmethod
    def start_logging():
        """Starts the logging thread."""
        if Globals.log_thread is None or not Globals.log_thread.is_alive():
            Globals.stop_logging.clear()
            Globals.log_thread = threading.Thread(target=Globals._log_worker, daemon=True)
            Globals.log_thread.start()

    @staticmethod
    def stop_logging_func():
        """Stops the logging thread gracefully."""
        Globals.stop_logging.set()  # Signal the thread to exit
        Globals.log_queue.join()  # Wait for all logs to be written
        if Globals.log_thread:
            Globals.log_thread.join()
