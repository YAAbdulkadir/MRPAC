"""A module for helper functions."""

import os
import time
import json
from typing import List
from pathlib import Path
import numpy as np
from pydicom import dcmread
from scipy import ndimage
from skimage.morphology import ball
from scipy.ndimage import label
import torch
import torch.nn.functional as F
from torch.amp import autocast
import torchio as tio
from mrpac._globals import Globals


def get_image_position_along_imaging_axis(ds):
    try:
        if isinstance(ds, (str, Path)):
            ds = dcmread(ds, stop_before_pixels=True)

        image_position_patient = np.array(ds.ImagePositionPatient, dtype=float)
        image_orientation_patient = np.array(ds.ImageOrientationPatient, dtype=float)
        row_cosines = image_orientation_patient[:3]
        col_cosines = image_orientation_patient[3:]
        imaging_axis = np.cross(row_cosines, col_cosines)
        return np.dot(image_position_patient, imaging_axis)

    except Exception as e:
        print(f"Could not read dataset: {e}")
        return float("inf")


def sort_by_image_position_patient(file_names_or_datasets):
    """
    Sorts DICOM image files or datasets based on their position along the imaging axis.

    This function sorts a list of DICOM file paths or datasets based on the ImagePositionPatient
    tag and the orientation of the image (using ImageOrientationPatient).

    Parameters
    ----------
    file_names_or_datasets : list of str or list of pydicom.Dataset
        The list of DICOM file paths or datasets to sort.

    Returns
    -------
    list of str or list of pydicom.Dataset
        The sorted list of DICOM file paths or datasets.

    Notes
    -----
    This function computes the imaging axis using the ImageOrientationPatient tag
    and sorts the files based on the ImagePositionPatient tag along that axis.

    Examples
    --------
    >>> sorted_files = sort_by_image_position_patient(dicom_file_list)
    >>> print(sorted_files)
    ['file1.dcm', 'file2.dcm', 'file3.dcm']
    """
    sorted_items = sorted(file_names_or_datasets, key=get_image_position_along_imaging_axis)
    return sorted_items


def load_scan(path: str):
    """Load all DICOM images in path into a list for manipulation.

    Parameters
    ----------
    path : str
        The path to a directory containing DICOM files.

    Returns
    -------
    List
        List of DICOM slices sorted according to their location on the
        patient axis from inferior to superior.
    """

    slices = [dcmread(os.path.join(path, s)) for s in os.listdir(path) if ".dcm" in s]
    slices = sort_by_image_position_patient(slices)

    # Get the slice thickness to use for mapping with RTstruct DICOM file
    slice_thickness = np.abs(
        get_image_position_along_imaging_axis(slices[0])
        - get_image_position_along_imaging_axis(slices[1])
    )

    for s in slices:
        s.SliceThickness = slice_thickness

    return slices


def get_pixels(slices: list) -> np.ndarray:
    """Extract and adjust pixel data from DICOM slices.

    Parameters
    ----------
    slices : list
        List of DICOM slices.

    Returns
    -------
    np.ndarray
        Adjusted pixel data array.
    """

    # Extract the original pixel data
    image = np.stack([s.pixel_array for s in slices]).astype(float)

    return image


def preprocess_mri(img_array, stack_size=32, target_size=(256, 256), stride=1):
    """
    Efficiently preprocesses a 3D MRI volume by slicing it into overlapping stacks,
    resizing, and applying z-score normalization.

    Parameters
    ----------
    img_array : np.ndarray
        The input 3D MRI volume of shape [D, H, W].
    stack_size : int
        Number of slices in each stack.
    target_size : tuple
        Tuple (H, W) to resize each 2D slice to.
    stride : int
        Step size for the sliding window along the depth axis.

    Returns
    -------
    batch_tensor : torch.Tensor
        Tensor of shape [num_stacks, 1, stack_size, H, W].
    depth : int
        Original depth of the input image.
    """
    depth, height, width = img_array.shape
    num_stacks = (depth - stack_size) // stride + 1
    batch_tensor = torch.empty((num_stacks, 1, stack_size, *target_size), dtype=torch.float32)

    z_norm = tio.ZNormalization()

    for i, start_idx in enumerate(range(0, depth - stack_size + 1, stride)):
        img_stack = img_array[start_idx : start_idx + stack_size]  # [stack_size, H, W]
        img_tensor = torch.from_numpy(img_stack).float().unsqueeze(0)  # [1, stack_size, H, W]
        img_tensor = F.interpolate(
            img_tensor, size=target_size, mode="bilinear", align_corners=False
        )

        # Apply z-score normalization to this stack
        subject = tio.Subject(image=tio.ScalarImage(tensor=img_tensor))
        subject = z_norm(subject)
        batch_tensor[i] = subject.image.data  # [1, stack_size, H, W]

    return batch_tensor, depth


