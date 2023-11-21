"""A module for Autocontouring CT images using TotalSegmentator."""
import os
import sys
import logging
import argparse
import numpy as np
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator


from .RTstruct import RTstruct, Contour


class AutocontourCT:
    """A class to autocontour CT images."""

    def __init__(self, slices_path, struct_path, uid_prefix, logger):
        """Initialize the `Autocontour` class with the given parameters.

        Arguments:
            slices_path -- The path to the DICOM images.
            struct_path -- The path where RTstruct file will be written.
            uid_prefix -- DICOM compliant UID prefix to use.
            logger -- A logger object.
        """
        self.slices_path = slices_path
        self.struct_path = struct_path
        self.uid_prefix = uid_prefix
        self.logger = logger

    def load_nifti(self, path):
        """_summary_

        Parameters
        ----------
        path : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """
        segs_list = os.listdir(path)
        all_masks = {}
        for segs_path in segs_list:
            mask = nib.load(os.path.join(path, segs_path))
            if np.max(mask.get_fdata()) > 0:
                mask_arr = mask.get_fdata()
                mask_arr = np.rot90(mask_arr)
                mask_arr = np.transpose(mask_arr, (2, 0, 1))
                all_masks[segs_path.split(".")[0]] = mask_arr

        return all_masks

    def run(self):
        """Run the autocontour algorithm."""
        try:
            totalsegmentator(self.slices_path, self.struct_path)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)
            sys.exit(1)

        all_contours = self.load_nifti(self.struct_path)

        # Create an empty RTstruct object
        rtstruct = RTstruct()

        # Create a Contour object for all the segmentation results
        # and add them to the RTstruct object
        for contour_name, contour_mask in all_contours.items():
            contour = Contour(name=contour_name, mask=contour_mask)
            contour.contour_generation_algorithm("AUTOMATIC")
            rtstruct.add_contour(contour)

        rtstruct.add_series_description("TotalSegAutoContours")
        rtstruct.add_structure_set_name("Autocontours")
        rtstruct.change_media_storage_uid(self.uid_prefix)

        # Build the RTstruct
        rtstruct.build(self.slices_path)

        # Save the RTstruct DICOM file
        if not os.path.exists(self.struct_path):
            os.makedirs(self.struct_path)
        RTDCM_path = os.path.join(self.struct_path, "AutoContour.dcm")
        try:
            rtstruct.save_as(RTDCM_path)
            self.logger.info(
                str(rtstruct.ds_struct.PatientName)
                + " "
                + str(rtstruct.ds_struct.PatientID)
                + " : "
                + "saved structure set"
            )
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)


if __name__ == "__main__":
    from _globals import LOGS_DIRECTORY, LOG_FORMATTER, UID_PREFIX

    parser = argparse.ArgumentParser(description="Auto-Contour femr_rt")
    parser.add_argument("Data_path", type=str, help="Path to the DICOM slices")
    parser.add_argument(
        "RTSTruct_output_path", type=str, help="Path to where to save the RTSTruct DICOM file"
    )
    args = parser.parse_args()

    slices_path = args.Data_path
    output_path = args.RTSTruct_output_path

    autocontour_logger = logging.getLogger("autocontour_ct")
    autocontour_logger.setLevel(logging.DEBUG)
    file_handler_autocontour = logging.FileHandler(
        os.path.join(LOGS_DIRECTORY, "autocontour_ct.log")
    )
    file_handler_autocontour.setFormatter(LOG_FORMATTER)
    autocontour_logger.addHandler(file_handler_autocontour)

    try:
        autocontour_pelvis = AutocontourCT(slices_path, output_path, UID_PREFIX, autocontour_logger)
        autocontour_pelvis.run()
    except Exception as e:
        autocontour_logger.error(e)
        autocontour_logger.debug(e, exc_info=True)
