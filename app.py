from flask import Flask, request, jsonify, session, render_template, redirect, url_for
import csv, os, hashlib, base64
from werkzeug.utils import secure_filename
from image_scan import scan_and_match  # Import the matching function
import uuid

app = Flask(__name__)
app.secret_key = "very_secret_key_change_this_in_production"

# File Paths
CSV_FILE = "data/users.csv"
ADDRESS_FILE = "data/Photographer_address.csv"
POSTS_CSV_FILE = "data/photographer_post_file_name.csv"
FOLDERS_CSV_FILE = "data/photographer_folder.csv"
CAMERA_IMAGES_CSV = "data/cemara_image_name.csv"

# Upload Folders
UPLOAD_FOLDER = "static/photographer_post_image"
CAMERA_UPLOAD_FOLDER = "static/cemara_image"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CAMERA_UPLOAD_FOLDER'] = CAMERA_UPLOAD_FOLDER

# --------------------------------------------------
# DATABASE & FOLDER INITIALIZATION
# --------------------------------------------------

def init_users_db():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "role", "name", "email", "phone", "password"])

def init_address_db():
    if not os.path.exists(ADDRESS_FILE):
        with open(ADDRESS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "name", "address"])

def init_posts_db():
    if not os.path.exists(POSTS_CSV_FILE):
        with open(POSTS_CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "filename"])
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def init_folders_db():
    if not os.path.exists(FOLDERS_CSV_FILE):
        with open(FOLDERS_CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "folder_id", "folder_name"])

def init_camera_db():
    # Initialize CSV for folder images
    if not os.path.exists(CAMERA_IMAGES_CSV):
        with open(CAMERA_IMAGES_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["cem_id", "user_id", "folder_id", "image_name"])
    
    # Initialize folder for storage
    if not os.path.exists(CAMERA_UPLOAD_FOLDER):
        os.makedirs(CAMERA_UPLOAD_FOLDER)

init_users_db()
init_address_db()
init_posts_db()
init_folders_db()
init_camera_db()


# --------------------------------------------------
# UTILITIES
# --------------------------------------------------

def hash_password(password):
    if not password:
        return ""
    return hashlib.sha256(password.encode()).hexdigest()

def get_next_user_id():
    max_id = 0
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    uid = int(row["user_id"])
                    max_id = max(max_id, uid)
                except:
                    pass
    return max_id + 1

