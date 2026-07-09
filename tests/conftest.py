from werkzeug.security import generate_password_hash
import pytest
from app import create_app
from app.extensions import db
from app.models import User, List, Task


@pytest.fixture
def app():
    """
    Initializes and configures a fresh application instance for testing.

    This fixture operates on the default function scope to ensure test
    isolation. It instantiates the application in testing mode with a
    dedicated test database connection.

    Setup:
        - Establishes the application context.
        - Synchronously creates all database tables.

    Yields:
        Flask: The configured application instance.

    Teardown:
        - Cleans up the database session.
        - Drops all tables to ensure a clean slate for subsequent tests.
    """
    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "postgresql://marcobernacer@localhost:5432/test_db",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "testing-key"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Creates a fresh test client for the application.

    Operates in-memory and bypasses the network layer to provide
    isolated, simulated HTTP requests for each individual test.
    """
    return app.test_client()


@pytest.fixture
def seed_data(app):
    """
    Seed test database with mock data for smooth integration testing.

    Creates mock user first, then lists and tasks.
    """
    print("Creating mock user...")
    test_user = User(
        username="test_user",
        email="test@example.com",
        password=generate_password_hash("password123")
    )
    db.session.add(test_user)
    db.session.commit()

    print("Creating mock lists and tasks...")
    list_1 = List(title="Groceries", author_id=test_user.id)
    list_2 = List(title="Project Milestones", author_id=test_user.id)

    db.session.add_all([list_1, list_2])
    db.session.commit()

    tasks = [
        Task(content="Buy milk", is_completed=False, parent_list_id=list_1.id),
        Task(content="Buy eggs", is_completed=True, parent_list_id=list_1.id),
        Task(content="Write unit tests", is_completed=False, parent_list_id=list_2.id),
        Task(content="Setup database seeding", is_completed=True, parent_list_id=list_2.id),
    ]

    db.session.add_all(tasks)
    db.session.commit()

    print("Database seeded successfully!")