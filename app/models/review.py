from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):
    __tablename__ = "review"

    reviewID: Optional[int] = Field(default=None, primary_key=True)
    bookingID: int = Field(foreign_key="booked.bookingID", unique=True)
    propertyID: int = Field(foreign_key="property.propertyID")
    userID: int = Field(foreign_key="user.id")
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)