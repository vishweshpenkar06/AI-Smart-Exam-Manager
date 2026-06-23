
from app import app, init_db
from models import db, Branch, Invigilator, Room, Subject, Student, InventoryItem, StaffDuty, Exam

with app.app_context():
    print(f"Branches: {Branch.query.count()}")
    print(f"Invigilators: {Invigilator.query.count()}")
    print(f"Rooms: {Room.query.count()}")
    print(f"Subjects: {Subject.query.count()}")
    print(f"Students: {Student.query.count()}")
    print(f"Inventory: {InventoryItem.query.count()}")
    print(f"Staff Duties: {StaffDuty.query.count()}")
    print(f"Exams: {Exam.query.count()}")
