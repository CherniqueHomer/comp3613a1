from sqlmodel import SQLModel
from typing import Literal

AccountRole = Literal["tenant", "landlord"]

class SigninRequest(SQLModel):
    username: str
    password: str

class SignupRequest(SQLModel):
    username: str
    email: str
    password: str
    role: AccountRole