"""A module for DICOM networking using pynetdicom."""

import datetime
import logging
import os
from typing import Union
import shutil
import subprocess
import sys
import traceback
from ping3 import ping
from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.events import EventHandlerType
from pynetdicom.sop_class import Verification
from pathlib import Path

from ._globals import Globals

# Initialize the Logger files
pynet_logger = logging.getLogger("network")
mrpac_logger = logging.getLogger("mrpac")
database_logger = logging.getLogger("database")


evt.EVT_PDU_RECV


def validEntry(input_text: Union[str, int], entry_type: str) -> bool:
    """Checks whether a text input from the user contains invalid
    characters.

    Parameters
    ----------
    input_text : Union[str, int]
        The text input to a given field.
    entry_type : str
        The type of field where the text was input. The different
        types are:
        * AET
        * Port
        * IP

    Returns
    -------
    bool
        Whether the input was valid or not.
    """
    if (
        " " in input_text
        or '"' in input_text
        or "'" in input_text
        or "\\" in input_text
        or "*" in input_text
    ):
        return False
    else:
        if entry_type == "AET":
            return True
        elif entry_type == "Port":
            try:
                int(input_text)
                return True
            except ValueError:
                return False
        elif entry_type == "IP":
            return True
        else:
            return False


def pingTest(ip: str) -> str:
    """Verify whether the device with the ip address typed accepts
    packets over the network.

    Parameters
    ----------
    ip : str
        The IPv4 address of the device to ping.

    Returns
    -------
    str
        Success or Failed.
    """

    response = ping(ip, timeout=0.01)

    if response is None:
        return "Failed"
    elif response is False:
        return "Failed"
    else:
        return "Success"


def verifyEcho(scpAET: str, aet: str, ip: str, port: Union[str, int]) -> str:
    """Verifies whether a DICOM association can be established given
    an AE (Application Entity) title, IP address and port number of a
    peer AE.

    Parameters
    ----------
    scpAET : str
        A calling AE title to use.
    aet : str
        The AE title of the peer AE.
    ip : str
        The IPv4 address of the peer AE.
    port : Union[str, int]
        The port number of the peer AE.

    Returns
    -------
    str
        A DICOM response status as a string or `Failed` if association
        could not be established or no response was received.
    """

    ae = AE(scpAET)
    ae.add_requested_context(Verification)
    assoc = ae.associate(ip, int(port), ae_title=aet)
    result = None
    if assoc.is_established:
        status = assoc.send_c_echo()
        if status:
            result = "{0:04x}".format(status.Status)
        else:
            result = "Failed"
    else:
        result = "Failed"

    assoc.release()
    return result


def send_c_store(recAET: str, recIP: str, recPort: Union[str, int], struct_path: str) -> None:
    """Start a StorageSCU AE and send the given DICOM file.

    Parameters
    ----------
    recAET : str
        The AE title for the called AE.
    recIP : str
        The IP address for the called AE.
    recPort : Union[str, int]
        The port number for the called AE.
    struct_path : str
        The path to the DICOM file to be sent.
    """
    try:
        storagescu = StorageSCU(recAET, recIP, recPort)
    except Exception as e:
        pynet_logger.error(e)
        pynet_logger.debug(e, exc_info=True)
        stack_trace = traceback.format_exc()
        Globals.log_to_db("network", "ERROR", str(e), None)
        Globals.log_to_db("network", "DEBUG", str(e), stack_trace)

    try:
        storagescu.c_store(os.path.join(struct_path, "AutoContour.dcm"))
    except Exception as e:
        pynet_logger.error(e)
        pynet_logger.debug(e, exc_info=True)
        stack_trace = traceback.format_exc()
        Globals.log_to_db("network", "ERROR", str(e), None)
        Globals.log_to_db("network", "DEBUG", str(e), stack_trace)


