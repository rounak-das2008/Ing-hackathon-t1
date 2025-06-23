"""
Chat service for AI-powered financial assistance.
"""
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from ..database.models import ChatHistory


class ChatService:
    """AI chat service using Google Gemini."""
    
    def __init__(self):
        self.model = None
        self.api_key = os.getenv("GEMINI_API_KEY")
    
    async def initialize(self):
        """Initialize the chat service."""
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY not found. Using mock responses.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            print("✅ Gemini AI initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini AI: {e}")
            self.model = None
    
    async def generate_response(
        self,
        user_message: str,
        user_cluster: str,
        cluster_description: str,
        forecast_summary: str,
        recommendations: List[Dict[str, Any]],
        chat_history: List[ChatHistory]
    ) -> str:
        """Generate AI response to user message."""
        
        # Build context
        context = self._build_context(
            user_cluster, cluster_description, forecast_summary, 
            recommendations, chat_history
        )
        
        # Create system prompt
        system_prompt = f"""You are 'FinCoach', an expert, friendly, and encouraging personal finance assistant. Your goal is to provide insightful, actionable advice based on the user's financial data. NEVER give financial advice that could be construed as professional investment or legal advice. Keep responses concise and clear.

**User's Financial Context (DO NOT mention this context to the user directly, use it to inform your answers):**
{context}

---
User: {user_message}
FinCoach:"""

        if self.model:
            try:
                response = self.model.generate_content(system_prompt)
                return response.text
            except Exception as e:
                print(f"Gemini API error: {e}")
                return self._get_fallback_response(user_message, user_cluster)
        else:
            return self._get_fallback_response(user_message, user_cluster)
    
    def _build_context(
        self,
        user_cluster: str,
        cluster_description: str,
        forecast_summary: str,
        recommendations: List[Dict[str, Any]],
        chat_history: List[ChatHistory]
    ) -> str:
        """Build context string for the AI."""
        context_parts = []
        
        # Cluster information
        context_parts.append(f"- **Behavioral Profile (Cluster):** {user_cluster} - {cluster_description}")
        
        # Forecast
        context_parts.append(f"- **Spending Forecast:** {forecast_summary}")
        
        # Recommendations
        if recommendations:
            rec_list = []
            for rec in recommendations[:3]:
                rec_list.append(f"{rec['name']} ({rec['category']})")
            context_parts.append(f"- **Relevant Products for You:** {', '.join(rec_list)}")
        
        # Recent conversation
        if chat_history:
            history_parts = []
            for chat in reversed(chat_history[-3:]):  # Last 3 exchanges
                history_parts.append(f"User: {chat.user_message}")
                history_parts.append(f"FinCoach: {chat.ai_response}")
            context_parts.append(f"- **Recent Conversation:**\n{chr(10).join(history_parts)}")
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self, user_message: str, user_cluster: str) -> str:
        """Generate fallback response when AI is not available."""
        message_lower = user_message.lower()
        
        # Simple keyword-based responses
        if any(word in message_lower for word in ['budget', 'spending', 'expense']):
            return f"As a {user_cluster}, I'd recommend tracking your expenses carefully. Consider using the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings. Would you like specific budgeting tips for your spending pattern?"
        
        elif any(word in message_lower for word in ['save', 'saving', 'savings']):
            return "Building an emergency fund is crucial! Start with saving $500-$1000 for unexpected expenses. Even small amounts saved regularly can make a big difference. What's your current savings goal?"
        
        elif any(word in message_lower for word in ['invest', 'investment', 'investing']):
            return "Investment decisions should align with your risk tolerance and financial goals. Consider starting with low-cost index funds or speaking with a financial advisor. Remember, I can't provide specific investment advice, but I can help you understand general principles!"
        
        elif any(word in message_lower for word in ['debt', 'loan', 'credit']):
            return "Managing debt effectively is key to financial health. Consider the debt avalanche method (paying off highest interest first) or debt snowball (smallest balance first). Would you like to discuss debt management strategies?"
        
        elif any(word in message_lower for word in ['forecast', 'future', 'predict']):
            return "Based on your spending patterns, I can help you understand potential future scenarios. Your financial forecast depends on maintaining current habits. Would you like tips on improving your financial trajectory?"
        
        else:
            return f"Thanks for your question! As a {user_cluster}, you have unique financial patterns. I'm here to help with budgeting, saving, spending analysis, and general financial guidance. What specific area would you like to explore?"