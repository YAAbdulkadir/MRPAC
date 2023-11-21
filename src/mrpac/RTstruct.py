"""A module for converting binary masks to DICOM Structure Set."""
import os
import random
import time
import datetime
import tempfile
import numpy as np
from skimage import measure

from pydicom.dataset import Dataset, FileMetaDataset, FileDataset
from pydicom.sequence import Sequence
from pydicom import dcmread
from pydicom.uid import generate_uid
from ._version import __version__


class Contour:
    """A mutable contour object."""

    def __init__(
        self,
        name: str = None,
        mask: np.ndarray = None,
        color: list = None,
        opacity: float = 0.0,
        thickness: int = 1,
        line_thickness: int = 2,
        ROIGenerationAlgorithm: str = "",
    ) -> None:
        """Initialize a contour object.

        Parameters
        ----------
        name : str, optional
            The name of the contour object, by default None.
        mask : np.ndarray, optional
            The 3D binary mask for the `Contour`, by default None.
        color : list, optional
            ROIDisplayColor as RGB values, by default None.
        opacity : float, optional
            The opacity of the contour, by default 0.0.
        thickness : int, optional
            The thickness of the contour, by default 1.
        line_thickness : int, optional
            The line thickness of the contour, by default 2.
        ROIGenerationAlgorithm : str, optional
            Type of algorithm used to generate ROI, by default "".
            Choose from:
            * AUTOMATIC
            * SEMIAUTOMATIC
            * MANUAL
        """
        self.name = name
        self.mask = mask
        self.color = color
        if color is None:
            self.color = random.sample(range(0, 256, 1), 3)
        self.opacity = opacity
        self.thickness = thickness
        self.line_thickness = line_thickness
        self.ROIGenerationAlgorithm = ROIGenerationAlgorithm

    def add_mask(self, mask: np.ndarray) -> None:
        """Add a binary mask of the contour as an array.

        Parameters
        ----------
        mask : np.ndarray
            The 3D binary mask for the contour.
        """
        self.mask = mask

    def change_name(self, name: str) -> None:
        """Change the name of the contour object.

        Parameters
        ----------
        name : str
            The name of the contour object.
        """
        self.name = name

    def change_color(self, color: list) -> None:
        """Change the color of the contour object.

        Parameters
        ----------
        color : list
            The ROIDisplayColor of the contour object as RGB.
        """
        self.color = color

    def change_opacity(self, opacity: float) -> None:
        """Change the opacity of the contour object.

        Parameters
        ----------
        opacity : float
            The opacity of the contour.
        """
        self.opacity = opacity

    def change_thickness(self, thickness: int) -> None:
        """Change the thickness of the contour object.

        Parameters
        ----------
        thickness : int
            The thickness of the contour object.
        """
        self.thickness = thickness

    def change_line_thickness(self, line_thickness: int) -> None:
        """Change the line thickness of the contour object.

        Parameters
        ----------
        line_thickness : int
            The line thickness of the contour object.
        """
        self.line_thickness = line_thickness

    def contour_generation_algorithm(self, alg: str) -> None:
        """The ROI generation algorithm.

        Parameters
        ----------
        alg : str
            The algorithm used to generate the contour binary mask.
            Choose from:
            * AUTOMATIC
            * SEMIAUTOMATIC
            * MANUAL
        """
        self.ROIGenerationAlgorithm = alg