def process_dicom(event):
    """Processes and stores an incoming DICOM file."""
    ds = event.dataset
    ds.file_meta = event.file_meta

    patient_id = ds.PatientID
    modality = ds.Modality
    series_uid = ds.SeriesInstanceUID
    sop_uid = ds.SOPInstanceUID

    try:
        # Construct paths
        base_dir = os.path.join(Globals.TEMP_DIRECTORY, patient_id, modality, series_uid)
        os.makedirs(base_dir, exist_ok=True)

        # Save the dataset
        dicom_path = os.path.abspath(os.path.join(base_dir, f"{sop_uid}.dcm"))
        ds.save_as(dicom_path, write_like_original=False)

        # Log successful storage
        msg = f"Stored DICOM {modality} for {patient_id} - Series {series_uid} at {dicom_path}"
        Globals.log_to_db("network", "INFO", msg, None)

        # Store the path for tracking
        if patient_id not in Globals.stored_paths:
            Globals.stored_paths[patient_id] = {}
        if modality not in Globals.stored_paths[patient_id]:
            Globals.stored_paths[patient_id][modality] = {}
        if series_uid not in Globals.stored_paths[patient_id][modality]:
            Globals.stored_paths[patient_id][modality][series_uid] = base_dir

    except Exception as e:
        err_msg = f"Error processing DICOM for {patient_id}: {str(e)}"
        Globals.log_to_db("network", "ERROR", err_msg, traceback.format_exc())

    return 0x0000


def handle_open(event):
    """Log the remote's (host, port) when connected."""

    msg = "Connected with remote at {}".format(event.address)
    pynet_logger.info(msg)
    Globals.log_to_db("network", "INFO", msg, None)


# Implement the handler for evt.EVT_C_STORE
def handle_store(event):
    """Adds DICOM processing tasks to a queue for worker threads to handle."""
    ds = event.dataset
    ds.file_meta = event.file_meta

    patient_name = ds.PatientName
    patient_id = ds.PatientID
    modality = ds.Modality
    series_uid = ds.SeriesInstanceUID
    sender_address = event.assoc.requestor.address  # The sending DICOM node

    # Track the session
    with Globals.active_sessions_lock:
        if sender_address not in Globals.active_sessions:
            Globals.active_sessions[sender_address] = {
                "patientName": patient_name,
                "patientID": patient_id,
                "modality": modality,
                "seriesUIDs": set(),
            }
        Globals.active_sessions[sender_address]["seriesUIDs"].add(series_uid)

    # Add to processing queue
    Globals.dicom_queue.put(event)
    return 0x0000


