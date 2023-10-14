import os
import numpy as np
import SimpleITK as sitk
from skimage.morphology import ball
from scipy import ndimage

from pydicom import dcmread


def load_scan(path):
    """Load all DICOM images in path into a list for manipulation.

    Arguments:
        path -- The path to a directory containing DICOM files.

    Returns:
        List of Dicom slices sorted according to their location on the
        patient axis from inferior to superior.
    """

    slices = [dcmread(os.path.join(path, s)) for s in os.listdir(path) if ".dcm" in s]
    slices.sort(key=lambda x: float(x.SliceLocation))

    # Get the slice thickness to use for mapping with RTstruct DICOM file
    try:
        slice_thickness = np.abs(
            slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2]
        )
    except Exception:
        slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)

    for s in slices:
        s.SliceThickness = slice_thickness

    return slices


def get_pixels(slices):
    """Extract pixel data from DICOM slices and return as array.

    Arguments:
        slices -- List of DICOM slices.

    Returns:
        Numpy array of the pixel data of the slices.
    """
    image = np.stack([s.pixel_array for s in slices])
    image = image.astype(float)

    return image


def mean_zero_normalization(arr):
    """Process 2D gray-scale images to have a mean of zero and std of 1.

    First a simple thresholding is applied to get the body mask,
    then statistics from the body region is used to center and normalize
    the array.

    Arguments:
        arr -- The 2D image to be normalized.

    Returns:
        The normalized image.
    """

    thresholded_pos = arr[arr > 50]
    mean = np.mean(thresholded_pos)
    std = np.std(thresholded_pos)
    arr = (arr - mean) / std
    arr[arr > 5] = 5
    arr[arr < -5] = -5
    arr = arr + abs(np.min(arr))
    arr = arr / np.max(arr)

    return arr


def mean_zero_normalization_3d(arr):
    """Process 3D gray-scale image to have a mean of zero and std of 1.

    Arguments:
        arr -- The 3D image to be normalized.

    Returns:
        The normalized image.
    """

    img_dims = arr.shape
    img_depth = img_dims[0]
    for i in range(img_depth):
        arr[i] = mean_zero_normalization(arr[i])

    return arr


def autocontour_bladder(model, imgs):
    """Predict a binary mask for bladder given the model and a 3D image.

    Given a 3D MR image with dimensions (288, img_rows, img_columns, img_channels),
    predict segmentation masks for a stack of 32 slices (first axis) in a sliding
    window fashion with step size of 1.

    Arguments:
        model -- A tensorflow model for bladder segmentation.
        imgs -- A 3D MR image.

    Returns:
        List of binary mask predictions.
    """

    iters = 288 - 32 + 1
    predictions = []
    for i in range(iters):
        img = imgs[i : i + 32, ...]
        img = np.expand_dims(img, axis=0)
        predicted = model.predict(img)
        predictions.append(predicted > 0.5)

    return predictions


def autocontour_rectum(model, imgs):
    """Predict a binary mask for rectum given the model and a 3D image.

    Given a 3D MR image with dimensions (288, img_rows, img_columns, img_channels),
    predict segmentation masks for a stack of 32 slices (first axis) in a sliding
    window fashion with step size of 1.

    Arguments:
        model -- A tensorflow model for rectum segmentation.
        imgs -- A 3D MR image.

    Returns:
        List of binary mask predictions.
    """

    cropped = imgs[:, 100:228, 100:228]
    cropped = np.expand_dims(cropped, axis=-1)
    iters = 288 - 32 + 1
    predictions = []
    for i in range(iters):
        img = cropped[i : i + 32, ...]
        img = np.expand_dims(img, axis=0)
        predicted = model.predict(img)
        predicted = predicted > 0.5
        full_preds = np.zeros((1, 32, 300, 334, 1))
        full_preds[:, :, 100:228, 100:228] = predicted
        predictions.append(full_preds)

    return predictions


def biggest_volume_fm(arr):
    """Keep the biggest consecutive slices with contours.

    Arguments:
        arr -- A 3D binary mask prediction of the femoral heads.

    Returns:
        The 3D binary mask after processing.
    """

    begin = False
    starts = None
    ends = None
    ranges = []
    for i in range(len(arr)):
        if begin:
            if np.sum(arr[i]) < 5:
                ends = i
                begin = False
                ranges.append((starts, ends))

        else:
            if np.sum(arr[i]) > 5:
                begin = True
                starts = i

    biggest_range = 0
    min_ = None
    max_ = None
    for r in ranges:
        if (r[1] - r[0]) > biggest_range:
            min_ = r[0]
            max_ = r[1]
            biggest_range = r[1] - r[0]

    if (max_ - min_) > 70:
        min_ = max_ - 70

    vol = np.zeros_like(arr)
    vol[min_ : max_ + 1] = arr[min_ : max_ + 1]

    return vol, max_


