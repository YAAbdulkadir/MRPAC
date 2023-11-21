"""A module for Autocontouring MR images with models trained with UNet++ and VNET."""
import os
import logging
import argparse

from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K

from .RTstruct import RTstruct, Contour
from .Utils import (load_scan, get_pixels, 
                    mean_zero_normalization_3d, 
                    post_process_fmrt,post_process_fmlt, 
                    autocontour_bladder, 
                    get_consensus_mask, 
                    post_process_bldr, 
                    autocontour_rectum, 
                    get_middle_contour, 
                    post_process_rctm,
                    ) 
from ._globals import MODELS_DIRECTORY


class Autocontour:
    """A class to autocontour pelvis MR images from ViewRay."""

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
        self.models_directory = MODELS_DIRECTORY
        self.uid_prefix = uid_prefix
        self.logger = logger

    def run(self):
        """Run the autocontour algorithm."""
        # load the DICOM image and pre-process it
        slices = load_scan(self.slices_path)
        stack_pixels = get_pixels(slices)
        normalized_pixels = mean_zero_normalization_3d(stack_pixels)

        # load the model for the right femoral head
        fmrt_model = load_model(
            os.path.join(self.models_directory, "model_femr_rt_10_16"), compile=False
        )

        # get the mask for the right femoral head
        preds_fmrt = fmrt_model.predict(normalized_pixels, verbose=0)
        preds_fmrt = preds_fmrt > 0.5

        # run post-processing for the right femoral head
        try:
            preds_fmrt, fmrt_max = post_process_fmrt(preds_fmrt)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)

        # clear the session and load the model for the left femoral head
        K.clear_session()
        fmlt_model = load_model(
            os.path.join(self.models_directory, "model_femr_lt_10_17"), compile=False
        )

        # get the mask for the left femoral head
        preds_fmlt = fmlt_model.predict(normalized_pixels, verbose=0)
        preds_fmlt = preds_fmlt > 0.5

        # run the post-processing for the left femoral head
        try:
            preds_fmlt, fmlt_max = post_process_fmlt(preds_fmlt)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)

        # clear the session and load the model for the bladder
        K.clear_session()
        bldr_model = load_model(
            os.path.join(self.models_directory, "bladder_full_3D"), compile=False
        )

        # get the mask for the bladder
        list_bldr = autocontour_bladder(bldr_model, normalized_pixels)
        # preds_bldr = get_middle_contour(list_bldr, 32)
        preds_bldr = get_consensus_mask(list_bldr, 32)

        # run the post-processing for the bladder
        try:
            preds_bldr = post_process_bldr(preds_bldr)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)

        # clear the session and load the model for the rectum
        K.clear_session()
        rctm_model = load_model(
            os.path.join(self.models_directory, "rectum_cropped_3D"), compile=False
        )

        # get the mask for the rectum
        list_rctm = autocontour_rectum(rctm_model, normalized_pixels)
        preds_rctm = get_middle_contour(list_rctm, 32)

        # determine the most superior slice for femoral heads and set the superior
        # most contour of the rectum based on that
        fm_max = None
        if fmrt_max is not None:
            fm_max = fmrt_max
        elif fmlt_max is not None:
            fm_max = fmlt_max

        # run the post-processing for the rectum
        try:
            preds_rctm = post_process_rctm(preds_rctm, fm_max)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)

        # Create a contour object for each contour
        fmrt_contour = Contour(name="O_Femr_rt", mask=preds_fmrt, color=[0, 255, 0])
        fmrt_contour.contour_generation_algorithm("AUTOMATIC")
        fmlt_contour = Contour(name="O_Femr_lt", mask=preds_fmlt, color=[255, 0, 0])
        fmlt_contour.contour_generation_algorithm("AUTOMATIC")
        bldr_contour = Contour(name="O_Bldr", mask=preds_bldr, color=[255, 255, 0])
        bldr_contour.contour_generation_algorithm("AUTOMATIC")
        rctm_contour = Contour(name="O_Rctm", mask=preds_rctm, color=[191, 146, 96])
        rctm_contour.contour_generation_algorithm("AUTOMATIC")

        # Create a RTstruct object and add all the contours
        rtstruct = RTstruct(fmrt_contour, fmlt_contour, bldr_contour, rctm_contour)
        rtstruct.add_series_description("MRPAutoContour")
        rtstruct.add_structure_set_name("PelvisAutoContours")
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
    from _globals import (
        LOGS_DIRECTORY,
        LOG_FORMATTER,
        UID_PREFIX,
    )

    parser = argparse.ArgumentParser(description="Auto-Contour femr_rt")
    parser.add_argument("Data_path", type=str, help="Path to the DICOM slices")
    parser.add_argument(
        "RTSTruct_output_path", type=str, help="Path to where to save the RTSTruct DICOM file"
    )
    args = parser.parse_args()

    slices_path = args.Data_path
    output_path = args.RTSTruct_output_path

    autocontour_logger = logging.getLogger("autocontour")
    autocontour_logger.setLevel(logging.DEBUG)
    file_handler_autocontour = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "autocontour.log"))
    file_handler_autocontour.setFormatter(LOG_FORMATTER)
    autocontour_logger.addHandler(file_handler_autocontour)

    try:
        autocontour_pelvis = Autocontour(slices_path, output_path, UID_PREFIX, autocontour_logger)
        autocontour_pelvis.run()
    except Exception as e:
        autocontour_logger.error(e)
        autocontour_logger.debug(e, exc_info=True)
