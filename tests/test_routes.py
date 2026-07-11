from sqlalchemy import select, func
from unittest.mock import patch
from app.models import List
from app.extensions import db

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
        # Arrange
        login_response = client.post('/api/login', json={
            'identifier': 'test@example.com',
            'password': 'password123'
        })

        # Guard assertion: Ensure the setup (login) succeeded before proceeding
        assert login_response.status_code == 200

        # Act
        response = client.get('/')

        # Assert
        assert response.status_code == 200

        # Verify the database objects successfully rendered in the HTML
        assert b"Groceries" in response.data
        assert b"Project Milestones" in response.data
        assert b"Buy milk" in response.data


class TestListRoutes:
    """Tests for the List creation and management API endpoints."""

    def test_create_list_success(self, client, seed_data):
        """
        Verifies that a logged-in user can successfully create a new task list.

        Steps:
        1. Authenticate the test client.
        2. Record the initial count of lists in the database.
        3. Make a POST request to '/api/new-list' with a valid JSON payload.
        4. Assert the API returns a 200 OK status.
        5. Assert the database list count increased by 1.
        6. Verify the newly created list exists and belongs to the authenticated user.
        """
        # Arrange
        client.post('/api/login', json={
            'identifier': 'test@example.com',
            'password': 'password123'
        })

        stmt = select(func.count()).select_from(List)
        initial_count = db.session.scalar(stmt)

        # Act
        response = client.post('/api/new-list', json={
            'title': 'Tech Stacks to Learn'
        })

        # Assert
        assert response.status_code == 200
        assert db.session.scalar(stmt) == initial_count + 1

        new_list = db.session.scalar(
            select(List).filter_by(title='Tech Stacks to Learn')
        )

        assert new_list is not None
        assert new_list.author_id == seed_data.id

    @patch('app.routes.main.ListSvc.create_list')
    def test_create_list_error(self, mock_svc, client):
        """
        Verifies the API handles service-level errors gracefully without crashing.

        Steps:
        1. Mock the ListSvc.create_list method to force a ValueError.
        2. Make a POST request to '/api/new-list'.
        3. Assert the API catches the error and returns a 400 Bad Request status.
        4. Assert the JSON response contains the specific error message.
        5. Verify that no new list was actually inserted into the database.
        """
        # Arrange
        mock_svc.side_effect = ValueError("Unable to create list")

        # Act
        response = client.post('/api/new-list', json={
            'title': 'Tech Stacks to Learn'
        })

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to create list"}

        new_list = db.session.scalar(
            select(List).filter_by(title='Tech Stacks to Learn')
        )

        assert new_list is None





