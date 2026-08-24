import cv2
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def preprocess_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Full preprocessing pipeline for scanned newspaper notice images.
    
    Steps:
    1. Decode image from bytes
    2. Convert to grayscale
    3. Apply adaptive thresholding (handles uneven lighting)
    4. Deskew using minAreaRect on contours
    5. Denoise with fastNlMeansDenoising
    6. Resize if DPI is too low (upscale small images)
    
    Returns preprocessed image as numpy array, or None on failure.
    """
    try:
        # 1. Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            logger.error("Failed to decode image bytes")
            return None
        
        # 2. Grayscale
        try:
            image = _to_grayscale(image)
        except Exception as e:
            logger.warning(f"Grayscale conversion failed: {e}")
            
        # 3. Deskew
        try:
            image = _deskew(image)
        except Exception as e:
            logger.warning(f"Deskewing failed: {e}")

        # 4. Adaptive Thresholding
        try:
            image = _adaptive_threshold(image)
        except Exception as e:
            logger.warning(f"Adaptive thresholding failed: {e}")

        # 5. Denoise
        try:
            image = _denoise(image)
        except Exception as e:
            logger.warning(f"Denoising failed: {e}")

        # 6. Resize
        try:
            image = _resize_if_needed(image)
        except Exception as e:
            logger.warning(f"Resizing failed: {e}")

        return image
    except Exception as e:
        logger.error(f"Image preprocessing pipeline failed: {e}")
        return None

def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def _adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Apply adaptive thresholding — better than global for newspaper scans."""
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

def _deskew(image: np.ndarray) -> np.ndarray:
    """Detect and correct skew angle using minAreaRect."""
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    if abs(angle) < 0.5:
        return image
        
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated

def _denoise(image: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(image, None, h=3, templateWindowSize=7, searchWindowSize=21)

def _resize_if_needed(image: np.ndarray, min_height: int = 800) -> np.ndarray:
    """Upscale small images to improve OCR accuracy."""
    h, w = image.shape[:2]
    if h < min_height:
        scale = min_height / h
        return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return image
