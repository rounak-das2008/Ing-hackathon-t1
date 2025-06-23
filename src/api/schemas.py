"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "customer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    cluster_id: Optional[int]
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime


class TransactionResponse(BaseModel):
    id: int
    date: datetime
    category: str
    debit: float
    credit: float
    balance: float
    description: Optional[str]
    
    class Config:
        from_attributes = True


class ClusterResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str
    tags: Optional[str]
    interest_rate: Optional[float]
    fees: Optional[float]
    min_balance: Optional[float]
    relevance_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class UserContextResponse(BaseModel):
    user: UserResponse
    cluster: Optional[ClusterResponse]
    transactions: List[TransactionResponse]
    forecast: Dict[str, Any]
    recommendations: List[ProductResponse]


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_transactions: int
    cluster_distribution: Dict[str, int]
    avg_transaction_value: float
    total_balance: float


class UserListResponse(BaseModel):
    users: List[UserResponse]