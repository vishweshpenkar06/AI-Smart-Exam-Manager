import pytest
from app import app, db, User, Message


class TestMessages:
    def test_send_message(self, admin_client):
        with app.app_context():
            teacher = User.query.filter_by(username='Teacher').first()
            tid = teacher.id

        resp = admin_client.post('/api/messages', json={
            'receiver_id': tid,
            'subject': 'Test Subject',
            'body': 'Hello Teacher!'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['subject'] == 'Test Subject'
        assert data['body'] == 'Hello Teacher!'

    def test_read_inbox(self, admin_client):
        with app.app_context():
            admin = User.query.filter_by(username='AdminPro').first()
            teacher = User.query.filter_by(username='Teacher').first()
            msg = Message(sender_id=teacher.id, receiver_id=admin.id, subject='Inbox Test', body='Hi')
            db.session.add(msg)
            db.session.commit()

        resp = admin_client.get('/api/messages?box=inbox')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1

    def test_read_sent(self, admin_client):
        with app.app_context():
            teacher = User.query.filter_by(username='Teacher').first()
            admin = User.query.filter_by(username='AdminPro').first()
            msg = Message(sender_id=admin.id, receiver_id=teacher.id, subject='Sent Test', body='Hi')
            db.session.add(msg)
            db.session.commit()

        resp = admin_client.get('/api/messages?box=sent')
        assert resp.status_code == 200

    def test_thread_replies(self, admin_client):
        with app.app_context():
            teacher = User.query.filter_by(username='Teacher').first()
            admin = User.query.filter_by(username='AdminPro').first()
            msg1 = Message(sender_id=admin.id, receiver_id=teacher.id, subject='Thread', body='Original')
            db.session.add(msg1)
            db.session.flush()
            msg2 = Message(sender_id=teacher.id, receiver_id=admin.id, subject='Thread', body='Reply', thread_id=msg1.id)
            db.session.add(msg2)
            db.session.commit()
            tid = msg1.id

        resp = admin_client.get(f'/api/messages/thread/{tid}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 2

    def test_archive_message(self, admin_client):
        with app.app_context():
            teacher = User.query.filter_by(username='Teacher').first()
            admin = User.query.filter_by(username='AdminPro').first()
            msg = Message(sender_id=admin.id, receiver_id=teacher.id, subject='Archive', body='Gone')
            db.session.add(msg)
            db.session.commit()
            mid = msg.id

        resp = admin_client.post(f'/api/messages/{mid}/archive')
        assert resp.status_code == 200
        assert resp.get_json()['is_archived'] is True

    def test_unread_count(self, admin_client):
        with app.app_context():
            admin = User.query.filter_by(username='AdminPro').first()
            teacher = User.query.filter_by(username='Teacher').first()
            msg = Message(sender_id=teacher.id, receiver_id=admin.id, subject='Unread', body='Test', is_read=False)
            db.session.add(msg)
            db.session.commit()

        resp = admin_client.get('/api/messages/unread-count')
        assert resp.status_code == 200
        assert resp.get_json()['count'] >= 1

    def test_get_users(self, admin_client):
        resp = admin_client.get('/api/messages/users')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 2

    def test_send_without_receiver(self, admin_client):
        resp = admin_client.post('/api/messages', json={'body': 'No receiver'})
        assert resp.status_code == 400
