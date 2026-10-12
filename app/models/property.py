from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Property(SQLModel, table=True):
    __tablename__ = "property"

    propertyID: Optional[int] = Field(default=None, primary_key=True)
    landlordID: int = Field(foreign_key="user.id")
    title: str
    address: str
    price: float
    description: str
    amenities: str
    photo_url: str
    availability_start: date
    availability_end: date
    lease_duration_months: int
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)