def handle_close(event):
    """ """
    sender_address = event.assoc.requestor.address
    msg = f"Disconnected from remote at {sender_address}"
    pynet_logger.info(msg)
    Globals.log_to_db("network", "INFO", msg, None)

    with Globals.active_sessions_lock:
        session_data = Globals.active_sessions.pop(sender_address, None)
    if not session_data:
        msg = f"No active session found for sender {sender_address}."
        pynet_logger.error(msg)
        Globals.log_to_db("network", "ERROR", msg, None)
        return

    patient_name = session_data["patientName"]
    patient_id = session_data["patientID"]
    modality = session_data["modality"]
    series_uids = session_data["seriesUIDs"]
    series_description = session_data["seriesDescription"]

    # Iterate through all received SeriesInstanceUIDs
    for series_uid in series_uids:
        if patient_id in Globals.stored_paths and modality in Globals.stored_paths[patient_id]:
            if series_uid in Globals.stored_paths[patient_id][modality]:
                slices_path = Globals.stored_paths[patient_id][modality][series_uid]
            else:
                msg = f"Series {series_uid} for {patient_id}, {modality} not found."
                pynet_logger.error(msg)
                Globals.log_to_db("network", "ERROR", msg, None)
                continue
        else:
            msg = f"No stored DICOMs found for {patient_id}, {modality}."
            pynet_logger.error(msg)
            Globals.log_to_db("network", "ERROR", msg, None)
            continue

        # Define RTSTRUCT storage path
        struct_path = os.path.join(slices_path, os.pardir, "RTSTRUCT", series_uid)
        os.makedirs(struct_path, exist_ok=True)

        status = "Success"
        error = ""

        # Auto-contouring process
        try:
            Globals.setup_screen.contouringStatus.setText(
                f"Auto-contouring {modality} for {patient_id}"
            )

            if modality == "MR":
                autocontour_script = os.path.join(Globals.PARENT_DIRECTORY, "AutocontourMR.py")
                cmd = [
                    str(sys.executable),
                    str(autocontour_script),
                    str(slices_path),
                    str(struct_path),
                    str(Globals.UID_PREFIX),
                ]
            elif modality == "CT":
                if (
                    "HDR".lower() in series_description.lower()
                    or "BRACHY".lower() in series_description.lower()
                ):

                    autocontour_script = os.path.join(
                        Globals.PARENT_DIRECTORY, "AutocontourHDR.py"
                    )
                    cmd = [
                        str(sys.executable),
                        str(autocontour_script),
                        str(slices_path),
                        str(struct_path),
                        str(Globals.UID_PREFIX),
                    ]
                else:
                    # print("running TS")
                    autocontour_script = os.path.join(
                        Globals.PARENT_DIRECTORY, "AutocontourCT_TS.py"
                    )
                    total_seg_env = Path(
                        r"C:\Users\yabdulkadir\Anaconda3\envs\totalsegmentator\python.exe"
                    )
                    cmd = [
                        str(total_seg_env),
                        str(autocontour_script),
                        str(slices_path),
                        str(struct_path),
                        str(Globals.UID_PREFIX),
                    ]
            else:
                msg = f"Unsupported modality: {modality}"
                pynet_logger.error(msg)
                Globals.log_to_db("network", "ERROR", msg, None)
                continue

            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                msg = f"Successfully auto-contoured {modality} for " f"{patient_name} {patient_id}"
                Globals.log_to_db(
                    "autocontour",
                    "INFO",
                    msg,
                    None,
                )

            except subprocess.CalledProcessError as e:
                status = "Failed"

                process_output = e.stderr.strip() or e.stdout.strip() or str(e)

                error = (
                    f"Auto-contouring failed for {patient_name} " f"{patient_id}: {process_output}"
                )

                pynet_logger.error(error)

                Globals.log_to_db(
                    "autocontour",
                    "ERROR",
                    error,
                    process_output,
                )

        except Exception as e:
            status = "Failed"
            error = f"Auto-contouring failed for {patient_id}: {e}"
            pynet_logger.error(error)
            Globals.log_to_db("network", "ERROR", error, None)

        # Send RTSTRUCT to configured DICOM destination
        try:
            if Globals.selected_server:
                serverAET, serverIP, serverPort = Globals.selected_server[1:4]
                Globals.setup_screen.contouringStatus.setText(
                    f"Transferring RTSTRUCT to {serverAET}"
                )
                send_c_store(serverAET, serverIP, int(serverPort), struct_path)
            else:
                status = "Failed"
                error = f"Failed to transfer RTSTRUCT for {patient_id}: No server selected."
                pynet_logger.error(error)
                Globals.log_to_db("network", "ERROR", error, None)

        except Exception as e:
            status = "Failed"
            error = f"Failed RTSTRUCT transfer for {patient_id}: {e}"
            pynet_logger.error(error)
            Globals.log_to_db("network", "ERROR", error, None)

        # Cleanup processed data
        shutil.rmtree(slices_path, ignore_errors=True)
        shutil.rmtree(struct_path, ignore_errors=True)

        # Remove stored_paths entry for this patient, modality, and series
        try:
            del Globals.stored_paths[patient_id][modality][series_uid]
            if not Globals.stored_paths[patient_id][
                modality
            ]:  # If modality dict is emtpy, remove it
                del Globals.stored_paths[patient_id][modality]
            if not Globals.stored_paths[patient_id]:  # If patient dict is empty, remove it
                del Globals.stored_paths[patient_id]
        except KeyError:
            warn = (
                f"Could not remove stored_paths entry for {patient_id}, {modality}, {series_uid}"
            )
            pynet_logger.warning(warn)
            Globals.log_to_db("network", "WARNING", warn, None)

        # Get thread-local database connection
        conn, cursor = Globals.get_db_connection()

        # Update database history
        try:
            query = (
                "INSERT INTO history (patientName, patientID, time, status, errors) "
                "VALUES (?, ?, ?, ?, ?)"
            )
            cursor.execute(
                query,
                (
                    str(patient_name),
                    patient_id,
                    str(datetime.datetime.now()),
                    status,
                    error,
                ),
            )
            conn.commit()

        except Exception as e:
            error = f"Database logging failed: {str(e)}"
            pynet_logger.error(error)
            Globals.log_to_db("network", "ERROR", error, None)

        Globals.close_db_connection()
        # Reset UI Status
        Globals.setup_screen.contouringStatus.setText("")


