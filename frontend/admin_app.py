"""
Streamlit admin application for the Financial Assistant.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="FinCoach Admin - Analytics Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #d32f2f;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #d32f2f;
    }
    .admin-section {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ff9800;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def authenticate_admin(username: str, password: str) -> dict:
    """Authenticate admin user and get access token."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        st.error("❌ Unable to connect to the server. Please check if the API is running.")
        return None


def get_admin_dashboard(token: str) -> dict:
    """Get admin dashboard data."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/admin/dashboard", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def get_all_users(token: str) -> dict:
    """Get all users data."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/admin/users", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def train_clustering_model(token: str) -> dict:
    """Train clustering model."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE_URL}/api/admin/train-clustering", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def train_recommendation_model(token: str) -> dict:
    """Train recommendation model."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE_URL}/api/admin/train-recommendations", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def login_page():
    """Display admin login page."""
    st.markdown('<h1 class="main-header">🏦 FinCoach Admin</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Analytics & Management Dashboard</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Admin Login")
        
        # Default admin credentials
        st.info("💡 **Default Admin**: username=admin, password=admin123")
        
        username = st.text_input("Username:", value="admin")
        password = st.text_input("Password:", type="password", value="admin123")
        
        if st.button("🚀 Login", type="primary", use_container_width=True):
            with st.spinner("Authenticating..."):
                auth_result = authenticate_admin(username, password)
                
                if auth_result:
                    st.session_state.admin_token = auth_result["access_token"]
                    st.session_state.admin_authenticated = True
                    st.success("✅ Admin login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials. Please try again.")


def dashboard_overview(token: str):
    """Display dashboard overview."""
    st.markdown("### 📊 System Overview")
    
    with st.spinner("Loading dashboard data..."):
        dashboard_data = get_admin_dashboard(token)
    
    if not dashboard_data:
        st.error("❌ Failed to load dashboard data.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 Total Customers", 
            dashboard_data["total_users"]
        )
    
    with col2:
        st.metric(
            "💳 Total Transactions", 
            f"{dashboard_data['total_transactions']:,}"
        )
    
    with col3:
        st.metric(
            "💰 Average Transaction", 
            f"${dashboard_data['avg_transaction_value']:,.2f}"
        )
    
    with col4:
        st.metric(
            "🏦 Total System Balance", 
            f"${dashboard_data['total_balance']:,.2f}"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Customer Segmentation")
        cluster_dist = dashboard_data["cluster_distribution"]
        
        if cluster_dist:
            fig = px.pie(
                values=list(cluster_dist.values()),
                names=list(cluster_dist.keys()),
                title="Customer Distribution by Cluster"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No cluster data available. Train the clustering model first.")
    
    with col2:
        st.markdown("### 📈 System Health")
        
        # Create a simple health metrics chart
        health_metrics = {
            "Active Users": dashboard_data["total_users"],
            "Avg Transaction Value": dashboard_data["avg_transaction_value"],
            "System Balance (K)": dashboard_data["total_balance"] / 1000
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(health_metrics.keys()),
                y=list(health_metrics.values()),
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
            )
        ])
        
        fig.update_layout(
            title="Key System Metrics",
            yaxis_title="Value",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)


def user_management(token: str):
    """Display user management interface."""
    st.markdown("### 👥 User Management")
    
    with st.spinner("Loading user data..."):
        users_data = get_all_users(token)
    
    if not users_data:
        st.error("❌ Failed to load user data.")
        return
    
    users = users_data["users"]
    
    if users:
        # Convert to DataFrame for better display
        df = pd.DataFrame(users)
        
        # Add cluster names
        cluster_names = {
            0: "Frugal Savers",
            1: "Average Spenders", 
            2: "High-Value Transactors",
            3: "New/Infrequent Users"
        }
        
        df['cluster_name'] = df['cluster_id'].map(cluster_names).fillna('Unassigned')
        
        # Display summary
        st.markdown("#### 📋 User Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", len(df))
        
        with col2:
            assigned_users = df['cluster_id'].notna().sum()
            st.metric("Clustered Users", assigned_users)
        
        with col3:
            unassigned_users = df['cluster_id'].isna().sum()
            st.metric("Unassigned Users", unassigned_users)
        
        # User table
        st.markdown("#### 📊 User Details")
        
        # Select columns to display
        display_columns = ['username', 'full_name', 'email', 'cluster_name']
        display_df = df[display_columns].copy()
        display_df.columns = ['Username', 'Full Name', 'Email', 'Cluster']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Cluster distribution
        st.markdown("#### 🎯 Cluster Distribution")
        cluster_counts = df['cluster_name'].value_counts()
        
        fig = px.bar(
            x=cluster_counts.index,
            y=cluster_counts.values,
            title="Users per Cluster",
            labels={'x': 'Cluster', 'y': 'Number of Users'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No users found in the system.")


def ml_management(token: str):
    """Display ML model management interface."""
    st.markdown("### 🤖 ML Model Management")
    
    st.markdown("""
    <div class="admin-section">
        <h4>🎯 Customer Clustering</h4>
        <p>Train the customer segmentation model to group users based on their financial behavior.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Train Clustering Model", type="primary"):
            with st.spinner("Training clustering model... This may take a few minutes."):
                result = train_clustering_model(token)
                
                if "error" in result:
                    st.error(f"❌ Training failed: {result['error']}")
                else:
                    st.success("✅ Clustering model trained successfully!")
                    st.json(result)
    
    with col2:
        if st.button("🔄 Train Recommendation Model", type="primary"):
            with st.spinner("Training recommendation model..."):
                result = train_recommendation_model(token)
                
                if "error" in result:
                    st.error(f"❌ Training failed: {result['error']}")
                else:
                    st.success("✅ Recommendation model trained successfully!")
                    st.json(result)
    
    st.markdown("""
    <div class="admin-section">
        <h4>📈 Forecasting Models</h4>
        <p>Individual forecasting models are trained automatically when users access their forecasts.</p>
        <p><strong>Note:</strong> Each user gets a personalized forecasting model based on their transaction history.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📁 Model Status")
    
    # Check for model files
    import os
    
    model_status = []
    
    # Check clustering model
    if os.path.exists("ml_models/cluster_model.joblib"):
        model_status.append({"Model": "Customer Clustering", "Status": "✅ Trained", "File": "cluster_model.joblib"})
    else:
        model_status.append({"Model": "Customer Clustering", "Status": "❌ Not Trained", "File": "cluster_model.joblib"})
    
    # Check recommendation model
    if os.path.exists("ml_models/product_index.faiss"):
        model_status.append({"Model": "Product Recommendations", "Status": "✅ Trained", "File": "product_index.faiss"})
    else:
        model_status.append({"Model": "Product Recommendations", "Status": "❌ Not Trained", "File": "product_index.faiss"})
    
    # Check forecasting models
    forecast_models = [f for f in os.listdir("ml_models") if f.startswith("forecast_user_") and f.endswith(".pkl")] if os.path.exists("ml_models") else []
    model_status.append({"Model": "Forecasting Models", "Status": f"✅ {len(forecast_models)} Users", "File": f"{len(forecast_models)} files"})
    
    status_df = pd.DataFrame(model_status)
    st.dataframe(status_df, use_container_width=True)


def main():
    """Main admin application function."""
    # Initialize session state
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        login_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🏦 Admin Panel")
        st.markdown("---")
        
        page = st.selectbox(
            "Select Page:",
            ["📊 Dashboard", "👥 User Management", "🤖 ML Models"]
        )
        
        st.markdown("---")
        
        if st.button("🚪 Logout"):
            st.session_state.admin_authenticated = False
            st.session_state.admin_token = None
            st.rerun()
    
    # Main content
    st.markdown('<h1 class="main-header">🏦 FinCoach Admin Dashboard</h1>', unsafe_allow_html=True)
    
    if page == "📊 Dashboard":
        dashboard_overview(st.session_state.admin_token)
    elif page == "👥 User Management":
        user_management(st.session_state.admin_token)
    elif page == "🤖 ML Models":
        ml_management(st.session_state.admin_token)


if __name__ == "__main__":
    main()