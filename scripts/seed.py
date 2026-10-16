"""Create a demo user and ~12 months of fake transactions.

Run from the repo root:  python -m scripts.seed
Safe to run repeatedly: does nothing if the demo user already exists.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker
from sqlmodel import Session, select

from api.auth import hash_password
from api.database import create_db_and_tables, engine
from api.models import Transaction, User

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"
MONTHS = 12

fake = Faker()


def money(low: float, high: float) -> Decimal:
    return Decimal(str(round(random.uniform(low, high), 2)))


def generate_transactions(user_id: int, start: date, end: date) -> list[Transaction]:
    txns = []

    def add(day: date, amount: Decimal, category: str, description: str):
        txns.append(Transaction(user_id=user_id, date=day, amount=amount,
                                category=category, description=description))

    day = start
    while day <= end:
        # Fixed monthly items
        if day.day == 1:
            add(day, Decimal("-1450.00"), "Rent", "Monthly rent")
            add(day, money(-140, -90), "Utilities", "Electric & internet")
        if day.day in (1, 15):
            add(day, Decimal("2400.00"), "Income", "Paycheck")

        # Variable everyday spending
        if day.weekday() == 5:
            add(day, money(-160, -60), "Groceries", f"{fake.last_name()} Market")
        if random.random() < 0.25:
            add(day, money(-65, -12), "Dining", fake.company())
        if random.random() < 0.15:
            add(day, money(-55, -25), "Transportation", "Gas")
        if random.random() < 0.08:
            add(day, money(-180, -20), "Shopping", fake.company())
        if random.random() < 0.06:
            add(day, money(-90, -10), "Entertainment", fake.catch_phrase())

        day += timedelta(days=1)
    return txns


def seed(session: Session) -> bool:
    """Seed the demo user and data. Returns False if already seeded."""
    existing = session.exec(select(User).where(User.username == DEMO_USERNAME)).first()
    if existing:
        return False

    random.seed(42)
    Faker.seed(42)

    user = User(username=DEMO_USERNAME, hashed_password=hash_password(DEMO_PASSWORD))
    session.add(user)
    session.commit()
    session.refresh(user)

    end = date.today()
    start = (end.replace(day=1) - timedelta(days=30 * (MONTHS - 1))).replace(day=1)
    session.add_all(generate_transactions(user.id, start, end))
    session.commit()
    return True


if __name__ == "__main__":
    create_db_and_tables()
    with Session(engine) as session:
        if seed(session):
            count = len(session.exec(select(Transaction)).all())
            print(f"Seeded user '{DEMO_USERNAME}' with {count} transactions.")
        else:
            print(f"User '{DEMO_USERNAME}' already exists; nothing to do.")
