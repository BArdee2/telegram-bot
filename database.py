from sqlalchemy.exc import SQLAlchemyError
from models import User, Task, UserTask
from config import Config
from sqlalchemy import and_
import datetime

def add_user(session, telegram_id, username, first_name, last_name):
    """Add new user to database"""
    try:
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            registered_at=datetime.datetime.utcnow()
        )
        session.add(new_user)
        session.commit()
        return new_user
    except SQLAlchemyError as e:
        session.rollback()
        raise e

def add_task(session, title, description, reward, task_type):
    """Add new task to database"""
    try:
        new_task = Task(
            title=title,
            description=description,
            reward=reward,
            task_type=task_type,
            created_at=datetime.datetime.utcnow()
        )
        session.add(new_task)
        session.commit()
        return new_task
    except SQLAlchemyError as e:
        session.rollback()
        raise e

def get_tasks(session, active_only=True):
    """Get list of tasks"""
    query = session.query(Task)
    if active_only:
        query = query.filter_by(is_active=True)
    return query.all()

def delete_task(session, task_id):
    """Mark task as inactive"""
    try:
        task = session.query(Task).get(task_id)
        if task:
            task.is_active = False
            session.commit()
        return task
    except SQLAlchemyError as e:
        session.rollback()
        raise e

def update_task_status(session, user_task_id, status, proof=None):
    """Update user task status"""
    try:
        user_task = session.query(UserTask).get(user_task_id)
        if user_task:
            user_task.status = status
            if proof:
                user_task.proof = proof
            if status == 'completed':
                user_task.completed_at = datetime.datetime.utcnow()
            session.commit()
        return user_task
    except SQLAlchemyError as e:
        session.rollback()
        raise e
