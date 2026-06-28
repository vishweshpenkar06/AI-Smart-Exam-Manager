import pytest
from app import app, db, User, Notification


class TestNotifications:
    def test_create_notification(self, admin_client):
        with app.app_context():
            user = User.query.filter_by(username='AdminPro').first()
            notif = Notification(
                user_id=user.id,
                title='Test Notification',
                message='This is a test',
                category='info',
                severity='low'
            )
            db.session.add(notif)
            db.session.commit()
            assert notif.id is not None
            assert notif.title == 'Test Notification'

    def test_get_notifications(self, admin_client):
        with app.app_context():
            user = User.query.filter_by(username='AdminPro').first()
            n1 = Notification(user_id=user.id, title='Notif 1', message='Msg 1')
            n2 = Notification(user_id=user.id, title='Notif 2', message='Msg 2', is_read=True)
            db.session.add_all([n1, n2])
            db.session.commit()

        resp = admin_client.get('/api/notifications')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 2

    def test_unread_count(self, admin_client):
        with app.app_context():
            user = User.query.filter_by(username='AdminPro').first()
            n = Notification(user_id=user.id, title='Unread', message='Test', is_read=False)
            db.session.add(n)
            db.session.commit()

        resp = admin_client.get('/api/notifications/unread-count')
        assert resp.status_code == 200
        assert resp.get_json()['count'] >= 1

    def test_mark_read(self, admin_client):
        with app.app_context():
            user = User.query.filter_by(username='AdminPro').first()
            n = Notification(user_id=user.id, title='Read me', message='Test', is_read=False)
            db.session.add(n)
            db.session.commit()
            nid = n.id

        resp = admin_client.post(f'/api/notifications/{nid}/read')
        assert resp.status_code == 200

    def test_mark_all_read(self, admin_client):
        resp = admin_client.post('/api/notifications/read-all')
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_notification_categories(self, admin_client):
        with app.app_context():
            user = User.query.filter_by(username='AdminPro').first()
            for cat in ['info', 'warning', 'emergency', 'task']:
                n = Notification(user_id=user.id, title=f'{cat} notif', message='Test', category=cat)
                db.session.add(n)
            db.session.commit()

        resp = admin_client.get('/api/notifications')
        assert resp.status_code == 200
        data = resp.get_json()
        categories = {n['category'] for n in data}
        assert 'info' in categories
        assert 'emergency' in categories