def get_next_folder_id():
    max_id = 0
    if os.path.exists(FOLDERS_CSV_FILE):
        with open(FOLDERS_CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    fid = int(row["folder_id"])
                    max_id = max(max_id, fid)
                except:
                    pass
    return max_id + 1

def get_next_cem_id():
    max_id = 0
    if os.path.exists(CAMERA_IMAGES_CSV):
        with open(CAMERA_IMAGES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cid = int(row["cem_id"])
                    max_id = max(max_id, cid)
                except:
                    pass
    return max_id + 1

def get_photographer_address(user_id):
    if not os.path.exists(ADDRESS_FILE):
        return None
    with open(ADDRESS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["user_id"] == str(user_id):
                return row["address"]
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


# --------------------------------------------------
# PAGE ROUTES
# --------------------------------------------------

@app.route("/")
def index():
    if "user" in session and "role" in session:
        if session["role"] == "finder":
            return redirect(url_for("photo_finder_page"))
        elif session["role"] == "photographer":
            return redirect(url_for("photographer_page"))
    return render_template("index.html")

@app.route("/photo_finder.html")
def photo_finder_page():
    if "user" not in session or session["role"] != "finder":
        return redirect(url_for("index"))
    return render_template("photo_finder.html")

@app.route("/Photographer.html")
def photographer_page():
    if "user" not in session or session["role"] != "photographer":
        return redirect(url_for("index"))
    return render_template("Photographer.html")

@app.route("/mobile_capture/<user_id>/<folder_id>")
def mobile_capture_page(user_id, folder_id):
    folder_name = "Unknown Folder"
    if os.path.exists(FOLDERS_CSV_FILE):
        with open(FOLDERS_CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == str(user_id) and row["folder_id"] == str(folder_id):
                    folder_name = row["folder_name"]
                    break
    
    return render_template("mobile_capture.html", user_id=user_id, folder_id=folder_id, folder_name=folder_name)


# --------------------------------------------------
# AUTH APIs
# --------------------------------------------------

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = hash_password(data.get("password"))
    role = data.get("role")

    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"] == email and row["password"] == password and row["role"] == role:
                session["user"] = email
                session["role"] = role
                session["user_id"] = row["user_id"]

                redirect_url = "/photo_finder.html" if role == "finder" else "/Photographer.html"
                return jsonify({"redirect": redirect_url})

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.json
    role = data.get("role")
    email = data.get("email")
    password = data.get("password")

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["email"] == email:
                    return jsonify({"error": "User already exists"}), 409

    user_id = get_next_user_id()

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            user_id, role, data.get("name"), email, data.get("phone"), hash_password(password)
        ])

    session["user"] = email
    session["role"] = role
    session["user_id"] = user_id

    redirect_url = "/photo_finder.html" if role == "finder" else "/Photographer.html"
    return jsonify({"redirect": redirect_url})

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# --------------------------------------------------
# USER PROFILE & ADDRESS
# --------------------------------------------------

@app.route("/api/current_user", methods=["GET"])
def current_user():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    email = session["user"]
    user_id = session["user_id"]
    
    found_user = None
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"] == email:
                found_user = row
                break
    
    if found_user:
        address = None
        if found_user["role"] == "photographer":
            address = get_photographer_address(user_id)
            
        return jsonify({
            "user_id": found_user["user_id"],
            "name": found_user["name"],
            "email": found_user["email"],
            "phone": found_user["phone"],
            "role": found_user["role"],
            "address": address
        })

    return jsonify({"error": "User not found"}), 404

@app.route("/api/save_address", methods=["POST"])
def save_address():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    address = data.get("address")
    user_id = str(session["user_id"])
    email = session["user"]

    if not address:
        return jsonify({"error": "Address required"}), 400

    rows = []
    updated = False

    if os.path.exists(ADDRESS_FILE):
        with open(ADDRESS_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == user_id:
                    row["address"] = address
                    updated = True
                rows.append(row)

    if not updated:
        rows.append({"user_id": user_id, "name": email, "address": address})

    with open(ADDRESS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "name", "address"])
        writer.writeheader()
        writer.writerows(rows)

    return jsonify({"message": "Address saved"})


# --------------------------------------------------
# FACE SCAN & MATCH API
# --------------------------------------------------

@app.route("/api/scan_face", methods=["POST"])
def scan_face():
    """
    Receives a single captured image from the frontend.
    1. Decodes base64.
    2. Saves temporarily to disk.
    3. Runs facial recognition matching.
    4. Fetches detailed metadata for each match from CSVs.
    5. Deletes the temporary file.
    6. Returns matches with full details.
    """
    data = request.json
    image_data = data.get("image")

    if not image_data:
        return jsonify({"error": "No image data provided"}), 400

    temp_filename = f"temp_scan_{uuid.uuid4().hex}.jpg"
    temp_path = os.path.join("static", temp_filename)

    try:
        # 1. Decode Base64
        if "," in image_data:
            header, encoded = image_data.split(",", 1)
        else:
            encoded = image_data
        
        decoded_image = base64.b64decode(encoded)

        # 2. Save Temporarily
        with open(temp_path, "wb") as f:
            f.write(decoded_image)

        # 3. Match against Database (folder)
        matched_filenames = scan_and_match(temp_path)

        # 4. Gather Metadata from CSVs
        
        # Load necessary data into memory (efficient for small-medium datasets)
        img_map = {}
        if os.path.exists(CAMERA_IMAGES_CSV):
             with open(CAMERA_IMAGES_CSV, 'r') as f:
                 reader = csv.DictReader(f)
                 for row in reader:
                     img_map[row['image_name']] = row

        user_map = {}
        if os.path.exists(CSV_FILE):
             with open(CSV_FILE, 'r') as f:
                 reader = csv.DictReader(f)
                 for row in reader:
                     user_map[row['user_id']] = row

        addr_map = {}
        if os.path.exists(ADDRESS_FILE):
             with open(ADDRESS_FILE, 'r') as f:
                 reader = csv.DictReader(f)
                 for row in reader:
                     addr_map[row['user_id']] = row['address']

        folder_map = {}
        if os.path.exists(FOLDERS_CSV_FILE):
             with open(FOLDERS_CSV_FILE, 'r') as f:
                 reader = csv.DictReader(f)
                 for row in reader:
                     # Key by (user_id, folder_id) to be safe
                     folder_map[(row['user_id'], row['folder_id'])] = row['folder_name']

        posts_map = {}
        if os.path.exists(POSTS_CSV_FILE):
             with open(POSTS_CSV_FILE, 'r') as f:
                 reader = csv.DictReader(f)
                 for row in reader:
                     uid = row['user_id']
                     if uid not in posts_map: posts_map[uid] = []
                     posts_map[uid].append(row['filename'])

        # 5. Construct Result Objects
        results = []
        for fname in matched_filenames:
            # Default Metadata structure
            meta = {
                "url": url_for('static', filename=f"cemara_image/{fname}"),
                "filename": fname,
                "folder_name": "Unknown Folder",
                "folder_id": "",
                "photographer": {
                    "user_id": "",
                    "name": "Unknown Photographer",
                    "email": "",
                    "phone": "N/A",
                    "address": "Not Available",
                    "posts": []
                }
            }

            # Enrich if data exists
            if fname in img_map:
                info = img_map[fname]
                uid = info['user_id']
                fid = info['folder_id']
                
                meta['folder_id'] = fid
                meta['photographer']['user_id'] = uid

                # Get Folder Name
                if (uid, fid) in folder_map:
                    meta['folder_name'] = folder_map[(uid, fid)]

                # Get User Details
                if uid in user_map:
                    u = user_map[uid]
                    meta['photographer']['name'] = u['name']
                    meta['photographer']['email'] = u['email']
                    meta['photographer']['phone'] = u['phone']
                
                # Get Address
                if uid in addr_map:
                    meta['photographer']['address'] = addr_map[uid]
                
                # Get Posts
                if uid in posts_map:
                    # Convert post filenames to full URLs
                    meta['photographer']['posts'] = [
                        url_for('static', filename=f"photographer_post_image/{p}") 
                        for p in posts_map[uid]
                    ]

            results.append(meta)

        return jsonify({"matches": results})

    except Exception as e:
        print(f"Error processing scan: {e}")
        return jsonify({"error": "Failed to process image or no face detected"}), 500
        
    finally:
        # 6. Clean up: Delete the temp file if it exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Error deleting temp file: {e}")


# --------------------------------------------------
# FOLDER MANAGEMENT
# --------------------------------------------------

@app.route("/api/create_folder", methods=["POST"])
def create_folder():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    folder_name = data.get("folder_name")
    
    if not folder_name:
        return jsonify({"error": "Folder name required"}), 400

    user_id = str(session["user_id"])
    folder_id = get_next_folder_id()

    with open(FOLDERS_CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, folder_id, folder_name])

    return jsonify({"message": "Folder created", "folder": {"folder_id": folder_id, "folder_name": folder_name}})

@app.route("/api/get_folders", methods=["GET"])
def get_folders():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401
        
    user_id = str(session["user_id"])
    
    # First, calculate counts from camera images csv
    folder_counts = {}
    if os.path.exists(CAMERA_IMAGES_CSV):
        with open(CAMERA_IMAGES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == user_id:
                    fid = row["folder_id"]
                    folder_counts[fid] = folder_counts.get(fid, 0) + 1

    folders = []
    if os.path.exists(FOLDERS_CSV_FILE):
        with open(FOLDERS_CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == user_id:
                    count = folder_counts.get(row["folder_id"], 0)
                    folders.append({
                        "folder_id": row["folder_id"],
                        "folder_name": row["folder_name"],
                        "image_count": count
                    })
    
    return jsonify(folders[::-1])


# --------------------------------------------------
# FOLDER IMAGES (Upload, Get, Delete, Reupload)
# --------------------------------------------------

@app.route("/api/upload_folder_image", methods=["POST"])
def upload_folder_image():
    user_id = None
    if "user" in session and session["role"] == "photographer":
        user_id = str(session["user_id"])
    else:
        form_user_id = request.form.get('user_id')
        if form_user_id:
            user_id = form_user_id
    
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    folder_id = request.form.get('folder_id')
    if not folder_id:
        return jsonify({"error": "Folder ID required"}), 400

    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        random_hex = os.urandom(8).hex()
        image_name = f"{folder_id}_{random_hex}.{ext}"
        
        file.save(os.path.join(app.config['CAMERA_UPLOAD_FOLDER'], image_name))
        
        cem_id = get_next_cem_id()
        
        with open(CAMERA_IMAGES_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([cem_id, user_id, folder_id, image_name])
            
        return jsonify({"message": "Image uploaded to folder", "image_name": image_name})
        
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/get_folder_images", methods=["GET"])
def get_folder_images():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401
    
    folder_id = request.args.get('folder_id')
    if not folder_id:
        return jsonify({"error": "Folder ID required"}), 400
        
    user_id = str(session["user_id"])
    images = []
    
    if os.path.exists(CAMERA_IMAGES_CSV):
        with open(CAMERA_IMAGES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == user_id and row["folder_id"] == str(folder_id):
                    image_url = url_for('static', filename=f"cemara_image/{row['image_name']}")
                    images.append({
                        "cem_id": row["cem_id"],
                        "url": image_url,
                        "image_name": row["image_name"]
                    })
    
    return jsonify(images)

@app.route("/api/delete_folder_image", methods=["POST"])
def delete_folder_image():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    image_name = data.get("image_name")
    
    if not image_name:
        return jsonify({"error": "Image name required"}), 400
        
    user_id = str(session["user_id"])
    rows = []
    found = False
    
    if os.path.exists(CAMERA_IMAGES_CSV):
        with open(CAMERA_IMAGES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["image_name"] == image_name and row["user_id"] == user_id:
                    found = True
                    file_path = os.path.join(app.config['CAMERA_UPLOAD_FOLDER'], image_name)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Error deleting file: {e}")
                else:
                    rows.append(row)
    
    if found:
        with open(CAMERA_IMAGES_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["cem_id", "user_id", "folder_id", "image_name"])
            writer.writeheader()
            writer.writerows(rows)
        return jsonify({"message": "Image deleted"})
    else:
        return jsonify({"error": "Image not found"}), 404

@app.route("/api/reupload_folder_image", methods=["POST"])
def reupload_folder_image():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401
    
    old_image_name = request.form.get("old_image_name")
    if not old_image_name:
        return jsonify({"error": "Old image name required"}), 400
        
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        user_id = str(session["user_id"])
        
        rows = []
        found_row = None
        
        if os.path.exists(CAMERA_IMAGES_CSV):
            with open(CAMERA_IMAGES_CSV, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["image_name"] == old_image_name and row["user_id"] == user_id:
                        found_row = row
                    else:
                        rows.append(row)
        
        if not found_row:
            return jsonify({"error": "Original image not found"}), 404
            
        old_file_path = os.path.join(app.config['CAMERA_UPLOAD_FOLDER'], old_image_name)
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except:
                pass
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        random_hex = os.urandom(8).hex()
        folder_id = found_row["folder_id"]
        new_image_name = f"{folder_id}_{random_hex}.{ext}"
        
        file.save(os.path.join(app.config['CAMERA_UPLOAD_FOLDER'], new_image_name))
        
        found_row["image_name"] = new_image_name
        rows.append(found_row)
        
        with open(CAMERA_IMAGES_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["cem_id", "user_id", "folder_id", "image_name"])
            writer.writeheader()
            writer.writerows(rows)
            
        return jsonify({"message": "Re-uploaded successfully", "new_image_name": new_image_name})

    return jsonify({"error": "Invalid file type"}), 400


# --------------------------------------------------
# POSTS (PUBLIC PROFILE) MANAGEMENT
# --------------------------------------------------

@app.route("/api/upload_post", methods=["POST"])
def upload_post():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        user_id = str(session["user_id"])
        ext = file.filename.rsplit('.', 1)[1].lower()
        random_hex = os.urandom(8).hex()
        new_filename = f"{user_id}_{random_hex}.{ext}"
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        
        with open(POSTS_CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([user_id, new_filename])
            
        return jsonify({"message": "Image uploaded successfully", "filename": new_filename})
        
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/get_photographer_posts", methods=["GET"])
def get_photographer_posts():
    if "user" not in session: 
         return jsonify({"error": "Unauthorized"}), 401
    
    target_user_id = str(session["user_id"])
    posts = []
    
    if os.path.exists(POSTS_CSV_FILE):
        with open(POSTS_CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == target_user_id:
                    image_url = url_for('static', filename=f"photographer_post_image/{row['filename']}")
                    posts.append({
                        "url": image_url,
                        "filename": row["filename"]
                    })
    
    return jsonify(posts[::-1])

@app.route("/api/delete_post", methods=["POST"])
def delete_post():
    if "user" not in session or session["role"] != "photographer":
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    filename_to_delete = data.get("filename")
    
    if not filename_to_delete:
        return jsonify({"error": "Filename required"}), 400
        
    user_id = str(session["user_id"])
    rows = []
    found = False
    
    if os.path.exists(POSTS_CSV_FILE):
        with open(POSTS_CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == user_id and row["filename"] == filename_to_delete:
                    found = True
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Error deleting file from disk: {e}")
                else:
                    rows.append(row)
    
    if found:
        with open(POSTS_CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["user_id", "filename"])
            writer.writeheader()
            writer.writerows(rows)
        return jsonify({"message": "Post deleted successfully"})
    else:
        return jsonify({"error": "Post not found or permission denied"}), 404


# --------------------------------------------------
# APP START
# --------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists("templates"):
        os.makedirs("templates")
    app.run(debug=True, port=5000, host='0.0.0.0')