def run_mr_pelvis_inference(model, input_tensor, num_classes, device):
    """
    Runs inference using an optimal batch size to fit GPU memory.

    Parameters
    ----------
    model : torch.nn.Module
        The trained model.
    input_tensor : torch.Tensor
        Preprocessed input MRI tensor `[num_stacks, 1, stack_size, H, W]`.
    device : torch.device
        Target device (GPU/CPU).

    Returns
    -------
    torch.Tensor
        The predicted segmentation masks `[num_stacks, stack_size, H, W]`.
    """
    model.to(device)
    model.eval()

    input_shape = input_tensor.shape[1:]  # Remove batch dimension
    candidate_batch_sizes = [1, *list(range(2, 34, 2))]
    optimal_batch_size = get_cached_optimal_batch_size(
        model, input_shape, device, candidate_batch_sizes
    )
    # optimal_batch_size = 1

    # Process in chunks
    num_slices = input_tensor.shape[0]
    output_list = []

    with torch.no_grad():
        for i in range(0, num_slices, optimal_batch_size):
            batch = input_tensor[i : i + optimal_batch_size].to(device)

            with autocast(device_type=device.type):
                batch_output = model(batch)
                batch_output = torch.softmax(batch_output, dim=1)

            batch_pred = torch.argmax(batch_output, dim=1)  # Get predicted mask
            # Convert to one-hot encoding `[B, num_classes, stack_size, H, W]`
            batch_one_hot = (
                F.one_hot(batch_pred, num_classes=num_classes).permute(0, 4, 1, 2, 3).float()
            )
            output_list.append(batch_one_hot.cpu())  # Move to CPU to save memory

    # Concatenate outputs
    return torch.cat(output_list, dim=0)


def get_consensus_mask(
    mask_list: List[np.ndarray], stack_size: int, original_shape: tuple, stride=1
) -> np.ndarray:
    """
    Generate a consensus prediction mask by majority vote using a sliding window approach
    with a given stride, then rescale it back to the original image shape.

    Parameters
    ----------
    mask_list : List[np.ndarray]
        List of binary mask predictions from the VNet model.
        Each element in the list is a `stack_size`-depth prediction.
    stack_size : int
        The stack size (depth) used for VNet predictions.
    original_shape : tuple
        The original image shape `(D, H_original, W_original)` before resizing.
    stride : int, optional
        The number of slices to move per step in the sliding window (default is 1).

    Returns
    -------
    np.ndarray
        A 3D binary consensus mask of shape `[D, H_original, W_original]`.
    """
    mask_depth, mask_rows, mask_columns = original_shape  # Original image shape before resizing
    target_size = (256, 256)  # Model inference resolution

    # Create an empty 3D volume for storing votes
    vote_counts = np.zeros((mask_depth, target_size[0], target_size[1]), dtype=np.uint8)

    # Accumulate votes from each stack
    for stack_idx, stack in enumerate(mask_list):
        start_slice = stack_idx * stride  # Start slice in the final volume
        end_slice = min(start_slice + stack_size, mask_depth)  # Ensure within depth bounds

        # Add votes only for valid range
        vote_counts[start_slice:end_slice] += stack[: end_slice - start_slice]

    # Perform fast majority voting using NumPy
    consensus_mask = (vote_counts > (vote_counts.max() / 2)).astype(np.uint8)  # Majority threshold

    min_pixels = 5  # Only keep components with at least this many pixels

    for i in range(consensus_mask.shape[0]):
        labeled_slice, num_features = label(consensus_mask[i])
        for region_label in range(1, num_features + 1):
            region = labeled_slice == region_label
            if np.sum(region) < min_pixels:
                consensus_mask[i][region] = 0

    # Resize the consensus mask back to the original shape
    consensus_tensor = (
        torch.from_numpy(consensus_mask).float().unsqueeze(0).unsqueeze(0)
    )  # [1, 1, D, H, W]
    resized_mask = F.interpolate(
        consensus_tensor, size=(mask_depth, mask_rows, mask_columns), mode="nearest"
    )

    return resized_mask.squeeze().numpy().astype(np.uint8)


