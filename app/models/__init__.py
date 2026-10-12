"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.property import Property
from app.models.booking import Booked
from app.models.review import Review

__all__ = ["User", "Property", "Booked", "Review"]
