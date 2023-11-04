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
    ):
        """Initialize a contour object.

        Keyword Arguments:
            name -- The name of the contour object. (default: {None})
            mask -- The 3D binary mask for the contour. (default: {None})
            color -- ROIDisplayColor as RGB values. (default: {None})
            opacity -- The opacity of the contour. (default: {0.0})
            thickness -- The thickness of the contour. (default: {1})
            line_thickness -- The line thickness of the contour. (default: {2})
            ROIGenerationAlgorithm -- Type of algorithm used to generate ROI. (default: {""})
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

    def add_mask(self, mask: np.ndarray):
        """Add a binary mask of the contour as an array.

        Arguments:
            mask -- The 3D binary mask for the contour.
        """
        self.mask = mask

    def change_name(self, name: str):
        """Change the name of the contour object.

        Arguments:
            name -- The name of the contour object
        """
        self.name = name

    def change_color(self, color: list):
        """Change the color of the contour object.

        Arguments:
            color -- The ROIDisplayColor of the contour object as RGB.
        """
        self.color = color

    def change_opacity(self, opacity: float):
        """Change the opacity of the contour object.

        Arguments:
            opacity -- The opacity of the contour.
        """
        self.opacity = opacity

    def change_thickness(self, thickness: int):
        """Change the thickness of the contour object.

        Arguments:
            thickness -- The thickness of the contour object.
        """
        self.thickness = thickness

    def change_line_thickness(self, line_thickness: int):
        """Change the line thickness of the contour object.

        Arguments:
            line_thickness -- The line thickness of the contour object.
        """
        self.line_thickness = line_thickness

    def contour_generation_algorithm(self, alg: str):
        """The ROI generation algorithm.

        Arguments:
            alg -- The algorithm used to generate the contour binary mask.
            Choose from AUTOMATIC, SEMIAUTOMATIC, or MANUAL.
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

    def __init__(self, *contours: Contour):
        """Initializes an RTstruct object given contour objects."""
        self.contours = list(contours)
        self.series_description = ""
        self.structure_set_name = ""
        self.UID_PREFIX = "1.2.3"
        self.INSTANCE_UID = self.UID_PREFIX + ".1.1"

    def add_contour(self, contour: Contour):
        """Add a new `Contour` object to the `RTstruct` object.

        Arguments:
            contour -- A new `Contour` object.
        """
        self.contours.append(contour)

    def add_series_description(self, series_description: str):
        """Add a series description to the RTstruct object.

        Arguments:
            series_description -- A description of the `RTstruct` object.
        """
        self.series_description = series_description

    def add_structure_set_name(self, structure_set_name: str):
        """Add a structure set name to the `RTstruct` object.

        Arguments:
            structure_set_name -- A structure set name to be added
            when generating the RTstruct DICOM file.
        """
        self.structure_set_name = structure_set_name

    def change_media_storage_uid(self, UID: str):
        """Change the media storage SOP instance UID prefix.

        The defualt UID prefix is not DICOM compliant.
        In addition, the InstanceUID by default is the given UID + '.1.1` + str(time.time()).
        It can be changed by using the `change_instance_uid` function.

        Arguments:
            UID -- A DICOM UID prefix for the media storage SOP instance UID.
        """
        self.UID_PREFIX = UID
        self.INSTANCE_UID = self.UID_PREFIX + ".1.1" + "".join(str(time.time()).split("."))

    def change_instance_uid(self, instanceUID: str):
        """Change the SOP Instance UID.

        Arguments:
            instanceUID -- The new SOP Instance UID.
        """
        self.INSTANCE_UID = instanceUID

    def build(self, input_dicom_path: str):
        """Build a Pydicom `Dataset` object of an RTstruct CIOD.

        Arguments:
            input_dicom_path -- The path to the DICOM images that is going
            to be referenced by this RTstruct `Dataset` object.
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
        file_meta.MediaStorageSOPInstanceUID = self.INSTANCE_UID
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # (Implicit VR Little Endian)
        file_meta.ImplementationClassUID = self.UID_PREFIX + ".1"
        file_meta.ImplementationVersionName = ""

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
        self.ds_struct.SOPInstanceUID = self.INSTANCE_UID
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
        self.ds_struct.SoftwareVersions = "1.3"
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
        self.ds_struct.SeriesInstanceUID = self.INSTANCE_UID
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
