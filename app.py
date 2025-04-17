
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta

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
filtered = df[(df["DATA DE VENDA"] >= first_day) & (df["DATA DE VENDA"] <= today)]

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1("Wine Locals • Dashboards", className="header-title"),
        dcc.DatePickerRange(
            id='date-range',
            min_date_allowed=df["DATA DE VENDA"].min(),
            max_date_allowed=df["DATA DE VENDA"].max(),
            start_date=first_day,
            end_date=today,
            display_format="DD/MM/YYYY"
        )
    ], className="header"),
    
    html.Div([
        dcc.Graph(id='tpv-evolucao')
    ], className="section")
], className="container")

@app.callback(
    Output('tpv-evolucao', 'figure'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_tpv_chart(start_date, end_date):
    if not start_date or not end_date:
        return go.Figure()
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    atual = df[(df["DATA DE VENDA"] >= start_date) & (df["DATA DE VENDA"] <= end_date)]
    days_range = (end_date - start_date).days
    anterior = df[(df["DATA DE VENDA"] >= start_date - timedelta(days=days_range+1)) & (df["DATA DE VENDA"] <= end_date - timedelta(days=days_range+1))]
    yoy = df[(df["DATA DE VENDA"] >= start_date - timedelta(days=365)) & (df["DATA DE VENDA"] <= end_date - timedelta(days=365))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=atual["DATA DE VENDA"], y=atual["total"], mode='lines+markers', name="Atual", line_shape="spline"))
    fig.add_trace(go.Scatter(x=anterior["DATA DE VENDA"], y=anterior["total"], mode='lines', name="Período anterior", line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=yoy["DATA DE VENDA"], y=yoy["total"], mode='lines', name="Ano anterior", line=dict(dash='dash')))

    fig.update_layout(title="Evolução Diária de TPV", xaxis_title="Data", yaxis_title="Total (R$)")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
