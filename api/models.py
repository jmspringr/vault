from datetime import date as Date
from decimal import Decimal

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str


class TransactionBase(SQLModel):
    date: Date
    # Positive = income, negative = expense
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    category: str = Field(index=True)
    description: str | None = None


class Transaction(TransactionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)


# Request/response schemas
class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(SQLModel):
    date: Date | None = None
    amount: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    category: str | None = None
    description: str | None = None


class TransactionRead(TransactionBase):
    id: int
