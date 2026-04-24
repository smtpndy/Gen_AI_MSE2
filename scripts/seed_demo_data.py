#!/usr/bin/env python3
"""
Seed script: populates database with demo students and attendance records.
Usage: python scripts/seed_demo_data.py
"""
import sys
import random
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.database import engine, Base, SessionLocal
from backend.models.models import Student, Attendance, Admin
from backend.utils.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

BRANCHES = ["CSE", "ECE", "ME", "CE", "EE", "IT"]
NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Gupta", "Anjali Singh", "Vikram Rao",
    "Neha Verma", "Arjun Nair", "Pooja Mishra", "Karan Malhotra", "Divya Reddy",
    "Siddharth Joshi", "Kavya Kumar", "Rahul Bajaj", "Simran Kaur", "Aditya Mehta",
    "Riya Agarwal", "Manish Tiwari", "Shreya Bhatt", "Nikhil Choudhary", "Tanvi Shah",
    "Yash Pandey", "Ishaan Saxena", "Nisha Yadav", "Akash Dubey", "Pallavi Jain",
    "Harsh Srivastava", "Ananya Chatterjee", "Rishabh Mukherjee", "Swati Banerjee", "Deepak Bose",
]

print("🌱 Seeding demo data...")

# Create students
students_created = 0
for i, name in enumerate(NAMES):
    sid = f"STU2024{i+1:03d}"
    roll = f"{random.choice(BRANCHES)}{2024}{i+1:02d}"
    branch = random.choice(BRANCHES)
    existing = db.query(Student).filter(Student.student_id == sid).first()
    if not existing:
        s = Student(
            student_id=sid, name=name,
            roll_number=roll, branch=branch,
            email=f"{name.split()[0].lower()}@college.edu",
            image_count=random.randint(5, 30),
            is_active=True
        )
        db.add(s)
        students_created += 1

db.commit()
print(f"  ✓ Created {students_created} students")

# Seed attendance for past 30 days
students = db.query(Student).filter(Student.is_active == True).all()
records_created = 0
today = date.today()

for day_offset in range(30, 0, -1):
    target_date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    # ~75% attendance rate
    attending = random.sample(students, k=int(len(students) * random.uniform(0.6, 0.92)))
    for stu in attending:
        exists = db.query(Attendance).filter(
            Attendance.student_id == stu.id,
            Attendance.date == target_date
        ).first()
        if not exists:
            from datetime import datetime
            att = Attendance(
                student_id=stu.id, date=target_date,
                time_in=datetime.strptime(
                    f"{target_date} {random.randint(8,10):02d}:{random.randint(0,59):02d}:00",
                    "%Y-%m-%d %H:%M:%S"
                ),
                status="present",
                confidence=round(random.uniform(78, 98), 1),
                marked_by="face_recognition"
            )
            db.add(att)
            records_created += 1

db.commit()
print(f"  ✓ Created {records_created} attendance records (30 days)")
print("\n✅ Demo data seeded successfully!")
print("   Login: admin / Admin@123")
db.close()
