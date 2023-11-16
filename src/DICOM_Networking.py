import os
import logging
from ping3 import ping
from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelMove,
    MRImageStorage,
    Verification,
)
from _globals import LOGS_DIRECTORY, LOG_FORMATTER

# Initialize the Logger files
pynet_logger = logging.getLogger("network")
pynet_logger.setLevel(logging.DEBUG)
file_handler_pynet = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "network.log"))
file_handler_pynet.setFormatter(LOG_FORMATTER)
pynet_logger.addHandler(file_handler_pynet)

evt.EVT_PDU_RECV


def validEntry(input_text, entry_type):
    """
    Checks whether a text input from the user contains invalid characters.
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


def pingTest(ip):
    """
    Verififes whether the ip address typed accepts packets over the network.
    """

    response = ping(ip, timeout=0.01)

    if response is None:
        return "Failed"
    elif response is False:
        return "Failed"
    else:
        return "Success"


def verifyEcho(scpAET, aet, ip, port):
    """
    Verifies whether a DICOM handshake can be established
    given an AE title, IP address and port number.
    """

    ae = AE(scpAET)
    ae.add_requested_context(Verification)
    assoc = ae.associate(ip, port, ae_title=aet)
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


class StorageSCU:
    """A DICOM SCU for C-Store requests."""

    def __init__(self, recAET, recIP, recPort):
        """Initialize the SCU with the given parameters.

        Arguments:
            recAET -- The called AE title.
            recIP -- _The called AE IP address.
            recPort -- The called AE port number.
        """
        self.recAET = recAET
        self.recIP = recIP
        self.recPort = recPort

        self.ae = AE("MRPAC")
        self.ae.requested_contexts = StoragePresentationContexts

    def c_store(self, dcmFile_path):
        """Send C-Store request with the given DICOM file.

        Arguments:
            dcmFile_path -- The path to the DICOM file to be sent.
        """

        ds_file = dcmread(dcmFile_path)
        self.assoc = self.ae.associate(self.recIP, self.recPort, ae_title=self.recAET)
        if self.assoc.is_established:
            status = self.assoc.send_c_store(ds_file)
            if status:
                # If the storage request succeeded this will be 0x0000
                pynet_logger.info("C-STORE request status: 0x{0:04x}".format(status.Status))
            else:
                pynet_logger.error(
                    "Connection timed out, was aborted or received invalid response"
                )
            self.assoc.release()
        else:
            pynet_logger.error("Association rejected, aborted or never connected")


class MoveSCP:
    """A DICOM SCP that handles move requests."""

    slices_path = ""

    def __init__(self, aet, ip, port):
        """Initialize the SCP to handle move requests.

        Arguments:
            aet -- The AE title to use.
            ip -- The IP address to use.
            port -- The port number to use.
        """
        self.scpAET = aet
        self.scpIP = ip
        self.scpPort = port

        self.ae = AE(self.scpAET)
        # Add the requested presentation contexts (Storage SCU)
        self.ae.requested_contexts = StoragePresentationContexts
        # Add a supported presentation context (QR Move SCP)
        self.ae.add_supported_context(PatientRootQueryRetrieveInformationModelMove)
        self.ae.add_supported_context(MRImageStorage)
        self.ae.add_supported_context(Verification)

    def set_handlers(self, handle_open=None, handle_close=None, handle_store=None):
        """Set event handlers for this SCP.

        Keyword Arguments:
            handle_open -- A function to execute during connection establishment. (default: {None})
            handle_close -- A function to execute when association is released. (default: {None})
            handle_store -- A function that handles C-Store requests. (default: {None})
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
        self.scp = self.ae.start_server(
            (self.scpIP, self.scpPort), block=False, evt_handlers=self.handlers
        )

    def stop(self):
        """Stop the DICOM SCP server."""
        self.scp.unbind(evt.EVT_CONN_OPEN, self.handle_open)
        self.scp.bind(evt.EVT_CONN_CLOSE, self.handle_close)
        self.scp.shutdown()
