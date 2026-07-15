from sqlalchemy import select, func
from unittest.mock import patch
from app.models import List, Task
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
        list_id = 1
        list_to_edit = db.session.get(List, list_id)

        original_title = list_to_edit.title

        # Act
        response = auth_client.patch(f'/api/lists/{list_id}/title', json={
            'title': 'Camping Checklist'
        })

        # Assert
        assert response.status_code == 204
        assert response.data == b""

        # Refresh the original object to grab the latest DB state
        db.session.refresh(list_to_edit)

        assert list_to_edit.title != original_title
        assert list_to_edit.title == 'Camping Checklist'

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
        list_id = 1
        list_to_edit = db.session.get(List, list_id)

        original_title = list_to_edit.title

        mock_svc.side_effect = ValueError("Unable to edit list title")

        # Act
        response = auth_client.patch(f'/api/lists/{list_id}/title', json={
            'title': 'Camping Checklist'
        })

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to edit list title"}

        db.session.refresh(list_to_edit)

        assert list_to_edit.title == original_title
        assert list_to_edit.title != 'Camping Checklist'

    def test_delete_list_success(self, auth_client):
        """
        Verifies that the API successfully deletes a list and its database record.

        Steps:
        1. Define the target list ID for deletion.
        2. Make a DELETE request to the delete endpoint.
        3. Assert the API returns a 204 No Content status code.
        4. Assert the response data is empty.
        5. Query the database by ID to verify the list record has been removed.
        """
        # Arrange
        list_id = 1

        # Act
        response = auth_client.delete(f'/api/lists/{list_id}/delete')

        # Assert
        assert response.status_code == 204
        assert response.data == b""

        deleted_list = db.session.get(List, list_id)
        assert deleted_list is None

    @patch('app.routes.main.ListSvc.delete_list')
    def test_delete_list_error(self, mock_svc, auth_client):
        """
        Verifies that the API handles service-level errors gracefully when deleting a list.

        Steps:
        1. Mock the ListSvc.delete_list method to force a ValueError.
        2. Make a DELETE request to the delete endpoint.
        3. Assert the API catches the error and returns a 400 Bad Request status.
        4. Assert the JSON response contains the specific error message.
        5. Query the database by ID to verify the list record was not deleted.
        """
        # Arrange
        mock_svc.side_effect = ValueError("Unable to delete list.")
        list_id = 1

        # Act
        response = auth_client.delete(f'/api/lists/{list_id}/delete')

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to delete list."}

        list_to_delete = db.session.get(List, list_id)
        assert list_to_delete is not None


