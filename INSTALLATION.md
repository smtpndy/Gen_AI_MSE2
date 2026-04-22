# FaceAttend AI - Installation Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Ubuntu/Linux Installation](#ubuntulinux-installation)
3. [macOS Installation](#macos-installation)
4. [Windows Installation](#windows-installation)
5. [Docker Installation](#docker-installation)
6. [Cloud Deployment](#cloud-deployment)
7. [Verification Steps](#verification-steps)

---

## System Requirements

### Minimum Specifications
- **CPU**: Dual-core processor @ 2.0 GHz+
- **RAM**: 2 GB (4 GB recommended)
- **Storage**: 500 MB for application, +100 MB per 1000 students
- **Network**: 10 Mbps internet connection

### Recommended Specifications
- **CPU**: Quad-core processor @ 2.5 GHz+ (with GPU for faster processing)
- **RAM**: 8 GB
- **Storage**: SSD with 50 GB+ available space
- **Network**: 100 Mbps or faster
- **GPU**: NVIDIA CUDA-enabled GPU (optional, for CNN face detection)

### Supported Operating Systems
- Linux: Ubuntu 18.04+, Debian 10+, CentOS 7+
- macOS: 10.13+ (Intel or Apple Silicon)
- Windows: 10 or 11 (Pro/Enterprise recommended)
- Cloud: AWS, GCP, Azure, DigitalOcean, Heroku

---

## Ubuntu/Linux Installation

### Step 1: Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install Dependencies
```bash
sudo apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    git
```

### Step 3: Clone/Download Project
```bash
cd /opt
git clone https://github.com/yourusername/faceattend.git
cd faceattend
```

Or download the files manually and extract.

### Step 4: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 5: Install Python Packages
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 6: Initialize Database
```bash
python3 app.py
```
This will create `attendance.db` and seed default data.

### Step 7: Run Backend
```bash
python3 app.py
```
Backend should be running on `http://localhost:5000`

### Step 8: Serve Frontend (New Terminal)
```bash
cd /opt/faceattend
python3 -m http.server 8000 --directory .
```
Frontend should be available at `http://localhost:8000`

### Step 9: Access Application
Open browser and navigate to:
```
http://localhost:8000
Username: admin
Password: admin123
```

### Optional: Setup Systemd Service

Create `/etc/systemd/system/faceattend.service`:
```ini
[Unit]
Description=FaceAttend AI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/faceattend
Environment="PATH=/opt/faceattend/venv/bin"
ExecStart=/opt/faceattend/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable faceattend
sudo systemctl start faceattend
sudo systemctl status faceattend
```

---

## macOS Installation

### Step 1: Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies
```bash
brew install python@3.10
brew install cmake
brew install openblas
brew install lapack
```

### Step 3: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Python Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Note: If dlib installation fails:
```bash
# For Intel Macs:
pip install dlib --only-binary :all:

# For Apple Silicon (M1/M2):
conda install dlib  # or use pre-built wheel
```

### Step 5: Initialize and Run
```bash
python3 app.py
```

### Step 6: Frontend Server (New Terminal)
```bash
python3 -m http.server 8000
```

### Optional: Keep Running with Supervisor
Install supervisor:
```bash
pip install supervisor
```

Create `/usr/local/etc/supervisor.d/faceattend.conf`:
```ini
[program:faceattend]
command=/path/to/venv/bin/python /path/to/app.py
directory=/path/to/project
autostart=true
autorestart=true
```

---

## Windows Installation

### Step 1: Install Python
- Download Python 3.10+ from [python.org](https://www.python.org)
- ✅ Check "Add Python to PATH"
- Run installer

### Step 2: Install Visual C++ Build Tools
- Download from [Microsoft Visual Studio](https://visualstudio.microsoft.com/downloads/)
- Install "Desktop development with C++"

### Step 3: Create Virtual Environment
```cmd
cd C:\faceattend
python -m venv venv
venv\Scripts\activate
```

### Step 4: Install Dependencies
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

If face_recognition fails:
```cmd
# Use pre-built wheels (recommended for Windows)
pip install dlib --only-binary :all:
```

### Step 5: Initialize Database
```cmd
python app.py
```

### Step 6: Create Batch Files for Easy Startup

Create `start-backend.bat`:
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python app.py
pause
```

Create `start-frontend.bat`:
```batch
@echo off
cd /d "%~dp0"
python -m http.server 8000
pause
```

### Step 7: Double-click batch files to run

Or create `start-all.bat`:
```batch
@echo off
start start-backend.bat
start start-frontend.bat
start http://localhost:8000
```

### Optional: Windows Task Scheduler
- Create scheduled task to run `start-backend.bat` on startup
- Set to run with highest privileges

---

## Docker Installation

### Prerequisites
- Install [Docker](https://www.docker.com/products/docker-desktop)
- Install [Docker Compose](https://docs.docker.com/compose/install/)

### Step 1: Build Image
```bash
docker build -t faceattend-ai .
```

### Step 2: Run with Docker Compose
```bash
docker-compose up -d
```

### Step 3: Access Application
- Frontend: http://localhost:80
- Backend: http://localhost:5000

### Step 4: View Logs
```bash
docker-compose logs -f backend
```

### Management Commands
```bash
# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access container shell
docker exec -it faceattend-backend bash

# Check health
docker ps
```

---

## Cloud Deployment

### AWS EC2
```bash
# 1. Create Ubuntu 22.04 LTS instance
# 2. SSH into instance
ssh -i key.pem ubuntu@ip-address

# 3. Run Linux installation steps above
# 4. Configure security groups to allow ports 80, 443, 5000

# 5. Setup Nginx reverse proxy
sudo apt install nginx
# Edit /etc/nginx/sites-enabled/default
# Point to localhost:5000 for API
```

### Heroku Deployment
```bash
# 1. Install Heroku CLI
# 2. Create Procfile:
echo "web: python app.py" > Procfile

# 3. Deploy
heroku create faceattend-app
git push heroku main
```

### Google Cloud Platform
```bash
# Create Cloud Run service with Docker image
gcloud run deploy faceattend-app \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --port 5000
```

### DigitalOcean App Platform
- Connect GitHub repository
- Set start command: `python app.py`
- Configure environment variables
- Deploy

### Azure Container Instances
```bash
az container create \
  --resource-group mygroup \
  --name faceattend \
  --image faceattend-ai \
  --ports 5000 80 \
  --environment-variables DEBUG=False
```

---

## Verification Steps

### 1. Check Backend Connection
```bash
curl http://localhost:5000/api/health
# Should return: {"status":"healthy","timestamp":"..."}
```

### 2. Check Database
```bash
sqlite3 attendance.db ".tables"
# Should list: user, student, attendance_record, face_dataset
```

### 3. Test Face Recognition
```python
from app import extract_face_encoding
import cv2

# Test with sample image
encoding, error = extract_face_encoding('path/to/face.jpg')
if not error:
    print("✅ Face recognition working")
else:
    print(f"❌ Error: {error}")
```

### 4. Test API Endpoints
```bash
# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"test123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Get stats
curl http://localhost:5000/api/dashboard/stats
```

### 5. Camera Access
- Open browser console (F12)
- Verify no camera permission errors
- Check browser camera settings

### 6. Performance Test
```bash
# Test API response time
time curl http://localhost:5000/api/students

# Should complete in <500ms
```

---

## Troubleshooting Installation

### "dlib installation failed"
**Solution:**
```bash
# Use pre-built wheels
pip install dlib --only-binary :all:

# Or use conda
conda install dlib
```

### "ModuleNotFoundError: No module named 'face_recognition'"
**Solution:**
```bash
# Reinstall with verbose output
pip install --verbose face_recognition

# Check installation
python -c "import face_recognition; print(face_recognition.__version__)"
```

### "Permission denied: /app/attendance.db"
**Solution:**
```bash
# Fix file permissions
sudo chown -R $(whoami) /path/to/project
chmod -R 755 /path/to/project
```

### "Port 5000 already in use"
**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python app.py --port 5001
```

### "Camera not detected"
**Solution:**
- Check browser permissions (chrome://settings/content/camera)
- Use HTTPS or localhost only
- Try different browser
- Check `/dev/video0` on Linux: `ls /dev/video*`

### "Out of memory errors"
**Solution:**
```bash
# Increase swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Database Lock Error
**Solution:**
```bash
# Remove database lock file
rm attendance.db-journal

# Restart application
python app.py
```

---

## Post-Installation Configuration

### 1. Change Default Password
```bash
python3 -c "
from app import app, db, User
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('new-secure-password')
    db.session.commit()
    print('✅ Password changed')
"
```

### 2. Configure Email Notifications
Edit `.env`:
```
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Enable HTTPS
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Or use Let's Encrypt (Certbot)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

### 4. Setup Regular Backups
```bash
# Create backup script: backup.sh
#!/bin/bash
cp attendance.db attendance.db.backup.$(date +%Y%m%d_%H%M%S)
```

Schedule with cron:
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

---

## Next Steps

After successful installation:
1. ✅ Change admin password
2. ✅ Create user accounts for staff
3. ✅ Test camera and face recognition
4. ✅ Register test students
5. ✅ Verify attendance marking
6. ✅ Configure backup schedule
7. ✅ Setup SSL/HTTPS
8. ✅ Train deployment staff

For support: Check README.md and API documentation.
