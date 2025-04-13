
from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from app.core.config import settings
from typing import Dict, List
import pandas as pd

class FinancialService:
    def __init__(self, access_token: str):
        configuration = Configuration(
            host=settings.PLAID_URL,
            api_key={
                'clientId': settings.PLAID_CLIENT_ID,
                'secret': settings.PLAID_CLIENT_SECRET
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        self.access_token = access_token
        
    async def get_transactions(self, start_date: str, end_date: str) -> List[Dict]:
        try:
            response = self.client.transactions_get(
                access_token=self.access_token,
                start_date=start_date,
                end_date=end_date
            )
            return response.transactions
        except Exception as e:
            raise Exception(f"Error fetching transactions: {str(e)}")
        
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
            
        for category, amount in spending_analysis["spending_by_category"].items():
            if amount > 1000:
                recommendations.append(f"High spending detected in {category}. Consider reviewing expenses.")
                
        return recommendations
