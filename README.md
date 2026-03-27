# AI Face Finder

AI Face Finder is a web application built using Python and Flask that allows photographers to upload event photos and users to upload their selfie to automatically find their photos using face recognition.

## 🚀 Features

* Photographer login and upload event photos
* User registration and login
* User uploads selfie to find their photos
* Face recognition matching
* Automatic photo matching
* Event photo storage
* Simple web interface
* CSV-based data storage

## 🛠️ Technologies Used

* Python
* Flask
* OpenCV
* face_recognition
* NumPy
* HTML
* CSS
* JavaScript
* CSV Database

## 📁 Project Structure

```
AI_FACEFINDER/
│
├── data/
│   ├── users.csv
│   ├── photographer_address.csv
│   ├── photographer_folder.csv
│   ├── camera_image_name.csv
│
├── static/
│   ├── camera_image/
│   └── photographer_post_image/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── photographer.html
│   ├── photo_finder.html
│   └── mobile_capture.html
│
├── app.py
├── image_scan.py
├── requirements.txt
├── README.md
└── License
```

## ⚙️ Installation

1. Clone the repository

```
git clone https://github.com/pavan-gs-dev/ai-facefinder.git
```

2. Go to project folder

```
cd ai-facefinder
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Run the application

```
python app.py
```

5. Open browser

```
http://127.0.0.1:5000
```

## 📸 How It Works

1. Photographer uploads event photos
2. Photos are stored in server folders
3. User uploads a selfie
4. System scans event photos
5. Face recognition matches faces
6. Matching photos are shown to the user

## 📄 Requirements

Make sure Python is installed, then install:

```
flask
opencv-python
face_recognition
numpy
pandas
```

## 🔒 Note

Face recognition may take time if there are many photos. Performance depends on system speed.

## 👨‍💻 Author

Pavan Kumar G S 
