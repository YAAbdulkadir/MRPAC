"""A module for DICOM networking using pynetdicom."""

import logging
from typing import Int, Union
from ping3 import ping
from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.sop_class import Verification
from pynetdicom.events import EventHandlerType
from ._globals import LOGS_DIRECTORY, LOG_FORMATTER

# Initialize the Logger files
pynet_logger = logging.getLogger("network")

evt.EVT_PDU_RECV


def validEntry(input_text: Union[str, Int], entry_type: str) -> bool:
    """Checks whether a text input from the user contains invalid
    characters.

    Parameters
    ----------
    input_text : Union[str, Int]
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


def verifyEcho(scpAET: str, aet: str, ip: str, port: Union[str, Int]) -> str:
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
    port : Union[str, Int]
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


class StorageSCU:
    """A DICOM SCU for C-Store requests."""

    def __init__(self, recAET: str, recIP: str, recPort: Union[str, Int]) -> None:
        """Initialize the SCU with the given parameters.

        Parameters
        ----------
        recAET : str
            The called AE title.
        recIP : str
            The called AE IPv4 address.
        recPort : Union[str, Int]
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
                pynet_logger.info("C-STORE request status: 0x{0:04x}".format(status.Status))
            else:
                pynet_logger.error(
                    "Connection timed out, was aborted or received invalid response"
                )
            self.assoc.release()
        else:
            pynet_logger.error("Association rejected, aborted or never connected")


class StorageSCP:
    """A DICOM SCP that handles store requests."""

    slices_path = ""

    def __init__(self, aet: str, ip: str, port: Union[str, Int]) -> None:
        """Initialize the SCP to handle store requests.

        Parameters
        ----------
        aet : str
            The AE title to use.
        ip : str
            The IPv4 address to use.
        port : Union[str, Int]
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

    def set_handlers(self, handle_open: EventHandlerType=None, handle_close: EventHandlerType=None, handle_store: EventHandlerType=None) -> None:
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
        self.scp = self.ae.start_server(
            (self.scpIP, self.scpPort), block=False, evt_handlers=self.handlers
        )

    def stop(self):
        """Stop the DICOM SCP server."""
        self.scp.unbind(evt.EVT_CONN_OPEN, self.handle_open)
        self.scp.bind(evt.EVT_CONN_CLOSE, self.handle_close)
        self.scp.shutdown()
