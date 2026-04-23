import uuid
from app.extensions import db
from app.models import User

class UserSvc:

    @classmethod
    def _active_users_query(cls):
        """
        Internal helper: Returns a Select object pre-filtered for active users.
        """
        return db.select(User)


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
        Creates a guest user.

        Returns:
            tuple: A user object and a guest UUID
        """
        guest_uuid = str(uuid.uuid4())
        guest_user = User(
            username=f"guest_{guest_uuid}",
            email=f"guest_{guest_uuid}@temp.local",
            password="unusable_password_hash"
        )

        db.session.add(guest_user)
        db.session.commit()

        return guest_user, guest_uuid