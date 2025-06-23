"""
Data ingestion script to populate the database with sample data.
"""
import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.base import create_tables, SessionLocal
from src.database.models import User, Transaction, Product, Cluster
from src.core.security import hash_password


def create_sample_users(db: Session):
    """Create sample users including admin and customers."""
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@finassist.com",
        hashed_password=hash_password("admin123"),
        role="admin",
        full_name="System Administrator"
    )
    db.add(admin_user)
    
    # Create sample customers
    customers = [
        {
            "username": "james_smith",
            "email": "james.smith@email.com",
            "password": "password123",
            "full_name": "James Smith"
        },
        {
            "username": "sarah_johnson",
            "email": "sarah.johnson@email.com", 
            "password": "password123",
            "full_name": "Sarah Johnson"
        },
        {
            "username": "mike_brown",
            "email": "mike.brown@email.com",
            "password": "password123", 
            "full_name": "Mike Brown"
        },
        {
            "username": "lisa_davis",
            "email": "lisa.davis@email.com",
            "password": "password123",
            "full_name": "Lisa Davis"
        }
    ]
    
    for customer_data in customers:
        customer = User(
            username=customer_data["username"],
            email=customer_data["email"],
            hashed_password=hash_password(customer_data["password"]),
            role="customer",
            full_name=customer_data["full_name"]
        )
        db.add(customer)
    
    db.commit()
    print("✅ Sample users created")


def create_clusters(db: Session):
    """Create predefined clusters."""
    clusters = [
        {
            "id": 0,
            "name": "Frugal Savers",
            "description": "Conservative spenders who prioritize savings and make careful financial decisions."
        },
        {
            "id": 1,
            "name": "Average Spenders",
            "description": "Moderate spenders with balanced financial habits and regular transaction patterns."
        },
        {
            "id": 2,
            "name": "High-Value Transactors", 
            "description": "High-volume transactors with significant spending power and frequent activity."
        },
        {
            "id": 3,
            "name": "New/Infrequent Users",
            "description": "New customers or infrequent users with limited transaction history."
        }
    ]
    
    for cluster_data in clusters:
        cluster = Cluster(**cluster_data)
        db.add(cluster)
    
    db.commit()
    print("✅ Clusters created")


def ingest_transaction_data(db: Session):
    """Ingest transaction data from CSV files."""
    data_dir = "data/sample_transactions"
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"⚠️ Created {data_dir} directory. Please add CSV files.")
        return
    
    # Get all users
    users = db.query(User).filter(User.role == "customer").all()
    user_mapping = {user.username: user.id for user in users}
    
    # Process CSV files
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        file_path = os.path.join(data_dir, csv_file)
        
        # Extract user identifier from filename
        if csv_file == "James_Smith_25M.csv":
            username = "james_smith"
        else:
            # For other files, extract from filename
            username = csv_file.replace('.csv', '').lower().replace('_', '_')
        
        if username not in user_mapping:
            print(f"⚠️ No user found for {csv_file}, skipping...")
            continue
        
        user_id = user_mapping[username]
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Insert transactions
            transactions_added = 0
            for _, row in df.iterrows():
                transaction = Transaction(
                    user_id=user_id,
                    date=row['date'],
                    category=row['category'],
                    debit=float(row['debit']) if pd.notna(row['debit']) else 0.0,
                    credit=float(row['credit']) if pd.notna(row['credit']) else 0.0,
                    balance=float(row['balance'])
                )
                db.add(transaction)
                transactions_added += 1
            
            db.commit()
            print(f"✅ Processed {csv_file}: {transactions_added} transactions for user {username}")
            
        except Exception as e:
            print(f"❌ Error processing {csv_file}: {e}")
            db.rollback()


def create_sample_products(db: Session):
    """Create sample financial products."""
    products = [
        {
            "name": "Basic Savings Account",
            "category": "Savings",
            "description": "A simple savings account with competitive interest rates and no monthly fees.",
            "tags": "savings, low-fee, conservative, beginner",
            "interest_rate": 2.5,
            "fees": 0.0,
            "min_balance": 100.0,
            "target_cluster": "frugal savers"
        },
        {
            "name": "High-Yield Savings",
            "category": "Savings", 
            "description": "Premium savings account with higher interest rates for larger balances.",
            "tags": "high-yield, savings, investment, premium",
            "interest_rate": 4.2,
            "fees": 0.0,
            "min_balance": 10000.0,
            "target_cluster": "high-value transactors"
        },
        {
            "name": "Rewards Credit Card",
            "category": "Credit",
            "description": "Credit card with cashback rewards on everyday purchases and travel benefits.",
            "tags": "rewards, credit, cashback, premium, high-limit",
            "interest_rate": 18.9,
            "fees": 95.0,
            "min_balance": None,
            "target_cluster": "high-value transactors"
        },
        {
            "name": "Student Credit Card",
            "category": "Credit",
            "description": "Low-limit credit card designed for students and new credit users.",
            "tags": "credit, beginner, low-limit, student",
            "interest_rate": 21.9,
            "fees": 0.0,
            "min_balance": None,
            "target_cluster": "new/infrequent users"
        },
        {
            "name": "Personal Loan",
            "category": "Loan",
            "description": "Flexible personal loan for debt consolidation or major purchases.",
            "tags": "loan, credit, debt consolidation, budgeting",
            "interest_rate": 12.5,
            "fees": 200.0,
            "min_balance": None,
            "target_cluster": "average spenders"
        },
        {
            "name": "Investment Portfolio",
            "category": "Investment",
            "description": "Diversified investment portfolio with professional management.",
            "tags": "investment, growth, portfolio, professional",
            "interest_rate": None,
            "fees": 1.2,
            "min_balance": 5000.0,
            "target_cluster": "high-value transactors"
        },
        {
            "name": "Budget Tracker App",
            "category": "Tool",
            "description": "Mobile app to track expenses and manage budgets with AI insights.",
            "tags": "budgeting tool, app, tracking, financial assistance",
            "interest_rate": None,
            "fees": 9.99,
            "min_balance": None,
            "target_cluster": "average spenders"
        },
        {
            "name": "Emergency Fund Builder",
            "category": "Savings",
            "description": "Automated savings program to build emergency funds with goal tracking.",
            "tags": "emergency fund, savings, automated, conservative",
            "interest_rate": 3.0,
            "fees": 0.0,
            "min_balance": 50.0,
            "target_cluster": "frugal savers"
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        db.add(product)
    
    db.commit()
    print("✅ Sample products created")


def main():
    """Main ingestion function."""
    print("🚀 Starting data ingestion...")
    
    # Create tables
    create_tables()
    print("✅ Database tables created")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create sample data
        create_clusters(db)
        create_sample_users(db)
        create_sample_products(db)
        ingest_transaction_data(db)
        
        print("🎉 Data ingestion completed successfully!")
        print("\n📋 Sample Login Credentials:")
        print("Admin: username=admin, password=admin123")
        print("Customer: username=james_smith, password=password123")
        print("Customer: username=sarah_johnson, password=password123")
        print("Customer: username=mike_brown, password=password123")
        print("Customer: username=lisa_davis, password=password123")
        
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()