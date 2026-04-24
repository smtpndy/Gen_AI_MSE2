#!/bin/bash
# install_face_recognition.sh
# Installs dlib + face_recognition on Ubuntu/Debian/macOS
set -e

echo "🔧 Installing face_recognition dependencies..."
OS="$(uname -s)"

if [ "$OS" = "Linux" ]; then
    echo "📦 Detected Linux — installing system deps..."
    sudo apt-get update
    sudo apt-get install -y build-essential cmake libopenblas-dev \
        liblapack-dev libx11-dev libgtk-3-dev python3-dev
elif [ "$OS" = "Darwin" ]; then
    echo "🍎 Detected macOS — installing via Homebrew..."
    brew install cmake openblas
fi

echo "🐍 Installing Python packages..."
pip install dlib==19.24.4
pip install face-recognition==1.3.0
pip install opencv-python-headless==4.10.0.84

echo "✅ face_recognition installed successfully!"
echo ""
echo "🧪 Testing installation..."
python3 -c "import face_recognition; import cv2; print('✓ face_recognition OK'); print('✓ OpenCV OK')"
