from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from datetime import datetime
from dotenv import dotenv_values

import pandas as pd
import random
import string
import pytz
import json

class QBO_CLIENT: 
  envPath = './vol/.env'

  def __init__(
        self, 
        client_name: str = 'hunter',
        realm_name: str = 'mvp', 
        production: bool = True
      ) -> None:
    
    self.startTime = datetime.utcnow()
    client_name = client_name.upper()
    realm_name = realm_name.upper()
    
    if production: env = 'production' 
    else: env ='sandbox'

    envVars = dotenv_values(QBO_CLIENT.envPath)
    try:
      id = envVars[f"{client_name}_CLIENT_ID"]
      secret = envVars[f"{client_name}_CLIENT_SECRET"]
      redir_url = envVars["REDIRECT_URL"]
      token = envVars[f"{realm_name}_REFRESH_TOKEN"]
      realm = envVars[f"{realm_name}_REALM_ID"]
    except KeyError as e:
      raise KeyError(f"Missing configuration key: {e.args[0]}")
    
    self.client = QuickBooks(
                    auth_client=AuthClient(
                        client_id=id,
                        client_secret=secret,
                        environment=env,
                        redirect_uri=redir_url,
                    ),
                    refresh_token=token,
                    company_id=realm,
                  )
  
  def ExcTime(self, msg: str = ''):
    time = (datetime.utcnow() - self.startTime).seconds.__round__(2)
    print(f"{msg} {time} seconds")
    
  def GeneralLedger(self, **kwargs):
    QBO_CLIENT.ExcTime(self, 'Fetching GeneralLedger ')

    print(kwargs)

    if not "start_date" in kwargs.keys():
      dt = datetime.now(pytz.timezone('US/Eastern'))

      kwargs["start_date"] = dt.replace(month=1, day=1).strftime('%Y-%m-%d')
      kwargs["end_date"] = dt.strftime('%Y-%m-%d')

    data = self.client.get_report('TransactionList', qs=kwargs)
    
    columns = [col['ColTitle'] for col in data['Columns']['Column']]
    rows = [[col['value'] for col in row['ColData']] for row in data['Rows']['Row']]
    df = pd.DataFrame(rows, columns=columns
          ).assign(**{
            "Date": lambda x: pd.to_datetime(x["Date"]),
            "Amount": lambda x: pd.to_numeric(x["Amount"], errors='coerce'),
            "Num": lambda x: pd.to_numeric(x["Num"], errors='coerce')
          }).astype({
            "Transaction Type": 'string',
            "Posting": 'string',
            "Name": 'string',
            "Memo/Description": 'string',
            "Account": "string",
            "Split": "string",
          }).sort_values('Date')
    
    QBO_CLIENT.ExcTime(self, 'pd.DataFrame after ')
    
    return df

  def AccountList(self, **kwargs):
    QBO_CLIENT.ExcTime(self, 'Fetching AccountList')

    data = self.client.get_report('AccountList')
    
    columns = [col['ColTitle'] for col in data['Columns']['Column']]
    rows = [[col['value'] for col in row['ColData']] for row in data['Rows']['Row']]
    df = pd.DataFrame(rows, columns=columns
          ).astype({
            "Account": 'string',
            "Type": 'string',
            "Detail type": 'string',
          })

    QBO_CLIENT.ExcTime(self, 'pd.DataFrame after ')

    if "merge" in kwargs.keys():
      return df[["Account", "Type", "Detail type"]]
    
    return df
  
  def JournalEntry(self, **kwargs):
    QBO_CLIENT.ExcTime(self, 'Fetching JournalReport')
    print(kwargs)
    data = self.client.get_report('JournalReport', qs=kwargs)
    print(data)

    with open('t.json', 'w') as f: json.dump(data, f, indent=4)
    
    columns = [col['ColTitle'] for col in data['Columns']['Column']]

    rows = []
    for row in data['Rows']['Row']:
      if row['type'] == 'Data':
        rows.append([col.get('value', '') for col in row['ColData']])


    
    '''
    columns = [col['ColTitle'] for col in data['Columns']['Column']]
    rows = [
        [col['value'] for col in row['ColData']]
          if row['type'] == 'Data'
          else [col['value'] for col in row['Summary']['ColData']]
        for row in data['Rows']['Row']
      ]'''

    df = pd.DataFrame(rows, columns=columns)
    df.to_csv('t.csv')

    QBO_CLIENT.ExcTime(self, 'pd.DataFrame after ')

    return df
  
  def DetailedLedger(self, **kwargs):
    df = QBO_CLIENT.GeneralLedger(self, **kwargs
                  ).drop(["Posting"], axis=1)

    kwargs["merge"] = True
    accs = QBO_CLIENT.AccountList(self, **kwargs
                    ).rename({"Account": "Split"}, axis=1)

    df = df.merge(accs, on='Split', how='left')
    
    if "randomize" in kwargs.keys():
      if kwargs["randomize"]:
        
        df['Name'] = df['Name'].apply(
            lambda x: (lambda s, m={}: 
              m.setdefault(s, ''.join(
                random.choices(
                  string.ascii_letters + string.digits, k=len(s)))))(x))
          
    print(df)
    df.to_csv('a.csv')

if __name__ == "__main__":
  ledger, accounts, journal = False, False, False
  dledg = True

  x = QBO_CLIENT('hunter', 'mvp', True)

  if ledger: print(x.GeneralLedger(
                      start_date='2023-01-01',
                      end_date='2023-12-31',
                    ))
    
  if accounts: print(x.AccountList(merge=True))
  if journal: print(x.JournalEntry(date_macro='Last Fiscal Year'))

  if dledg: x.DetailedLedger(
              start_date='2023-01-01',
              end_date='2023-12-31',
              #randomize=True
            )
  