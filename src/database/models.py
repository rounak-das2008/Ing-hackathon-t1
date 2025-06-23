"""
Database models for the Financial Assistant platform.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for customers and admins."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")  # 'customer' or 'admin'
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    cluster = relationship("Cluster", back_populates="users")


class Transaction(Base):
    """Transaction model for financial data."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    category = Column(String(50), nullable=False)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    balance = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")


class Cluster(Base):
    """Cluster model for customer segmentation."""
    __tablename__ = "clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="cluster")


class ChatHistory(Base):
    """Chat history model for conversation tracking."""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")


class Product(Base):
    """Product model for financial products and recommendations."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(String(255), nullable=True)
    interest_rate = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    min_balance = Column(Float, nullable=True)
    target_cluster = Column(String(50), nullable=True)