def post_process_mask(preds: np.ndarray) -> np.ndarray:
    """Post process the prediction mask for the rectum.

    Parameters
    ----------
    preds : np.ndarray
        The binary mask for the rectum.
    fm_max : int
        The slice number of the superior most slice of the right
        femoral head.

    Returns
    -------
    np.ndarray
        The 3D mask after post processing.
    """

    rcm_ball = ball(3)

    preds = np.squeeze(preds)

    preds = ndimage.binary_opening(preds, structure=rcm_ball)
    preds = ndimage.binary_closing(preds, structure=rcm_ball)

    labeled_mask, _ = ndimage.label(preds)
    structure_sizes = np.bincount(labeled_mask.ravel())[1:]
    largest_structure_label = np.argmax(structure_sizes) + 1
    largest_structure_mask = labeled_mask == largest_structure_label

    return largest_structure_mask.astype(np.uint8)


def load_config():
    """Load configuration from the JSON file if it exists; return an empty dict otherwise."""
    if os.path.exists(Globals.MODELS_CONFIG_PATH):
        try:
            with open(Globals.MODELS_CONFIG_PATH, "r") as f:
                return json.load(f)
        except json.decoder.JSONDecodeError:
            # If the file is empty or invalid, return an empty dictionary.
            return {}
    else:
        return {}


def save_config(config):
    """Save configuration to the JSON file."""
    with open(Globals.MODELS_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def find_optimal_batch_size(
    model, input_shape, device, candidate_batch_sizes, num_runs=10, warmup=2, patience=3
):
    """
    Evaluates candidate batch sizes by timing forward passes and returns
    the optimal batch size based on throughput (samples processed per second).
    Stops early if throughput hasn't improved in `patience` consecutive candidates.

    Parameters
    ----------
    model : torch.nn.Module
        The PyTorch model to evaluate.
    input_shape : tuple
        The shape of a single input (excluding batch dimension).
    device : torch.device
        The device to test on (e.g., torch.device("cuda")).
    candidate_batch_sizes : list of int
        List of batch sizes to test.
    num_runs : int
        Number of timed inference runs per batch size.
    warmup : int
        Number of warmup runs before timing.
    patience : int
        Stop early if no improvement for this many batch size candidates.

    Returns
    -------
    optimal_batch_size : int or None
        The batch size that yielded highest throughput, or None if all failed.
    performance : dict
        Dictionary with detailed timing info for each tested batch size.
    """
    performance = {}
    model = model.to(device)
    device_type = device.type

    best_throughput = 0
    no_improvement_counter = 0

    for bs in candidate_batch_sizes:
        try:
            test_input = torch.randn((bs, *input_shape), device=device)
            # Warmup iterations.
            for _ in range(warmup):
                with torch.no_grad(), autocast(device_type=device_type):
                    _ = model(test_input)
                if device_type == "cuda":
                    torch.cuda.synchronize()

            start_time = time.perf_counter()
            for _ in range(num_runs):
                with torch.no_grad(), autocast(device_type=device_type):
                    _ = model(test_input)
                if device_type == "cuda":
                    torch.cuda.synchronize()
            end_time = time.perf_counter()

            avg_time = (end_time - start_time) / num_runs
            throughput = bs / avg_time  # samples per second
            performance[bs] = {"avg_time": avg_time, "throughput": throughput}

            if throughput > best_throughput:
                best_throughput = throughput
                no_improvement_counter = 0
            else:
                no_improvement_counter += 1

            del test_input
            torch.cuda.empty_cache()

            if no_improvement_counter >= patience:
                break

        except RuntimeError as e:
            if "out of memory" in str(e):
                performance[bs] = {"avg_time": None, "throughput": 0}
                torch.cuda.empty_cache()
                break
            else:
                raise e

    valid_results = {bs: stats for bs, stats in performance.items() if stats["throughput"] > 0}
    optimal_batch_size = (
        max(valid_results, key=lambda bs: valid_results[bs]["throughput"])
        if valid_results
        else None
    )
    return optimal_batch_size, performance


def get_model_identifier(model):
    """
    Automatically derive a model identifier.
    If the model has a 'name' attribute, it uses that;
    otherwise, it uses the class name.
    """
    return getattr(model, "name", model.__class__.__name__)


def get_cached_optimal_batch_size(model, input_shape, device, candidate_batch_sizes):
    """
    Checks if an optimal batch size is saved in the configuration file for the given model.
    If not, computes it, saves it under a unique model identifier, and returns it.

    This function automatically derives a model identifier from the model.
    """
    model_identifier = get_model_identifier(model)
    config = load_config()
    if model_identifier in config and "optimal_batch_size" in config[model_identifier]:
        return config[model_identifier]["optimal_batch_size"]
    else:
        optimal_bs, performance = find_optimal_batch_size(
            model, input_shape, device, candidate_batch_sizes
        )
        config[model_identifier] = {"optimal_batch_size": optimal_bs, "performance": performance}
        save_config(config)
        return optimal_bs
