import os
import logging
import argparse

from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K

from RTstruct import RTstruct, Contour
import Utils


class Autocontour:
    """A class to autocontour pelvis MR images from ViewRay."""

    def __init__(self, mr_path, struct_path, uid_prefix, logger):
        """Initialize the `Autocontour` class with the given parameters.

        Arguments:
            mr_path -- The path the the MR images.
            struct_path -- The path where RTstruct file will be written.
            uid_prefix -- DICOM compliant UID prefix to use.
            logger -- A logger object.
        """
        self.mr_path = mr_path
        self.struct_path = struct_path
        self.parent_directory = os.path.abspath((os.path.join(os.getcwd(), "..")))
        self.models_directory = os.path.join(self.parent_directory, "models")
        self.uid_prefix = uid_prefix
        self.logger = logger

    def run(self):
        """Run the autocontour algorithm."""
        # load the mr image and pre-process it
        slices = Utils.load_scan(self.mr_path)
        stack_pixels = Utils.get_pixels(slices)
        normalized_pixels = Utils.mean_zero_normalization_3d(stack_pixels)

        # load the model for the right femoral head
        fmrt_model = load_model(
            os.path.join(self.models_directory, "model_femr_rt_10_16"), compile=False
        )

        # get the mask for the right femoral head
        preds_fmrt = fmrt_model.predict(normalized_pixels, verbose=0)
        preds_fmrt = preds_fmrt > 0.5

        # run post-processing for the right femoral head
        try:
            preds_fmrt, fmrt_max = Utils.post_process_fmrt(preds_fmrt)
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
            preds_fmlt, fmlt_max = Utils.post_process_fmlt(preds_fmlt)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)

        # clear the session and load the model for the bladder
        K.clear_session()
        bldr_model = load_model(
            os.path.join(self.models_directory, "bladder_full_3D"), compile=False
        )

        # get the mask for the bladder
        list_bldr = Utils.autocontour_bladder(bldr_model, normalized_pixels)
        # preds_bldr = get_middle_contour(list_bldr, 32)
        preds_bldr = Utils.get_consensus_mask(list_bldr, 32)

        # run the post-processing for the bladder
        try:
            preds_bldr = Utils.post_process_bldr(preds_bldr)
        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)

        # clear the session and load the model for the rectum
        K.clear_session()
        rctm_model = load_model(
            os.path.join(self.models_directory, "rectum_cropped_3D"), compile=False
        )

        # get the mask for the rectum
        list_rctm = Utils.autocontour_rectum(rctm_model, normalized_pixels)
        preds_rctm = Utils.get_middle_contour(list_rctm, 32)

        # determine the most superior slice for femoral heads and set the superior most contour of the
        # rectum based on that
        fm_max = None
        if fmrt_max is not None:
            fm_max = fmrt_max
        elif fmlt_max is not None:
            fm_max = fmlt_max

        # run the post-processing for the rectum
        try:
            preds_rctm = Utils.post_process_rctm(preds_rctm, fm_max)
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
        rtstruct.build(self.mr_path)

        # Save the RTstruct DICOM file
        if not os.path.exists(self.struct_path):
            os.makedirs(self.struct_path)
        RTDCM_path = os.path.join(self.struct_path, "MRPAutoContour.dcm")
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
    parser = argparse.ArgumentParser(description="Auto-Contour femr_rt")
    parser.add_argument("Data_path", type=str, help="Path to the DICOM slices")
    parser.add_argument(
        "RTSTruct_output_path", type=str, help="Path to where to save the RTSTruct DICOM file"
    )
    args = parser.parse_args()

    slices_path = args.Data_path
    output_path = args.RTSTruct_output_path
    PARENT_DIRECTORY = os.path.abspath((os.path.join(os.getcwd(), "..")))
    MODELS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "models")
    RESOURCES_DIRECTORY = os.path.join(PARENT_DIRECTORY, "resources")
    LOGS_DIRECTORY = os.path.join(PARENT_DIRECTORY, "logs")

    uid_file = os.path.join(RESOURCES_DIRECTORY, "uid_prefix.txt")

    LOG_FORMATTER = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s:%(lineno)d")
    autocontour_logger = logging.getLogger("autocontour")
    autocontour_logger.setLevel(logging.DEBUG)
    file_handler_autocontour = logging.FileHandler(os.path.join(LOGS_DIRECTORY, "autocontour.log"))
    file_handler_autocontour.setFormatter(LOG_FORMATTER)
    autocontour_logger.addHandler(file_handler_autocontour)
    try:
        with open("uid_file", "r") as uid:
            uid_prefix = uid.readline()
    except FileNotFoundError:
        uid_predix = "1.2.3.4.5"

    try:
        autocontour_pelvis = Autocontour(slices_path, output_path, uid_prefix, autocontour_logger)
        autocontour_pelvis.run()
    except Exception as e:
        autocontour_logger.error(e)
        autocontour_logger.debug(e, exc_info=True)
