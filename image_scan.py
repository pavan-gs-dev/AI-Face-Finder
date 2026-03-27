import os
import face_recognition

# Ensure this path matches the one in app.py
CAMERA_IMAGE_DIR = "static/cemara_image"

def load_known_faces():
    """
    Loads all faces from the camera_image directory.
    This is called every time a scan happens to ensure up-to-date data.
    """
    known_encodings = []
    known_files = []

    if not os.path.exists(CAMERA_IMAGE_DIR):
        print(f"Directory {CAMERA_IMAGE_DIR} not found.")
        return [], []

    for file in os.listdir(CAMERA_IMAGE_DIR):
        path = os.path.join(CAMERA_IMAGE_DIR, file)
        
        # Skip non-image files
        if not file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue

        try:
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            
            # If a face is found in the image, store the first encoding
            if encodings:
                known_encodings.append(encodings[0])
                known_files.append(file)
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue

    return known_encodings, known_files


def scan_and_match(scan_image_path, tolerance=0.5):
    """
    Compares the uploaded scan_image against all images in CAMERA_IMAGE_DIR.
    Returns a list of filenames that match.
    """
    known_encodings, known_files = load_known_faces()

    if not known_encodings:
        print("No known faces in database.")
        return []

    try:
        # Load the temporarily captured snapshot
        scan_image = face_recognition.load_image_file(scan_image_path)
        scan_encodings = face_recognition.face_encodings(scan_image)

        if not scan_encodings:
            print("No face found in the scanned image.")
            # We return empty here so the frontend knows no face was found
            return []

        # We assume the user is the primary face in the selfie (index 0)
        scan_encoding = scan_encodings[0]

        # Compare against all known encodings
        matches = face_recognition.compare_faces(
            known_encodings, scan_encoding, tolerance=tolerance
        )

        matched_files = [
            known_files[i] for i, match in enumerate(matches) if match
        ]

        return matched_files

    except Exception as e:
        print(f"Error during scan_and_match: {e}")
        return []