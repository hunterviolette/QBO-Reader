import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

print("App starting")
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.SUPERHERO])
server = app.server

sidebar = dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.Div(page["name"], className="ms-2"),
                    ],
                    href=page["path"],
                    active="exact",
                )
                for page in dash.page_registry.values()
            ],

            pills=True,
            className="dbc",
)

app.layout = dbc.Container([

    dbc.Row(
            [   
                dbc.Row(
                    [
                        sidebar
                    ]),

                dbc.Col(
                    [
                        dash.page_container
                    ], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10)
            ]
        )
    ], className="dbc", fluid=True)


if __name__ == "__main__":
    print("App running")
    app.run(host='0.0.0.0', port='8050', debug=False)