class RTstruct:
    """An RTstruct object that can be constructed by adding contour objects.

    Examples
    --------
    Create a new RTstruct object and add a contour object to it.

    >>> mask = np.zeros((512,512,60), dtype=int)
    >>> mask[200:250,200:250,30:40] = 1
    >>> roi_1 = Contour(name='roi_1', mask=mask, color=[0,255,0])
    >>> roi_1.contour_generation_algorithm('manual')
    >>> rtstruct = RTstruct(roi_1)
    >>> rtstruct.add_structure_set_name('bounding box')
    >>> rtstruct.add_series_description('bounding box')
    >>> rtsturct.build('path_to_dicom_images')
    >>> rtstruct.save_as('path_to_new_file_location')
    """

    def __init__(self, *contours: Contour) -> None:
        """Initializes an RTstruct object given contour objects."""
        self.contours = list(contours)
        self.series_description = ""
        self.structure_set_name = ""
        self.UID_PREFIX = "1.2.826.0.1.3680043.8.498."
        self.SeriesInstanceUID = generate_uid()
        self.SOPInstanceUID = generate_uid()

    def add_contour(self, contour: Contour) -> None:
        """Add a new `Contour` object to the `RTstruct` object.

        Parameters
        ----------
        contour : Contour
            A new `Contour` object to add.
        """
        self.contours.append(contour)

    def add_series_description(self, series_description: str) -> None:
        """Add a series description to the `RTstruct` object.

        Parameters
        ----------
        series_description : str
            A description of the `RTstruct` object.
        """
        self.series_description = series_description

    def add_structure_set_name(self, structure_set_name: str) -> None:
        """Add a structure set name to the `RTstruct` object.

        Parameters
        ----------
        structure_set_name : str
            A structure set name to be added when generating
            the `DICOM Structure Set` file.
        """
        self.structure_set_name = structure_set_name

    def change_media_storage_uid(self, UID_prefix: str) -> None:
        """Change the media storage SOP Instance UID prefix.

        The default UID prefix that is used by this class is the
        `pydicom` UID prefix. If you have your own UID prefix, you
        can supply it here and it will use that. If you set it to
        `None`, the `pydicom.uid.generate_uid` function is used with
        the `prefix` set to `None` which will use the `uuid.uuid4()`
        algorithm to generate a unique UID for the SeriesInstanceUID
        and the SOPInstanceUID.

        Parameters
        ----------
        UID : str
            A DICOM UID prefix for the media storage SOP Instance UID.
        """
        self.UID_PREFIX = UID_prefix
        if self.UID_PREFIX:
            self.SeriesInstanceUID = self.UID_PREFIX + "1.2.1." + "".join(str(time.time()).split("."))
            self.SOPInstanceUID = self.UID_PREFIX + "1.3.1." + "".join(str(time.time()).split("."))
        else:
            self.SeriesInstanceUID = generate_uid(prefix=self.UID_PREFIX)
            self.SOPInstanceUID = generate_uid(prefix=self.UID_PREFIX)

    def change_instance_uid(self, instanceUID: str) -> None:
        """Change the SOP Instance UID.

        Parameters
        ----------
        instanceUID : str
            The new SOP Instance UID to use.
        """
        self.SOPInstanceUID = instanceUID

    def build(self, input_dicom_path: str) -> None:
        """Build a `pydicom.dataset.Dataset` object (RTstruct CIOD).

        Parameters
        ----------
        input_dicom_path : str
            The path to the DICOM images that is going to be referenced
            by the `Dataset` object being created.
        """
        self.input_dicom_path = input_dicom_path
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        current_time = datetime.datetime.now().strftime("%H%M%S.%f")
        # Create a dictionary of all contours with their mask and attributes
        all_rois = {}
        roi_number = 1
        for contour in self.contours:
            all_rois[contour.name] = {
                "coordinates": [],
                "mask_volume": np.squeeze(contour.mask.astype(float)),
                "color": contour.color,
                "roi_number": roi_number,
                "opacity": contour.opacity,
                "thickness": contour.thickness,
                "line_thickness": contour.line_thickness,
                "algorithm": contour.ROIGenerationAlgorithm,
            }
            roi_number = roi_number + 1

        # The UID specific to RTstruct modality
        self.RTSTRUCT_UID = "1.2.840.10008.5.1.4.1.1.481.3"

        # Collect DICOM files in a list and get the total number of DICOM files in the path
        dicom_files = next(os.walk(input_dicom_path))[2]
        dicom_files = [s for s in dicom_files if ".dcm" in s]
        num_dcm_imgs = len(dicom_files)

        # Read the DICOM files
        dcms = [os.path.join(input_dicom_path, f"{dcm_file}") for dcm_file in dicom_files]
        dcms = [dcmread(dcm) for dcm in dcms]

        # Sort the DICOM files based on their z position
        dcms.sort(key=lambda x: float(x.ImagePositionPatient[2]))

        # Get the first slice
        ds = dcms[0]

        # Find position of first slice
        patient_position = ds.ImagePositionPatient
        initial_z = ds.ImagePositionPatient[2]

        # Find the pixel spacings
        x_pixel_spacing = ds.PixelSpacing[0]
        y_pixel_spacing = ds.PixelSpacing[1]
        z_pixel_spacing = ds.SliceThickness

        # Convert the masks to contour points
        for key in all_rois.keys():
            # Loop over slices in volume, get contours for each slice
            for slice in range(all_rois[key]["mask_volume"].shape[0]):
                all_coordinates_this_slice = []
                # AllCoordinatesThisSlice = []
                image = all_rois[key]["mask_volume"][slice, :, :]
                # Get contours in this slice using scikit-image
                contours = measure.find_contours(image, 0.5)
                # Save contours for later use
                biggest_ = 0
                biggest_indx = None
                for c_indx in range(len(contours)):
                    if len(contours[c_indx]) > biggest_:
                        biggest_ = len(contours[c_indx])
                        biggest_indx = c_indx

                for n, contour in enumerate(contours):
                    if biggest_indx is not None:
                        if n == biggest_indx:
                            num_coordinates = len(contour[:, 0])
                            z_coordinates = slice * np.ones((num_coordinates, 1))
                            reg_contour = np.append(contour, z_coordinates, -1)
                            # Add patient position offset
                            # Assume no other orientations for simplicity and convert to mm
                            # instead of voxel location
                            reg_contour[:, 0] = (
                                reg_contour[:, 0] * y_pixel_spacing + patient_position[1]
                            )
                            reg_contour[:, 1] = (
                                reg_contour[:, 1] * x_pixel_spacing + patient_position[0]
                            )
                            reg_contour[:, 2] = reg_contour[:, 2] * z_pixel_spacing + initial_z
                            # Flatten the contour array (x,y corresponds to column,row)
                            coordinates = np.concatenate(
                                (
                                    np.expand_dims(reg_contour[:, 1], axis=-1),
                                    np.expand_dims(reg_contour[:, 0], axis=-1),
                                    np.expand_dims(reg_contour[:, 2], axis=-1),
                                ),
                                axis=1,
                            ).flatten("C")
                            coordinates = np.squeeze(coordinates)
                            all_coordinates_this_slice.append(coordinates)

                all_rois[key]["coordinates"].append(all_coordinates_this_slice)

        # Starting writing the rtstruct file
        # File meta info data elements
        file_meta = FileMetaDataset()
        file_meta.FileMetaInformationGroupLength = 194
        file_meta.FileMetaInformationVersion = b"\x00\x01"
        file_meta.MediaStorageSOPClassUID = (
            "1.2.840.10008.5.1.4.1.1.481.3"  # (RT Structure Set Storage)
        )
        file_meta.MediaStorageSOPInstanceUID = self.SOPInstanceUID
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # (Implicit VR Little Endian)
        if self.UID_PREFIX:
            file_meta.ImplementationClassUID = self.UID_PREFIX + "1"
        else:
            file_meta.ImplementationClassUID = "1.2.826.0.1.3680043.8.498" + ".1"
        file_meta.ImplementationVersionName = f"MRPAC_{__version__}"

        # Main data elements
        suffix = ".dcm"
        filename_little_endian = tempfile.NamedTemporaryFile(suffix=suffix).name
        self.ds_struct = FileDataset(
            filename_little_endian,
            dataset={},
            file_meta=file_meta,
            preamble=b"\0" * 128,
        )
        self.ds_struct.SpecificCharacterSet = "ISO_IR 100"
        self.ds_struct.InstanceCreationDate = current_date
        self.ds_struct.InstanceCreationTime = current_time
        self.ds_struct.SOPInstanceUID = self.SOPInstanceUID
        self.ds_struct.StudyDate = ds.StudyDate  # same as the image
        self.ds_struct.SeriesDate = current_date
        self.ds_struct.StudyTime = ds.StudyTime
        self.ds_struct.SeriesTime = current_time
        self.ds_struct.AccessionNumber = ds.AccessionNumber
        self.ds_struct.Manufacturer = ""
        self.ds_struct.ReferringPhysicianName = ds.ReferringPhysicianName
        self.ds_struct.StationName = ""
        try:
            self.ds_struct.StudyDescription = ds.StudyDescription
        except Exception:
            self.ds_struct.StudyDescription = ""

        self.ds_struct.ManufacturerModelName = ""
        self.ds_struct.PatientName = ds.PatientName
        self.ds_struct.PatientID = ds.PatientID
        self.ds_struct.PatientBirthDate = ds.PatientBirthDate
        self.ds_struct.PatientSex = ds.PatientSex
        self.ds_struct.PatientAge = ""
        self.ds_struct.SoftwareVersions = __version__
        self.ds_struct.StudyInstanceUID = ds.StudyInstanceUID
        self.ds_struct.SeriesNumber = ds.SeriesNumber
        self.ds_struct.StructureSetLabel = "RTstruct"
        self.ds_struct.StructureSetName = self.structure_set_name
        self.ds_struct.StructureSetDate = current_date
        self.ds_struct.StructureSetTime = current_time

        # Referenced Frame of Reference Sequence
        refd_frame_of_ref_sequence = Sequence()
        self.ds_struct.ReferencedFrameOfReferenceSequence = refd_frame_of_ref_sequence

        # Referenced Frame of Reference Sequence: Referenced Frame of Reference 1
        refd_frame_of_ref1 = Dataset()
        refd_frame_of_ref1.FrameOfReferenceUID = ds.FrameOfReferenceUID

        # RT Referenced Study Sequence
        rt_refd_study_sequence = Sequence()
        refd_frame_of_ref1.RTReferencedStudySequence = rt_refd_study_sequence

        # RT Referenced Study Sequence: RT Referenced Study 1
        rt_refd_study1 = Dataset()
        rt_refd_study1.ReferencedSOPClassUID = ds.SOPClassUID
        rt_refd_study1.ReferencedSOPInstanceUID = ds.SOPInstanceUID

        # RT Referenced Series Sequence
        rt_refd_series_sequence = Sequence()
        rt_refd_study1.RTReferencedSeriesSequence = rt_refd_series_sequence

        # RT Referenced Series Sequence: RT Referenced Series 1
        rt_refd_series1 = Dataset()
        rt_refd_series1.SeriesInstanceUID = ds.SeriesInstanceUID

        # Contour Image Sequence
        contour_image_sequence = Sequence()
        rt_refd_series1.ContourImageSequence = contour_image_sequence

        # Loop over all DICOM images
        for image in range(1, num_dcm_imgs + 1):
            dstemp = dcmread(
                os.path.join(input_dicom_path, f"{dicom_files[image-1]}"),
                stop_before_pixels=True,
            )
            # Contour Image Sequence: Contour Image
            contour_image = Dataset()
            contour_image.ReferencedSOPClassUID = dstemp.SOPClassUID
            contour_image.ReferencedSOPInstanceUID = dstemp.SOPInstanceUID
            contour_image_sequence.append(contour_image)

        rt_refd_series_sequence.append(rt_refd_series1)
        rt_refd_study_sequence.append(rt_refd_study1)
        refd_frame_of_ref_sequence.append(refd_frame_of_ref1)

        # Structure Set ROI Sequence
        structure_set_roi_sequence = Sequence()
        self.ds_struct.StructureSetROISequence = structure_set_roi_sequence

        # Loop over ROIs
        for key in all_rois.keys():
            structure_set_roi = Dataset()
            structure_set_roi.ROINumber = str(all_rois[key]["roi_number"])
            structure_set_roi.ReferencedFrameOfReferenceUID = ds.FrameOfReferenceUID
            structure_set_roi.ROIName = key
            structure_set_roi.ROIGenerationAlgorithm = all_rois[key]["algorithm"]
            structure_set_roi_sequence.append(structure_set_roi)

        # ROI Contour Sequence
        roi_contour_sequence = Sequence()
        self.ds_struct.ROIContourSequence = roi_contour_sequence

        # Loop over ROI contour sequences
        for key in all_rois.keys():
            # ROI Contour Sequence
            roi_contour = Dataset()
            roi_contour.ROIDisplayColor = all_rois[key]["color"]

            # Contour Sequence
            contour_sequence = Sequence()
            roi_contour.ContourSequence = contour_sequence

            # Loop over slices in volume (ROI)
            for slice in range(all_rois[key]["mask_volume"].shape[0]):
                # Loop over contour sequences in this slice
                numberOfContoursInThisSlice = len(all_rois[key]["coordinates"][slice])
                for c in range(numberOfContoursInThisSlice):
                    currentCoordinates = all_rois[key]["coordinates"][slice][c]

                    # Contour Sequence: Contour 1
                    contour = Dataset()

                    # Contour Image Sequence
                    contour_image_sequence = Sequence()
                    contour.ContourImageSequence = contour_image_sequence

                    # Load the corresponding dicom file to get the SOPInstanceUID
                    dstemp = dcmread(
                        os.path.join(input_dicom_path, f"{dicom_files[0]}"),
                        stop_before_pixels=True,
                    )

                    # Contour Image Sequence: Contour Image 1
                    contour_image = Dataset()
                    contour_image.ReferencedSOPClassUID = dstemp.SOPClassUID
                    contour_image.ReferencedSOPInstanceUID = dstemp.SOPInstanceUID
                    contour_image_sequence.append(contour_image)

                    contour.ContourGeometricType = "CLOSED_PLANAR"
                    contour.NumberOfContourPoints = len(currentCoordinates)
                    contour.ContourData = currentCoordinates.tolist()
                    contour_sequence.append(contour)

            roi_contour.ReferencedROINumber = all_rois[key]["roi_number"]
            roi_contour_sequence.append(roi_contour)

        # RT ROI Observations Sequence
        rtroi_observations_sequence = Sequence()
        self.ds_struct.RTROIObservationsSequence = rtroi_observations_sequence

        # Loop over ROI observations
        for key in all_rois.keys():
            # RT ROI Observations Sequence: RT ROI Observations 1
            rtroi_observations = Dataset()
            rtroi_observations.ObservationNumber = str(all_rois[key]["roi_number"])
            rtroi_observations.ReferencedROINumber = str(all_rois[key]["roi_number"])
            rtroi_observations.ROIObservationLabel = ""
            rtroi_observations.RTROIInterpretedType = "OAR"
            rtroi_observations.ROIInterpreter = ""
            rtroi_observations.ROIObservationDescription = (
                f"Type:Soft, \
                  Range:*/*, \
                  Fill:0, \
                  Opacity:{str(all_rois[key]['opacity'])}, \
                  Thickness:{str(all_rois[key]['thickness'])}, \
                  LineThickness:{str(all_rois[key]['line_thickness'])},\
                  read-only:false",
            )
            rtroi_observations.RTROIInterpretedType = ""
            rtroi_observations.ROIInterpreter = ""
            rtroi_observations_sequence.append(rtroi_observations)

        # Add RTSTRUCT specifics
        self.ds_struct.Modality = "RTSTRUCT"
        self.ds_struct.SOPClassUID = self.RTSTRUCT_UID
        self.ds_struct.SeriesDescription = self.series_description
        self.ds_struct.SeriesInstanceUID = self.SeriesInstanceUID
        self.ds_struct.ApprovalStatus = "UNAPPROVED"

        self.ds_struct.file_meta = file_meta
        self.ds_struct.is_implicit_VR = True
        self.ds_struct.is_little_endian = True

    def save_as(self, rtstruct_name="rtstruct.dcm"):
        """Write the object `self.ds_struct` to `rtstruct_name`.

        Args:
            rtstruct_name (str, optional):The path to and name of the RTstruct DICOM to write.
                                          Defaults to 'rtstruct.dcm'.
        """
        self.ds_struct.save_as(rtstruct_name)
