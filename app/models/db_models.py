from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import func, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db, login_manager


class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False
    )
    password: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )

    authored_lists: Mapped[list["List"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        lazy=True, passive_deletes=True
    )

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return str(self.id)

@login_manager.user_loader
def load_user(user_id) -> User:
    return db.session.get(User, int(user_id))



class List(db.Model):
    __tablename__ = 'lists'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    # parent:
    author: Mapped[User] = relationship(back_populates='authored_lists')
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    # children:
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="parent_list",
        cascade="all, delete-orphan",
        lazy=True, passive_deletes=True
    )



class Task(db.Model):
    __tablename__ = 'tasks'
    id:Mapped[int] = mapped_column(primary_key=True)
    content:Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    # parent:
    parent_list: Mapped[List] = relationship(back_populates='tasks')
    parent_list_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=False
    )