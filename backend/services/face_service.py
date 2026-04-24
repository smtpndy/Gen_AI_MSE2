import os
import json
import base64
import logging
import numpy as np
from typing import Optional, List, Tuple
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

FACE_RECOGNITION_AVAILABLE = False
cv2 = None
face_recognition = None

try:
    import cv2 as _cv2
    import face_recognition as _face_recognition
    cv2 = _cv2
    face_recognition = _face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("face_recognition and OpenCV loaded successfully")
except ImportError:
    logger.warning("face_recognition or OpenCV not available. Using mock mode.")

TOLERANCE = float(os.getenv("FACE_TOLERANCE", "0.5"))
MIN_IMAGES = int(os.getenv("MIN_FACE_IMAGES", "5"))
FACE_IMAGES_DIR = os.getenv("FACE_IMAGES_DIR", "database/face_images")
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)


def encode_image_from_base64(image_b64: str) -> Optional[np.ndarray]:
    """Decode base64 image to numpy array."""
    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]
        img_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        if cv2:
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return img
        return np_arr
    except Exception as e:
        logger.error(f"Failed to decode image: {e}")
        return None


def get_face_encoding(image_array: np.ndarray) -> Optional[List[float]]:
    """Extract face encoding from image array."""
    if not FACE_RECOGNITION_AVAILABLE:
        # Mock encoding for testing
        import random
        return [random.uniform(-0.5, 0.5) for _ in range(128)]
    try:
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if encodings:
            return encodings[0].tolist()
        return None
    except Exception as e:
        logger.error(f"Face encoding error: {e}")
        return None


def detect_faces_in_image(image_array: np.ndarray) -> int:
    """Return number of faces detected."""
    if not FACE_RECOGNITION_AVAILABLE:
        return 1  # mock
    try:
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        return len(locations)
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return 0


def match_face(
    unknown_encoding: List[float],
    known_encodings_json: str,
    tolerance: float = TOLERANCE
) -> Tuple[bool, float]:
    """Compare unknown face encoding against stored encodings. Returns (match, confidence)."""
    if not known_encodings_json:
        return False, 0.0
    try:
        stored = json.loads(known_encodings_json)
        if not stored:
            return False, 0.0

        if FACE_RECOGNITION_AVAILABLE:
            unknown_arr = np.array(unknown_encoding)
            known_arrays = [np.array(enc) for enc in stored]
            distances = face_recognition.face_distance(known_arrays, unknown_arr)
            min_distance = float(np.min(distances))
            confidence = max(0.0, (1.0 - min_distance) * 100)
            matched = min_distance <= tolerance
            return matched, round(confidence, 2)
        else:
            # Mock matching
            import random
            confidence = random.uniform(75, 95)
            return True, confidence
    except Exception as e:
        logger.error(f"Face matching error: {e}")
        return False, 0.0


def save_face_image(student_id: str, image_array: np.ndarray, index: int) -> str:
    """Save face image to disk, return path."""
    student_dir = os.path.join(FACE_IMAGES_DIR, student_id)
    os.makedirs(student_dir, exist_ok=True)
    filename = f"face_{index}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
    path = os.path.join(student_dir, filename)
    if cv2 is not None:
        cv2.imwrite(path, image_array)
    return path


def process_frame_for_recognition(frame_b64: str, students_encodings: list) -> dict:
    """
    Given a base64 frame and list of {student_id, name, roll_number, encodings_json},
    return recognition result.
    """
    image = encode_image_from_base64(frame_b64)
    if image is None:
        return {"success": False, "message": "Could not decode image"}

    if FACE_RECOGNITION_AVAILABLE:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if not locations:
            return {"success": False, "message": "No face detected in frame"}
        encodings = face_recognition.face_encodings(rgb, locations)
        if not encodings:
            return {"success": False, "message": "Could not encode face"}
        unknown_encoding = encodings[0].tolist()
    else:
        import random
        unknown_encoding = [random.uniform(-0.5, 0.5) for _ in range(128)]

    best_match = None
    best_confidence = 0.0
    for student in students_encodings:
        if not student.get("face_encodings"):
            continue
        matched, confidence = match_face(unknown_encoding, student["face_encodings"])
        if matched and confidence > best_confidence:
            best_confidence = confidence
            best_match = student

    if best_match:
        return {
            "success": True,
            "student_id": best_match["student_id"],
            "name": best_match["name"],
            "roll_number": best_match.get("roll_number", ""),
            "confidence": best_confidence,
            "message": f"Recognized: {best_match['name']} ({best_confidence:.1f}%)"
        }
    return {"success": False, "message": "Face not recognized"}
