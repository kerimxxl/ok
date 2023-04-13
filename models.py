from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    due_date = Column(DateTime)

    user = relationship("User", back_populates="tasks")

User.tasks = relationship("Task", back_populates="user", cascade="all, delete, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    event_date = Column(DateTime)

    user = relationship("User", back_populates="events")

User.events = relationship("Event", back_populates="user", cascade="all, delete, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    file_id = Column(String)
    file_type = Column(String)

    user = relationship("User", back_populates="files")

User.files = relationship("File", back_populates="user", cascade="all, delete, delete-orphan")populates="user", cascade="all, delete, delete-orphan")