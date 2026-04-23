import logging
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import List, Task, User

logger = logging.getLogger(__name__)

class ListSvc:

    @classmethod
    def _active_list_query(cls):

        return db.select(List)

    @classmethod
    def get_list_by_id(cls, list_id: int) -> List | None:

        stmt = cls._active_list_query().where(List.id == list_id)
        return db.session.execute(stmt).scalar_one_or_none()


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

    @classmethod
    def create_task(cls, list_id: int, content: str) -> List | None:
        parent_list = cls.get_list_by_id(list_id)

        new_task = Task(parent_list=parent_list, content=content)

        try:
            db.session.add(new_task)
            db.session.commit()

        except IntegrityError as e:
            logger.error(f"Unable to create list: {e}")

            db.session.rollback()
            raise ValueError("Unable to create list")

        return new_task
