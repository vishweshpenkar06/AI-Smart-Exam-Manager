class TestAPI:
    def test_get_stats_admin(self, admin_client):
        response = admin_client.get('/api/stats')
        assert response.status_code == 200
        data = response.json
        assert 'total_invigilators' in data
        assert 'total_exams' in data

    def test_invigilator_crud(self, admin_client):
        # Create
        response = admin_client.post('/api/invigilators', json={
            'name': 'Test Invigilator',
            'email': 'test@example.com',
            'phone': '1234567890',
            'department': 'CS'
        })
        assert response.status_code == 201
        data = response.json
        inv_id = data['id']
        assert data['name'] == 'Test Invigilator'

        # Read
        response = admin_client.get('/api/invigilators')
        assert response.status_code == 200
        assert len(response.json) == 1

        # Update
        response = admin_client.put(f'/api/invigilators/{inv_id}', json={
            'name': 'Updated Invigilator'
        })
        assert response.status_code == 200
        assert response.json['name'] == 'Updated Invigilator'

        # Delete
        response = admin_client.delete(f'/api/invigilators/{inv_id}')
        assert response.status_code == 200
        assert response.json['success'] is True

    def test_room_crud(self, admin_client):
        # Create
        response = admin_client.post('/api/rooms', json={
            'name': 'Room 101',
            'capacity': 50,
            'room_type': 'Lab'
        })
        assert response.status_code == 201
        assert response.json['name'] == 'Room 101'
        room_id = response.json['id']

        # Read
        response = admin_client.get('/api/rooms')
        assert response.status_code == 200
        assert len(response.json) == 1

        # Delete
        response = admin_client.delete(f'/api/rooms/{room_id}')
        assert response.status_code == 200
