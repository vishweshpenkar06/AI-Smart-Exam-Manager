import pytest
import os
from app import app, db, User, Setting

@pytest.fixture
def client():
    # Setup test config
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    # Disable rate limiting in tests
    app.config['RATELIMIT_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()

            # Seed default users (check existence first)
            if not User.query.filter_by(username='AdminPro').first():
                admin = User(username='AdminPro', role='admin', is_active=True)
                admin.set_password('admin@123')
                db.session.add(admin)

            if not User.query.filter_by(username='Teacher').first():
                teacher = User(username='Teacher', role='teacher', is_active=True)
                teacher.set_password('teacher@456')
                db.session.add(teacher)

            if not User.query.filter_by(username='Staff').first():
                staff = User(username='Staff', role='staff', is_active=True)
                staff.set_password('staff@789')
                db.session.add(staff)

            if not Setting.query.filter_by(key='passwords_hashed').first():
                db.session.add(Setting(key='passwords_hashed', value='true'))

            db.session.commit()

        yield client

        with app.app_context():
            db.session.remove()
            db.drop_all()

def _login_user(client, username, password):
    """Log in a user by setting the session directly (bypasses rate limiter)."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True

@pytest.fixture
def admin_client(client):
    _login_user(client, 'AdminPro', 'admin@123')
    return client

@pytest.fixture
def teacher_client(client):
    _login_user(client, 'Teacher', 'teacher@456')
    return client

@pytest.fixture
def staff_client(client):
    _login_user(client, 'Staff', 'staff@789')
    return client