class StorageSCU:
    """A DICOM SCU for C-Store requests."""

    def __init__(self, recAET: str, recIP: str, recPort: Union[str, int]) -> None:
        """Initialize the SCU with the given parameters.

        Parameters
        ----------
        recAET : str
            The called AE title.
        recIP : str
            The called AE IPv4 address.
        recPort : Union[str, int]
            The called AE port number.
        """
        self.recAET = recAET
        self.recIP = recIP
        self.recPort = int(recPort)

        self.ae = AE("MRPAC")
        self.ae.requested_contexts = StoragePresentationContexts

    def c_store(self, dcmFile_path: str) -> None:
        """Send C-Store request with the given DICOM file.

        Parameters
        ----------
        dcmFile_path : str
            The path to the DICOM file to be sent.
        """
        ds_file = dcmread(dcmFile_path)
        self.assoc = self.ae.associate(self.recIP, self.recPort, ae_title=self.recAET)
        if self.assoc.is_established:
            status = self.assoc.send_c_store(ds_file)
            if status:
                # If the storage request succeeded this will be 0x0000
                msg = "C-STORE request status: 0x{0:04x}".format(status.Status)
                pynet_logger.info(msg)
                Globals.log_to_db("network", "INFO", msg, None)
            else:
                msg = "Connection timed out, was aborted or received invalid response"
                pynet_logger.error(msg)
                Globals.log_to_db("network", "ERROR", msg, None)
            self.assoc.release()
        else:
            msg = "Association rejected, aborted or never connected"
            pynet_logger.error(msg)
            Globals.log_to_db("network", "ERROR", msg, None)


class StorageSCP:
    """A DICOM SCP that handles store requests."""

    slices_path = ""

    def __init__(self, aet: str, ip: str, port: Union[str, int]) -> None:
        """Initialize the SCP to handle store requests.

        Parameters
        ----------
        aet : str
            The AE title to use.
        ip : str
            The IPv4 address to use.
        port : Union[str, int]
            The port number to use (make sure it is not already used
            by another application on your computer).
        """
        self.scpAET = aet
        self.scpIP = ip
        self.scpPort = int(port)

        self.ae = AE(self.scpAET)

        # Add the supported presentation context (All Storage Contexts)
        self.ae.supported_contexts = StoragePresentationContexts
        self.ae.add_supported_context(Verification)

    def set_handlers(
        self,
        handle_open: EventHandlerType = None,
        handle_close: EventHandlerType = None,
        handle_store: EventHandlerType = None,
    ) -> None:
        """Set event handlers for this SCP.

        Parameters
        ----------
        handle_open : EventHandlerType, optional
            A handler function that is executed during connection
            establishment, by default None.
        handle_close : EventHandlerType, optional
            A handler function that is executed when association is
            released, by default None.
        handle_store : EventHandlerType, optional
            A handler function that is executed when C-Store requests
            are received, by default None.
        """
        self.handlers = []
        if handle_open:
            self.handle_open = handle_open
            self.handlers.append((evt.EVT_CONN_OPEN, self.handle_open))
        if handle_close:
            self.handle_close = handle_close
            self.handlers.append((evt.EVT_CONN_CLOSE, self.handle_close))
        if handle_store:
            self.handle_store = handle_store
            self.handlers.append((evt.EVT_C_STORE, self.handle_store))

    def start(self):
        """Start the DICOM SCP server."""
        Globals.log_to_db("network", "INFO", "Starting the DICOM SCP server ...")
        self.scp = self.ae.start_server(
            (self.scpIP, self.scpPort), block=False, evt_handlers=self.handlers
        )

    def stop(self):
        """Stop the DICOM SCP server."""
        Globals.log_to_db("network", "INFO", "Stopping the DICOM SCP server...")
        self.scp.unbind(evt.EVT_CONN_OPEN, self.handle_open)
        self.scp.bind(evt.EVT_CONN_CLOSE, self.handle_close)
        self.scp.shutdown()
