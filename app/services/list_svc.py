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
    def update_list(cls, list_id: int, new_title: str) -> List:

        if not new_title or not new_title.strip():
            new_title = "My List"

        existing_list = cls.get_list_by_id(list_id)
        if not existing_list:
            raise ValueError(f"Unable to find list with ID {list_id}")

        existing_list.title = new_title

        try:
            db.session.commit()

        except IntegrityError as e:
            logger.error(f"Unable to edit list title: {e}")

            db.session.rollback()
            raise ValueError("Unable to edit list title")

        return existing_list


    @classmethod
    def _active_task_query(cls):

        return db.select(Task)

    @classmethod
    def get_task_by_id(cls, task_id: int) -> List | None:

        stmt = cls._active_task_query().where(Task.id == task_id)
        return db.session.execute(stmt).scalar_one_or_none()

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

    @classmethod
    def complete_task(cls, task_id: int) -> Task:
        task = cls.get_task_by_id(task_id)

        if not task:
            raise ValueError(f"Unable to find task with ID {task_id}")

        task.is_completed = not task.is_completed

        try:
            db.session.commit()

        except IntegrityError as e:
            logger.error(f"Unable to mark task as complete: {e}")

            db.session.rollback()
            raise ValueError("Unable to mark task as complete")

        return task

