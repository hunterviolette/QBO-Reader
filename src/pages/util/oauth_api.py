import json
from requests_oauthlib import OAuth2Session
from decouple import config
import os
import time

TOKEN_FILE = 'quickbooks_tokens.json'

class QuickBooksClient:
    def __init__(self, client_id, client_secret, redirect_uri, company_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.company_id = company_id
        self.api_url_v3 = "https://quickbooks.api.intuit.com/v3"

        token = self.load_token()
        self.session = OAuth2Session(client_id, redirect_uri=redirect_uri, token=token)

    def load_token(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                token = json.load(f)
            return token
        else:
            return self.obtain_access_token()

    def save_token(self, token):
        with open(TOKEN_FILE, 'w') as f: json.dump(token, f)

    def obtain_access_token(self):
        scope = ['com.intuit.quickbooks.accounting']  # Add scopes as needed
        oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=scope)
        authorization_url, state = oauth.authorization_url('https://appcenter.intuit.com/connect/oauth2')
        print(f'Please go to {authorization_url} and authorize access.')
        
        authorization_response = input('Enter the full callback URL: ')
        token = oauth.fetch_token(
            'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
            authorization_response=authorization_response,
            client_secret=self.client_secret
        )

        self.save_token(token)
        return token

    def refresh_token(self):
        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        new_token = self.session.refresh_token(
            'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer', 
            refresh_token=self.session.token['refresh_token'], 
            **extra
        )
        self.save_token(new_token)
        return new_token

    def process_request(self, method, url, headers=None, body=None):
        if self.session.token['expires_at'] < time.time():
            print('Token expired, refreshing...')
            self.token = self.refresh_token()

        if headers is None:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.session.token["access_token"]}'
            }

        response = self.session.request(method, url, headers=headers, json=body)
        
        if response.status_code != 200:
            raise Exception(f"Error fetching data: {response.status_code}, {response.text}")

        return response.json()

    def JournalEntry(self, **kwargs):
        self.ExcTime('Fetching JournalEntry')
        print(kwargs)
        url = f"{self.api_url_v3}/company/{self.company_id}/journalentry/{kwargs['Id']}"
        data = self.process_request(method='GET', url=url)
        print(data)
        return data

if __name__ == "__main__":
    client_name, realm_name = 'hunter', 'mvph'
    client_name, realm_name = client_name.upper(), realm_name.upper()

    client_id = config(f"{client_name}_CLIENT_ID")
    client_secret = config(f"{client_name}_CLIENT_SECRET")
    redirect_uri = config("REDIRECT_URL")
    company_id = config(f"{realm_name}_REALM_ID")

    client = QuickBooksClient(client_id, client_secret, redirect_uri, company_id)
    journal_entry = client.JournalEntry(Id=19)
