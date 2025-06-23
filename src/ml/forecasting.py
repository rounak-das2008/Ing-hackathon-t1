"""
Balance forecasting using time series analysis.
"""
import pandas as pd
import numpy as np
from darts import TimeSeries
from darts.models import ExponentialSmoothing
import pickle
import os
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from ..database.models import Transaction
from datetime import datetime, timedelta


class BalanceForecasting:
    """Balance forecasting for financial planning."""
    
    def __init__(self):
        self.model = ExponentialSmoothing()
    
    def prepare_time_series(self, user_id: int, db: Session) -> Optional[pd.DataFrame]:
        """Prepare daily balance time series for a user."""
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.date).all()
        
        if not transactions:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date.date(),
            'balance': t.balance
        } for t in transactions])
        
        # Group by date and take the last balance of each day
        daily_balance = df.groupby('date')['balance'].last().reset_index()
        daily_balance['date'] = pd.to_datetime(daily_balance['date'])
        daily_balance = daily_balance.set_index('date')
        
        # Create complete date range and forward fill missing values
        start_date = daily_balance.index.min()
        end_date = daily_balance.index.max()
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        daily_balance = daily_balance.reindex(date_range)
        daily_balance['balance'] = daily_balance['balance'].fillna(method='ffill')
        
        return daily_balance
    
    def train_forecast_model(self, user_id: int, db: Session) -> Dict[str, any]:
        """Train forecasting model for a specific user."""
        daily_balance = self.prepare_time_series(user_id, db)
        
        if daily_balance is None or len(daily_balance) < 7:
            return {"error": "Insufficient data for forecasting"}
        
        try:
            # Convert to Darts TimeSeries
            ts = TimeSeries.from_dataframe(
                daily_balance.reset_index(),
                time_col='date',
                value_cols=['balance']
            )
            
            # Train model
            self.model.fit(ts)
            
            # Save model
            os.makedirs("ml_models", exist_ok=True)
            with open(f"ml_models/forecast_user_{user_id}.pkl", "wb") as f:
                pickle.dump(self.model, f)
            
            return {
                "status": "success",
                "data_points": len(daily_balance),
                "date_range": f"{daily_balance.index.min()} to {daily_balance.index.max()}"
            }
            
        except Exception as e:
            return {"error": f"Training failed: {str(e)}"}
    
    def generate_forecast(self, user_id: int, db: Session, days: int = 30) -> Dict[str, any]:
        """Generate balance forecast for a user."""
        try:
            # Load model
            with open(f"ml_models/forecast_user_{user_id}.pkl", "rb") as f:
                model = pickle.load(f)
            
            # Get recent data for context
            daily_balance = self.prepare_time_series(user_id, db)
            if daily_balance is None:
                return {"error": "No transaction data available"}
            
            # Convert to Darts TimeSeries
            ts = TimeSeries.from_dataframe(
                daily_balance.reset_index(),
                time_col='date',
                value_cols=['balance']
            )
            
            # Generate forecast
            forecast = model.predict(n=days)
            
            # Convert forecast to DataFrame
            forecast_df = forecast.pd_dataframe()
            forecast_df.index = pd.date_range(
                start=daily_balance.index.max() + timedelta(days=1),
                periods=days,
                freq='D'
            )
            
            # Calculate trend and summary
            current_balance = daily_balance['balance'].iloc[-1]
            final_balance = forecast_df['balance'].iloc[-1]
            trend = "increasing" if final_balance > current_balance else "decreasing"
            
            # Generate summary
            summary = self._generate_forecast_summary(
                current_balance, final_balance, forecast_df, trend
            )
            
            # Prepare response
            forecast_data = {
                "dates": forecast_df.index.strftime('%Y-%m-%d').tolist(),
                "values": forecast_df['balance'].round(2).tolist(),
                "current_balance": round(current_balance, 2),
                "predicted_balance": round(final_balance, 2),
                "trend": trend,
                "summary": summary
            }
            
            return forecast_data
            
        except FileNotFoundError:
            return {"error": "Forecast model not trained for this user"}
        except Exception as e:
            return {"error": f"Forecast generation failed: {str(e)}"}
    
    def _generate_forecast_summary(
        self, 
        current_balance: float, 
        final_balance: float, 
        forecast_df: pd.DataFrame,
        trend: str
    ) -> str:
        """Generate a human-readable forecast summary."""
        balance_change = final_balance - current_balance
        change_percent = (balance_change / current_balance) * 100 if current_balance != 0 else 0
        
        # Find when balance might go below certain thresholds
        low_balance_days = None
        critical_balance_days = None
        
        for i, balance in enumerate(forecast_df['balance']):
            if balance < 1000 and low_balance_days is None:
                low_balance_days = i + 1
            if balance < 500 and critical_balance_days is None:
                critical_balance_days = i + 1
        
        summary_parts = []
        
        if trend == "decreasing":
            summary_parts.append(f"Your balance is projected to {trend} by ${abs(balance_change):.2f} ({abs(change_percent):.1f}%) over the next 30 days.")
            
            if critical_balance_days:
                summary_parts.append(f"⚠️ Warning: Your balance may drop below $500 in approximately {critical_balance_days} days.")
            elif low_balance_days:
                summary_parts.append(f"⚠️ Caution: Your balance may drop below $1,000 in approximately {low_balance_days} days.")
            else:
                summary_parts.append("Your balance should remain stable above $1,000.")
        else:
            summary_parts.append(f"Your balance is projected to {trend} by ${balance_change:.2f} ({change_percent:.1f}%) over the next 30 days.")
            summary_parts.append("This is a positive trend for your financial health.")
        
        return " ".join(summary_parts)