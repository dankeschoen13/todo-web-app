import pytest
from app import create_app
from app.extensions import db


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
        "SQLALCHEMY_DATABASE_URI": "postgresql://marcobernacer@localhost:5432/test_db"
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