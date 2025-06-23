# GenAI-Powered Financial Assistant & Analytics Platform

A comprehensive financial assistant platform featuring AI-powered chatbot capabilities, customer segmentation, balance forecasting, and product recommendations. Built with FastAPI, Streamlit, and modern ML technologies.

## 🚀 Features

### Customer Portal
- **AI Financial Assistant**: Chat with FinCoach for personalized financial advice
- **Smart Dashboard**: View spending patterns, balance forecasts, and financial insights
- **Product Recommendations**: Get personalized financial product suggestions
- **Transaction Analytics**: Visualize spending by category and trends

### Admin Analytics Dashboard
- **Customer Segmentation**: ML-powered clustering of customer behavior
- **System Analytics**: Comprehensive view of user activity and financial metrics
- **ML Model Management**: Train and manage machine learning models
- **User Management**: Monitor and analyze customer data

### AI & ML Capabilities
- **Customer Clustering**: Behavioral segmentation using KMeans
- **Balance Forecasting**: Time series prediction with Darts/ExponentialSmoothing
- **Product Recommendations**: Semantic search with sentence transformers and FAISS
- **Conversational AI**: Context-aware financial assistant using Google Gemini

## 🛠 Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Lightweight database for MVP
- **Pydantic**: Data validation using Python type annotations

### Machine Learning
- **scikit-learn**: Machine learning library for clustering
- **Darts**: Time series forecasting
- **sentence-transformers**: Semantic embeddings for recommendations
- **FAISS**: Efficient similarity search
- **LangChain**: Framework for LLM applications

### Frontend
- **Streamlit**: Interactive web applications
- **Plotly**: Interactive visualizations
- **Altair**: Statistical visualization grammar

### AI Integration
- **Google Gemini**: Large language model for conversational AI
- **Ollama/LLMStudio**: Alternative local LLM options

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js (for development tools)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd financial-assistant-platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. **Initialize database and sample data**
```bash
python scripts/ingest_data.py
```

6. **Train ML models**
```bash
python scripts/train_models.py
```

## 🚀 Running the Application

### Start the Backend API
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start the Customer Portal
```bash
streamlit run frontend/customer_app.py --server.port 8501
```

### Start the Admin Dashboard
```bash
streamlit run frontend/admin_app.py --server.port 8502
```

## 🔐 Default Credentials

### Admin Access
- **Username**: admin
- **Password**: admin123

### Customer Demo Accounts
- **James Smith**: username=james_smith, password=password123
- **Sarah Johnson**: username=sarah_johnson, password=password123
- **Mike Brown**: username=mike_brown, password=password123
- **Lisa Davis**: username=lisa_davis, password=password123

## 📊 API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /token` - Get access token

#### Customer Endpoints
- `GET /api/users/me` - Get current user info
- `GET /api/users/me/context` - Get complete user context
- `POST /api/chat` - Chat with AI assistant

#### Admin Endpoints
- `GET /api/admin/dashboard` - Get dashboard analytics
- `GET /api/admin/users` - Get all users
- `POST /api/admin/train-clustering` - Train clustering model
- `POST /api/admin/train-recommendations` - Train recommendation model

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## 🏗 Architecture

### Project Structure
```
financial-assistant-platform/
├── src/
│   ├── api/           # FastAPI application
│   ├── core/          # Security and configuration
│   ├── database/      # Database models and connection
│   └── ml/            # Machine learning modules
├── frontend/          # Streamlit applications
├── scripts/           # Data ingestion and training scripts
├── tests/             # Test suite
├── data/              # Sample transaction data
└── ml_models/         # Trained ML models
```

### Data Flow
1. **Data Ingestion**: CSV transaction data → SQLite database
2. **ML Training**: User data → Trained models (clustering, forecasting, recommendations)
3. **API Layer**: FastAPI serves ML predictions and user data
4. **Frontend**: Streamlit apps consume API for user interfaces
5. **AI Chat**: LangChain + Gemini provide conversational interface

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key (optional)
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

### ML Model Configuration
- **Clustering**: KMeans with 4 clusters (configurable)
- **Forecasting**: ExponentialSmoothing for 30-day predictions
- **Recommendations**: sentence-transformers with FAISS indexing

## 🚀 Deployment

### Production Considerations
1. **Database**: Migrate from SQLite to PostgreSQL
2. **Security**: Use strong secret keys and HTTPS
3. **Scaling**: Deploy as microservices with Docker
4. **Monitoring**: Add logging and health checks
5. **ML Models**: Implement model versioning and A/B testing

### Docker Deployment (Future)
```bash
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: For the excellent web framework
- **Streamlit**: For rapid frontend development
- **Darts**: For time series forecasting capabilities
- **Hugging Face**: For sentence transformers
- **Google**: For Gemini AI capabilities

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation at `/docs`
- Review the test suite for usage examples

---

**Built with ❤️ for modern financial technology**