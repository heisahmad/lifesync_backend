
from plaid import Client
from app.core.config import settings
from typing import Dict, List
import pandas as pd

class FinancialService:
    def __init__(self, access_token: str):
        self.client = Client(
            client_id=settings.PLAID_CLIENT_ID,
            secret=settings.PLAID_CLIENT_SECRET,
            environment='development'
        )
        self.access_token = access_token
        
    async def get_transactions(self, start_date: str, end_date: str) -> List[Dict]:
        response = self.client.Transactions.get(
            self.access_token,
            start_date=start_date,
            end_date=end_date
        )
        return response['transactions']
        
    async def analyze_spending(self, transactions: List[Dict]) -> Dict:
        df = pd.DataFrame(transactions)
        
        analysis = {
            "total_spending": df['amount'].sum(),
            "spending_by_category": df.groupby('category').sum()['amount'].to_dict(),
            "largest_transaction": df.nlargest(1, 'amount').to_dict('records')[0],
            "average_transaction": df['amount'].mean()
        }
        
        return analysis
        
    async def generate_financial_recommendations(self, spending_analysis: Dict) -> List[str]:
        recommendations = []
        
        if spending_analysis["average_transaction"] > 100:
            recommendations.append("Consider setting a per-transaction spending limit")
            
        # Add category-specific recommendations
        for category, amount in spending_analysis["spending_by_category"].items():
            if amount > 1000:
                recommendations.append(f"High spending detected in {category}. Consider reviewing expenses.")
                
        return recommendations
