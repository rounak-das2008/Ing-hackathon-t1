"""
Streamlit customer application for the Financial Assistant.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="FinCoach - Your Personal Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)


def authenticate_user(username: str, password: str) -> dict:
    """Authenticate user and get access token."""
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


def get_user_context(token: str) -> dict:
    """Get user context from API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/users/me/context", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def send_chat_message(token: str, message: str) -> dict:
    """Send chat message to AI assistant."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            headers=headers,
            json={"message": message}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def login_page():
    """Display login page."""
    st.markdown('<h1 class="main-header">💰 FinCoach</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your Personal Financial Assistant</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login")
        
        # Demo user selection
        st.info("💡 **Demo Mode**: Select a user to login (password: password123)")
        
        demo_users = {
            "James Smith": "james_smith",
            "Sarah Johnson": "sarah_johnson", 
            "Mike Brown": "mike_brown",
            "Lisa Davis": "lisa_davis"
        }
        
        selected_user = st.selectbox("Select Demo User:", list(demo_users.keys()))
        username = demo_users[selected_user]
        password = "password123"
        
        # Manual login option
        with st.expander("🔧 Manual Login"):
            manual_username = st.text_input("Username:")
            manual_password = st.text_input("Password:", type="password")
            if manual_username and manual_password:
                username = manual_username
                password = manual_password
        
        if st.button("🚀 Login", type="primary", use_container_width=True):
            with st.spinner("Authenticating..."):
                auth_result = authenticate_user(username, password)
                
                if auth_result:
                    st.session_state.token = auth_result["access_token"]
                    st.session_state.authenticated = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")


def dashboard_tab(context: dict):
    """Display user dashboard."""
    user = context["user"]
    cluster = context["cluster"]
    forecast = context["forecast"]
    transactions = context["transactions"]
    
    # Welcome message
    st.markdown(f"### 👋 Welcome back, {user['full_name']}!")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_balance = forecast.get("current_balance", 0)
        st.metric("💰 Current Balance", f"${current_balance:,.2f}")
    
    with col2:
        predicted_balance = forecast.get("predicted_balance", 0)
        balance_change = predicted_balance - current_balance
        st.metric(
            "📈 30-Day Forecast", 
            f"${predicted_balance:,.2f}",
            delta=f"${balance_change:,.2f}"
        )
    
    with col3:
        total_transactions = len(transactions)
        st.metric("📊 Total Transactions", total_transactions)
    
    with col4:
        if cluster:
            st.metric("🎯 Profile Type", cluster["name"])
        else:
            st.metric("🎯 Profile Type", "Analyzing...")
    
    # Cluster information
    if cluster:
        st.markdown("### 🎯 Your Financial Profile")
        st.info(f"**{cluster['name']}**: {cluster['description']}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Spending by Category")
        if transactions:
            # Create spending by category chart
            df = pd.DataFrame(transactions)
            category_spending = df.groupby('category')['debit'].sum().reset_index()
            category_spending = category_spending[category_spending['debit'] > 0]
            
            if not category_spending.empty:
                fig = px.pie(
                    category_spending, 
                    values='debit', 
                    names='category',
                    title="Spending Distribution"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending data available")
        else:
            st.info("No transaction data available")
    
    with col2:
        st.markdown("### 📈 Balance Forecast")
        if forecast and "dates" in forecast and "values" in forecast:
            # Create forecast chart
            forecast_df = pd.DataFrame({
                'Date': pd.to_datetime(forecast['dates']),
                'Predicted Balance': forecast['values']
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Predicted Balance'],
                mode='lines+markers',
                name='Predicted Balance',
                line=dict(color='#1f77b4', width=3)
            ))
            
            fig.update_layout(
                title="30-Day Balance Forecast",
                xaxis_title="Date",
                yaxis_title="Balance ($)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Forecast data not available")
    
    # Forecast summary
    if forecast and "summary" in forecast:
        st.markdown("### 🔮 Forecast Insights")
        st.markdown(f"**Summary**: {forecast['summary']}")


def chat_tab(token: str):
    """Display chat interface."""
    st.markdown("### 💬 Chat with FinCoach")
    st.markdown("Ask me anything about your finances, budgeting, or financial planning!")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for i, (user_msg, assistant_msg, timestamp) in enumerate(st.session_state.chat_history):
            # User message
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong> {user_msg}
                <br><small>{timestamp}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Assistant message
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>FinCoach:</strong> {assistant_msg}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your message:", height=100, placeholder="e.g., How can I improve my spending habits?")
        submitted = st.form_submit_button("💬 Send", type="primary")
        
        if submitted and user_input.strip():
            with st.spinner("FinCoach is thinking..."):
                response = send_chat_message(token, user_input.strip())
                
                if response:
                    # Add to chat history
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.chat_history.append((
                        user_input.strip(),
                        response["response"],
                        timestamp
                    ))
                    st.rerun()
                else:
                    st.error("❌ Failed to get response from FinCoach. Please try again.")


def products_tab(context: dict):
    """Display recommended products."""
    recommendations = context["recommendations"]
    
    st.markdown("### 🎁 Recommended Products")
    st.markdown("Based on your financial profile and spending patterns, here are some products that might interest you:")
    
    if recommendations:
        for product in recommendations:
            with st.container():
                st.markdown(f"""
                <div class="product-card">
                    <h4>🏦 {product['name']}</h4>
                    <p><strong>Category:</strong> {product['category']}</p>
                    <p><strong>Description:</strong> {product['description']}</p>
                """, unsafe_allow_html=True)
                
                # Product details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if product.get('interest_rate'):
                        st.metric("Interest Rate", f"{product['interest_rate']}%")
                
                with col2:
                    if product.get('fees'):
                        st.metric("Fees", f"${product['fees']}")
                
                with col3:
                    if product.get('min_balance'):
                        st.metric("Min Balance", f"${product['min_balance']:,.0f}")
                
                if product.get('relevance_score'):
                    st.progress(min(product['relevance_score'], 1.0))
                    st.caption(f"Relevance Score: {product['relevance_score']:.2f}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("🔄 No recommendations available. Our AI is analyzing your profile to provide personalized suggestions.")


def main():
    """Main application function."""
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Get user context
    with st.spinner("Loading your financial dashboard..."):
        context = get_user_context(st.session_state.token)
    
    if not context:
        st.error("❌ Failed to load user data. Please login again.")
        st.session_state.authenticated = False
        st.rerun()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 User Info")
        st.write(f"**Name:** {context['user']['full_name']}")
        st.write(f"**Email:** {context['user']['email']}")
        
        if context['cluster']:
            st.write(f"**Profile:** {context['cluster']['name']}")
        
        st.markdown("---")
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.token = None
            if "chat_history" in st.session_state:
                del st.session_state.chat_history
            st.rerun()
    
    # Main content
    st.markdown('<h1 class="main-header">💰 FinCoach Dashboard</h1>', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💬 Chat with FinCoach", "🎁 Product Offers"])
    
    with tab1:
        dashboard_tab(context)
    
    with tab2:
        chat_tab(st.session_state.token)
    
    with tab3:
        products_tab(context)


if __name__ == "__main__":
    main()