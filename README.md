# FaceAttend AI - Face Recognition Attendance System

A complete AI-powered face recognition attendance management system with real-time face detection, student registration, attendance tracking, and reporting.

## Features

- **Face Recognition**: Real-time face detection and recognition using face_recognition library
- **Student Registration**: Multi-step enrollment with face capture and ML model training
- **Attendance Tracking**: Automatic attendance marking with confidence scoring
- **Dashboard**: Real-time statistics and attendance overview
- **Reporting**: Comprehensive attendance reports with analytics
- **JWT Authentication**: Secure user authentication with token-based access
- **RESTful API**: Complete backend API for all operations
- **Responsive UI**: Modern, dark-themed interface with real-time updates

## Tech Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLite with SQLAlchemy ORM
- **Face Recognition**: face_recognition, OpenCV, dlib
- **Authentication**: JWT (PyJWT)
- **API**: RESTful with Flask-CORS

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript**: Vanilla JS with async/await
- **Canvas API**: Real-time camera feed processing
- **Chart.js**: Data visualization
- **Responsive Grid System**: Mobile-friendly layout

## Installation

### Prerequisites
- Python 3.8+
- Node.js 12+ (optional, for frontend build tools)
- Modern web browser with camera access
- Linux/Mac/Windows with development tools installed

### Backend Setup

1. **Create virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

Note: `face_recognition` requires dlib, which may need compilation:
- **Ubuntu/Debian**: `sudo apt-get install build-essential python3-dev`
- **MacOS**: `brew install build-essential` (or use Xcode tools)
- **Windows**: Install Visual C++ Build Tools

3. **Database initialization**:
```bash
python3 app.py
```
This will:
- Create `attendance.db` SQLite database
- Initialize all tables
- Create default admin user (username: `admin`, password: `admin123`)

### Frontend Setup

1. **Open in web server** (development):
```bash
# Using Python's built-in server
cd /path/to/frontend
python3 -m http.server 8000
```

2. **Access the application**:
- Navigate to `http://localhost:8000`
- Login with admin credentials
- Ensure Flask backend is running on `http://localhost:5000`

## Configuration

### API Configuration
Edit `app.py` to change settings:

```python
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'

# JWT Secret Key (CHANGE THIS IN PRODUCTION)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Flask Port
app.run(host='0.0.0.0', port=5000)
```

### Frontend Configuration
Edit `index.html` JavaScript:

```javascript
const API_BASE = 'http://localhost:5000/api';
```

### Face Recognition Settings
In frontend settings page:
- **Confidence Threshold**: Minimum match confidence (default: 0.60)
- **Detection Model**: HOG (fast) or CNN (accurate)
- **Auto Capture Interval**: Milliseconds between captures

## Usage

### 1. Login
- Username: `admin`
- Password: `admin123`

### 2. Register a Student
1. Go to **Register** page
2. Fill in student information
3. Capture ≥20 face images (use auto-capture for convenience)
4. System trains face recognition model
5. Student is enrolled

**Capture Tips for Better Accuracy**:
- Good lighting (face clearly visible)
- Different angles (front, 45°, profile)
- Various expressions
- Different distances
- No obstructions (sunglasses, masks)

### 3. Mark Attendance
1. Go to **Mark Attendance** page
2. Click "Start Camera"
3. Position face in detection frame
4. System automatically recognizes and marks attendance
5. Recognized students appear in real-time list

### 4. View Reports
1. Go to **Reports** page
2. Select date range (optional)
3. View attendance summary table
4. Export as CSV, PDF, or Excel

## API Endpoints

### Authentication
```
POST   /api/auth/register       - Register new user
POST   /api/auth/login          - Login user
```

### Students
```
GET    /api/students            - Get all students
POST   /api/students            - Create new student
GET    /api/students/<id>       - Get student details
PUT    /api/students/<id>       - Update student
DELETE /api/students/<id>       - Delete student
```

### Face Recognition
```
POST   /api/students/<id>/capture-face    - Capture face image
POST   /api/students/<id>/train-model     - Train recognition model
POST   /api/attendance/recognize          - Recognize face & mark attendance
```

### Attendance
```
GET    /api/attendance/records                    - Get all attendance records
GET    /api/attendance/student/<id>/summary      - Get student summary
```

### Reports
```
GET    /api/dashboard/stats              - Get dashboard statistics
GET    /api/reports/attendance           - Generate attendance report
```

