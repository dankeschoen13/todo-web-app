class TestIndexRoute:

    def test_index_route_displays_lists(self, client, seed_data):
        """
        Verifies that the index route correctly fetches and renders a logged-in
        user's specific lists via the Jinja template.

        Steps:
        1. Authenticate the test client using the seeded user data.
        2. Make a GET request to the index route.
        3. Assert the route returns a 200 OK status.
        4. Assert the raw HTML response contains the specific list titles
           associated with the current user.
        """
        login_response = client.post('/api/login', json={
            'identifier': 'test@example.com',
            'password': 'password123'
        })

        # Guard assertion: Ensure the setup (login) succeeded before proceeding
        assert login_response.status_code == 200

        response = client.get('/')

        assert response.status_code == 200

        # Verify the database objects successfully rendered in the HTML
        assert b"Groceries" in response.data
        assert b"Project Milestones" in response.data
        assert b"Buy milk" in response.data



