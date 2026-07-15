"""A module for Autocontouring MR images with models trained with VNET."""

import argparse
import logging
import os
from typing import Union
import traceback
import numpy as np
import torch
from mrpac._globals import Globals
from mrpac.Utils import (
    get_consensus_mask,
    get_pixels,
    load_scan,
    preprocess_mri,
    run_mr_pelvis_inference,
)
from rt_utils import ds_helper, RTStruct
from pydicom.uid import generate_uid
import time


class AutocontourMR:
    """A class to autocontour pelvis MR images from ViewRay."""

    def __init__(
        self,
        slices_path: str,
        struct_path: str,
        uid_prefix: str,
        logger: Union[logging.Logger, None],
    ) -> None:
        """Initialize the `Autocontour` class with the given parameters.

        Parameters
        ----------
        slices_path : str
            The path to the DICOM images.
        struct_path : str
            The path where RTstruct file will be written.
        uid_prefix : str
            DICOM compliant UID prefix to use.
        logger : logging.Logger
            A logger object for logging.
        """
        self.slices_path = slices_path
        self.struct_path = struct_path
        self.models_directory = Globals.MODELS_DIRECTORY
        self.uid_prefix = uid_prefix
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(logging.StreamHandler())

    def run(self):
        """Run the autocontour algorithm."""
        # load the DICOM image and pre-process it
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            model_name = "vnet_mrpac_2025-04-01.pth"
            model = torch.load(
                os.path.join(self.models_directory, "vnet_mrpac", model_name),
                weights_only=False,
            )
            model.name = model_name
            model.eval()
        except Exception as e:
            print(str(e))

        slices = load_scan(self.slices_path)
        stack_pixels = get_pixels(slices)

        stride = 8

        input_tensor, original_depth = preprocess_mri(stack_pixels, stack_size=64, stride=stride)

        output_pred = run_mr_pelvis_inference(model, input_tensor, 5, device)

        output_per_class = output_pred.cpu().to(torch.uint8).permute(1, 0, 2, 3, 4)
        mask_list_per_class = [list(class_tensor.numpy()) for class_tensor in output_per_class]

        gt_colors = {
            "Bladder": [255, 255, 0],
            "Rectum": [165, 80, 65],
            "Femur_Head_R": [154, 205, 50],
            "Femur_Head_L": [255, 0, 0],
        }
        classes_key = {"Bladder": 1, "Rectum": 2, "Femur_Head_R": 3, "Femur_Head_L": 4}

        all_masks = []
        for key, indx in classes_key.items():
            mask = get_consensus_mask(
                mask_list_per_class[indx],
                stack_size=64,
                original_shape=stack_pixels.shape,
                stride=stride,
            )
            color = gt_colors[key]
            mask = np.moveaxis(mask, 0, -1)
            mask = mask > 0
            all_masks.append((mask, color, key))

        ds = ds_helper.create_rtstruct_dataset(slices)
        rtstruct = RTStruct(slices, ds)
        rtstruct.ds.Manufacturer = "ROSAML"
        rtstruct.ds.InstitutionName = ""
        rtstruct.ds.ManufacturerModelName = "MRPAC"
        rtstruct.frame_of_reference_uid = rtstruct.ds.ReferencedFrameOfReferenceSequence[
            -1
        ].FrameOfReferenceUID
        rtstruct.ds.SeriesDescription = "VR Pelvis Auto Contours Corrected"
        rtstruct.ds.StructureSetName = "PelvisAutoContours"
        rtstruct.ds.SeriesDate = rtstruct.ds.InstanceCreationDate
        rtstruct.ds.SeriesTime = rtstruct.ds.InstanceCreationTime

        if self.uid_prefix:
            rtstruct.ds.SeriesInstanceUID = (
                self.uid_prefix + "1.2.1." + "".join(str(time.time()).split("."))
            )
            rtstruct.ds.SOPInstanceUID = (
                self.uid_prefix + "1.3.1." + "".join(str(time.time()).split("."))
            )
        else:
            rtstruct.ds.SeriesInstanceUID = generate_uid(prefix=self.uid_prefix)
            rtstruct.ds.SOPInstanceUID = generate_uid(prefix=self.uid_prefix)

        for el in all_masks:
            rtstruct.add_roi(mask=el[0], color=el[1], name=el[2], approximate_contours=False)

        # Save the RTstruct DICOM file
        if not os.path.exists(self.struct_path):
            os.makedirs(self.struct_path)
        RTDCM_path = os.path.join(self.struct_path, "AutoContour.dcm")
        try:
            rtstruct.ds.save_as(RTDCM_path)
            msg = (
                "Saved RTSTRUCT for "
                + str(rtstruct.ds.PatientName)
                + " "
                + str(rtstruct.ds.PatientID)
            )
            self.logger.info(msg)

        except Exception as e:
            self.logger.error(e)
            self.logger.debug(e, exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-Contour MR images from ViewRay")
    parser.add_argument("Data_path", type=str, help="Path to the DICOM slices")
    parser.add_argument(
        "RTSTruct_output_path",
        type=str,
        help="Path to where to save the RTSTruct DICOM file",
    )
    parser.add_argument(
        "UID_PREFIX", type=str, help="A DICOM UID_PREFIX to use when generating UIDs"
    )
    args = parser.parse_args()

    slices_path = args.Data_path
    output_path = args.RTSTruct_output_path
    if args.UID_PREFIX != "None":
        UID_PREFIX = args.UID_PREFIX
    else:
        UID_PREFIX = None

    autocontour_logger = logging.getLogger("autocontour")
    autocontour_logger.setLevel(logging.DEBUG)
    file_handler_autocontour = logging.FileHandler(
        os.path.join(Globals.LOGS_DIRECTORY, "autocontour.log")
    )
    file_handler_autocontour.setFormatter(Globals.LOG_FORMATTER)
    autocontour_logger.addHandler(file_handler_autocontour)

    try:
        autocontour_pelvis = AutocontourMR(
            slices_path, output_path, UID_PREFIX, autocontour_logger
        )
        autocontour_pelvis.run()
    except Exception as e:
        autocontour_logger.error(e)
        autocontour_logger.debug(e, exc_info=True)
        stack_trace = traceback.format_exc()
