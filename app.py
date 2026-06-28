"""
AI EXAM MANAGER — Main Flask Application
Complete exam scheduling, invigilator management, inventory tracking,
and AI-powered intelligence.
"""
import os
import json
import time
import shutil
import secrets
import io
from datetime import datetime
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, flash, send_file, session, g)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from models import (db, User, Invigilator, Room, Subject, Student, Exam,
                    SeatingAssignment, DutyAssignment, InventoryItem,
                    RestockRequest, Branch, EmergencyLog, AuditLog,
                    Setting, StaffDuty, Notification, Message, ConflictPrediction)
from ai_engine import (AIExamScheduler, SocialGraphIsolation,
                       SelfHealingEngine, InventoryPredictor)
from excel_handler import (export_data, import_data, generate_template,
                           export_attendance_sheet)
from pdf_handler import export_exams_pdf, export_attendance_pdf
from seed_data import seed_all
from logger_setup import setup_logging
from config import config as app_config
from exceptions import AppException, ValidationError
from realtime import init_realtime, emit_notification, emit_broadcast, emit_role_notification, emit_conflict_alert
from notification_service import (create_notification, broadcast_notification,
                                  broadcast_role_notification, get_user_notifications,
                                  get_unread_count, mark_read, mark_all_read)

# ─── Load Environment Variables ───────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ─── App Configuration ────────────────────────────────────────────
app = Flask(__name__)
env_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(app_config[env_name])
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.getenv('DATABASE_URL') or f"sqlite:///{os.path.join(basedir, 'exam_manager.db')}"
)
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')

db.init_app(app)

# ─── Real-time WebSocket ──────────────────────────────────────────
init_realtime(app)

