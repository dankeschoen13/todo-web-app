from sqlalchemy import select, func
from flask_login import current_user
from unittest.mock import patch
from app.models import List, Task, User
from app.services import DuplicateUserError
from app.extensions import db

class TestIndexRoute:

    def test_index_route_anon_view(self, client):
        """
        Verifies that an anonymous visitor sees the registration and login prompts on the index page.

        Steps:
        1. Make a GET request to the index route without authentication.
        2. Assert the API returns a 200 OK status code.
        3. Assert the response HTML contains the "Sign In" text/button.
        4. Assert the response HTML contains the "Register" text/button.
        """
        # Act
        response = client.get('/')

        # Assert
        assert response.status_code == 200
        assert b"Sign In" in response.data
        assert b"Register" in response.data

    def test_index_route_guest_view(self, guest_client, seed_data):
        """
        Verifies that a logged-in guest user still sees the registration and login prompts.

        Steps:
        1. Make a POST request to the login API to authenticate as the seeded guest account.
        2. Assert the login request is successful (200 OK).
        3. Make a GET request to the index route using the authenticated client session.
        4. Assert the API returns a 200 OK status code.
        5. Assert the response HTML contains the "Sign In" text/button.
        6. Assert the response HTML contains the "Register" text/button.
        """

        # Act
        response = guest_client.get('/')

        # Assert
        assert response.status_code == 200
        assert b"Sign In" in response.data
        assert b"Register" in response.data

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
        assert new_list.author_id == seed_data[0].id

    def test_create_list_route_creates_guest_account(self, client, seed_data):
        """
        Verifies that creating a new list while unauthenticated automatically provisions a guest account.

        Steps:
        1. Query the initial total count of users in the database.
        2. Make a POST request to the new list creation endpoint with a title payload.
        3. Assert the API returns a 200 OK status code.
        4. Assert the total user count has incremented by exactly 1.
        5. Query the database for the newly created list by its title.
        6. Assert the list exists and the title matches.
        7. Query the user who authored the list and assert their `is_guest` property is True.
        """
        # Arrange
        stmt = select(func.count()).select_from(User)
        initial_user_count = db.session.scalar(stmt)

        # Act
        response = client.post('/api/new-list', json={
            'title': 'New List'
        })

        # Assert
        assert response.status_code == 200
        assert db.session.scalar(stmt) == initial_user_count + 1

        added_list = db.session.scalar(
            select(List).where(List.title == 'New List').order_by(List.id.desc())
        )

        assert added_list is not None
        assert added_list.title == 'New List'

        new_author = db.session.get(User, added_list.author_id)
        assert new_author.is_guest is True

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
        assert new_task.author_id == seed_data[0].id

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