class TestTaskRoutes:
    """Tests for the Task creation and management API endpoints."""

    def test_create_task_success(self, auth_client, seed_data):
        """
        Verifies that the API successfully creates a new task and correctly associates it with a list and author.

        Steps:
        1. Query the initial count of tasks belonging to the target list.
        2. Make a POST request to the task creation endpoint with a valid JSON payload.
        3. Assert the API returns a 200 OK status code.
        4. Assert the total task count for the target list has incremented by 1.
        5. Query the database to verify the new task exists with the correct content, parent list ID, and author ID.
        """
        # Arrange
        target_list_id = 1

        stmt = select(func.count()).select_from(Task).where(
            Task.parent_list_id == target_list_id
        )
        initial_count = db.session.scalar(stmt)

        # Act
        response = auth_client.post(f'/api/lists/{target_list_id}/task', json={
            'content': 'Buy Tomatoes'
        })

        # Assert
        assert response.status_code == 200
        assert db.session.scalar(stmt) == initial_count + 1

        new_task = db.session.scalar(
            select(Task).filter_by(content='Buy Tomatoes')
        )

        assert new_task is not None
        assert new_task.parent_list_id == target_list_id
        assert new_task.author_id == seed_data.id

    @patch('app.routes.main.ListSvc.create_task')
    def test_create_task_error(self, mock_svc, auth_client):
        """
        Verifies that the API handles service-level errors gracefully when creating a task.

        Steps:
        1. Mock the ListSvc.create_task method to force a ValueError.
        2. Make a POST request to the task creation endpoint with a JSON payload.
        3. Assert the API catches the error and returns a 400 Bad Request status.
        4. Assert the JSON response contains the specific error message.
        5. Query the database to verify the task was not created.
        """
        # Arrange
        mock_svc.side_effect = ValueError("Unable to create task")
        target_list_id = 1

        # Act
        response = auth_client.post(f'/api/lists/{target_list_id}/task', json={
            'content': 'Buy Tomatoes'
        })

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to create task"}

        new_task = db.session.scalar(
            select(Task).filter_by(content='Buy Tomatoes')
        )

        assert new_task is None

    def test_complete_task_success(self, auth_client):
        """
        Verifies that the API successfully toggles a task's completion status.

        Steps:
        1. Query the database for an existing incomplete task.
        2. Make a PATCH request to the task toggle endpoint.
        3. Assert the API returns a 204 No Content status code.
        4. Assert the response data is empty.
        5. Refresh the task instance from the database and verify its `is_completed` attribute is now True.
        """
        # Arrange
        stmt = select(Task).where(Task.is_completed == False).limit(1)
        target_task = db.session.scalars(stmt).first()

        # Act
        response = auth_client.patch(f'/api/task/{target_task.id}/toggle')

        # Assert
        assert response.status_code == 204
        assert response.data == b""

        db.session.refresh(target_task)
        assert target_task.is_completed == True

    @patch('app.routes.main.ListSvc.complete_task')
    def test_complete_task_error(self, mock_svc, auth_client):
        """
        Verifies that the API handles service-level errors gracefully when toggling a task.

        Steps:
        1. Query the database for an existing incomplete task.
        2. Mock the ListSvc.complete_task method to force a ValueError.
        3. Make a PATCH request to the task toggle endpoint.
        4. Assert the API catches the error and returns a 400 Bad Request status.
        5. Assert the JSON response contains the specific error message.
        6. Refresh the task instance and verify its `is_completed` attribute remains False.
        """
        # Arrange
        stmt = select(Task).where(Task.is_completed == False).limit(1)
        target_task = db.session.scalars(stmt).first()
        mock_svc.side_effect = ValueError('Unable to mark task as complete')

        # Act
        response = auth_client.patch(f'/api/task/{target_task.id}/toggle')

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {'error': 'Unable to mark task as complete'}

        db.session.refresh(target_task)
        assert target_task.is_completed == False

    def test_delete_task_success(self, auth_client):
        """
        Verifies that the API successfully deletes a task and its database record.

        Steps:
        1. Define the target task ID for deletion.
        2. Make a DELETE request to the task deletion endpoint.
        3. Assert the API returns a 204 No Content status code.
        4. Assert the response data is empty.
        5. Query the database by ID to verify the task record has been removed.
        """
        # Arrange
        task_id = 1

        # Act
        response = auth_client.delete(f'/api/task/{task_id}/delete')

        # Assert
        assert response.status_code == 204
        assert response.data == b""

        deleted_task = db.session.get(Task, task_id)
        assert deleted_task is None

    @patch('app.routes.main.ListSvc.delete_task')
    def test_delete_task_error(self, mock_svc, auth_client):
        """
        Verifies that the API handles service-level errors gracefully when deleting a task.

        Steps:
        1. Mock the ListSvc.delete_task method to force a ValueError.
        2. Make a DELETE request to the task deletion endpoint.
        3. Assert the API catches the error and returns a 400 Bad Request status.
        4. Assert the JSON response contains the specific error message.
        5. Query the database by ID to verify the task record was not deleted.
        """
        # Arrange
        mock_svc.side_effect = ValueError("Unable to delete task.")
        task_id = 1

        # Act
        response = auth_client.delete(f'/api/task/{task_id}/delete')

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {"error": "Unable to delete task."}

        task_to_delete = db.session.get(Task, task_id)
        assert task_to_delete is not None

