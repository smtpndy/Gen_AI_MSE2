"""
AI Face Recognition Attendance System - Backend
Flask application with face detection, recognition, and attendance tracking
"""

import face_recognition_models
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import face_recognition
import cv2
import numpy as np
import base64
import io
import json
import os
from datetime import datetime, timedelta
from functools import wraps
import jwt
import pickle
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Create directories
Path('uploads/faces').mkdir(parents=True, exist_ok=True)
Path('models').mkdir(parents=True, exist_ok=True)
Path('logs').mkdir(parents=True, exist_ok=True)

# ──── DATABASE MODELS ────────────────────────────────────────────────────

class User(db.Model):
    """User/Admin model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, teacher, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class Student(db.Model):
    """Student model"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    roll_number = db.Column(db.String(20))
    branch = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    face_encoding = db.Column(db.LargeBinary)  # Pickled numpy array
    face_count = db.Column(db.Integer, default=0)
    model_accuracy = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'roll_number': self.roll_number,
            'branch': self.branch,
            'semester': self.semester,
            'face_count': self.face_count,
            'model_accuracy': self.model_accuracy,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class AttendanceRecord(db.Model):
    """Attendance record model"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    confidence = db.Column(db.Float)  # Face match confidence
    status = db.Column(db.String(20), default='present')  # present, absent, late
    session_id = db.Column(db.String(50))
    camera_snapshot = db.Column(db.LargeBinary)  # Base64 encoded image

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'status': self.status,
            'session_id': self.session_id
        }


class FaceDataset(db.Model):
    """Store face dataset metadata"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    image_data = db.Column(db.LargeBinary)  # Raw face image
    encoding = db.Column(db.LargeBinary)  # Face encoding
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)


# ──── HELPER FUNCTIONS ──────────────────────────────────────────────────

def token_required(f):
    """JWT token validation decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def generate_token(user):
    """Generate JWT token"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def extract_face_encoding(image_data):
    """Extract face encoding from image"""
    try:
        # Decode base64 or handle raw bytes
        if isinstance(image_data, str):
            image_array = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            image = image_data

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image, model='hog')
        if not face_locations:
            return None, "No face detected in image"

        # Get face encoding
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if not encodings:
            return None, "Could not extract face encoding"

        return encodings[0], None
    except Exception as e:
        return None, str(e)


def match_face(test_encoding, student):
    """Match test encoding against student's stored encoding"""
    try:
        if not student.face_encoding:
            return False, 0.0

        stored_encoding = pickle.loads(student.face_encoding)
        distance = face_recognition.face_distance([stored_encoding], test_encoding)[0]
        confidence = 1 - distance

        return confidence > 0.6, confidence
    except Exception as e:
        return False, 0.0


# ──── AUTHENTICATION ROUTES ─────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'teacher')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()

        token = generate_token(user)
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        token = generate_token(user)
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ──── STUDENT MANAGEMENT ROUTES ─────────────────────────────────────────

