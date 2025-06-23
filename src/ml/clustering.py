"""
Customer clustering using machine learning.
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import joblib
import os
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from ..database.models import User, Transaction, Cluster


class CustomerClustering:
    """Customer clustering for behavioral segmentation."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=4, random_state=42)
        self.cluster_names = {
            0: "Frugal Savers",
            1: "Average Spenders", 
            2: "High-Value Transactors",
            3: "New/Infrequent Users"
        }
        self.cluster_descriptions = {
            0: "Conservative spenders who prioritize savings and make careful financial decisions.",
            1: "Moderate spenders with balanced financial habits and regular transaction patterns.",
            2: "High-volume transactors with significant spending power and frequent activity.",
            3: "New customers or infrequent users with limited transaction history."
        }
    
    def extract_features(self, user_id: int, db: Session) -> Dict[str, float]:
        """Extract RFM and behavioral features for a user."""
        transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
        
        if not transactions:
            return self._default_features()
        
        df = pd.DataFrame([{
            'date': t.date,
            'category': t.category,
            'debit': t.debit,
            'credit': t.credit,
            'balance': t.balance
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        
        # RFM Features
        recency = (pd.Timestamp.now() - df['date'].max()).days
        frequency = len(df)
        monetary = df['debit'].sum()
        
        # Spending Profile (normalized spending per category)
        category_spending = df.groupby('category')['debit'].sum()
        total_spending = category_spending.sum()
        
        # Common categories
        categories = ['Market', 'Transport', 'Coffe', 'Restuarant', 'Phone', 'Health', 'Learning']
        spending_profile = {}
        for cat in categories:
            spending_profile[f'spending_{cat.lower()}'] = (
                category_spending.get(cat, 0) / total_spending if total_spending > 0 else 0
            )
        
        # Behavioral ratios
        df['weekday'] = df['date'].dt.weekday
        weekday_spending = df[df['weekday'] < 5]['debit'].sum()
        weekend_spending = df[df['weekday'] >= 5]['debit'].sum()
        weekday_ratio = (
            weekday_spending / (weekday_spending + weekend_spending) 
            if (weekday_spending + weekend_spending) > 0 else 0.5
        )
        
        # Average transaction amount
        avg_transaction = df['debit'].mean() if len(df) > 0 else 0
        
        # Balance volatility
        balance_std = df['balance'].std() if len(df) > 1 else 0
        
        features = {
            'recency': recency,
            'frequency': frequency,
            'monetary': monetary,
            'avg_transaction': avg_transaction,
            'balance_std': balance_std,
            'weekday_ratio': weekday_ratio,
            **spending_profile
        }
        
        return features
    
    def _default_features(self) -> Dict[str, float]:
        """Return default features for users with no transactions."""
        categories = ['Market', 'Transport', 'Coffe', 'Restuarant', 'Phone', 'Health', 'Learning']
        features = {
            'recency': 365,
            'frequency': 0,
            'monetary': 0,
            'avg_transaction': 0,
            'balance_std': 0,
            'weekday_ratio': 0.5
        }
        for cat in categories:
            features[f'spending_{cat.lower()}'] = 0
        return features
    
    def train_cluster_model(self, db: Session) -> Dict[str, float]:
        """Train the clustering model on all users."""
        users = db.query(User).filter(User.role == "customer").all()
        
        # Extract features for all users
        features_list = []
        user_ids = []
        
        for user in users:
            features = self.extract_features(user.id, db)
            features_list.append(list(features.values()))
            user_ids.append(user.id)
        
        if not features_list:
            return {"error": "No customer data available"}
        
        # Convert to numpy array and scale
        X = np.array(features_list)
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit KMeans
        cluster_labels = self.kmeans.fit_predict(X_scaled)
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(X_scaled, cluster_labels)
        
        # Save models
        os.makedirs("ml_models", exist_ok=True)
        joblib.dump({
            'scaler': self.scaler,
            'kmeans': self.kmeans,
            'feature_names': list(self.extract_features(user_ids[0], db).keys())
        }, "ml_models/cluster_model.joblib")
        
        # Update user clusters in database
        self._update_user_clusters(db, user_ids, cluster_labels)
        
        return {
            "silhouette_score": silhouette_avg,
            "n_clusters": len(set(cluster_labels)),
            "n_users": len(user_ids)
        }
    
    def _update_user_clusters(self, db: Session, user_ids: List[int], cluster_labels: List[int]):
        """Update user cluster assignments in database."""
        # Create cluster records if they don't exist
        for cluster_id, name in self.cluster_names.items():
            existing_cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
            if not existing_cluster:
                cluster = Cluster(
                    id=cluster_id,
                    name=name,
                    description=self.cluster_descriptions[cluster_id]
                )
                db.add(cluster)
        
        # Update user cluster assignments
        for user_id, cluster_label in zip(user_ids, cluster_labels):
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.cluster_id = cluster_label
        
        db.commit()
    
    def predict_cluster(self, user_id: int, db: Session) -> int:
        """Predict cluster for a single user."""
        try:
            # Load trained model
            model_data = joblib.load("ml_models/cluster_model.joblib")
            self.scaler = model_data['scaler']
            self.kmeans = model_data['kmeans']
            
            # Extract features
            features = self.extract_features(user_id, db)
            X = np.array([list(features.values())])
            X_scaled = self.scaler.transform(X)
            
            # Predict cluster
            cluster = self.kmeans.predict(X_scaled)[0]
            
            # Update user cluster in database
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.cluster_id = cluster
                db.commit()
            
            return cluster
            
        except FileNotFoundError:
            # Return default cluster if model not trained
            return 3  # New/Infrequent Users
    
    def get_cluster_info(self, cluster_id: int) -> Dict[str, str]:
        """Get cluster name and description."""
        return {
            "name": self.cluster_names.get(cluster_id, "Unknown"),
            "description": self.cluster_descriptions.get(cluster_id, "No description available")
        }