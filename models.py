"""
AI Exam Manager — Database Models
All SQLAlchemy models for persistent storage.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, staff
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and store the user's password using PBKDF2-SHA256."""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password, password)

    def lock_account(self, duration_minutes=30):
        """Lock the account for the given number of minutes."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)

    def is_locked(self):
        """Return True if the account is currently locked."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False


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
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), index=True)
    date = db.Column(db.String(20), nullable=False, index=True)
    start_time = db.Column(db.String(10), default='09:00')
    end_time = db.Column(db.String(10), default='12:00')
    status = db.Column(db.String(20), default='scheduled', index=True)
    session_label = db.Column(db.String(40), default='Morning')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite indexes for common query patterns
    __table_args__ = (
        db.Index('idx_exam_date_room', 'date', 'room_id'),
        db.Index('idx_exam_status_date', 'status', 'date'),
    )

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
    invigilator_id = db.Column(db.Integer, db.ForeignKey('invigilators.id'), index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    date = db.Column(db.String(20), nullable=False, index=True)
    attended = db.Column(db.Boolean, default=False)
    check_in_time = db.Column(db.String(10), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite indexes for common query patterns
    __table_args__ = (
        db.Index('idx_duty_invigilator_date', 'invigilator_id', 'date'),
        db.Index('idx_duty_exam_attended', 'exam_id', 'attended'),
    )

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
    name = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(60), default='General', index=True)
    quantity = db.Column(db.Integer, default=0)
    min_threshold = db.Column(db.Integer, default=10)
    unit = db.Column(db.String(20), default='pcs')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    usage_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite index for low-stock queries
    __table_args__ = (
        db.Index('idx_inventory_low_stock', 'quantity', 'min_threshold'),
    )

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


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default='info')
    severity = db.Column(db.String(10), default='low')
    is_read = db.Column(db.Boolean, default=False, index=True)
    link = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id, 'user_id': self.user_id,
            'title': self.title, 'message': self.message,
            'category': self.category, 'severity': self.severity,
            'is_read': self.is_read, 'link': self.link,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    subject = db.Column(db.String(200), default='No Subject')
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_archived = db.Column(db.Boolean, default=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    def to_dict(self):
        return {
            'id': self.id, 'sender_id': self.sender_id,
            'receiver_id': self.receiver_id, 'subject': self.subject,
            'body': self.body, 'is_read': self.is_read,
            'is_archived': self.is_archived, 'thread_id': self.thread_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'sender_name': self.sender.username if self.sender else '',
            'receiver_name': self.receiver.username if self.receiver else ''
        }


class ConflictPrediction(db.Model):
    __tablename__ = 'conflict_predictions'
    id = db.Column(db.Integer, primary_key=True)
    conflict_type = db.Column(db.String(40), nullable=False, index=True)
    severity = db.Column(db.String(10), default='medium')
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    affected_resources = db.Column(db.Text, default='[]')
    suggested_fix = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='detected', index=True)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(80), default='')

    def to_dict(self):
        return {
            'id': self.id, 'conflict_type': self.conflict_type,
            'severity': self.severity, 'title': self.title,
            'description': self.description,
            'affected_resources': json.loads(self.affected_resources or '[]'),
            'suggested_fix': self.suggested_fix,
            'status': self.status,
            'detected_at': self.detected_at.strftime('%Y-%m-%d %H:%M') if self.detected_at else '',
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M') if self.resolved_at else ''
        }
