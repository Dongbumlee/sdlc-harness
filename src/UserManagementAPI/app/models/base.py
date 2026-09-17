"""Declarative base class for all SQLAlchemy ORM entities."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common base for ORM models."""

