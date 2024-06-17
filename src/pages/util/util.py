import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os 
import datetime

from dash import dcc, dash_table, html

class Util:

  @staticmethod
  def DarkDashTable(df, rows: int = 30):
    return dash_table.DataTable(
            data = df.to_dict('records'),
            columns = [{'name': i, 'id': i} for i in df.columns],
            export_format="csv",
            sort_action='native', 
            page_size=rows,
            filter_action='native',
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            style_data={'backgroundColor': 'rgb(50, 50, 50)','color': 'white'},
            style_table={'overflowX': 'auto'},
            style_cell={
                'height': 'auto',
                'minWidth': '70px', 'width': '70px', 'maxWidth': '180px',
                'whiteSpace': 'normal'
              }
          ) 

  @staticmethod
  def Formatting( 
                className: str = 'heading', 
                color: str = 'info',
                textAlign: str = 'center'
              ):

    if className == 'heading':
      return f"bg-opacity-50 p-1 m-1 bg-{color} text-dark fw-bold rounded text-{textAlign}"
    
    elif className == 'mdiv': return {"padding": "10px"} # style not className

    elif className == 'button': return f"btn btn-{color}"

    elif className == 'input': return 'form-control'

    elif className == 'textStyle': return {'text-align': 'center', 'color': 'black'} # style
    
    else: raise Exception("className not found")

  @staticmethod
  def StrTime(asInt: bool = False):
    x = int(datetime.datetime.utcnow().timestamp())
    if asInt: return x
    else: return str(x)

  @staticmethod
  def initDir(dir_path):
    if not os.path.exists(dir_path): os.makedirs(dir_path)
    else: print(f"Directory: {dir_path} exists")

if __name__ == "__main__":
  pass