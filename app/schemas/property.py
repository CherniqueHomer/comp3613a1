from datetime import date

from sqlmodel import SQLModel


class PropertyCreate(SQLModel):
    title: str
    address: str
    price: float
    description: str
    amenities: str
    photo_url: str
    availability_start: date
    availability_end: date
    lease_duration_months: int
