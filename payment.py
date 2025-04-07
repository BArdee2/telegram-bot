from sqlalchemy.exc import SQLAlchemyError
from database import Session
from models import User, Transaction
from config import Config
import datetime
import logging

logger = logging.getLogger(__name__)

def process_withdrawal(user_id: int, amount: float, method: str) -> tuple:
    """
    Process user withdrawal request
    Returns (success: bool, message: str)
    """
    if amount < Config.MIN_WITHDRAWAL:
        return False, f"Minimum withdrawal is {Config.MIN_WITHDRAWAL} {Config.CURRENCY}"
    
    session = Session()
    try:
        user = session.query(User).get(user_id)
        if not user:
            return False, "User not found"
        
        if user.balance < amount:
            return False, "Insufficient balance"
        
        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type='debit',
            status='pending',
            created_at=datetime.datetime.utcnow(),
            reference=f"WDR-{datetime.datetime.utcnow().timestamp()}",
            description=f"Withdrawal via {method}"
        )
        
        # Deduct from user balance
        user.balance -= amount
        
        session.add(transaction)
        session.commit()
        
        # Here you would integrate with actual payment API
        # For now, we'll simulate success
        transaction.status = 'completed'
        session.commit()
        
        return True, f"Withdrawal of {amount} {Config.CURRENCY} processed"
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Withdrawal error for user {user_id}: {str(e)}")
        return False, "Database error occurred"
    finally:
        session.close()

def credit_user(user_id: int, amount: float, reason: str) -> tuple:
    """Credit user balance for completed tasks"""
    session = Session()
    try:
        user = session.query(User).get(user_id)
        if not user:
            return False, "User not found"
        
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type='credit',
            status='completed',
            created_at=datetime.datetime.utcnow(),
            reference=f"CRD-{datetime.datetime.utcnow().timestamp()}",
            description=reason
        )
        
        user.balance += amount
        session.add(transaction)
        session.commit()
        return True, "Credit processed successfully"
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Credit error for user {user_id}: {str(e)}")
        return False, "Database error occurred"
    finally:
        session.close()
