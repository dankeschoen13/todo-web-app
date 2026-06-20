from psycopg2._psycopg import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, select, delete
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models import User
import uuid, logging

logger = logging.getLogger(__name__)

class UserSvc:

    @classmethod
    def _active_users_query(cls, id_only: bool = False):
        """
        Internal helper: Returns a Select object pre-filtered for active users.

        Args:
            id_only: Defaults to false. True if only a list of
            IDs are needed.
        """
        if id_only:
            stmt = db.select(User.id)
        else:
            stmt = db.select(User)

        return stmt

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
    def create_user(cls, email: str, username: str, password: str, guest_user: User | None = None) -> User:
        """
        Registers a new user. If a guest_user is provided, mutates the guest record
        into a fully registered user to preserve their existing session data.

        Args:
            email: The user's email address.
            username: The user's chosen display name.
            password: Plain text password (hashed internally before storage).
            guest_user: Optional. The current unauthenticated guest session user.

        Returns:
            User: The newly created or updated user instance.

        Raises:
            DuplicateUserError: If the email or username already exists.
            ValueError: On database commit failure.
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

        if guest_user:
            # Overwrite the guest account instead of creating a new row.
            # This ensures any foreign keys (like existing To-Do lists) stay attached
            # to the user without needing a massive data migration script.
            user_to_save = guest_user
            user_to_save.email = email
            user_to_save.username = username
            user_to_save.password = hash_and_salted_password
        else:
            # Fallback for users who blocked cookies or let their session expire
            user_to_save = User(
                email=email,
                username=username,
                password=hash_and_salted_password
            )
            db.session.add(user_to_save)

        try:
            db.session.commit()
        except IntegrityError as e:
            # Rollback is critical here to prevent the SQLAlchemy session from
            # hanging in a failed transaction state for future requests.
            logger.error(f"IntegrityError during user creation/conversion: {e}")
            db.session.rollback()
            raise ValueError("A database error occurred during registration.")

        return user_to_save

    @classmethod
    def fetch_guest_by_uuid(cls, guest_uuid: str) -> User | None:
        """
        Looks up a guest account with matching guest_uuid

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
    def fetch_all_guest_accounts_ids(cls, cut_off_hours: int = 24) -> list[User]:
        """
        Fetches all expired guest accounts in the database.

        Args:
            cut_off_hours: The number of hours from now that resulting data
            should be cut off. Defaults to 24 hours.

        Returns:
            list[User]: A list of guest user objects. Returns an empty list if none are found.
        """

        cut_off_time = datetime.now(timezone.utc) - timedelta(hours=cut_off_hours)

        conditions = [
            User.created_at < cut_off_time,
            User.is_guest
        ]

        stmt = cls._active_users_query(id_only=True).where(*conditions)

        return db.session.scalars(stmt).all()

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

    @classmethod
    def delete_guest_accounts(cls, retention_window: int = 24) -> int:

        ids_to_delete = cls.fetch_all_guest_accounts_ids(retention_window)

        if not ids_to_delete:
            return 0

        delete_stmt = (
            delete(User)
            .where(User.id.in_(ids_to_delete))
            .execution_options(synchronize_session="fetch")
        )

        try:
            result = db.session.execute(delete_stmt)
            db.session.commit()
        except IntegrityError as e:
            logger.error(f"Unable to delete guest users: {e}")

            db.session.rollback()
            raise ValueError("Unable to delete guest users.")

        return result.rowcount


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