"""
AI Exam Manager — Database Models
All SQLAlchemy models for persistent storage.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, staff

    def check_password(self, password):
        return self.password == password


class Invigilator(db.Model):
    __tablename__ = 'invigilators'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), default='')
    phone = db.Column(db.String(20), default='')
    department = db.Column(db.String(80), default='')
    available = db.Column(db.Boolean, default=True)
    duty_count = db.Column(db.Integer, default=0)
    max_duties = db.Column(db.Integer, default=5)
    group_id = db.Column(db.Integer, default=0)
    fatigue_score = db.Column(db.Float, default=0.0)
    consecutive_heavy = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'phone': self.phone, 'department': self.department,
            'available': self.available, 'duty_count': self.duty_count,
            'max_duties': self.max_duties, 'group_id': self.group_id,
            'fatigue_score': self.fatigue_score,
            'consecutive_heavy': self.consecutive_heavy
        }


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    capacity = db.Column(db.Integer, default=30)
    floor = db.Column(db.String(20), default='Ground')
    room_type = db.Column(db.String(40), default='Classroom')
    is_available = db.Column(db.Boolean, default=True)
    equipment = db.Column(db.String(200), default='')
    buffer_seats = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'capacity': self.capacity,
            'floor': self.floor, 'room_type': self.room_type,
            'is_available': self.is_available, 'equipment': self.equipment,
            'buffer_seats': self.buffer_seats
        }


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), default='')
    branch = db.Column(db.String(80), default='')
    student_count = db.Column(db.Integer, default=0)
    color = db.Column(db.String(20), default='#4A90D9')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'branch': self.branch, 'student_count': self.student_count,
            'color': self.color
        }


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)
    branch = db.Column(db.String(80), default='')
    group_id = db.Column(db.Integer, default=0)
    email = db.Column(db.String(120), default='')
    phone = db.Column(db.String(20), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'roll_no': self.roll_no,
            'branch': self.branch, 'group_id': self.group_id,
            'email': self.email, 'phone': self.phone
        }


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(10), default='09:00')
    end_time = db.Column(db.String(10), default='12:00')
    status = db.Column(db.String(20), default='scheduled')
    session_label = db.Column(db.String(40), default='Morning')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', backref='exams')
    room = db.relationship('Room', backref='exams')

    def to_dict(self):
        return {
            'id': self.id, 'subject_id': self.subject_id,
            'room_id': self.room_id, 'date': self.date,
            'start_time': self.start_time, 'end_time': self.end_time,
            'status': self.status, 'session_label': self.session_label,
            'subject_name': self.subject.name if self.subject else '',
            'subject_code': self.subject.code if self.subject else '',
            'room_name': self.room.name if self.room else ''
        }


class SeatingAssignment(db.Model):
    __tablename__ = 'seating_assignments'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    seat_no = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam = db.relationship('Exam', backref='seating')
    student = db.relationship('Student', backref='seating')
    room = db.relationship('Room', backref='seating_assignments')

    def to_dict(self):
        return {
            'id': self.id, 'exam_id': self.exam_id,
            'student_id': self.student_id, 'room_id': self.room_id,
            'seat_no': self.seat_no,
            'student_name': self.student.name if self.student else '',
            'student_roll': self.student.roll_no if self.student else '',
            'room_name': self.room.name if self.room else ''
        }


class DutyAssignment(db.Model):
    __tablename__ = 'duty_assignments'
    id = db.Column(db.Integer, primary_key=True)
    invigilator_id = db.Column(db.Integer, db.ForeignKey('invigilators.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    date = db.Column(db.String(20), nullable=False)
    attended = db.Column(db.Boolean, default=False)
    check_in_time = db.Column(db.String(10), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invigilator = db.relationship('Invigilator', backref='duties')
    exam = db.relationship('Exam', backref='duties')
    room = db.relationship('Room', backref='duty_assignments')

    def to_dict(self):
        return {
            'id': self.id, 'invigilator_id': self.invigilator_id,
            'exam_id': self.exam_id, 'room_id': self.room_id,
            'date': self.date, 'attended': self.attended,
            'check_in_time': self.check_in_time,
            'invigilator_name': self.invigilator.name if self.invigilator else '',
            'room_name': self.room.name if self.room else '',
            'subject_name': self.exam.subject.name if self.exam and self.exam.subject else ''
        }


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), default='General')
    quantity = db.Column(db.Integer, default=0)
    min_threshold = db.Column(db.Integer, default=10)
    unit = db.Column(db.String(20), default='pcs')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    usage_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'category': self.category,
            'quantity': self.quantity, 'min_threshold': self.min_threshold,
            'unit': self.unit, 'usage_rate': self.usage_rate,
            'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M') if self.last_updated else '',
            'low_stock': self.quantity <= self.min_threshold
        }


class RestockRequest(db.Model):
    __tablename__ = 'restock_requests'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    requested_qty = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    requested_by = db.Column(db.String(80), default='')
    reason = db.Column(db.String(200), default='')
    date = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('InventoryItem', backref='restock_requests')

    def to_dict(self):
        return {
            'id': self.id, 'item_id': self.item_id,
            'requested_qty': self.requested_qty, 'status': self.status,
            'requested_by': self.requested_by, 'reason': self.reason,
            'date': self.date.strftime('%Y-%m-%d %H:%M') if self.date else '',
            'item_name': self.item.name if self.item else ''
        }


class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), default='')
    color = db.Column(db.String(20), default='#4A90D9')
    student_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'color': self.color, 'student_count': self.student_count
        }


class EmergencyLog(db.Model):
    __tablename__ = 'emergency_logs'
    id = db.Column(db.Integer, primary_key=True)
    emergency_type = db.Column(db.String(40), default='room')
    old_resource = db.Column(db.String(120), default='')
    new_resource = db.Column(db.String(120), default='')
    reason = db.Column(db.String(200), default='')
    affected_students = db.Column(db.Integer, default=0)
    affected_exams = db.Column(db.String(200), default='')
    resolved = db.Column(db.Boolean, default=False)
    resolution_details = db.Column(db.String(500), default='')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'emergency_type': self.emergency_type,
            'old_resource': self.old_resource, 'new_resource': self.new_resource,
            'reason': self.reason, 'affected_students': self.affected_students,
            'affected_exams': self.affected_exams, 'resolved': self.resolved,
            'resolution_details': self.resolution_details,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else ''
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.String(500), default='')
    user = db.Column(db.String(80), default='System')
    log_type = db.Column(db.String(30), default='info')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'action': self.action, 'details': self.details,
            'user': self.user, 'log_type': self.log_type,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else ''
        }


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.String(500), default='')

    def to_dict(self):
        return {'id': self.id, 'key': self.key, 'value': self.value}


class StaffDuty(db.Model):
    __tablename__ = 'staff_duties'
    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(120), nullable=False)
    duty_description = db.Column(db.String(200), default='')
    location = db.Column(db.String(120), default='')
    date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(10), default='09:00')
    end_time = db.Column(db.String(10), default='17:00')
    attended = db.Column(db.Boolean, default=False)
    check_in_time = db.Column(db.String(10), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'staff_name': self.staff_name,
            'duty_description': self.duty_description,
            'location': self.location, 'date': self.date,
            'start_time': self.start_time, 'end_time': self.end_time,
            'attended': self.attended, 'check_in_time': self.check_in_time
        }
