from datetime import date
from decimal import Decimal

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: date
    # Positive = income, negative = expense
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    category: str = Field(index=True)
    description: str | None = None
