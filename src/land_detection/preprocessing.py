"""
Land2Home — Image Preprocessing for Land and Plot Sketch Detection
==================================================================

Prepares uploaded site photos, satellite map captures, and hand-drawn
sketches for contour segmentation and perspective rectification.
"""

from __future__ import annotations
import numpy as np
import cv2
from PIL import Image, ImageOps


def load_and_preprocess_image(image_input, max_size: tuple[int, int] = (1200, 1200)) -> tuple[np.ndarray, np.ndarray]:
    """
    Load an uploaded image (file path, file-like BytesIO, or PIL Image),
    correct EXIF orientation, resize while preserving aspect ratio,
    and return both the RGB image and an enhanced grayscale image.

    Returns:
        (image_rgb, image_gray) as numpy arrays.
    """
    if isinstance(image_input, Image.Image):
        pil_img = image_input
    elif hasattr(image_input, "read"):
        pil_img = Image.open(image_input)
    else:
        pil_img = Image.open(str(image_input))

    # Correct orientation if EXIF tag exists
    pil_img = ImageOps.exif_transpose(pil_img)
    pil_img = pil_img.convert("RGB")

    # Resize if larger than max_size while maintaining aspect ratio
    pil_img.thumbnail(max_size, Image.Resampling.LANCZOS)
    image_rgb = np.array(pil_img)

    # Convert to grayscale
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    # Contrast Limited Adaptive Histogram Equalization (CLAHE) for illumination variance
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    return image_rgb, enhanced_gray


def enhance_sketch(image_gray: np.ndarray) -> np.ndarray:
    """
    Enhance pencil/pen sketches on paper by removing background texture
    and boosting dark strokes.
    """
    # Bilateral filter smooths paper texture while keeping crisp boundary edges
    filtered = cv2.bilateralFilter(image_gray, d=7, sigmaColor=50, sigmaSpace=50)
    return filtered
