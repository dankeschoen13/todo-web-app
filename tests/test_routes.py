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

    def test_create_list_success(self, auth_client, seed_data):
        """
        Verifies that a logged-in user can successfully create a new task list.

        Steps:
        1. Authenticate the test client (auth_client fixture).
        2. Record the initial count of lists in the database.
        3. Make a POST request to '/api/new-list' with a valid JSON payload.
        4. Assert the API returns a 200 OK status.
        5. Assert the database list count increased by 1.
        6. Verify the newly created list exists and belongs to the authenticated user.
        """
        # Arrange
        stmt = select(func.count()).select_from(List)
        initial_count = db.session.scalar(stmt)

        # Act
        response = auth_client.post('/api/new-list', json={
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
    def test_create_list_error(self, mock_svc, auth_client):
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
        response = auth_client.post('/api/new-list', json={
            'title': 'Tech Stacks to Learn'
        })

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to create list"}

        new_list = db.session.scalar(
            select(List).filter_by(title='Tech Stacks to Learn')
        )

        assert new_list is None

    def test_edit_list_success(self, auth_client, seed_data):
        """
        Verifies that a logged-in user can successfully update the title of an existing list.

        Steps:
        1. Retrieve an existing list from the database and store its initial title.
        2. Make a PATCH request to the edit endpoint with a new title payload.
        3. Assert the API returns a 204 No Content status with an empty body.
        4. Refresh the database object to pull the latest state.
        5. Assert the title was mutated correctly and no longer matches the initial title.
        """
        # Arrange
        list_to_edit = db.session.scalar(select(List).where(List.id == 1))
        initial_title = list_to_edit.title

        # Act
        response = auth_client.patch('/api/lists/1/title', json={
            'title': 'Camping Checklist'
        })

        # Assert
        assert response.status_code == 204
        assert response.data == b""

        # Refresh the original object to grab the latest DB state
        db.session.refresh(list_to_edit)

        assert list_to_edit.title == 'Camping Checklist'
        assert list_to_edit.title != initial_title

    @patch('app.routes.main.ListSvc.update_list')
    def test_edit_list_error(self, mock_svc, auth_client):
        """
        Verifies that the API handles service-level validation errors gracefully when editing a list.

        Steps:
        1. Mock the ListSvc.update_list method to force a ValueError.
        2. Make a PATCH request to the edit endpoint with a new title payload.
        3. Assert the API catches the error and returns a 400 Bad Request status.
        4. Assert the JSON response contains the specific error message.
        5. Query the database to verify the title change was not applied.
        """
        # Arrange
        mock_svc.side_effect = ValueError("Unable to edit list title")

        # Act
        response = auth_client.patch('/api/lists/1/title', json={
            'title': 'Camping Checklist'
        })

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to edit list title"}

        edited_list = db.session.scalar(
            select(List).filter_by(title='Camping Checklist')
        )

        assert edited_list is None
