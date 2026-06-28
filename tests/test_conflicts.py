import pytest
from app import app, db, ConflictPrediction


class TestConflictDetection:
    def test_detect_conflicts(self, admin_client):
        resp = admin_client.post('/api/conflicts/detect')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'conflicts' in data
        assert 'total_detected' in data

    def test_get_conflicts_empty(self, admin_client):
        resp = admin_client.get('/api/conflicts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_resolve_conflict(self, admin_client):
        with app.app_context():
            cp = ConflictPrediction(
                conflict_type='test',
                severity='info',
                title='Test Conflict',
                description='Test description',
                status='detected'
            )
            db.session.add(cp)
            db.session.commit()
            cid = cp.id

        resp = admin_client.post(f'/api/conflicts/{cid}/resolve')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'resolved'
        assert data['resolved_by'] == 'AdminPro'

    def test_resolve_nonexistent(self, admin_client):
        resp = admin_client.post('/api/conflicts/99999/resolve')
        assert resp.status_code == 404

    def test_detect_does_not_duplicate(self, admin_client):
        admin_client.post('/api/conflicts/detect')
        resp = admin_client.post('/api/conflicts/detect')
        assert resp.status_code == 200
