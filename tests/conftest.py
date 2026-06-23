import pytest
import os
from app import app, db, User, Setting

@pytest.fixture
def client():
    # Setup test config
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Seed default users
            admin = User(username='AdminPro', role='admin', is_active=True)
            admin.set_password('admin@123')
            
            teacher = User(username='Teacher', role='teacher', is_active=True)
            teacher.set_password('teacher@456')
            
            staff = User(username='Staff', role='staff', is_active=True)
            staff.set_password('staff@789')
            
            db.session.add_all([admin, teacher, staff])
            
            db.session.add(Setting(key='passwords_hashed', value='true'))
            db.session.commit()
            
        yield client

        with app.app_context():
            db.session.remove()
            db.drop_all()

@pytest.fixture
def admin_client(client):
    client.post('/login', json={
        'username': 'AdminPro',
        'password': 'admin@123'
    })
    return client

@pytest.fixture
def teacher_client(client):
    client.post('/login', json={
        'username': 'Teacher',
        'password': 'teacher@456'
    })
    return client