## Database Schema

### Users Table
- id, username, email, password_hash, role, created_at

### Students Table
- id, student_id, name, email, roll_number, branch, semester
- face_encoding (pickled numpy array), face_count, model_accuracy, status
- created_at, attendance_records (relation)

### AttendanceRecord Table
- id, student_id, timestamp, confidence, status, session_id, camera_snapshot

### FaceDataset Table
- id, student_id, image_data, encoding (pickled face encoding), captured_at

## File Structure

```
project/
├── app.py                      # Flask backend application
├── requirements.txt            # Python dependencies
├── index.html                  # Frontend HTML/CSS/JS
├── attendance.db              # SQLite database (auto-created)
├── models/                    # Trained models (optional)
├── uploads/
│   └── faces/                 # Stored face images
└── logs/                      # System logs
```

## Security Considerations

### Development
- Default credentials should be changed immediately
- Use HTTPS in production
- Change `SECRET_KEY` to a random value

### Production Deployment
1. **Environment Variables**:
   ```python
   # app.py
   import os
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
   DEBUG = os.environ.get('FLASK_DEBUG', False)
   ```

2. **CORS Configuration**:
   ```python
   CORS(app, origins=['https://yourdomain.com'])
   ```

3. **Database**:
   - Use PostgreSQL instead of SQLite
   - Enable WAL (Write-Ahead Logging) for SQLite
   - Regular automated backups

4. **Face Data**:
   - Encrypt stored face encodings
   - Secure image storage with proper permissions
   - Consider GDPR compliance

## Troubleshooting

### Camera Not Working
- Browser must have camera permissions
- Check `index.html` permission requests
- Try in incognito/private mode
- Ensure HTTPS or localhost

### Face Not Detected
- Improve lighting
- Move closer to camera
- Remove obstructions
- Lower confidence threshold in settings
- Check face_recognition model compatibility

### API Connection Error
- Verify Flask backend is running: `python3 app.py`
- Check API_BASE URL in `index.html`
- Ensure CORS is enabled
- Check firewall settings

### Database Lock Error
- Close other connections
- Restart Flask application
- Delete `attendance.db-journal` file if corrupted

### dlib Installation Issues

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev libatlas-base-dev
pip install dlib face_recognition
```

**MacOS**:
```bash
brew install cmake
brew install openblas lapack
pip install dlib face_recognition
```

**Windows**:
- Use pre-built wheels: `pip install dlib --only-binary :all:`
- Or install Visual C++ Build Tools

## Performance Optimization

### For Better Recognition Accuracy
1. Capture ≥30 face images per student
2. Use varied lighting conditions
3. Include different angles (0°, 45°, 90°)
4. Regular model retraining (>1000 students)

### For Faster Processing
1. Reduce video resolution in camera
2. Use HOG detection model (CPU) vs CNN (GPU)
3. Implement face detection batching
4. Cache face encodings in memory

### For Scalability
1. Use PostgreSQL for database
2. Implement Redis caching
3. Deploy on cloud (AWS, GCP, Azure)
4. Use GPU for faster face recognition
5. Implement async task queue (Celery)

## API Authentication

Include JWT token in header:
```javascript
const headers = {
  'Authorization': `Bearer ${authToken}`,
  'Content-Type': 'application/json'
};
```

Token expires after 24 hours (configurable).

## Advanced Features

### Batch Processing
```python
# Process multiple images
for image in images:
    encoding, error = extract_face_encoding(image)
    if not error:
        # Store or match
```

### Custom Face Detector
```python
# Replace with custom detector if needed
face_locations = face_recognition.face_locations(rgb_image, model='cnn')
```

### Model Retraining
- Automatically triggered when new faces added
- Supports incremental learning
- Cross-validation for accuracy estimation

## Support & Contributions

For issues, feature requests, or contributions:
1. Report bugs with detailed error messages
2. Include system information (OS, Python version)
3. Provide steps to reproduce issues
4. Suggest improvements with examples

## License

This project is provided as-is for educational purposes.

## Author

FaceAttend AI Development Team
Version: 1.0
Last Updated: 2024

---

## Quick Start Commands

```bash
# 1. Setup backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py

# 2. Serve frontend (in another terminal)
cd /path/to/frontend
python3 -m http.server 8000

# 3. Open browser
# http://localhost:8000
# Login: admin / admin123
```

That's it! You now have a fully functional face recognition attendance system.