def get_consensus_mask(mask_list, stack_size):
    """Generate a consensus prediction mask by majority vote.

    For the VNet model predictions, given a stack size and a list
    of the predictions, it generates a consensus prediction mask by majority vote.

    Arguments:
        mask_list -- List of binary mask predictions from VNet model.
        stack_size -- The stack size (3rd dimension) of the masks.

    Returns:
        A 3D binary mask.
    """

    # define the 3D mask size
    mask_depth = 288
    mask_rows = 300
    mask_columns = 334
    mask_channels = 1

    # label for undecided pixels (equal votes as background and foreground)
    undecided_label = 1

    seg_lists = []
    majority_list = []
    for i in range(mask_depth):
        if i >= (stack_size - 1) and i <= (mask_depth - stack_size):
            stack_list = mask_list[i - (stack_size - 1) : i + 1]
            slices_list = []
            for j in range(stack_size):
                slice_ = np.squeeze(stack_list[j])
                slices_list.append(
                    sitk.GetImageFromArray(slice_[(stack_size - 1) - j, ...].astype(np.uint8))
                )
            seg_lists.append(slices_list)

    for k in range(len(seg_lists)):
        majority_seg = sitk.LabelVoting(seg_lists[k], undecided_label)
        majority_seg = sitk.GetArrayFromImage(majority_seg)
        majority_seg = np.squeeze(majority_seg)
        majority_list.append(majority_seg)

    consensus_mask = np.zeros((mask_depth, mask_rows, mask_columns, mask_channels))
    consensus_mask[31 : mask_depth - (stack_size - 1), ..., 0] = np.squeeze(
        np.array(majority_list)
    )

    return consensus_mask


def get_middle_contour(mask_list, stack_size):
    """Select the middle slice from each prediction.

    For the VNet model predictions, given a stack size and a list of the predictions,
    it selects the middle slice from each prediction.

    Arguments:
        mask_list -- List of binary mask predictions from VNet model.
        stack_size -- The stack size (3rd dimension) of the masks.

    Returns:
        A 3D binary mask.
    """
    img_rows = 300
    img_columns = 334
    img_channels = 1
    img_depth = 288
    middle_slice = int(stack_size / 2)

    masks = np.zeros((img_depth, img_rows, img_columns, img_channels))
    for i in range(len(mask_list)):
        masks[i + middle_slice] = mask_list[i][0, middle_slice, ...]

    return masks


def post_process_fmrt(preds_fmrt):
    """Post process the prediction mask for the right femoral head.

    Arguments:
        preds_fmrt -- The binary mask for the right femoral head.

    Returns:
        The 3D mask after post processing.
    """

    fm_ball = ball(3)
    preds_fmrt = np.squeeze(preds_fmrt)
    p_masks = np.copy(preds_fmrt)
    p_masks[:, :, 168:-1] = 0
    p_masks = ndimage.binary_opening(p_masks, structure=fm_ball)
    p_masks, max_ = biggest_volume_fm(p_masks)

    return p_masks, max_


def post_process_fmlt(preds_fmlt):
    """Post process the prediction mask for the left femoral head.

    Arguments:
        preds_fmlt -- The binary mask for the left femoral head.

    Returns:
        The 3D mask after post processing.
    """

    fm_ball = ball(3)
    preds_fmlt = np.squeeze(preds_fmlt)
    pl_masks = np.copy(preds_fmlt)
    pl_masks[:, :, 0:168] = 0
    pl_masks = ndimage.binary_opening(pl_masks, structure=fm_ball)
    pl_masks, max_ = biggest_volume_fm(pl_masks)

    return pl_masks, max_


def post_process_bldr(preds):
    """Post process the prediction mask for the bladder.

    Arguments:
        preds -- The binary mask for the bladder.

    Returns:
        The 3D mask after post processing.
    """

    bldr_ball = ball(5)

    preds = np.squeeze(preds)
    preds[:, 0:60] = 0
    preds[:, :, 0:100] = 0
    preds[:, 190:-1] = 0
    preds[:, :, 280:-1] = 0
    preds[0:58, ...] = 0
    preds[238:-1, ...] = 0

    preds = ndimage.binary_opening(preds, structure=bldr_ball)
    preds = ndimage.binary_closing(preds, structure=bldr_ball)

    begin = False
    starts = None
    ends = None
    ranges = []
    for i in range(len(preds)):
        if begin:
            if np.sum(preds[i]) < 5:
                ends = i
                begin = False
                ranges.append((starts, ends))

        else:
            if np.sum(preds[i]) > 5:
                begin = True
                starts = i

    biggest_range = 0
    min_ = None
    max_ = None
    for r in ranges:
        if (r[1] - r[0]) > biggest_range:
            min_ = r[0]
            max_ = r[1]
            biggest_range = r[1] - r[0]

    masks = np.zeros_like(preds)
    masks[min_ : max_ + 1] = preds[min_ : max_ + 1]

    return masks


def post_process_rctm(preds, fm_max):
    """Post process the prediction mask for the rectum.

    Arguments:
        preds -- The binary mask for the rectum.
        fm_max -- The slice number of the top slice of the right femoral head.

    Returns:
        The 3D mask after post processing.
    """

    rcm_ball = ball(3)

    preds = np.squeeze(preds)

    preds = ndimage.binary_opening(preds, structure=rcm_ball)
    preds = ndimage.binary_closing(preds, structure=rcm_ball)

    begin = False
    starts = None
    ends = None
    ranges = []
    for i in range(len(preds)):
        if begin:
            if np.sum(preds[i]) < 5:
                ends = i
                begin = False
                ranges.append((starts, ends))

        else:
            if np.sum(preds[i]) > 5:
                begin = True
                starts = i

    biggest_range = 0
    min_ = None
    max_ = None
    for r in ranges:
        if (r[1] - r[0]) > biggest_range:
            min_ = r[0]
            max_ = r[1]
            biggest_range = r[1] - r[0]

    masks = np.zeros_like(preds)
    if fm_max:
        max_ = fm_max
    masks[min_ : max_ + 1] = preds[min_ : max_ + 1]

    return masks
