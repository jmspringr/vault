from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.auth import get_current_user
from api.database import get_session
from api.models import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    User,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_owned_transaction(transaction_id: int, user: User, session: Session) -> Transaction:
    txn = session.get(Transaction, transaction_id)
    # Return 404 for other users' records so their existence isn't revealed
    if txn is None or txn.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txn = Transaction.model_validate(data, update={"user_id": user.id})
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.date.desc())
    )
    return session.exec(stmt).all()


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_owned_transaction(transaction_id, user, session)


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txn = get_owned_transaction(transaction_id, user, session)
    txn.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    txn = get_owned_transaction(transaction_id, user, session)
    session.delete(txn)
    session.commit()
