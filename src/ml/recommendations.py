"""
Product recommendation system using semantic search.
"""
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from ..database.models import Product, User


class ProductRecommendation:
    """Product recommendation using semantic search and rule-based filtering."""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.product_mapping = {}
    
    def build_product_embeddings(self, db: Session) -> Dict[str, any]:
        """Build FAISS index from product descriptions."""
        products = db.query(Product).all()
        
        if not products:
            return {"error": "No products available"}
        
        # Prepare product texts for embedding
        product_texts = []
        product_ids = []
        
        for product in products:
            # Combine name, category, description, and tags
            text = f"{product.name} {product.category} {product.description}"
            if product.tags:
                text += f" {product.tags}"
            
            product_texts.append(text)
            product_ids.append(product.id)
        
        # Generate embeddings
        embeddings = self.model.encode(product_texts)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        # Create product mapping
        self.product_mapping = {i: product_id for i, product_id in enumerate(product_ids)}
        
        # Save index and mapping
        os.makedirs("ml_models", exist_ok=True)
        faiss.write_index(self.index, "ml_models/product_index.faiss")
        
        with open("ml_models/product_mapping.pkl", "wb") as f:
            pickle.dump(self.product_mapping, f)
        
        return {
            "status": "success",
            "n_products": len(products),
            "embedding_dimension": dimension
        }
    
    def get_recommendations(
        self, 
        user_id: int, 
        user_cluster: str, 
        forecast_summary: str,
        db: Session,
        top_k: int = 5
    ) -> List[Dict[str, any]]:
        """Get product recommendations for a user."""
        try:
            # Load index and mapping
            self.index = faiss.read_index("ml_models/product_index.faiss")
            with open("ml_models/product_mapping.pkl", "rb") as f:
                self.product_mapping = pickle.load(f)
        except FileNotFoundError:
            return []
        
        # Get all products for filtering
        products = db.query(Product).all()
        products_dict = {p.id: p for p in products}
        
        # Rule-based filtering based on forecast and cluster
        filtered_products = self._filter_products_by_rules(
            products, user_cluster, forecast_summary
        )
        
        if not filtered_products:
            filtered_products = products  # Fallback to all products
        
        # Generate query based on user situation
        query = self._generate_search_query(user_cluster, forecast_summary)
        
        # Semantic search
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), len(self.product_mapping))
        
        # Filter results to only include rule-filtered products
        filtered_product_ids = {p.id for p in filtered_products}
        recommendations = []
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
                
            product_id = self.product_mapping[idx]
            if product_id in filtered_product_ids:
                product = products_dict[product_id]
                recommendations.append({
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "description": product.description,
                    "interest_rate": product.interest_rate,
                    "fees": product.fees,
                    "min_balance": product.min_balance,
                    "relevance_score": float(score),
                    "tags": product.tags
                })
                
                if len(recommendations) >= top_k:
                    break
        
        return recommendations
    
    def _filter_products_by_rules(
        self, 
        products: List[Product], 
        user_cluster: str, 
        forecast_summary: str
    ) -> List[Product]:
        """Apply rule-based filtering based on user profile."""
        filtered = []
        
        # Determine user needs based on forecast
        needs_credit = any(word in forecast_summary.lower() for word in ['decreasing', 'drop', 'low', 'warning'])
        has_surplus = any(word in forecast_summary.lower() for word in ['increasing', 'positive', 'stable'])
        
        for product in products:
            include = False
            
            # Filter by forecast-based needs
            if needs_credit:
                if any(tag in (product.tags or "").lower() for tag in ['credit', 'loan', 'budgeting']):
                    include = True
            elif has_surplus:
                if any(tag in (product.tags or "").lower() for tag in ['investment', 'savings', 'high-yield']):
                    include = True
            
            # Filter by cluster preferences
            if user_cluster == "Frugal Savers":
                if any(tag in (product.tags or "").lower() for tag in ['low-fee', 'savings', 'conservative']):
                    include = True
            elif user_cluster == "High-Value Transactors":
                if any(tag in (product.tags or "").lower() for tag in ['premium', 'rewards', 'high-limit']):
                    include = True
            elif user_cluster == "Average Spenders":
                if any(tag in (product.tags or "").lower() for tag in ['standard', 'balanced', 'everyday']):
                    include = True
            
            # Include products with matching target cluster
            if product.target_cluster and user_cluster.lower() in product.target_cluster.lower():
                include = True
            
            if include:
                filtered.append(product)
        
        return filtered
    
    def _generate_search_query(self, user_cluster: str, forecast_summary: str) -> str:
        """Generate search query based on user profile."""
        query_parts = []
        
        # Add cluster-based terms
        if user_cluster == "Frugal Savers":
            query_parts.append("low cost savings account conservative investment")
        elif user_cluster == "High-Value Transactors":
            query_parts.append("premium credit card rewards high limit")
        elif user_cluster == "Average Spenders":
            query_parts.append("standard checking account balanced financial products")
        else:
            query_parts.append("beginner friendly basic banking")
        
        # Add forecast-based terms
        if "decreasing" in forecast_summary.lower() or "warning" in forecast_summary.lower():
            query_parts.append("credit line loan budgeting tool financial assistance")
        elif "increasing" in forecast_summary.lower() or "positive" in forecast_summary.lower():
            query_parts.append("investment savings high yield growth")
        
        return " ".join(query_parts)