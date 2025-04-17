
import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from datetime import timedelta

sheet_url = "https://docs.google.com/spreadsheets/d/1iGN1gCZILFY1ejwz6IBhrOikC_aIMs5xUkEsCE2DW3U/export?format=csv"
df = pd.read_csv(sheet_url)
df["DATA DE VENDA"] = pd.to_datetime(df["DATA DE VENDA"], dayfirst=True, errors="coerce")
df["DATA DA EXPERIÊNCIA"] = pd.to_datetime(df["DATA DA EXPERIÊNCIA"], dayfirst=True, errors="coerce")
df["total"] = df["total"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
df["total"] = pd.to_numeric(df["total"], errors="coerce")
df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce")
df["order_status"] = df["order_status"].astype(str).str.lower()
df = df[df["order_status"] == "aprovado"]

today = df["DATA DE VENDA"].max()
first_day = today.replace(day=1)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container(fluid=True, children=[
    html.Div([
        html.Img(src="/assets/logo_winelocals.png", className="logo"),
        html.H2("Dashboard de Vendas", className="title")
    ], className="header"),

    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id='date-range',
                start_date=first_day,
                end_date=today,
                display_format="DD/MM/YYYY",
                className="date-picker"
            )
        ], width=12)
    ], className="mb-4"),

    dbc.Row(id="kpi-cards", className="mb-4"),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id="tpv-graph")
        ], width=12)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            html.H4("Tabela de Campanhas"),
            html.Div(id="campanhas-table")
        ], width=6),
        dbc.Col([
            html.H4("Tabela de Clientes"),
            html.Div(id="clientes-table")
        ], width=6)
    ])
])

@app.callback(
    Output("tpv-graph", "figure"),
    Output("kpi-cards", "children"),
    Output("campanhas-table", "children"),
    Output("clientes-table", "children"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_dashboard(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    days_range = (end_date - start_date).days

    atual = df[(df["DATA DE VENDA"] >= start_date) & (df["DATA DE VENDA"] <= end_date)]
    anterior = df[(df["DATA DE VENDA"] >= start_date - timedelta(days=days_range+1)) &
                  (df["DATA DE VENDA"] <= end_date - timedelta(days=days_range+1))]
    yoy = df[(df["DATA DE VENDA"] >= start_date - timedelta(days=365)) &
             (df["DATA DE VENDA"] <= end_date - timedelta(days=365))]

    # KPIs
    tpv = atual["total"].sum()
    compras = atual["partner_order_id"].nunique()
    tickets = atual["item_id"].sum()
    ticket_medio = tpv / tickets if tickets else 0

    kpis = [
        dbc.Col(html.Div([
            html.H5("TPV Total"),
            html.H4(f"R$ {tpv:,.2f}")
        ], className="kpi-card"), width=3),
        dbc.Col(html.Div([
            html.H5("Compras"),
            html.H4(f"{compras}")
        ], className="kpi-card"), width=3),
        dbc.Col(html.Div([
            html.H5("Tickets"),
            html.H4(f"{int(tickets)}")
        ], className="kpi-card"), width=3),
        dbc.Col(html.Div([
            html.H5("Ticket Médio"),
            html.H4(f"R$ {ticket_medio:,.2f}")
        ], className="kpi-card"), width=3),
    ]

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=atual["DATA DE VENDA"], y=atual["total"], name="Atual", mode="lines+markers", line_shape="spline"))
    fig.add_trace(go.Scatter(x=anterior["DATA DE VENDA"], y=anterior["total"], name="Período anterior", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=yoy["DATA DE VENDA"], y=yoy["total"], name="Ano anterior", line=dict(dash="dash")))
    fig.update_layout(title="Evolução Diária do TPV", xaxis_title="Data", yaxis_title="R$")

    # Tabela de campanhas
    campanhas = atual.dropna(subset=["Campanha"]).groupby("Campanha").agg(
        TPV=("total", "sum"),
        Compras=("partner_order_id", "nunique"),
        Tickets=("item_id", "sum")
    ).reset_index()
    campanhas["Ticket Médio"] = campanhas["TPV"] / campanhas["Tickets"]
    campanhas_html = dbc.Table.from_dataframe(
        campanhas.sort_values("TPV", ascending=False),
        striped=True, bordered=True, hover=True, responsive=True, class_name="table-sm"
    )

    # Tabela de clientes
    clientes = atual.dropna(subset=["client_name"]).groupby("client_name").agg(
        TPV=("total", "sum"),
        Compras=("partner_order_id", "nunique"),
        Tickets=("item_id", "sum")
    ).reset_index()
    clientes["Ticket Médio"] = clientes["TPV"] / clientes["Tickets"]
    clientes_html = dbc.Table.from_dataframe(
        clientes.sort_values("TPV", ascending=False),
        striped=True, bordered=True, hover=True, responsive=True, class_name="table-sm"
    )

    return fig, kpis, campanhas_html, clientes_html

if __name__ == "__main__":
    app.run_server(debug=True)
