class TestAuth:
    def test_login_success(self, client):
        response = client.post('/login', json={
            'username': 'AdminPro',
            'password': 'admin@123'
        })
        assert response.status_code == 200
        assert response.json['success'] is True
        assert '/admin' in response.json['redirect']

    def test_login_failure(self, client):
        response = client.post('/login', json={
            'username': 'AdminPro',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
        assert response.json['success'] is False

    def test_account_lockout(self, client):
        # Fail 5 times
        for _ in range(5):
            client.post('/login', json={
                'username': 'AdminPro',
                'password': 'wrongpassword'
            })
        
        # 6th attempt should hit rate limit (429) or lockout (423)
        response = client.post('/login', json={
            'username': 'AdminPro',
            'password': 'wrongpassword'
        })
        assert response.status_code in [429, 423]

    def test_protected_route_unauthenticated(self, client):
        response = client.get('/api/stats')
        assert response.status_code == 302  # redirects to login
        assert '/login' in response.headers.get('Location')
