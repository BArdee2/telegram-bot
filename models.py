from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)
    referral_code = Column(String(50), unique=True)
    referred_by = Column(Integer, ForeignKey('users.id'))
    
    tasks = relationship("UserTask", back_populates="user")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    reward = Column(Float, nullable=False)
    task_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    requirements = Column(String(300))
    
    assignments = relationship("UserTask", back_populates="task")

class UserTask(Base):
    __tablename__ = 'user_tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    status = Column(String(20), default='pending')  # pending/completed/rejected
    submitted_at = Column(DateTime)
    completed_at = Column(DateTime)
    proof = Column(String(500))
    
    user = relationship("User", back_populates="tasks")
    task = relationship("Task", back_populates="assignments")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(20))  # credit/debit
    status = Column(String(20), default='pending')  # pending/completed/failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    reference = Column(String(100))
    description = Column(String(200))
