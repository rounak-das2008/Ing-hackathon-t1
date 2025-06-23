"""
Unit and integration tests for the Financial Assistant API.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app
from src.database.base import get_db
from src.database.models import Base, User, Product
from src.core.security import hash_password

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    """Create a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_admin_user(test_db):
    """Create a test admin user."""
    admin = User(
        username="test_admin",
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role="admin",
        full_name="Test Admin"
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


@pytest.fixture
def test_customer_user(test_db):
    """Create a test customer user."""
    customer = User(
        username="test_customer",
        email="customer@test.com",
        hashed_password=hash_password("customer123"),
        role="customer",
        full_name="Test Customer"
    )
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    return customer


@pytest.fixture
def test_products(test_db):
    """Create test products."""
    products = [
        Product(
            name="Test Savings Account",
            category="Savings",
            description="A test savings account",
            tags="savings, test",
            interest_rate=2.5,
            fees=0.0,
            min_balance=100.0
        ),
        Product(
            name="Test Credit Card",
            category="Credit",
            description="A test credit card",
            tags="credit, test",
            interest_rate=18.9,
            fees=50.0,
            min_balance=None
        )
    ]
    
    for product in products:
        test_db.add(product)
    
    test_db.commit()
    return products


def get_auth_token(username: str, password: str):
    """Get authentication token for testing."""
    response = client.post(
        "/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, test_admin_user):
        """Test successful login."""
        response = client.post(
            "/token",
            data={"username": "test_admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post(
            "/token",
            data={"username": "invalid", "password": "invalid"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/users/me")
        assert response.status_code == 401


class TestCustomerEndpoints:
    """Test customer-specific endpoints."""
    
    def test_get_current_user(self, test_customer_user):
        """Test getting current user information."""
        token = get_auth_token("test_customer", "customer123")
        assert token is not None
        
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_customer"
        assert data["role"] == "customer"
    
    def test_get_user_context(self, test_customer_user):
        """Test getting user context."""
        token = get_auth_token("test_customer", "customer123")
        assert token is not None
        
        response = client.get(
            "/api/users/me/context",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "transactions" in data
        assert "forecast" in data
        assert "recommendations" in data
    
    def test_chat_endpoint(self, test_customer_user):
        """Test chat endpoint."""
        token = get_auth_token("test_customer", "customer123")
        assert token is not None
        
        response = client.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Hello, can you help me with my finances?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "timestamp" in data


class TestAdminEndpoints:
    """Test admin-specific endpoints."""
    
    def test_admin_dashboard(self, test_admin_user, test_customer_user):
        """Test admin dashboard endpoint."""
        token = get_auth_token("test_admin", "admin123")
        assert token is not None
        
        response = client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_transactions" in data
        assert "cluster_distribution" in data
        assert "avg_transaction_value" in data
        assert "total_balance" in data
    
    def test_admin_users_list(self, test_admin_user, test_customer_user):
        """Test admin users list endpoint."""
        token = get_auth_token("test_admin", "admin123")
        assert token is not None
        
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) >= 1
    
    def test_customer_cannot_access_admin_endpoints(self, test_customer_user):
        """Test that customers cannot access admin endpoints."""
        token = get_auth_token("test_customer", "customer123")
        assert token is not None
        
        response = client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]


class TestMLEndpoints:
    """Test ML model training endpoints."""
    
    def test_train_clustering_model(self, test_admin_user, test_customer_user):
        """Test clustering model training."""
        token = get_auth_token("test_admin", "admin123")
        assert token is not None
        
        response = client.post(
            "/api/admin/train-clustering",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        # Note: May return error due to insufficient data in test environment
    
    def test_train_recommendation_model(self, test_admin_user, test_products):
        """Test recommendation model training."""
        token = get_auth_token("test_admin", "admin123")
        assert token is not None
        
        response = client.post(
            "/api/admin/train-recommendations",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


# Cleanup
def teardown_module():
    """Clean up test database."""
    if os.path.exists("test.db"):
        os.remove("test.db")