from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

class FinancialService:
    def __init__(self, access_token: str):
        self.client = plaid_api.PlaidApi(plaid.Client(
            client_id=settings.PLAID_CLIENT_ID,
            secret=settings.PLAID_SECRET,
            environment=settings.PLAID_ENV
        ))
        self.access_token = access_token

    async def get_accounts(self) -> List[Dict]:
        request = AccountsGetRequest(access_token=self.access_token)
        response = self.client.accounts_get(request)
        return response['accounts']

    async def get_transactions(self, start_date: str, end_date: str) -> List[Dict]:
        request = TransactionsGetRequest(
            access_token=self.access_token,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date()
        )
        response = self.client.transactions_get(request)
        return response['transactions']

    async def analyze_spending(self, transactions: List[Dict]) -> Dict:
        df = pd.DataFrame(transactions)
        return {
            "total_spending": df['amount'].sum(),
            "by_category": df.groupby('category').sum()['amount'].to_dict(),
            "by_account": df.groupby('account_id').sum()['amount'].to_dict(),
            "recent_large_transactions": df.nlargest(5, 'amount').to_dict('records')
        }

    async def sync_transactions(self, start_date: str, end_date: str) -> Dict:
        accounts = await self.get_accounts()
        transactions = await self.get_transactions(start_date, end_date)
        analysis = await self.analyze_spending(transactions)
        
        return {
            "accounts": accounts,
            "transactions": transactions,
            "analysis": analysis
        }