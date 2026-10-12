from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Booked(SQLModel, table=True):
    __tablename__ = "booked"

    bookingID: Optional[int] = Field(default=None, primary_key=True)
    propertyID: int = Field(foreign_key="property.propertyID")
    userID: int = Field(foreign_key="user.id")
    move_in_date: date
    lease_duration_months: int
    applicant_name: str
    applicant_contact: str
    student_id: str
    message: str
    status: str = Field(default="Pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)