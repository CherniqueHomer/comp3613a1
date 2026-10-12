from datetime import date

from sqlmodel import SQLModel


class BookingCreate(SQLModel):
    move_in_date: date
    lease_duration_months: int
    applicant_name: str
    applicant_contact: str
    student_id: str
    message: str = ""
