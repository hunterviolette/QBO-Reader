import pandas as pd
from os import listdir

pd.set_option('display.max_rows', None)

class QuickbooksRegister:

  def __init__(self, 
              directory: str = 'pharms',
              basePath: str = './register_data',
              bankAccs: dict[str, str] = None,
              accList: dict[str, str] = None,
            ) -> None:

    if (bankAccs is not None) and (accList is not None):
      try: accList[directory]
      except: raise Exception('Bank accounts or account list mapped incorrectly')
    else: raise Exception("Bank account or account list mapping not provided")

    df = pd.DataFrame()
    for file in listdir(f"{basePath}/{directory}"):
      df = pd.concat([df, 
                      pd.read_csv(f"{basePath}/{directory}/{file}"
                        ).assign(**{"Bank Account": bankAccs[file.split('.')[0]]}) 
                    ])
    self.df = df.assign(**{
        "Date": lambda x: pd.to_datetime(x["Date"]),
        "Year": lambda x: x["Date"].dt.year,
        "Payment": lambda x: x["Payment"].replace(',', '', regex=True).fillna(0),
        "Deposit": lambda x: x["Deposit"].replace(',', '', regex=True).fillna(0),
      }).astype({
        "Ref No.": 'string',
        "Payee": 'string',
        "Memo": 'string',
        "Payment": 'float64',
        "Deposit": "float64",
        "Reconciliation Status": "string",
        "Account": "string",
        "Bank Account": "string",
      }).assign(**{"Amount": lambda x: x["Payment"]*-1 + x["Deposit"]
      }).sort_values('Date'
      ).merge(pd.read_csv(f'{basePath}/{accList[directory]}'
                ).drop(columns=["Description", "Balance"]
                ).rename(columns={
                  "Account": "Full name",
                  "Type": "Account type",
                  "Detail type": "Account Subtype"
                }).astype({
                  'Full name': 'string',
                  "Account type": 'string',
                  "Account Subtype": 'string'
                }),   
            left_on='Account', 
            right_on='Full name', 
            how='left'
      ).drop(columns=["Added in Banking", "Balance", "Type", 
                      "Payment", "Deposit", "Full name", "Account Subtype"]
      ).reset_index(drop=True)
    
    if self.df.loc[~self.df["Account"].isna()]["Account type"].isna().any(): 
      raise Exception(f"Update account list for {directory}")
    
  def GetAccounts(self, **kwargs):
    if "year" in kwargs.keys(): 
      df = self.df.loc[self.df["Year"] == kwargs["year"]]
      x = f' for year {kwargs["year"]}'
    else: df, x = self.df, ''

    if "verbose" in kwargs.keys(): print(
          f'--- Account List{x} ---', 
          df["Account"].sort_values().unique(),
          '---',
          sep='\n'
        )
      
    if "csv" in kwargs.keys():
      if kwargs["csv"]: pd.Series(df["Account"].unique()
                          ).sort_values(
                          ).to_csv('export/account_list.csv')

  def AccountSummary(self, **kwargs):
    if "year" in kwargs.keys(): df = self.df.loc[self.df["Year"] == kwargs["year"]]
    else: df = self.df

    df = df.groupby(['Year', 'Account', 'Account type']).sum()

    if "verbose" in kwargs.keys():
      if kwargs["verbose"]: print(df, '--- ---', sep='\n')

    if "csv" in kwargs.keys():
      if kwargs["csv"]: df.sort_values("Account").to_csv('export/accounts.csv')

    return df

  def AccountTransactions(self, **kwargs):
    if "year" in kwargs.keys(): df = self.df.loc[self.df["Year"] == kwargs["year"]]
    else: df = self.df

    if "account" in kwargs.keys(): 
      df = df.loc[df["Account"] == kwargs["account"]]

    if "verbose" in kwargs.keys():
      if kwargs["verbose"]: print(df, 
        f'Account total: {df["Amount"].sum()}', '--- ---', sep='\n')

    if "csv" in kwargs.keys():
      if kwargs["csv"]: df.to_csv('export/account.csv')
    
    return df

if __name__ == '__main__':
  from var import bankAccs, accList
  pharms, yr = False, 2022

  if pharms:
    x = QuickbooksRegister(directory='pharms',
                          bankAccs=bankAccs,
                          accList=accList)

    x.GetAccounts(year=yr, csv=True)
    x.AccountSummary(year=yr, verbose=True)
    x.AccountTransactions(year=yr, 
                          verbose=True, 
                          account='Distributions:Owner tax payments'
                        )
  else:
    x = QuickbooksRegister(directory='holdings',
                          bankAccs=bankAccs,
                          accList=accList)

    x.GetAccounts(year=yr, csv=False, verbose=True)
    df = x.AccountSummary(year=yr, verbose=True).reset_index()
    
    df = df.loc[(df["Account"].str.contains('498 Construction')) &
                (~df["Account"].str.contains('Exterior')) ]
    
    print(df, df["Amount"].sum().round(2), sep='\n')
  
