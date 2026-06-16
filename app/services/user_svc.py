from psycopg2._psycopg import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from app.extensions import db
from app.models import User
import uuid, logging

logger = logging.getLogger(__name__)

class UserSvc:

    @classmethod
    def _active_users_query(cls):
        """
        Internal helper: Returns a Select object pre-filtered for active users.
        """
        return db.select(User)

    @classmethod
    def _existing_user_query(cls, email: str | None = None, username: str | None = None) -> User | None:
        query = cls._active_users_query()

        conditions = []
        if email:
            conditions.append(User.email == email)
        if username:
            conditions.append(User.username == username)

        if not conditions:
            raise ValueError("You must provide either 'email' or 'username'.")

        stmt = query.where(or_(*conditions))

        return db.session.execute(stmt).scalar_one_or_none()



    @classmethod
    def lookup_guest(cls, guest_uuid: str) -> User | None:
        """
        Looks up a café with matching username UUID.

        Args:
            guest_uuid (str): The guest user's UUID

        Returns:
            User | None: A user object or None
        """
        stmt = cls._active_users_query().where(
            User.username == f"guest_{guest_uuid}"
        )
        return db.session.execute(stmt).scalar_one_or_none()


    @classmethod
    def create_guest(cls) -> tuple[User, str]:
        """
        Creates a guest user object and saves it to the database.

        Returns:
            tuple: A user object and a guest UUID
        """
        guest_uuid = uuid.uuid4().hex
        guest_user = User(
            username=f"guest_{guest_uuid}",
            email=f"guest_{guest_uuid}@temp.local",
            password="unusable_password_hash"
        )

        db.session.add(guest_user)
        db.session.commit()

        return guest_user, guest_uuid

    @classmethod
    def create_new_user(cls, email: str, username: str, password: str) -> User | None:
        """
        Creates a new user object and saves it to the database.

        Args:
            email: user's email address
            username: user's preferred username
            password: user's password

        Returns:
            User | None: A user object or None
        """

        existing_user = cls._existing_user_query(email, username)
        if existing_user:
            if existing_user.email == email:
                raise DuplicateUserError("This email is already registered.", "email")
            if existing_user.username == username:
                raise DuplicateUserError("This username is already taken.", "username")

        hash_and_salted_password = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8
        )

        new_user = User(
            email=email,
            username=username,
            password=hash_and_salted_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError as e:
            logger.error(f"IntegrityError during user creation: {e}")

            db.session.rollback()
            raise ValueError("A database error occurred during registration.")

        return new_user


    @classmethod
    def authenticate_user(cls, identifier: str, password: str) -> User:
        if "@" in identifier:
            user = cls._existing_user_query(email=identifier)
        else:
            user = cls._existing_user_query(username=identifier)

        # noinspection PyTypeChecker
        if not user or not check_password_hash(user.password, password):
            raise AuthenticationError("Invalid email/username or password.")

        return user


class DuplicateUserError(Exception):
    """
    Raised when a user attempts to register with an existing email or username.
    """
    def __init__(self, message, field_name):
        super().__init__(message)
        self.field_name = field_name


class AuthenticationError(Exception):
    """
    Raised when login fails for any reason.
    """
    pass