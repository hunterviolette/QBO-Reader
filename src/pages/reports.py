import numpy as np
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import plotly
from plotly import express as px
import os
import pytz

from dash import dcc, html, Input, Output, callback, State, dash_table, register_page
from dotenv import dotenv_values
from datetime import datetime
from typing import Optional

if __name__ == '__main__':
    from util.qbo import QBO_CLIENT
    from util.util import Util

else:
    from pages.util.qbo import QBO_CLIENT
    from pages.util.util import Util

register_page(__name__, 
              prevent_initial_callbacks=True,
              suppress_callback_exceptions=True
            )

class Reports(Util):
  envPath = './vol/.env'

  def __init__(self) -> None:
    pass
  
  @staticmethod
  def layout():
    dt = datetime.now(pytz.timezone('US/Eastern'))
    startDate = dt.replace(month=1, day=1).strftime('%Y-%m-%d')
    endDate = dt.strftime('%Y-%m-%d')

    return html.Div([

      dbc.Row([
        dbc.Col([
            html.H4("Report Type", style={'text-align': 'center'}),
            dcc.Dropdown(id='reports_reportType',
                        multi=False,
                        style=Reports.Formatting('textStyle'),
                        options={
                              "GeneralLedger": "General Ledger", 
                              "AccountList": "Account List", 
                              "DetailedLedger": "Detailed Ledger",
                              "SpendingSummary": "Spending Summary"
                            }
                        ),
        ]),
        dbc.Col([
            html.H4("Client Name", style={'text-align': 'center'}),
            dcc.Dropdown(id='reports_clientName', multi=False,
                        style=Reports.Formatting('textStyle'),
                      ),
        ]),
        dbc.Col([
            html.H4("Realm Name", style={'text-align': 'center'}),
            dcc.Dropdown(id='reports_realmName', multi=False,
                        style=Reports.Formatting('textStyle'),
                      ),
        ]),
        dbc.Col([
            html.H4("Start Date", style={'text-align': 'center'}),
            dcc.Input(id='reports_startDate', 
                      type='text', 
                      value=startDate,
                      placeholder='YYYY-MM-DD',
                      className=Reports.Formatting('input'),
                      style=Reports.Formatting('textStyle')
                    ),
        ]),
        dbc.Col([
            html.H4("End Date", style={'text-align': 'center'}),
            dcc.Input(id='reports_endDate', 
                      type='text', 
                      value=endDate,
                      placeholder='YYYY-MM-DD',
                      className=Reports.Formatting('input'),
                      style=Reports.Formatting('textStyle')
                    ),
        ]),
        dbc.Col([
            html.H4("GET Report"),
            html.Button("click here", n_clicks=0, id="reports_update", 
                        className=Reports.Formatting('button', 'info')
                      ),
        ], className='text-center'),

      ], align='center'), # end dbc.row

      html.Div(id='reports_div'),

    ], className='mb-4', style=Reports.Formatting('mdiv'))

  def callbacks(self):
    @callback(
      [Output("reports_clientName", "options"),
      Output("reports_realmName", "options")],
      Input("reports_update", "n_clicks"),
    )
    def initcb(clicks):
      return (
        [key for key, val in dotenv_values(Reports.envPath).items() if "_CLIENT_ID" in key],
        [key for key, val in dotenv_values(Reports.envPath).items() if "_REALM_ID" in key],
      )

    @callback(
      [Output("reports_clientName", 'value'),
      Output("reports_realmName", 'value'),
      Output("reports_startDate", 'value'),
      Output("reports_endDate", 'value'),
      Output("reports_reportType", 'value'),
      Output('reports_div', 'children'),
      ],
      Input("reports_update", "n_clicks"),
      [State("reports_clientName", "value"),
      State("reports_realmName", "value"),
      State("reports_startDate", 'value'),
      State("reports_endDate", 'value'),
      State("reports_reportType", 'value'),
      ],
    )
    def maincb(
            clicks: int, 
            clientName: str,
            realmName: str,
            startDate: str,
            endDate: str,
            report: str
          ):

      print(clicks, clientName, realmName, startDate, endDate, report, sep=' ')

      mdiv = []      
      if clicks > 0 \
      and realmName != None \
      and clientName != None \
      and report != None:
        
        obj = QBO_CLIENT(
            client_name=clientName.split("_CLIENT_ID")[0],
            realm_name=realmName.split("_REALM_ID")[0],
          )
        
        reports = {
            "GeneralLedger": obj.GeneralLedger,
            "SpendingSummary": obj.DetailedLedger,
            "DetailedLedger": obj.DetailedLedger,
            "AccountList": obj.AccountList,
          }

        df = reports[report](
            start_date=startDate,
            end_date=endDate
          )
        
        if report == 'SpendingSummary':
          df = (df
              .assign(**{
                "Month Year": lambda x: x["Date"].dt.strftime("%Y-%m")
                })
              .groupby(['Month Year', 'Transaction Type', 'Name', 
                        'Account', 'Split', 'Type'], as_index=False
                ).agg({"Amount": 'sum'})
            )
          
          barFig = go.Figure()
          df.groupby(['Month Year', 'Type'], as_index=False) \
            .agg({"Amount": 'sum'}) \
            .groupby('Type') \
            .apply(lambda x: barFig.add_trace(go.Bar(
                x=x["Month Year"],
                y=x["Amount"],
                name=x.name,
                text=np.round(x["Amount"]/1000, 2).astype(str) + 'K',
                textposition='auto'
            )))
          
          netFig = go.Figure()
          df.groupby(['Month Year'], as_index=False) \
            .agg({"Amount": 'sum'}) \
            .apply(lambda x: netFig.add_trace(go.Bar(
                x=[x["Month Year"]],
                y=[x["Amount"]],
                name=x["Month Year"],
                text=np.round(x["Amount"]/1000, 2).astype(str) + 'K',
                textposition='auto'
            )), axis=1)
          
          mdiv.extend([            
            dcc.Graph(figure=barFig.update_layout(barmode='relative', height=800)),
            dcc.Graph(figure=netFig.update_layout(height=400)),

            Reports.DarkDashTable(df, rows=10),
            ])
          
          for x in df["Type"].unique():
            d = (df.loc[df["Type"] == x]
                  .copy(deep=True)
                  .groupby(["Split", "Name"], as_index=False)
                  .agg({"Amount": 'sum'})
                  .assign(**{
                    "Type": x,
                    "Amount": lambda x: x["Amount"].__abs__()
                  })
                  .fillna(0)
                  .round(0)
                )

            fig = px.treemap(
                  d,
                  path=["Split", "Name"],
                  values='Amount',
                  color='Amount',
                  color_continuous_scale=px.colors.diverging.Tealrose
              )
            
            mdiv.extend([
                html.H4(f"Account splits for {x} accounts"),
                dcc.Graph(figure=fig.update_layout(height=1200))
            ])
            
        else: mdiv.append(Reports.DarkDashTable(df))
        
        print('plotting...')
      else:
        rules = dcc.Markdown('''
            ## What does clicking this button do? 
              -  Returns specified report using Quickbooks API 
            ''', 
          style={
              'backgroundColor': '#121212',
              'color': '#FFFFFF',       
              'padding': '20px',     
            }
          )

        mdiv.append(rules)
      return (clientName, realmName, startDate, endDate, report, mdiv)

x = Reports()
layout = x.layout()
x.callbacks()