import unittest
from flask import session
from app import create_app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_admin_route_get(self):
        """Test GET request to the /admin route."""
        with self.client as client:
            # Simulate a logged-in user with admin role
            with client.session_transaction() as sess:
                sess['user'] = {
                    "https://mobilab.demo.app.com/roles": ["admin"]
                }

            response = client.get('/admin')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Admin Page", response.data)

    def test_admin_route_post_invalid_csrf(self):
        """Test POST request to the /admin route with invalid CSRF."""
        with self.client as client:
            # Simulate a logged-in user with admin role
            with client.session_transaction() as sess:
                sess['user'] = {
                    "https://mobilab.demo.app.com/roles": ["admin"]
                }

            # Render the form to get a valid CSRF token
            response = client.get('/admin')
            self.assertEqual(response.status_code, 200)
            csrf_token = self._extract_csrf_token(response.data.decode())

            # Submit the form with an invalid CSRF token
            response = client.post('/admin', data={"csrf_token": "invalid_token"})
            self.assertEqual(response.status_code, 400)  # Bad Request due to invalid CSRF

    def _extract_csrf_token(self, html):
        """Helper function to extract CSRF token from rendered HTML."""
        import re
        match = re.search(r'name="csrf_token" value="(.+?)"', html)
        return match.group(1) if match else None

if __name__ == "__main__":
    unittest.main()