# ─── Security Extensions ──────────────────────────────────────────
csrf = CSRFProtect()
csrf.init_app(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

# ─── Logging Setup ────────────────────────────────────────────────
setup_logging(app)

# ─── File Upload Settings ─────────────────────────────────────────
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is permitted."""
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def validate_file_size(file):
    """Return True if file is within the 10MB limit."""
    file.seek(0, 2)        # Seek to end
    size = file.tell()
    file.seek(0)           # Reset to start
    return size <= MAX_FILE_SIZE


# ─── Login Manager ────────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ─── Security Headers ───────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# ─── Request / Response Logging ────────────────────────────────────────
@app.before_request
def before_request_hook():
    """Record request start time."""
    g.start_time = time.time()


@app.after_request
def log_response(response):
    """Log each request with method, path, status and duration."""
    elapsed = time.time() - g.get('start_time', time.time())
    app.logger.info(
        f'{request.method} {request.path} {response.status_code} '
        f'{elapsed:.3f}s ip={request.remote_addr}'
    )
    return response


# ─── Error Handlers ─────────────────────────────────────────────────
@app.errorhandler(AppException)
def handle_app_exception(error):
    return jsonify(error.to_dict()), error.status_code


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    app.logger.warning(f'CSRF error: {error.description}')
    return jsonify({'status': 'error', 'message': 'CSRF token invalid or missing'}), 400


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'status': 'error', 'message': 'Bad request'}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Resource not found'}), 404


@app.errorhandler(429)
def rate_limited(error):
    return jsonify({'status': 'error', 'message': 'Too many requests. Please slow down.'}), 429


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Internal server error: {error}')
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ─── Health Check ──────────────────────────────────────────────────
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and container liveness probes."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503


# ─── Database Initialization ──────────────────────────────────────
def init_db():
    """Create tables and seed default users, settings & sample data."""
    db.create_all()

    # ⭐ ONE-TIME PASSWORD MIGRATION (for existing plaintext passwords)
    migration_needed = Setting.query.filter_by(key='passwords_hashed').first()
    if not migration_needed:
        app.logger.info('[MIGRATION] Hashing existing plaintext passwords...')
        for user in User.query.all():
            if user.password and len(user.password) < 60:  # plaintext indicator
                try:
                    user.set_password(user.password)
                except:
                    pass  # Skip if already hashed
        db.session.add(Setting(key='passwords_hashed', value='true'))
        db.session.commit()
        app.logger.info('[MIGRATION] Password hashing complete!')

    # Seed users if not exist
    if not User.query.filter_by(username='AdminPro').first():
        user = User(username='AdminPro', role='admin', email='admin@college.edu', is_active=True)
        user.set_password('admin@123')
        db.session.add(user)
    if not User.query.filter_by(username='Teacher').first():
        user = User(username='Teacher', role='teacher', email='teacher@college.edu', is_active=True)
        user.set_password('teacher@456')
        db.session.add(user)
    if not User.query.filter_by(username='Staff').first():
        user = User(username='Staff', role='staff', email='staff@college.edu', is_active=True)
        user.set_password('staff@789')
        db.session.add(user)

    # Seed default settings
    defaults = {
        'college_name': 'AI Smart College',
        'college_code': 'AISC',
        'address': '123 Education Lane, Knowledge City',
        'phone': '+91-9876543210',
        'email': 'admin@aismartcollege.edu',
        'exam_duration': '3',
        'sessions_per_day': '2',
        'morning_start': '09:00',
        'morning_end': '12:00',
        'afternoon_start': '14:00',
        'afternoon_end': '17:00',
    }
    for key, value in defaults.items():
        if not Setting.query.filter_by(key=key).first():
            db.session.add(Setting(key=key, value=value))

    db.session.commit()

    # ── Seed sample data for all sections (only if tables are empty) ──
    models = {
        'Branch': Branch, 'Invigilator': Invigilator, 'Room': Room,
        'Subject': Subject, 'Student': Student, 'InventoryItem': InventoryItem,
        'StaffDuty': StaffDuty, 'Exam': Exam,
    }
    seed_summary = seed_all(db, models)
    if seed_summary:
        print(f'[SEED] Sample data loaded: {seed_summary}')


def log_action(action, details='', user='System', log_type='info'):
    """Add entry to audit log and emit to structured app logger."""
    entry = AuditLog(action=action, details=details, user=user, log_type=log_type)
    db.session.add(entry)
    db.session.commit()

    # Mirror to app logger at the appropriate level
    log_fn = {
        'info': app.logger.info,
        'warning': app.logger.warning,
        'error': app.logger.error,
        'security': app.logger.warning,
        'auth': app.logger.info,
        'emergency': app.logger.warning,
    }.get(log_type, app.logger.info)
    log_fn(f'[AUDIT] {action} | user={user} | {details}')


# ─── Authentication Routes ────────────────────────────────────────
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_portal'))
        else:
            return redirect(url_for('staff_portal'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Input validation
        if not username or not password:
            msg = 'Username and password are required'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg)
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        # Account locked check
        if user and user.is_locked():
            msg = 'Account locked due to too many failed attempts. Try again later.'
            app.logger.warning(f'Login attempt on locked account: {username}')
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 429
            flash(msg)
            return render_template('login.html')

        # Active account check
        if user and not user.is_active:
            msg = 'This account has been deactivated.'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 401
            flash(msg)
            return render_template('login.html')

        # Verify credentials
        if user and user.check_password(password):
            # Reset lockout on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db.session.commit()

            login_user(user)
            app.logger.info(f'Successful login: {username} (role={user.role})')
            log_action('Login', f'{username} logged in', username, 'auth')

            if request.is_json:
                redirect_url = (
                    url_for('admin_dashboard') if user.role == 'admin' else
                    url_for('teacher_portal') if user.role == 'teacher' else
                    url_for('staff_portal')
                )
                return jsonify({'success': True, 'redirect': redirect_url, 'role': user.role})

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_portal'))
            else:
                return redirect(url_for('staff_portal'))

        # Failed login — track attempts
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.lock_account(30)
                app.logger.warning(
                    f'Account locked after 5 failed attempts: {username}'
                )
                log_action(
                    'Account Locked',
                    f'{username} locked for 30 minutes after repeated failures',
                    'System', 'security'
                )
            db.session.commit()

        app.logger.warning(
            f'Failed login attempt for "{username}" from {request.remote_addr}'
        )
        log_action('Login Failed', f'Failed attempt for {username}', 'System', 'security')
        msg = 'Invalid username or password'
        if request.is_json:
            return jsonify({'success': False, 'message': msg}), 401
        flash(msg)
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    log_action('Logout', f'{current_user.username} logged out', current_user.username, 'auth')
    logout_user()
    return redirect(url_for('login'))


# ─── Portal Routes ────────────────────────────────────────────────
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('admin.html')


@app.route('/teacher')
@login_required
def teacher_portal():
    if current_user.role not in ('teacher', 'admin'):
        return redirect(url_for('index'))
    return render_template('teacher.html')


@app.route('/staff')
@login_required
def staff_portal():
    if current_user.role not in ('staff', 'admin'):
        return redirect(url_for('index'))
    return render_template('staff.html')


# ─── Dashboard API ────────────────────────────────────────────────
@app.route('/api/stats')
@login_required
def get_stats():
    stats = {
        'total_invigilators': Invigilator.query.count(),
        'available_invigilators': Invigilator.query.filter_by(available=True).count(),
        'total_rooms': Room.query.count(),
        'available_rooms': Room.query.filter_by(is_available=True).count(),
        'total_subjects': Subject.query.count(),
        'total_students': Student.query.count(),
        'total_exams': Exam.query.count(),
        'scheduled_exams': Exam.query.filter_by(status='scheduled').count(),
        'completed_exams': Exam.query.filter_by(status='completed').count(),
        'total_inventory': InventoryItem.query.count(),
        'low_stock_items': InventoryItem.query.filter(
            InventoryItem.quantity <= InventoryItem.min_threshold
        ).count(),
        'pending_restocks': RestockRequest.query.filter_by(status='pending').count(),
        'total_branches': Branch.query.count(),
        'total_duties': DutyAssignment.query.count(),
        'attended_duties': DutyAssignment.query.filter_by(attended=True).count(),
    }

    # Chart data: students per subject
    subjects = Subject.query.all()
    stats['subjects_chart'] = {
        'labels': [s.name for s in subjects],
        'data': [s.student_count for s in subjects],
        'colors': [s.color for s in subjects]
    }

    # Chart data: exams by date (eager load with relationships)
    exams = Exam.query.options(
        joinedload(Exam.subject),
        joinedload(Exam.room)
    ).all()
    from collections import Counter
    date_counts = Counter(e.date for e in exams)
    sorted_dates = sorted(date_counts.keys())
    stats['sessions_chart'] = {
        'labels': sorted_dates,
        'data': [date_counts[d] for d in sorted_dates]
    }

    # Chart data: invigilator availability
    stats['invigilator_chart'] = {
        'labels': ['Available', 'Unavailable'],
        'data': [stats['available_invigilators'],
                 stats['total_invigilators'] - stats['available_invigilators']],
        'colors': ['#2ecc71', '#e74c3c']
    }

    # Recent activity
    recent = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    stats['recent_activity'] = [a.to_dict() for a in recent]

    # Resource health
    rooms_data = [r.to_dict() for r in Room.query.all()]
    inv_data = [i.to_dict() for i in Invigilator.query.all()]
    items_data = [it.to_dict() for it in InventoryItem.query.all()]
    exams_data = [e.to_dict() for e in exams]
    stats['resource_health'] = InventoryPredictor.resource_health_check(
        rooms_data, inv_data, items_data, exams_data
    )

    return jsonify(stats)


# ─── Invigilator API ──────────────────────────────────────────────
@app.route('/api/invigilators', methods=['GET'])
@login_required
def get_invigilators():
    search = request.args.get('search', '')
    query = Invigilator.query
    if search:
        query = query.filter(Invigilator.name.contains(search))
    invs = query.order_by(Invigilator.name).all()
    return jsonify([i.to_dict() for i in invs])


@app.route('/api/invigilators', methods=['POST'])
@login_required
def add_invigilator():
    data = request.get_json()
    inv = Invigilator(
        name=data.get('name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        department=data.get('department', ''),
        available=data.get('available', True),
        max_duties=data.get('max_duties', 5),
        group_id=data.get('group_id', 0)
    )
    db.session.add(inv)
    db.session.commit()
    log_action('Added Invigilator', f'Added {inv.name}', current_user.username, 'create')
    return jsonify(inv.to_dict()), 201


@app.route('/api/invigilators/<int:inv_id>', methods=['PUT'])
@login_required
def update_invigilator(inv_id):
    inv = db.session.get(Invigilator, inv_id)
    if not inv:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    for key in ['name', 'email', 'phone', 'department', 'available', 'max_duties', 'group_id']:
        if key in data:
            setattr(inv, key, data[key])
    db.session.commit()
    log_action('Updated Invigilator', f'Updated {inv.name}', current_user.username, 'update')
    return jsonify(inv.to_dict())


@app.route('/api/invigilators/<int:inv_id>', methods=['DELETE'])
@login_required
def delete_invigilator(inv_id):
    inv = db.session.get(Invigilator, inv_id)
    if not inv:
        return jsonify({'error': 'Not found'}), 404
    name = inv.name
    db.session.delete(inv)
    db.session.commit()
    log_action('Deleted Invigilator', f'Deleted {name}', current_user.username, 'delete')
    return jsonify({'success': True})


@app.route('/api/invigilators/<int:inv_id>/toggle', methods=['POST'])
@login_required
def toggle_invigilator(inv_id):
    inv = db.session.get(Invigilator, inv_id)
    if not inv:
        return jsonify({'error': 'Not found'}), 404
    inv.available = not inv.available
    db.session.commit()
    status = 'available' if inv.available else 'unavailable'
    log_action('Toggled Invigilator', f'{inv.name} set to {status}', current_user.username, 'update')
    return jsonify(inv.to_dict())


# ─── Room API ─────────────────────────────────────────────────────
@app.route('/api/rooms', methods=['GET'])
@login_required
def get_rooms():
    rooms = Room.query.order_by(Room.name).all()
    return jsonify([r.to_dict() for r in rooms])


@app.route('/api/rooms', methods=['POST'])
@login_required
def add_room():
    data = request.get_json()
    room = Room(
        name=data.get('name', ''),
        capacity=data.get('capacity', 30),
        floor=data.get('floor', 'Ground'),
        room_type=data.get('room_type', 'Classroom'),
        is_available=data.get('is_available', True),
        equipment=data.get('equipment', ''),
        buffer_seats=data.get('buffer_seats', 5)
    )
    db.session.add(room)
    db.session.commit()
    log_action('Added Room', f'Added {room.name}', current_user.username, 'create')
    return jsonify(room.to_dict()), 201


@app.route('/api/rooms/<int:room_id>', methods=['PUT'])
@login_required
def update_room(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    for key in ['name', 'capacity', 'floor', 'room_type', 'is_available', 'equipment', 'buffer_seats']:
        if key in data:
            setattr(room, key, data[key])
    db.session.commit()
    log_action('Updated Room', f'Updated {room.name}', current_user.username, 'update')
    return jsonify(room.to_dict())


@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
@login_required
def delete_room(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({'error': 'Not found'}), 404
    name = room.name
    db.session.delete(room)
    db.session.commit()
    log_action('Deleted Room', f'Deleted {name}', current_user.username, 'delete')
    return jsonify({'success': True})


# ─── Subject API ──────────────────────────────────────────────────
@app.route('/api/subjects', methods=['GET'])
@login_required
def get_subjects():
    subjects = Subject.query.order_by(Subject.name).all()
    return jsonify([s.to_dict() for s in subjects])


@app.route('/api/subjects', methods=['POST'])
@login_required
def add_subject():
    data = request.get_json()
    subj = Subject(
        name=data.get('name', ''),
        code=data.get('code', ''),
        branch=data.get('branch', ''),
        student_count=data.get('student_count', 0),
        color=data.get('color', '#4A90D9')
    )
    db.session.add(subj)
    db.session.commit()
    log_action('Added Subject', f'Added {subj.name}', current_user.username, 'create')
    return jsonify(subj.to_dict()), 201


@app.route('/api/subjects/<int:subj_id>', methods=['PUT'])
@login_required
def update_subject(subj_id):
    subj = db.session.get(Subject, subj_id)
    if not subj:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    for key in ['name', 'code', 'branch', 'student_count', 'color']:
        if key in data:
            setattr(subj, key, data[key])
    db.session.commit()
    log_action('Updated Subject', f'Updated {subj.name}', current_user.username, 'update')
    return jsonify(subj.to_dict())


@app.route('/api/subjects/<int:subj_id>', methods=['DELETE'])
@login_required
def delete_subject(subj_id):
    subj = db.session.get(Subject, subj_id)
    if not subj:
        return jsonify({'error': 'Not found'}), 404
    name = subj.name
    db.session.delete(subj)
    db.session.commit()
    log_action('Deleted Subject', f'Deleted {name}', current_user.username, 'delete')
    return jsonify({'success': True})


# ─── Student API ──────────────────────────────────────────────────
@app.route('/api/students', methods=['GET'])
@login_required
def get_students():
    branch = request.args.get('branch', '')
    query = Student.query
    if branch:
        query = query.filter_by(branch=branch)
    students = query.order_by(Student.roll_no).all()
    return jsonify([s.to_dict() for s in students])


@app.route('/api/students', methods=['POST'])
@login_required
def add_student():
    data = request.get_json()
    student = Student(
        name=data.get('name', ''),
        roll_no=data.get('roll_no', ''),
        branch=data.get('branch', ''),
        group_id=data.get('group_id', 0),
        email=data.get('email', ''),
        phone=data.get('phone', '')
    )
    db.session.add(student)
    db.session.commit()
    log_action('Added Student', f'Added {student.name}', current_user.username, 'create')
    return jsonify(student.to_dict()), 201


@app.route('/api/students/<int:sid>', methods=['PUT'])
@login_required
def update_student(sid):
    student = db.session.get(Student, sid)
    if not student:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    for key in ['name', 'roll_no', 'branch', 'group_id', 'email', 'phone']:
        if key in data:
            setattr(student, key, data[key])
    db.session.commit()
    log_action('Updated Student', f'Updated {student.name}', current_user.username, 'update')
    return jsonify(student.to_dict())


@app.route('/api/students/<int:sid>', methods=['DELETE'])
@login_required
def delete_student(sid):
    student = db.session.get(Student, sid)
    if not student:
        return jsonify({'error': 'Not found'}), 404
    name = student.name
    db.session.delete(student)
    db.session.commit()
    log_action('Deleted Student', f'Deleted {name}', current_user.username, 'delete')
    return jsonify({'success': True})


# ─── AI Exam Generator API ────────────────────────────────────────
@app.route('/api/exams/generate', methods=['POST'])
@login_required
def generate_exams():
    data = request.get_json()
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    sessions_per_day = data.get('sessions_per_day', 2)
    subject_ids = data.get('subject_ids', [])

    # Clear existing exams, seating and duties before generating new ones
    SeatingAssignment.query.delete()
    DutyAssignment.query.delete()
    Exam.query.delete()
    # Reset invigilator duty counts
    for inv in Invigilator.query.all():
        inv.duty_count = 0
    db.session.commit()

    # Get settings
    settings = {s.key: s.value for s in Setting.query.all()}

    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400

    # Gather data
    if subject_ids:
        subjects = [s.to_dict() for s in Subject.query.filter(Subject.id.in_(subject_ids)).all()]
    else:
        subjects = [s.to_dict() for s in Subject.query.all()]

    rooms = [r.to_dict() for r in Room.query.filter_by(is_available=True).all()]
    invigilators = [i.to_dict() for i in Invigilator.query.filter_by(available=True).all()]
    students = [s.to_dict() for s in Student.query.all()]

    if not subjects:
        return jsonify({'error': 'No subjects selected'}), 400
    if not rooms:
        return jsonify({'error': 'No available rooms'}), 400

    # Run AI scheduler
    scheduler = AIExamScheduler(subjects, rooms, invigilators, students)
    schedule = scheduler.generate_timetable(
        start_date, end_date,
        sessions_per_day=sessions_per_day,
        morning_start=settings.get('morning_start', '09:00'),
        morning_end=settings.get('morning_end', '12:00'),
        afternoon_start=settings.get('afternoon_start', '14:00'),
        afternoon_end=settings.get('afternoon_end', '17:00')
    )
    conflicts = scheduler.get_conflicts()
    duty_assignments = scheduler.get_duty_assignments()

    # Save exams to database
    saved_exams = []
    for exam_data in schedule:
        exam = Exam(
            subject_id=exam_data['subject_id'],
            room_id=exam_data['room_id'],
            date=exam_data['date'],
            start_time=exam_data['start_time'],
            end_time=exam_data['end_time'],
            status='scheduled',
            session_label=exam_data['session_label']
        )
        db.session.add(exam)
        db.session.flush()
        saved_exams.append(exam)

        # Generate seating with social-graph isolation
        subj_students = [s for s in students if s['branch'] == exam_data.get('subject_code', '')]
        if not subj_students:
            # Use all students for demo purposes
            branch = Subject.query.get(exam_data['subject_id'])
            if branch:
                subj_students = [s for s in students if s['branch'] == branch.branch]

        if subj_students:
            seats = SocialGraphIsolation.generate_seating(
                subj_students,
                [{'id': exam_data['room_id'], 'name': exam_data['room_name'],
                  'capacity': exam_data['room_capacity'], 'is_available': True}],
                exam.id
            )
            for seat in seats:
                sa = SeatingAssignment(
                    exam_id=exam.id,
                    student_id=seat['student_id'],
                    room_id=seat['room_id'],
                    seat_no=seat['seat_no']
                )
                db.session.add(sa)

    # Save duty assignments
    for duty_data in duty_assignments:
        # Find the actual exam
        matching_exam = None
        for se in saved_exams:
            if (se.date == duty_data['date'] and
                se.start_time == duty_data['start_time'] and
                se.room_id == duty_data['room_id']):
                matching_exam = se
                break

        duty = DutyAssignment(
            invigilator_id=duty_data['invigilator_id'],
            exam_id=matching_exam.id if matching_exam else None,
            room_id=duty_data['room_id'],
            date=duty_data['date']
        )
        db.session.add(duty)

        # Update invigilator duty count
        inv = db.session.get(Invigilator, duty_data['invigilator_id'])
        if inv:
            inv.duty_count += 1

    db.session.commit()
    log_action('AI Exam Generation',
               f'Generated {len(schedule)} exams from {start_date} to {end_date}',
               current_user.username, 'ai')

    broadcast_notification(
        'Exam Schedule Generated',
        f'{len(schedule)} exams scheduled from {start_date} to {end_date}',
        category='info', severity='medium'
    )

    return jsonify({
        'success': True,
        'exams': schedule,
        'conflicts': conflicts,
        'duties_assigned': len(duty_assignments),
        'total_exams': len(schedule)
    })


@app.route('/api/exams', methods=['GET'])
@login_required
def get_exams():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 200)  # Max 200 per page for better dropdown support

    paginated = Exam.query.options(
        joinedload(Exam.subject),
        joinedload(Exam.room)
    ).order_by(Exam.date, Exam.start_time).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages,
        'data': [e.to_dict() for e in paginated.items]
    })


@app.route('/api/exams/<int:eid>', methods=['DELETE'])
@login_required
def delete_exam(eid):
    exam = db.session.get(Exam, eid)
    if not exam:
        return jsonify({'error': 'Not found'}), 404
    # Delete related seating and duties
    SeatingAssignment.query.filter_by(exam_id=eid).delete()
    DutyAssignment.query.filter_by(exam_id=eid).delete()
    db.session.delete(exam)
    db.session.commit()
    log_action('Deleted Exam', f'Deleted exam #{eid}', current_user.username, 'delete')
    return jsonify({'success': True})


@app.route('/api/exams/clear', methods=['POST'])
@login_required
def clear_exams():
    SeatingAssignment.query.delete()
    DutyAssignment.query.delete()
    Exam.query.delete()
    # Reset duty counts
    for inv in Invigilator.query.all():
        inv.duty_count = 0
    db.session.commit()
    log_action('Cleared All Exams', 'All exams, seating, and duties cleared', current_user.username, 'delete')
    return jsonify({'success': True})


# ─── Seating API ──────────────────────────────────────────────────
@app.route('/api/seating', methods=['GET'])
@login_required
def get_seating():
    exam_id = request.args.get('exam_id', type=int)
    room_id = request.args.get('room_id', type=int)
    query = SeatingAssignment.query
    if exam_id:
        query = query.filter_by(exam_id=exam_id)
    if room_id:
        query = query.filter_by(room_id=room_id)
    seats = query.order_by(SeatingAssignment.seat_no).all()
    return jsonify([s.to_dict() for s in seats])


# ─── Duty API ─────────────────────────────────────────────────────
@app.route('/api/duties', methods=['GET'])
@login_required
def get_duties():
    date = request.args.get('date', '')
    inv_id = request.args.get('invigilator_id', type=int)
    query = DutyAssignment.query
    if date:
        query = query.filter_by(date=date)
    if inv_id:
        query = query.filter_by(invigilator_id=inv_id)
    duties = query.order_by(DutyAssignment.date).all()
    return jsonify([d.to_dict() for d in duties])


@app.route('/api/duties/<int:did>/attend', methods=['POST'])
@login_required
def mark_duty_attended(did):
    duty = db.session.get(DutyAssignment, did)
    if not duty:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    duty.attended = data.get('attended', True)
    duty.check_in_time = data.get('check_in_time', datetime.now().strftime('%H:%M'))
    db.session.commit()
    status = 'attended' if duty.attended else 'not attended'
    log_action('Duty Attendance', f'Duty #{did} marked as {status}', current_user.username, 'attendance')
    return jsonify(duty.to_dict())


# ─── Staff Duty API ───────────────────────────────────────────────
@app.route('/api/staff-duties', methods=['GET'])
@login_required
def get_staff_duties():
    date = request.args.get('date', '')
    query = StaffDuty.query
    if date:
        query = query.filter_by(date=date)
    duties = query.order_by(StaffDuty.date).all()
    return jsonify([d.to_dict() for d in duties])


@app.route('/api/staff-duties', methods=['POST'])
@login_required
def add_staff_duty():
    data = request.get_json()
    duty = StaffDuty(
        staff_name=data.get('staff_name', ''),
        duty_description=data.get('duty_description', ''),
        location=data.get('location', ''),
        date=data.get('date', ''),
        start_time=data.get('start_time', '09:00'),
        end_time=data.get('end_time', '17:00')
    )
    db.session.add(duty)
    db.session.commit()
    log_action('Added Staff Duty', f'Added duty for {duty.staff_name}', current_user.username, 'create')
    return jsonify(duty.to_dict()), 201


@app.route('/api/staff-duties/<int:did>', methods=['DELETE'])
@login_required
def delete_staff_duty(did):
    duty = db.session.get(StaffDuty, did)
    if not duty:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(duty)
    db.session.commit()
    log_action('Deleted Staff Duty', f'Deleted duty #{did}', current_user.username, 'delete')
    return jsonify({'success': True})


@app.route('/api/staff-duties/<int:did>/attend', methods=['POST'])
@login_required
def mark_staff_attended(did):
    duty = db.session.get(StaffDuty, did)
    if not duty:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    duty.attended = data.get('attended', True)
    duty.check_in_time = data.get('check_in_time', datetime.now().strftime('%H:%M'))
    db.session.commit()
    status = 'attended' if duty.attended else 'not attended'
    log_action('Staff Attendance', f'Staff duty #{did} marked as {status}', current_user.username, 'attendance')
    return jsonify(duty.to_dict())


# ─── Inventory API ────────────────────────────────────────────────
@app.route('/api/inventory', methods=['GET'])
@login_required
def get_inventory():
    items = InventoryItem.query.order_by(InventoryItem.name).all()
    return jsonify([i.to_dict() for i in items])


@app.route('/api/inventory', methods=['POST'])
@login_required
def add_inventory():
    data = request.get_json()
    item = InventoryItem(
        name=data.get('name', ''),
        category=data.get('category', 'General'),
        quantity=data.get('quantity', 0),
        min_threshold=data.get('min_threshold', 10),
        unit=data.get('unit', 'pcs')
    )
    db.session.add(item)
    db.session.commit()
    log_action('Added Inventory', f'Added {item.name}', current_user.username, 'create')
    return jsonify(item.to_dict()), 201


@app.route('/api/inventory/<int:iid>', methods=['PUT'])
@login_required
def update_inventory(iid):
    item = db.session.get(InventoryItem, iid)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    for key in ['name', 'category', 'quantity', 'min_threshold', 'unit']:
        if key in data:
            setattr(item, key, data[key])
    item.last_updated = datetime.utcnow()
    db.session.commit()
    log_action('Updated Inventory', f'Updated {item.name}', current_user.username, 'update')
    return jsonify(item.to_dict())


@app.route('/api/inventory/<int:iid>', methods=['DELETE'])
@login_required
def delete_inventory(iid):
    item = db.session.get(InventoryItem, iid)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    name = item.name
    db.session.delete(item)
    db.session.commit()
    log_action('Deleted Inventory', f'Deleted {name}', current_user.username, 'delete')
    return jsonify({'success': True})


@app.route('/api/inventory/<int:iid>/adjust', methods=['POST'])
@login_required
def adjust_inventory(iid):
    item = db.session.get(InventoryItem, iid)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    amount = data.get('amount', 0)
    old_qty = item.quantity
    item.quantity = max(0, item.quantity + amount)
    # Update usage rate
    if amount < 0:
        item.usage_rate = max(item.usage_rate, abs(amount) / 7)  # weekly rate estimate
    item.last_updated = datetime.utcnow()
    db.session.commit()
    direction = 'increased' if amount > 0 else 'decreased'
    log_action('Inventory Adjustment',
               f'{item.name}: {old_qty} → {item.quantity} ({direction} by {abs(amount)})',
               current_user.username, 'update')
    return jsonify(item.to_dict())


@app.route('/api/inventory/predict', methods=['GET'])
@login_required
def predict_inventory():
    items = [i.to_dict() for i in InventoryItem.query.all()]
    predictions = InventoryPredictor.predict_low_stock(items)
    return jsonify(predictions)


# ─── Restock Requests API ─────────────────────────────────────────
@app.route('/api/restocks', methods=['GET'])
@login_required
def get_restocks():
    status = request.args.get('status', '')
    query = RestockRequest.query
    if status:
        query = query.filter_by(status=status)
    restocks = query.order_by(RestockRequest.date.desc()).all()
    return jsonify([r.to_dict() for r in restocks])


@app.route('/api/restocks', methods=['POST'])
@login_required
def add_restock():
    data = request.get_json()
    req = RestockRequest(
        item_id=data.get('item_id'),
        requested_qty=data.get('requested_qty', 0),
        requested_by=data.get('requested_by', current_user.username),
        reason=data.get('reason', '')
    )
    db.session.add(req)
    db.session.commit()
    log_action('Restock Request', f'Requested {req.requested_qty} units', current_user.username, 'create')

    broadcast_role_notification(
        'admin',
        'New Restock Request',
        f'{current_user.username} requested {req.requested_qty} units of item #{req.item_id}',
        category='task', severity='medium'
    )

    return jsonify(req.to_dict()), 201


@app.route('/api/restocks/<int:rid>/approve', methods=['POST'])
@login_required
def approve_restock(rid):
    req = db.session.get(RestockRequest, rid)
    if not req:
        return jsonify({'error': 'Not found'}), 404
    req.status = 'approved'
    # Update inventory
    item = db.session.get(InventoryItem, req.item_id)
    if item:
        item.quantity += req.requested_qty
        item.last_updated = datetime.utcnow()
    db.session.commit()
    log_action('Restock Approved', f'Approved restock #{rid}', current_user.username, 'approve')

    if req.requested_by:
        requester = User.query.filter_by(username=req.requested_by).first()
        if requester:
            create_notification(
                requester.id, 'Restock Approved',
                f'Your restock request for {req.requested_qty} units has been approved',
                category='task', severity='low'
            )

    return jsonify(req.to_dict())


@app.route('/api/restocks/<int:rid>/reject', methods=['POST'])
@login_required
def reject_restock(rid):
    req = db.session.get(RestockRequest, rid)
    if not req:
        return jsonify({'error': 'Not found'}), 404
    req.status = 'rejected'
    db.session.commit()
    log_action('Restock Rejected', f'Rejected restock #{rid}', current_user.username, 'reject')

    if req.requested_by:
        requester = User.query.filter_by(username=req.requested_by).first()
        if requester:
            create_notification(
                requester.id, 'Restock Rejected',
                f'Your restock request for {req.requested_qty} units has been rejected',
                category='task', severity='medium'
            )

    return jsonify(req.to_dict())


# ─── Branch API ───────────────────────────────────────────────────
@app.route('/api/branches', methods=['GET'])
@login_required
def get_branches():
    branches = Branch.query.order_by(Branch.name).all()
    return jsonify([b.to_dict() for b in branches])


@app.route('/api/branches', methods=['POST'])
@login_required
def add_branch():
    data = request.get_json()
    branch = Branch(
        name=data.get('name', ''),
        code=data.get('code', ''),
        color=data.get('color', '#4A90D9'),
        student_count=data.get('student_count', 0)
    )
    db.session.add(branch)
    db.session.commit()
    log_action('Added Branch', f'Added {branch.name}', current_user.username, 'create')
    return jsonify(branch.to_dict()), 201


@app.route('/api/branches/<int:bid>', methods=['PUT'])
@login_required
def update_branch(bid):
    branch = db.session.get(Branch, bid)
    if not branch:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    for key in ['name', 'code', 'color', 'student_count']:
        if key in data:
            setattr(branch, key, data[key])
    db.session.commit()
    log_action('Updated Branch', f'Updated {branch.name}', current_user.username, 'update')
    return jsonify(branch.to_dict())


@app.route('/api/branches/<int:bid>', methods=['DELETE'])
@login_required
def delete_branch(bid):
    branch = db.session.get(Branch, bid)
    if not branch:
        return jsonify({'error': 'Not found'}), 404
    name = branch.name
    db.session.delete(branch)
    db.session.commit()
    log_action('Deleted Branch', f'Deleted {name}', current_user.username, 'delete')
    return jsonify({'success': True})


# ─── Emergency Handler API ────────────────────────────────────────
@app.route('/api/emergency/room', methods=['POST'])
@login_required
def emergency_room():
    data = request.get_json()
    room_id = data.get('room_id')
    reason = data.get('reason', 'Room unavailable')

    if not room_id:
        return jsonify({'error': 'Room ID required'}), 400

    # Mark room unavailable
    room = db.session.get(Room, room_id)
    if room:
        room.is_available = False
        db.session.commit()

    # Get current exams and rooms
    exams = [e.to_dict() for e in Exam.query.filter_by(status='scheduled').all()]
    rooms = [r.to_dict() for r in Room.query.filter_by(is_available=True).all()]

    result = SelfHealingEngine.handle_room_emergency(room_id, exams, rooms)

    if result['success']:
        # Apply reassignments
        for ra in result['reassignments']:
            exam = db.session.get(Exam, ra.get('exam_id'))
            if exam:
                old_room = exam.room.name if exam.room else 'Unknown'
                exam.room_id = ra['new_room_id']
                db.session.commit()

                # Update seating assignments
                SeatingAssignment.query.filter_by(
                    exam_id=exam.id, room_id=room_id
                ).update({'room_id': ra['new_room_id']})

                # Update duty assignments
                DutyAssignment.query.filter_by(
                    exam_id=exam.id, room_id=room_id
                ).update({'room_id': ra['new_room_id']})

        # Log emergency
        elog = EmergencyLog(
            emergency_type='room',
            old_resource=room.name if room else str(room_id),
            new_resource=', '.join([r['new_room'] for r in result['reassignments']]),
            reason=reason,
            affected_students=result['displaced_students'],
            affected_exams=json.dumps([r.get('subject_name', '') for r in result['reassignments']]),
            resolved=True,
            resolution_details=result['message']
        )
        db.session.add(elog)
        db.session.commit()

        log_action('Emergency: Room', f'Room emergency handled. {result["message"]}',
                   current_user.username, 'emergency')

        broadcast_notification(
            'Room Emergency Handled',
            f'{room.name if room else "Room"}: {result["message"]}',
            category='emergency', severity='critical'
        )

    return jsonify(result)


@app.route('/api/emergency/invigilator', methods=['POST'])
@login_required
def emergency_invigilator():
    data = request.get_json()
    inv_id = data.get('invigilator_id')
    reason = data.get('reason', 'Invigilator unavailable')

    if not inv_id:
        return jsonify({'error': 'Invigilator ID required'}), 400

    # Mark invigilator unavailable
    inv = db.session.get(Invigilator, inv_id)
    if inv:
        inv.available = False
        db.session.commit()

    duties = [d.to_dict() for d in DutyAssignment.query.filter_by(invigilator_id=inv_id).all()]
    invigilators = [i.to_dict() for i in Invigilator.query.filter_by(available=True).all()]

    result = SelfHealingEngine.handle_invigilator_emergency(inv_id, duties, invigilators)

    if result['success']:
        for ra in result['reassignments']:
            duty = db.session.get(DutyAssignment, ra.get('duty_id'))
            if duty:
                duty.invigilator_id = ra['new_invigilator_id']

        elog = EmergencyLog(
            emergency_type='invigilator',
            old_resource=inv.name if inv else str(inv_id),
            new_resource=', '.join([r['new_invigilator'] for r in result['reassignments']]),
            reason=reason,
            resolved=True,
            resolution_details=result['message']
        )
        db.session.add(elog)
        db.session.commit()

        log_action('Emergency: Invigilator', f'Invigilator emergency handled. {result["message"]}',
                   current_user.username, 'emergency')

        broadcast_notification(
            'Invigilator Emergency Handled',
            f'{inv.name if inv else "Invigilator"}: {result["message"]}',
            category='emergency', severity='critical'
        )

    return jsonify(result)


@app.route('/api/emergency/logs', methods=['GET'])
@login_required
def get_emergency_logs():
    logs = EmergencyLog.query.order_by(EmergencyLog.timestamp.desc()).all()
    return jsonify([l.to_dict() for l in logs])


# ─── Audit Log API ────────────────────────────────────────────────
@app.route('/api/audit', methods=['GET'])
@login_required
def get_audit():
    limit = request.args.get('limit', 50, type=int)
    log_type = request.args.get('type', '')
    query = AuditLog.query
    if log_type:
        query = query.filter_by(log_type=log_type)
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return jsonify([l.to_dict() for l in logs])


# ─── Conflict Detection API ──────────────────────────────────────
@app.route('/api/conflicts', methods=['GET'])
@login_required
def get_conflicts():
    status = request.args.get('status', '')
    query = ConflictPrediction.query
    if status:
        query = query.filter_by(status=status)
    conflicts = query.order_by(ConflictPrediction.detected_at.desc()).all()
    return jsonify([c.to_dict() for c in conflicts])


@app.route('/api/conflicts/detect', methods=['POST'])
@login_required
def detect_conflicts():
    from ai_engine import ConflictPredictor
    conflicts = ConflictPredictor.detect_all_conflicts()
    saved = []
    for c in conflicts:
        existing = ConflictPrediction.query.filter_by(
            conflict_type=c['conflict_type'], status='detected'
        ).first()
        if not existing:
            cp = ConflictPrediction(
                conflict_type=c['conflict_type'],
                severity=c['severity'],
                title=c['title'],
                description=c['description'],
                affected_resources=json.dumps(c.get('affected_resources', [])),
                suggested_fix=c.get('suggested_fix', '')
            )
            db.session.add(cp)
            saved.append(cp)
    db.session.commit()

    for cp in saved:
        if cp.severity == 'critical':
            broadcast_notification(cp.title, cp.description, category='emergency', severity='critical')
        emit_conflict_alert(cp.to_dict())

    log_action('Conflict Detection', f'Detected {len(saved)} new conflicts', current_user.username, 'ai')
    return jsonify({'conflicts': [c.to_dict() for c in saved], 'total_detected': len(conflicts)})


@app.route('/api/conflicts/<int:cid>/resolve', methods=['POST'])
@login_required
def resolve_conflict(cid):
    cp = db.session.get(ConflictPrediction, cid)
    if not cp:
        return jsonify({'error': 'Not found'}), 404
    cp.status = 'resolved'
    cp.resolved_at = datetime.utcnow()
    cp.resolved_by = current_user.username
    db.session.commit()
    log_action('Conflict Resolved', f'Resolved conflict #{cid}: {cp.title}', current_user.username, 'update')
    return jsonify(cp.to_dict())


# ─── Analytics API ────────────────────────────────────────────────
@app.route('/api/analytics/overview', methods=['GET'])
@login_required
def analytics_overview():
    total_exams = Exam.query.count()
    scheduled = Exam.query.filter_by(status='scheduled').count()
    completed = Exam.query.filter_by(status='completed').count()
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(is_available=True).count()
    total_invs = Invigilator.query.count()
    available_invs = Invigilator.query.filter_by(available=True).count()
    total_students = Student.query.count()
    total_inventory = InventoryItem.query.count()
    low_stock = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.min_threshold
    ).count()
    total_duties = DutyAssignment.query.count()
    attended_duties = DutyAssignment.query.filter_by(attended=True).count()
    total_emergencies = EmergencyLog.query.count()
    unresolved_emergencies = EmergencyLog.query.filter_by(resolved=False).count()
    active_conflicts = ConflictPrediction.query.filter_by(status='detected').count()

    duty_completion = round((attended_duties / max(total_duties, 1)) * 100, 1)

    return jsonify({
        'exams': {'total': total_exams, 'scheduled': scheduled, 'completed': completed},
        'rooms': {'total': total_rooms, 'available': available_rooms},
        'invigilators': {'total': total_invs, 'available': available_invs},
        'students': total_students,
        'inventory': {'total': total_inventory, 'low_stock': low_stock},
        'duties': {'total': total_duties, 'attended': attended_duties, 'completion_rate': duty_completion},
        'emergencies': {'total': total_emergencies, 'unresolved': unresolved_emergencies},
        'active_conflicts': active_conflicts
    })


@app.route('/api/analytics/trends', methods=['GET'])
@login_required
def analytics_trends():
    from collections import defaultdict

    exams_by_date = defaultdict(int)
    exams = Exam.query.all()
    for e in exams:
        exams_by_date[e.date] += 1

    duties_by_date = defaultdict(lambda: {'total': 0, 'attended': 0})
    duties = DutyAssignment.query.all()
    for d in duties:
        duties_by_date[d.date]['total'] += 1
        if d.attended:
            duties_by_date[d.date]['attended'] += 1

    emergencies_by_date = defaultdict(int)
    emergencies = EmergencyLog.query.all()
    for em in emergencies:
        day = em.timestamp.strftime('%Y-%m-%d') if em.timestamp else ''
        emergencies_by_date[day] += 1

    sorted_dates = sorted(set(list(exams_by_date.keys()) + list(duties_by_date.keys()) + list(emergencies_by_date.keys())))

    return jsonify({
        'dates': sorted_dates[-30:],
        'exams': [exams_by_date[d] for d in sorted_dates[-30:]],
        'duty_total': [duties_by_date[d]['total'] for d in sorted_dates[-30:]],
        'duty_attended': [duties_by_date[d]['attended'] for d in sorted_dates[-30:]],
        'emergencies': [emergencies_by_date[d] for d in sorted_dates[-30:]]
    })


@app.route('/api/analytics/invigilator-load', methods=['GET'])
@login_required
def invigilator_load():
    invigilators = Invigilator.query.all()
    data = []
    for inv in invigilators:
        duty_count = DutyAssignment.query.filter_by(invigilator_id=inv.id).count()
        attended = DutyAssignment.query.filter_by(invigilator_id=inv.id, attended=True).count()
        data.append({
            'id': inv.id,
            'name': inv.name,
            'department': inv.department,
            'duty_count': duty_count,
            'attended': attended,
            'fatigue_score': inv.fatigue_score,
            'max_duties': inv.max_duties,
            'utilization': round((duty_count / max(inv.max_duties, 1)) * 100, 1)
        })
    data.sort(key=lambda x: x['duty_count'], reverse=True)
    return jsonify(data)


@app.route('/api/analytics/room-utilization', methods=['GET'])
@login_required
def room_utilization():
    rooms = Room.query.all()
    data = []
    for room in rooms:
        exam_count = Exam.query.filter_by(room_id=room.id).count()
        scheduled = Exam.query.filter_by(room_id=room.id, status='scheduled').count()
        seat_usage = 0
        exams_in_room = Exam.query.filter_by(room_id=room.id).all()
        for ex in exams_in_room:
            seat_usage += SeatingAssignment.query.filter_by(exam_id=ex.id).count()
        avg_utilization = round((seat_usage / max(exam_count * room.capacity, 1)) * 100, 1) if room.capacity > 0 else 0
        data.append({
            'id': room.id,
            'name': room.name,
            'capacity': room.capacity,
            'room_type': room.room_type,
            'is_available': room.is_available,
            'exam_count': exam_count,
            'scheduled': scheduled,
            'total_seats_used': seat_usage,
            'avg_utilization': avg_utilization
        })
    data.sort(key=lambda x: x['avg_utilization'], reverse=True)
    return jsonify(data)


# ─── Notification API ──────────────────────────────────────────────
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    unread_only = request.args.get('unread_only', 'false') == 'true'
    limit = request.args.get('limit', 50, type=int)
    notifs = get_user_notifications(current_user.id, limit, unread_only)
    return jsonify([n.to_dict() for n in notifs])


@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def notification_unread_count():
    return jsonify({'count': get_unread_count(current_user.id)})


@app.route('/api/notifications/<int:nid>/read', methods=['POST'])
@login_required
def mark_notification_read(nid):
    notif = mark_read(nid, current_user.id)
    if not notif:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(notif.to_dict())


@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    mark_all_read(current_user.id)
    return jsonify({'success': True})


# ─── Messaging API ─────────────────────────────────────────────────
@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    box = request.args.get('box', 'inbox')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Message.query
    if box == 'inbox':
        query = query.filter_by(receiver_id=current_user.id, is_archived=False)
    elif box == 'sent':
        query = query.filter_by(sender_id=current_user.id, is_archived=False)
    elif box == 'archived':
        query = query.filter(
            ((Message.receiver_id == current_user.id) | (Message.sender_id == current_user.id)),
            Message.is_archived == True
        )

    paginated = query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages,
        'data': [m.to_dict() for m in paginated.items]
    })


@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    if not receiver_id:
        return jsonify({'error': 'Receiver required'}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        subject=data.get('subject', 'No Subject'),
        body=data.get('body', ''),
        thread_id=data.get('thread_id')
    )
    db.session.add(msg)
    db.session.commit()

    create_notification(
        receiver_id,
        f'New message from {current_user.username}',
        msg.body[:100],
        category='task',
        severity='medium',
        link=f'/messages'
    )

    log_action('Message Sent', f'To user #{receiver_id}', current_user.username, 'create')
    return jsonify(msg.to_dict()), 201


@app.route('/api/messages/<int:mid>/read', methods=['POST'])
@login_required
def mark_message_read(mid):
    msg = Message.query.filter(
        Message.id == mid,
        (Message.receiver_id == current_user.id) | (Message.sender_id == current_user.id)
    ).first()
    if not msg:
        return jsonify({'error': 'Not found'}), 404
    msg.is_read = True
    db.session.commit()
    return jsonify(msg.to_dict())


@app.route('/api/messages/<int:mid>/archive', methods=['POST'])
@login_required
def archive_message(mid):
    msg = Message.query.filter(
        Message.id == mid,
        (Message.receiver_id == current_user.id) | (Message.sender_id == current_user.id)
    ).first()
    if not msg:
        return jsonify({'error': 'Not found'}), 404
    msg.is_archived = True
    db.session.commit()
    return jsonify(msg.to_dict())


@app.route('/api/messages/unread-count', methods=['GET'])
@login_required
def message_unread_count():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False, is_archived=False).count()
    return jsonify({'count': count})


@app.route('/api/messages/thread/<int:tid>', methods=['GET'])
@login_required
def get_thread(tid):
    msgs = Message.query.filter(
        (Message.thread_id == tid) | (Message.id == tid),
        (Message.receiver_id == current_user.id) | (Message.sender_id == current_user.id)
    ).order_by(Message.created_at.asc()).all()
    return jsonify([m.to_dict() for m in msgs])


@app.route('/api/messages/users', methods=['GET'])
@login_required
def get_message_users():
    users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role} for u in users])


# ─── Settings API ─────────────────────────────────────────────────
@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    settings = Setting.query.all()
    return jsonify({s.key: s.value for s in settings})


@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    for key, value in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            db.session.add(Setting(key=key, value=str(value)))
    db.session.commit()
    log_action('Updated Settings', 'College settings updated', current_user.username, 'update')
    return jsonify({'success': True})


# ─── Import/Export API ────────────────────────────────────────────
@app.route('/api/import/<section>', methods=['POST'])
@login_required
def import_excel(section):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Validate file type
    if not file or not allowed_file(file.filename):
        app.logger.warning(f'Invalid file upload attempt: {file.filename}')
        return jsonify({'error': 'Invalid file type. Use Excel files only (.xlsx, .xls, .csv)'}), 400

    # Validate file size
    if not validate_file_size(file):
        app.logger.warning(f'File too large: {file.filename}')
        return jsonify({'error': 'File too large. Maximum 10MB allowed.'}), 413

    # Secure filename
    filename = secure_filename(file.filename)
    filename = f"{secrets.token_hex(4)}_{filename}"

    file_bytes = io.BytesIO(file.read())
    data, error = import_data(section, file_bytes)
    if error:
        return jsonify({'error': error}), 400

    # Save imported data
    count = 0
    # Map sections to corresponding models and matching database fields for deduplication
    config = {
        'invigilators': {'model': Invigilator, 'match': 'name'},
        'rooms': {'model': Room, 'match': 'name'},
        'subjects': {'model': Subject, 'match': 'name'},
        'students': {'model': Student, 'match': 'roll_no'},
        'inventory': {'model': InventoryItem, 'match': 'name'},
        'branches': {'model': Branch, 'match': 'name'},
        'staff_duties': {'model': StaffDuty, 'match': 'staff_name', 'additional': ['date', 'location']},
        'exams': {'model': Exam},
        'attendance': {'model': None}
    }

    if section not in config:
        return jsonify({'error': f'Unknown section: {section}'}), 400

    count = 0
    updates = 0
    
    for item in data:
        try:
            # --- SPECIAL HANDLING: ATTENDANCE IMPORT ---
            if section == 'attendance':
                inv = Invigilator.query.filter_by(name=item.get('name')).first()
                date_str = item.get('date')
                if inv:
                    duty = DutyAssignment.query.filter_by(invigilator_id=inv.id, date=date_str).first()
                    if duty:
                        duty.attended = item.get('attended', False)
                        duty.check_in_time = item.get('check_in_time', '')
                        updates += 1
                        continue
                
                staff_duty = StaffDuty.query.filter_by(staff_name=item.get('name'), date=date_str).first()
                if staff_duty:
                    staff_duty.attended = item.get('attended', False)
                    staff_duty.check_in_time = item.get('check_in_time', '')
                    updates += 1
                continue

            # --- SPECIAL HANDLING: EXAMS ---
            if section == 'exams':
                subject = Subject.query.filter_by(name=item.get('subject_name', '')).first()
                room = Room.query.filter_by(name=item.get('room_name', '')).first()
                if not subject: continue
                
                existing = Exam.query.filter_by(
                    subject_id=subject.id, date=item.get('date', ''),
                    start_time=item.get('start_time', '')
                ).first()
                
                if existing:
                    existing.room_id = room.id if room else existing.room_id
                    existing.session_label = item.get('session_label', existing.session_label)
                    existing.status = item.get('status', existing.status)
                    updates += 1
                else:
                    obj = Exam(
                        subject_id=subject.id, room_id=room.id if room else None,
                        date=item.get('date', ''), start_time=item.get('start_time', ''),
                        end_time=item.get('end_time', ''),
                        session_label=item.get('session_label', 'Morning'),
                        status=item.get('status', 'scheduled')
                    )
                    db.session.add(obj)
                    count += 1
                continue

            # --- GENERAL DEDUPLICATION HANDLING ---
            model_info = config[section]
            model_class = model_info['model']
            match_field = model_info['match']
            
            # Build filter for deduplication
            filters = {match_field: item.get(match_field)}
            for add_field in model_info.get('additional', []):
                filters[add_field] = item.get(add_field)
            
            existing = model_class.query.filter_by(**filters).first()
            if existing:
                for k, v in item.items():
                    setattr(existing, k, v)
                updates += 1
            else:
                obj = model_class(**item)
                db.session.add(obj)
                count += 1

        except Exception as e:
            app.logger.error(f"[IMPORT ERROR] Section: {section}, Error: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            continue

    db.session.commit()
    log_action(f'Import {section.title()}',
               f'Processed {len(data)} rows ({count} new, {updates} updated)',
               current_user.username, 'import')

    return jsonify({'success': True, 'imported': count, 'updated': updates, 'total': len(data)})


@app.route('/api/export/<section>', methods=['GET'])
@login_required
def export_excel(section):
    model_map = {
        'invigilators': Invigilator,
        'rooms': Room,
        'subjects': Subject,
        'students': Student,
        'inventory': InventoryItem,
        'branches': Branch,
        'staff_duties': StaffDuty,
        'exams': Exam,
    }

    model = model_map.get(section)
    if not model:
        return jsonify({'error': f'Unknown section: {section}'}), 400

    items = model.query.all()
    data = [i.to_dict() for i in items]

    output = export_data(section, data)
    if not output:
        return jsonify({'error': 'Export failed'}), 500

    log_action(f'Export {section.title()}',
               f'Exported {len(data)} records to Excel',
               current_user.username, 'export')

    filename = f'AI_Exam_Manager_{section}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/export/<section>/pdf', methods=['GET'])
@login_required
def export_pdf(section):
    if section != 'exams':
        return jsonify({'error': 'PDF export only available for exams currently'}), 400

    from sqlalchemy.orm import joinedload
    items = Exam.query.options(joinedload(Exam.subject), joinedload(Exam.room)).order_by(Exam.date, Exam.start_time).all()
    data = [i.to_dict() for i in items]
    
    if not data:
        return jsonify({'error': 'No exams found to export. Please generate a timetable first.'}), 400

    log_action('Export Exams PDF', f'Exported {len(data)} records to PDF', current_user.username, 'export')

    filename = f'AI_Exam_Manager_Exams_{datetime.now().strftime("%Y%m%d")}.pdf'
    output = export_exams_pdf(data)
    if not output:
        return jsonify({'error': 'Export failed'}), 500

    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/template/<section>', methods=['GET'])
@login_required
def download_template(section):
    output = generate_template(section)
    if not output:
        return jsonify({'error': 'Unknown section'}), 400

    filename = f'AI_Exam_Manager_{section}_template.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/export/attendance/<role>', methods=['GET'])
@login_required
def export_attendance(role):
    if role == 'teacher':
        duties = DutyAssignment.query.all()
        data = [d.to_dict() for d in duties]
        title = 'Invigilator Duty Attendance'
    elif role == 'staff':
        duties = StaffDuty.query.all()
        data = [d.to_dict() for d in duties]
        title = 'Staff Duty Attendance'
    else:
        return jsonify({'error': 'Invalid role'}), 400

    output = export_attendance_sheet(data, title)
    filename = f'AI_Exam_Manager_{role}_attendance_{datetime.now().strftime("%Y%m%d")}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/export/attendance/<role>/pdf', methods=['GET'])
@login_required
def export_attendance_pdf_route(role):
    if role == 'teacher':
        duties = DutyAssignment.query.all()
        data = [d.to_dict() for d in duties]
        title = 'Invigilator Duty Attendance'
    elif role == 'staff':
        duties = StaffDuty.query.all()
        data = [d.to_dict() for d in duties]
        title = 'Staff Duty Attendance'
    else:
        return jsonify({'error': 'Invalid role'}), 400

    output = export_attendance_pdf(data, title)
    filename = f'AI_Exam_Manager_{role}_attendance_{datetime.now().strftime("%Y%m%d")}.pdf'
    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


# ─── AI Suggestions API ───────────────────────────────────────────
@app.route('/api/ai/suggest', methods=['POST'])
@login_required
def ai_suggest():
    """Generic AI suggestion endpoint."""
    data = request.get_json()
    context = data.get('context', '')
    section = data.get('section', '')

    suggestions = []

    if section == 'scheduling':
        rooms = Room.query.filter_by(is_available=True).count()
        subjects = Subject.query.count()
        invs = Invigilator.query.filter_by(available=True).count()

        if rooms == 0:
            suggestions.append({'type': 'warning', 'message': 'No rooms available. Add rooms before scheduling.'})
        if subjects == 0:
            suggestions.append({'type': 'warning', 'message': 'No subjects found. Add subjects first.'})
        if invs == 0:
            suggestions.append({'type': 'warning', 'message': 'No invigilators available. Add invigilators first.'})
        if rooms > 0 and subjects > 0 and invs > 0:
            suggestions.append({'type': 'success', 'message': f'Ready to schedule! {rooms} rooms, {subjects} subjects, {invs} invigilators available.'})
            # Calculate optimal days needed
            slots_per_day = 2
            total_slots = rooms * slots_per_day
            days_needed = max(1, -(-subjects // total_slots))  # Ceiling division
            suggestions.append({'type': 'info', 'message': f'AI recommends minimum {days_needed} day(s) for {subjects} exams with {rooms} rooms.'})

    elif section == 'inventory':
        items = [i.to_dict() for i in InventoryItem.query.all()]
        predictions = InventoryPredictor.predict_low_stock(items)
        for pred in predictions[:5]:
            suggestions.append({
                'type': pred['urgency'],
                'message': f"{pred['item_name']}: {pred['days_until_low']} days until low stock. Restock {pred['recommended_restock']} units recommended."
            })
        if not predictions:
            suggestions.append({'type': 'success', 'message': 'All inventory levels are healthy.'})

    elif section == 'emergency':
        rooms = Room.query.filter_by(is_available=True).all()
        invs = Invigilator.query.filter_by(available=True).all()
        suggestions.append({'type': 'info', 'message': f'{len(rooms)} backup rooms available for emergency re-routing.'})
        suggestions.append({'type': 'info', 'message': f'{len(invs)} reserve invigilators on standby.'})

    elif section == 'dashboard':
        rooms_data = [r.to_dict() for r in Room.query.all()]
        inv_data = [i.to_dict() for i in Invigilator.query.all()]
        items_data = [it.to_dict() for it in InventoryItem.query.all()]
        exams_data = [e.to_dict() for e in Exam.query.all()]
        health = InventoryPredictor.resource_health_check(rooms_data, inv_data, items_data, exams_data)
        for rec in health.get('recommendations', []):
            suggestions.append({'type': 'info', 'message': rec})

    if not suggestions:
        suggestions.append({'type': 'info', 'message': 'No specific AI suggestions at this time.'})

    return jsonify({'suggestions': suggestions})


# ─── Administrative and Backup API ────────────────────────────────
@app.route('/admin/backup', methods=['POST'])
@login_required
def backup_database():
    """Create a database backup."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    try:
        if not os.path.exists('backups'):
            os.mkdir('backups')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'backups/exam_manager_{timestamp}.db'
        shutil.copy2('exam_manager.db', backup_path)

        app.logger.info(f'Database backed up: {backup_path}')
        log_action('Database Backup', f'Backup created: {backup_path}', current_user.username, 'info')

        return jsonify({'status': 'success', 'backup_file': backup_path})
    except Exception as e:
        app.logger.error(f'Backup failed: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/admin/restore/<backup_name>', methods=['POST'])
@login_required
def restore_backup(backup_name):
    """Restore from a backup point."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    try:
        backup_path = f'backups/{backup_name}'
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup not found'}), 404

        # Create safety backup first
        safety_backup = f'backups/safety_{int(datetime.now().timestamp())}.db'
        shutil.copy2('exam_manager.db', safety_backup)

        # Restore
        shutil.copy2(backup_path, 'exam_manager.db')

        app.logger.info(f'Database restored from: {backup_path}')
        log_action('Database Restore', f'Restored from: {backup_path}', current_user.username, 'security')

        return jsonify({
            'status': 'success',
            'message': 'Database restored',
            'safety_backup': safety_backup
        })
    except Exception as e:
        app.logger.error(f'Restore failed: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/admin/backups', methods=['GET'])
@login_required
def list_backups():
    """List available backups."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    if not os.path.exists('backups'):
        return jsonify({'backups': []})

    backups = []
    for f in os.listdir('backups'):
        path = os.path.join('backups', f)
        backups.append({
            'filename': f,
            'size_mb': round(os.path.getsize(path) / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat()
        })

    return jsonify({'backups': sorted(backups, key=lambda x: x['created'], reverse=True)})


# ─── App Entry Point ──────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        init_db()
    socketio.run(app, debug=True, port=5000)