@app.route('/api/students', methods=['GET'])
@token_required
def get_students(current_user):
    """Get all students"""
    try:
        students = Student.query.all()
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/students', methods=['POST'])
@token_required
def create_student(current_user):
    """Create new student"""
    try:
        data = request.get_json()
        
        if Student.query.filter_by(student_id=data['student_id']).first():
            return jsonify({'error': 'Student ID already exists'}), 400

        student = Student(
            student_id=data['student_id'],
            name=data['name'],
            email=data.get('email'),
            roll_number=data.get('roll_number'),
            branch=data.get('branch'),
            semester=data.get('semester')
        )

        db.session.add(student)
        db.session.commit()

        return jsonify({
            'message': 'Student created successfully',
            'student': student.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/students/<int:student_id>', methods=['GET'])
@token_required
def get_student(current_user, student_id):
    """Get student details"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify(student.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/students/<int:student_id>', methods=['PUT'])
@token_required
def update_student(current_user, student_id):
    """Update student information"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json()
        for key, value in data.items():
            if hasattr(student, key) and key not in ['id', 'face_encoding']:
                setattr(student, key, value)

        db.session.commit()
        return jsonify({
            'message': 'Student updated successfully',
            'student': student.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@token_required
def delete_student(current_user, student_id):
    """Delete student"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        db.session.delete(student)
        db.session.commit()

        return jsonify({'message': 'Student deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# ──── FACE CAPTURE & TRAINING ROUTES ────────────────────────────────────

@app.route('/api/students/<int:student_id>/capture-face', methods=['POST'])
@token_required
def capture_face(current_user, student_id):
    """Capture and store face image for student"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json()
        image_data = data.get('image')  # Base64 encoded image

        if not image_data:
            return jsonify({'error': 'No image provided'}), 400

        # Decode and process image
        image_array = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Extract face encoding
        encoding, error = extract_face_encoding(image)
        if error:
            return jsonify({'error': error}), 400

        # Store in database
        dataset = FaceDataset(
            student_id=student_id,
            image_data=image_array.tobytes(),
            encoding=pickle.dumps(encoding)
        )

        db.session.add(dataset)
        student.face_count += 1
        db.session.commit()

        return jsonify({
            'message': 'Face captured successfully',
            'face_count': student.face_count,
            'student': student.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/students/<int:student_id>/train-model', methods=['POST'])
@token_required
def train_model(current_user, student_id):
    """Train face recognition model for student"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get all face images for this student
        datasets = FaceDataset.query.filter_by(student_id=student_id).all()

        if len(datasets) < 5:
            return jsonify({'error': 'Minimum 5 face images required for training'}), 400

        encodings = []
        for dataset in datasets:
            encoding = pickle.loads(dataset.encoding)
            encodings.append(encoding)

        # Average the encodings
        averaged_encoding = np.mean(encodings, axis=0)
        student.face_encoding = pickle.dumps(averaged_encoding)

        # Calculate accuracy (simplified)
        accuracy = min(95.0, 70.0 + (len(datasets) * 2))
        student.model_accuracy = accuracy

        db.session.commit()

        return jsonify({
            'message': 'Model trained successfully',
            'accuracy': accuracy,
            'samples_used': len(datasets),
            'student': student.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# ──── ATTENDANCE ROUTES ─────────────────────────────────────────────────

@app.route('/api/attendance/recognize', methods=['POST'])
def recognize_attendance():
    """Recognize face and mark attendance"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        session_id = data.get('session_id', 'default')

        if not image_data:
            return jsonify({'error': 'No image provided'}), 400

        # Extract face encoding from uploaded image
        encoding, error = extract_face_encoding(image_data)
        if error:
            return jsonify({'error': error}), 400

        # Try to match against all students
        students = Student.query.filter_by(status='active').all()
        matches = []

        for student in students:
            if not student.face_encoding:
                continue

            is_match, confidence = match_face(encoding, student)
            if is_match:
                matches.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'confidence': confidence,
                    'student_roll': student.roll_number
                })

        if not matches:
            return jsonify({
                'recognized': False,
                'message': 'No matching student found'
            }), 200

        # Get best match
        best_match = max(matches, key=lambda x: x['confidence'])
        student = Student.query.get(best_match['student_id'])

        # Record attendance
        attendance = AttendanceRecord(
            student_id=student.id,
            confidence=best_match['confidence'],
            session_id=session_id,
            status='present'
        )

        db.session.add(attendance)
        db.session.commit()

        return jsonify({
            'recognized': True,
            'student': best_match,
            'attendance_id': attendance.id,
            'timestamp': attendance.timestamp.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/attendance/records', methods=['GET'])
@token_required
def get_attendance_records(current_user):
    """Get attendance records"""
    try:
        # Filter by student_id if provided
        student_id = request.args.get('student_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        query = AttendanceRecord.query

        if student_id:
            query = query.filter_by(student_id=student_id)

        if from_date:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(AttendanceRecord.timestamp >= from_dt)

        if to_date:
            to_dt = datetime.fromisoformat(to_date)
            query = query.filter(AttendanceRecord.timestamp <= to_dt)

        records = query.order_by(AttendanceRecord.timestamp.desc()).all()
        return jsonify([r.to_dict() for r in records]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/attendance/student/<int:student_id>/summary', methods=['GET'])
@token_required
def get_attendance_summary(current_user, student_id):
    """Get attendance summary for student"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        records = AttendanceRecord.query.filter_by(student_id=student_id).all()

        total = len(records)
        present = len([r for r in records if r.status == 'present'])
        absent = len([r for r in records if r.status == 'absent'])
        late = len([r for r in records if r.status == 'late'])

        attendance_percentage = (present / total * 100) if total > 0 else 0

        return jsonify({
            'student_id': student_id,
            'student_name': student.name,
            'total_days': total,
            'present': present,
            'absent': absent,
            'late': late,
            'attendance_percentage': round(attendance_percentage, 2),
            'status': 'good' if attendance_percentage >= 75 else 'warning'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ──── STATISTICS & REPORTS ─────────────────────────────────────────────

@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """Get dashboard statistics"""
    try:
        total_students = Student.query.count()
        active_students = Student.query.filter_by(status='active').count()
        today_attendance = AttendanceRecord.query.filter(
            AttendanceRecord.timestamp >= datetime.utcnow().date()
        ).count()

        trained_students = Student.query.filter(Student.face_encoding != None).count()

        avg_accuracy = db.session.query(db.func.avg(Student.model_accuracy)).scalar() or 0

        return jsonify({
            'total_students': total_students,
            'active_students': active_students,
            'today_attendance': today_attendance,
            'trained_students': trained_students,
            'average_model_accuracy': round(avg_accuracy, 2),
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/reports/attendance', methods=['GET'])
@token_required
def generate_attendance_report(current_user):
    """Generate attendance report"""
    try:
        # Get all students with their attendance
        students = Student.query.all()
        report_data = []

        for student in students:
            records = AttendanceRecord.query.filter_by(student_id=student.id).all()
            total = len(records)
            present = len([r for r in records if r.status == 'present'])
            percentage = (present / total * 100) if total > 0 else 0

            report_data.append({
                'student_id': student.student_id,
                'name': student.name,
                'roll_number': student.roll_number,
                'branch': student.branch,
                'total_days': total,
                'present': present,
                'attendance_percentage': round(percentage, 2)
            })

        return jsonify({
            'report': report_data,
            'generated_at': datetime.utcnow().isoformat(),
            'total_students': len(report_data)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ──── HEALTH CHECK ──────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ──── ERROR HANDLERS ────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


# ──── MAIN ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin user if doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@faceattend.local',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created (username: admin, password: admin123)")

    app.run(debug=True, host='0.0.0.0', port=5001)
