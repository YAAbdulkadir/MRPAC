"""Global variables for MRPAC"""

import os
import logging

# Directory paths
PARENT_DIRECTORY = os.path.abspath((os.path.join(os.getcwd(), "..")))
UI_DIRECTORY = os.path.join(PARENT_DIRECTORY, "ui_files")
RESOURCES_DIRECTORY = os.path.join(PARENT_DIRECTORY, "resources")
MODELS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "models")
LOGS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "logs")
TEMP_DIRECTORY = os.path.join(PARENT_DIRECTORY, "Temp")

# Set the log formatter
LOG_FORMATTER = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s:%(lineno)d")

# Get the UID prefix if present
try:
    with open(os.path.join(RESOURCES_DIRECTORY, "uid_prefix.txt"), "r") as uid:
        UID_PREFIX = uid.readline()
except FileNotFoundError:
    UID_PREFIX = None

if __name__ == "__main__":
    print(UID_PREFIX)