class TestAuthRoutes:
    """Tests for the Account Creation and Authentication API endpoints."""

    def test_register_page_anon_access(self, client, seed_data):
        """
        Verifies that an anonymous visitor can successfully access the registration page.

        Steps:
        1. Make a GET request to the registration route without authentication.
        2. Assert the API returns a 200 OK status code.
        3. Assert the response HTML contains the required form labels and buttons.
        """
        # Act
        response = client.get('/register')

        # Assert
        assert response.status_code == 200

        # Verify the form fields successfully rendered in the HTML
        assert b"Username" in response.data
        assert b"Confirm Password" in response.data
        assert b"Sign Up" in response.data

    def test_register_page_guest_access(self, guest_client, seed_data):
        """
        Verifies that a logged-in guest user can access the registration page to upgrade their account.

        Steps:
        1. Make a POST request to the login API to authenticate as the seeded guest account.
        2. Assert the login request is successful (200 OK).
        3. Make a GET request to the registration route.
        4. Assert the API returns a 200 OK status code.
        5. Assert the response HTML contains the required form labels and buttons.
        """

        # Act
        response = guest_client.get('/register')

        # Assert
        assert response.status_code == 200

        # Verify the form fields successfully rendered in the HTML
        assert b"Username" in response.data
        assert b"Confirm Password" in response.data
        assert b"Sign Up" in response.data

    def test_register_route_redirects_authenticated_user(self, auth_client, seed_data):
        """
        Verifies that a fully authenticated user is blocked from the register page and redirected.

        Steps:
        1. Make a GET request to the registration route using the pre-authenticated client fixture.
        2. Set follow_redirects=True to automatically fetch the redirect destination.
        3. Assert the final API response returns a 200 OK status code.
        4. Assert the final request path matches the main index route.
        5. Assert the flashed warning message is rendered in the final HTML response.
        """
        # Act
        response = auth_client.get('/register', follow_redirects=True)

        # Assert
        # Check that we ultimately landed on a valid page
        assert response.status_code == 200

        # Verify the client was bounced to the index route
        assert response.request.path == '/'

        # Verify the flash message was successfully passed through the session and rendered
        assert b"You are already logged in!" in response.data

    def test_register_api_anon_user_success(self, client, seed_data, app):
        """
        Verifies that an anonymous user can successfully register an account via the API.

        Steps:
        1. Query the initial total count of users in the database.
        2. Make a POST request to the registration API within a client context manager.
        3. Assert the API returns a 201 Created status code.
        4. Assert the JSON response contains the success message.
        5. Assert the total user count incremented by exactly 1.
        6. Query the database for the newly created user and verify the username matches.
        7. Assert that the newly created user was automatically authenticated (logged in) during the request.
        """
        # Arrange
        stmt = select(func.count()).select_from(User)
        initial_count = db.session.scalar(stmt)

        # Act - Wrap the request in a context manager to keep current_user alive
        with client:
            response = client.post('/api/register', json={
                'email': 'new_account@gmail.com',
                'password': 'password789',
                'username': 'Steve Jobs'
            })

            # Assert
            assert response.status_code == 201
            assert response.get_json() == {"message": "User created successfully"}

            assert db.session.scalar(stmt) == initial_count + 1

            new_user = db.session.scalar(
                select(User).where(User.email == "new_account@gmail.com")
            )

            assert new_user.username == 'Steve Jobs'

            # Because we are inside 'with client:', the request context is preserved so we can
            # reference the current_user object
            assert current_user.is_authenticated
            assert current_user.id == new_user.id

    def test_register_api_guest_user_success(self, guest_client, seed_data):
        """
        Verifies that a guest user can successfully convert their account into a real account via
        the register api.

        Steps:
        1. Query the ID of the seeded guest account and the total user count.
        2. Make a POST request to the registration API within a client context manager.
        3. Assert the API returns a 201 Created status code.
        4. Assert the JSON response contains the success message.
        5. Refresh the db session and assert the same guest account details were updated.
        6. Assert that no new account was created by matching ID and total user count.
        7. Assert the user is no longer flagged as a guest.
        8. Assert that the newly converted user remains authenticated during the request.
        """
        # Arrange
        guest_account = db.session.scalar(
            select(User).where(User.email == seed_data[1].email)
        )
        id_prior_conversion = guest_account.id

        stmt = select(func.count()).select_from(User)
        initial_user_count = db.session.scalar(stmt)

        # Act
        with guest_client:
            response = guest_client.post('/api/register', json={
                'email': 'converted_account@gmail.com',
                'password': 'password789',
                'username': 'Official Account'
            })

            # Assert
            assert response.status_code == 201
            assert response.get_json() == {"message": "User created successfully"}

            # Sync Python object with new database state
            db.session.refresh(guest_account)

            # Verify credentials updated
            assert guest_account.email == 'converted_account@gmail.com'
            assert guest_account.username == 'Official Account'

            # Verify it is the exact same row and no additional rows were created
            assert guest_account.id == id_prior_conversion
            assert db.session.scalar(stmt) == initial_user_count

            # Verify the guest status was successfully revoked
            assert guest_account.is_guest is False

            # Verify session context
            assert current_user.is_authenticated
            assert current_user.id == guest_account.id

    @patch('app.routes.main.UserSvc.create_user')
    def test_register_api_duplicate_user_error(self, mock_svc, client):
        """
        Verifies that the API handles duplicate user errors gracefully when registration fails.

        Steps:
        1. Mock the UserSvc.create_user method to force a custom DuplicateUserError.
        2. Make a POST request to the user registration endpoint.
        3. Assert the API catches the error and returns a 400 Bad Request status.
        4. Assert the JSON response contains the specific error message.
        5. Query the database to ensure no new account was added.
        """
        # Arrange
        stmt = select(func.count()).select_from(User)
        initial_count = db.session.scalar(stmt)

        mock_svc.side_effect = DuplicateUserError("This email is already registered.", "email")

        # Act
        response = client.post('/api/register', json={
            'email': 'new_account@gmail.com',
            'password': 'password789',
            'username': 'Steve Jobs'
        })

        # Assert
        assert response.status_code == 400
        assert response.get_json() == {
            "error": "This email is already registered.", "field": "email"
        }

        assert db.session.scalar(stmt) == initial_count

    @patch('app.routes.main.UserSvc.create_user')
    def test_register_api_value_error(self, mock_svc, client):
        """
        Verifies that the API handles service-level errors gracefully when registration fails.

        Steps:
        1. Mock the UserSvc.create_user method to force a ValueError.
        2. Make a POST request to the user registration endpoint.
        3. Assert the API catches the error and returns a 500 Internal Server Error.
        4. Assert the JSON response contains the specific error message.
        5. Query the database to ensure no new account was added.
        """
        # Arrange
        stmt = select(func.count()).select_from(User)
        initial_count = db.session.scalar(stmt)

        mock_svc.side_effect = ValueError("A database error occurred during registration.")

        # Act
        response = client.post('/api/register', json={
            'email': 'new_account@gmail.com',
            'password': 'password789',
            'username': 'Steve Jobs'
        })

        # Assert
        assert response.status_code == 500
        assert response.get_json() == {
            "error": "A database error occurred during registration.", "field": "global"
        }

        assert db.session.scalar(stmt) == initial_count

    def test_login_page_anon_access(self, client, seed_data):
        """
        Verifies that an anonymous visitor can successfully access the login page.

        Steps:
        1. Make a GET request to the registration route without authentication.
        2. Assert the API returns a 200 OK status code.
        3. Assert the response HTML contains the required form labels and buttons.
        """
        # Act
        response = client.get('/login')

        # Assert
        assert response.status_code == 200

        # Verify the form fields successfully rendered in the HTML
        assert b"Username or email address" in response.data
        assert b"Login to your account" in response.data

    def test_login_page_guest_user_access(self, guest_client, seed_data):
        """
        Verifies that a visitor with a guest user account can successfully access the registration page.

        Steps:
        1. Make a GET request to the registration route with an authenticated guest user.
        2. Assert the API returns a 200 OK status code.
        3. Assert the response HTML contains the required form labels and buttons.
        """
        # Act
        response = guest_client.get('/login')

        # Assert
        assert response.status_code == 200

        # Verify the form fields successfully rendered in the HTML
        assert b"Username or email address" in response.data
        assert b"Login to your account" in response.data


