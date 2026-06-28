import pytest
from app import app, db, Exam, Room, Invigilator, Student, DutyAssignment


class TestAnalytics:
    def test_overview(self, admin_client):
        resp = admin_client.get('/api/analytics/overview')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'exams' in data
        assert 'rooms' in data
        assert 'invigilators' in data
        assert 'duties' in data
        assert 'inventory' in data
        assert 'emergencies' in data
        assert 'active_conflicts' in data
        assert isinstance(data['exams']['total'], int)
        assert isinstance(data['duties']['completion_rate'], float)

    def test_trends(self, admin_client):
        resp = admin_client.get('/api/analytics/trends')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'dates' in data
        assert 'exams' in data
        assert 'duty_total' in data
        assert 'duty_attended' in data
        assert 'emergencies' in data
        assert isinstance(data['dates'], list)
        assert isinstance(data['exams'], list)

    def test_invigilator_load(self, admin_client):
        resp = admin_client.get('/api/analytics/invigilator-load')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert 'name' in item
            assert 'duty_count' in item
            assert 'fatigue_score' in item
            assert 'utilization' in item

    def test_room_utilization(self, admin_client):
        resp = admin_client.get('/api/analytics/room-utilization')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert 'name' in item
            assert 'capacity' in item
            assert 'exam_count' in item
            assert 'avg_utilization' in item

    def test_overview_has_correct_structure(self, admin_client):
        resp = admin_client.get('/api/analytics/overview')
        data = resp.get_json()
        assert 'total' in data['exams']
        assert 'scheduled' in data['exams']
        assert 'completed' in data['exams']
        assert 'total' in data['rooms']
        assert 'available' in data['rooms']
        assert 'total' in data['invigilators']
        assert 'available' in data['invigilators']
        assert 'total' in data['duties']
        assert 'attended' in data['duties']
