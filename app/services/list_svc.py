import logging
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import List, Task, User

logger = logging.getLogger(__name__)

class ListSvc:

    @classmethod
    def create_list(cls, author: User, title: str) -> List:

        if not title or not title.strip():
            title = "New List"

        new_list = List(title=title.strip(), author=author)

        try:
            db.session.add(new_list)
            db.session.commit()

        except IntegrityError as e:
            logger.error(f"Unable to create list: {e}")

            db.session.rollback()
            raise ValueError("Unable to create list")

        return new_list
