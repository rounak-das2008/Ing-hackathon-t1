"""
Script to train all ML models.
"""
import os
import sys
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.base import SessionLocal
from src.database.models import User
from src.ml.clustering import CustomerClustering
from src.ml.forecasting import BalanceForecasting
from src.ml.recommendations import ProductRecommendation


def train_clustering_model(db: Session):
    """Train the customer clustering model."""
    print("🔄 Training clustering model...")
    
    clustering_service = CustomerClustering()
    result = clustering_service.train_cluster_model(db)
    
    if "error" in result:
        print(f"❌ Clustering training failed: {result['error']}")
    else:
        print(f"✅ Clustering model trained successfully!")
        print(f"   - Silhouette Score: {result['silhouette_score']:.3f}")
        print(f"   - Number of clusters: {result['n_clusters']}")
        print(f"   - Number of users: {result['n_users']}")


def train_forecasting_models(db: Session):
    """Train forecasting models for all users."""
    print("🔄 Training forecasting models...")
    
    forecasting_service = BalanceForecasting()
    users = db.query(User).filter(User.role == "customer").all()
    
    successful_models = 0
    failed_models = 0
    
    for user in users:
        result = forecasting_service.train_forecast_model(user.id, db)
        
        if "error" in result:
            print(f"⚠️ Forecasting model for user {user.username} failed: {result['error']}")
            failed_models += 1
        else:
            print(f"✅ Forecasting model for user {user.username} trained successfully")
            successful_models += 1
    
    print(f"📊 Forecasting training summary: {successful_models} successful, {failed_models} failed")


def train_recommendation_model(db: Session):
    """Train the product recommendation model."""
    print("🔄 Training recommendation model...")
    
    recommendation_service = ProductRecommendation()
    result = recommendation_service.build_product_embeddings(db)
    
    if "error" in result:
        print(f"❌ Recommendation training failed: {result['error']}")
    else:
        print(f"✅ Recommendation model trained successfully!")
        print(f"   - Number of products: {result['n_products']}")
        print(f"   - Embedding dimension: {result['embedding_dimension']}")


def main():
    """Main training function."""
    print("🚀 Starting ML model training...")
    
    # Create ml_models directory
    os.makedirs("ml_models", exist_ok=True)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Train all models
        train_clustering_model(db)
        train_forecasting_models(db)
        train_recommendation_model(db)
        
        print("🎉 All ML models trained successfully!")
        print("\n📁 Model files saved in ml_models/ directory:")
        print("   - cluster_model.joblib")
        print("   - forecast_user_*.pkl")
        print("   - product_index.faiss")
        print("   - product_mapping.pkl")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()