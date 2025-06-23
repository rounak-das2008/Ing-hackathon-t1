"""
FastAPI main application with all endpoints.
"""
import os
from datetime import timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.base import get_db, create_tables
from ..database.models import User, Transaction, Cluster, ChatHistory, Product
from ..core.security import (
    hash_password, verify_password, create_access_token, 
    get_current_user, require_admin, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..ml.clustering import CustomerClustering
from ..ml.forecasting import BalanceForecasting
from ..ml.recommendations import ProductRecommendation
from .schemas import *
from .chat_service import ChatService

# Create tables on startup
create_tables()

# Initialize FastAPI app
app = FastAPI(title="Financial Assistant API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML services
clustering_service = CustomerClustering()
forecasting_service = BalanceForecasting()
recommendation_service = ProductRecommendation()
chat_service = ChatService()

# Load ML models at startup
@app.on_event("startup")
async def startup_event():
    """Load ML models and initialize services."""
    try:
        # Initialize chat service
        await chat_service.initialize()
        print("✅ Chat service initialized")
    except Exception as e:
        print(f"⚠️ Chat service initialization failed: {e}")


# Authentication endpoints
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# Customer endpoints
@app.get("/api/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.get("/api/users/me/context", response_model=UserContextResponse)
async def get_user_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete user context for dashboard."""
    # Get user cluster info
    cluster = None
    if current_user.cluster_id is not None:
        cluster = db.query(Cluster).filter(Cluster.id == current_user.cluster_id).first()
    
    # Get recent transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).limit(100).all()
    
    # Generate forecast
    forecast = forecasting_service.generate_forecast(current_user.id, db)
    
    # Get recommendations
    cluster_name = cluster.name if cluster else "Unknown"
    forecast_summary = forecast.get("summary", "No forecast available")
    recommendations = recommendation_service.get_recommendations(
        current_user.id, cluster_name, forecast_summary, db
    )
    
    return {
        "user": current_user,
        "cluster": cluster,
        "transactions": transactions,
        "forecast": forecast,
        "recommendations": recommendations
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_assistant(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with the AI financial assistant."""
    try:
        # Get user context
        cluster = None
        if current_user.cluster_id is not None:
            cluster = db.query(Cluster).filter(Cluster.id == current_user.cluster_id).first()
        
        # Get forecast
        forecast = forecasting_service.generate_forecast(current_user.id, db)
        
        # Get recommendations
        cluster_name = cluster.name if cluster else "Unknown"
        forecast_summary = forecast.get("summary", "No forecast available")
        recommendations = recommendation_service.get_recommendations(
            current_user.id, cluster_name, forecast_summary, db, top_k=3
        )
        
        # Get recent chat history
        recent_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == current_user.id
        ).order_by(ChatHistory.timestamp.desc()).limit(5).all()
        
        # Generate AI response
        ai_response = await chat_service.generate_response(
            user_message=message.message,
            user_cluster=cluster_name,
            cluster_description=cluster.description if cluster else "",
            forecast_summary=forecast_summary,
            recommendations=recommendations,
            chat_history=recent_chats
        )
        
        # Save chat history
        chat_record = ChatHistory(
            user_id=current_user.id,
            user_message=message.message,
            ai_response=ai_response
        )
        db.add(chat_record)
        db.commit()
        
        return ChatResponse(response=ai_response, timestamp=chat_record.timestamp)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}"
        )


# Admin endpoints
@app.get("/api/admin/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard data."""
    # Get statistics
    total_users = db.query(User).filter(User.role == "customer").count()
    total_transactions = db.query(Transaction).count()
    
    # Cluster distribution
    cluster_dist = db.query(
        Cluster.name, func.count(User.id)
    ).join(User, User.cluster_id == Cluster.id).group_by(Cluster.name).all()
    
    cluster_distribution = {name: count for name, count in cluster_dist}
    
    # Average transaction value
    avg_transaction = db.query(func.avg(Transaction.debit)).scalar() or 0
    
    # Total balance (sum of latest balance for each user)
    latest_balances = db.query(
        Transaction.user_id,
        func.max(Transaction.balance).label('latest_balance')
    ).group_by(Transaction.user_id).subquery()
    
    total_balance = db.query(func.sum(latest_balances.c.latest_balance)).scalar() or 0
    
    return {
        "total_users": total_users,
        "total_transactions": total_transactions,
        "cluster_distribution": cluster_distribution,
        "avg_transaction_value": round(avg_transaction, 2),
        "total_balance": round(total_balance, 2)
    }


@app.get("/api/admin/users", response_model=UserListResponse)
async def get_all_users(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users for admin view."""
    users = db.query(User).filter(User.role == "customer").all()
    return {"users": users}


# ML training endpoints (admin only)
@app.post("/api/admin/train-clustering")
async def train_clustering_model(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Train the customer clustering model."""
    result = clustering_service.train_cluster_model(db)
    return result


@app.post("/api/admin/train-recommendations")
async def train_recommendation_model(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Build product recommendation embeddings."""
    result = recommendation_service.build_product_embeddings(db)
    return result


@app.post("/api/admin/train-forecasting/{user_id}")
async def train_forecasting_model(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Train forecasting model for a specific user."""
    result = forecasting_service.train_forecast_model(user_id, db)
    return result


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Financial Assistant API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)