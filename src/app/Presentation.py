#!/usr/bin/env python
"""
My Python module
"""
from datetime import datetime as _dt

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from dash import dcc, html

from . import config as cfg
from .Logger import log
from .Analytics import Spark
from .Helper import fetch_host_ip

DEFAULT_RANGE = "1d"
TOPICS = (cfg.HTTP_TOPIC_NAME, cfg.APP_TOPIC_NAME)


log.info("Call engine")
spark = Spark()
spark.start(app_name=cfg.APP_NAME)
spark.subscribe(topics=TOPICS)
engine = None


web = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

web.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Kafka > Spark > Dash"),
            dcc.Dropdown(
                id='time-range-dropdown',
                options=[
                    {'value': '1h', 'label': 'Last hour'},
                    {'value': '1d', 'label': 'Last 24 hours'},
                    {'value': '7d', 'label': 'Last 7 days'},
                    {'value': '1m', 'label': 'Last 30 days'},
                ],
                value=DEFAULT_RANGE
            ),
            dcc.Graph(id='line-plot'),
            dcc.Interval(
                id='interval-component',
                interval=60 * 1000,
                n_intervals=0
            ),
        ], width=12)
    ])
], fluid=True)


@web.callback(
    Output('line-plot', 'figure'),
    [Input('time-range-dropdown', 'value'), Input('interval-component', 'n_intervals')]
)
def update_line_plot(*args):
    log.debug(f"Method update_line_plot called with args: {args}")

    selected_range, update_seq = args[:2]
    log.debug(f"App requested data of {selected_range=}, after {update_seq=}")

    global engine
    if not engine:
        engine = spark.process()

    try:
        data = []
        for topic in TOPICS:
            topic = topic.split("-")[-1]
            df = engine.sql(f"SELECT window.end as range_end, {topic} FROM {topic}").toPandas()
            df['range_end'] = pd.to_datetime(df['range_end'])
            data.append(df)

    except Exception as e:
        log.critical(f"Error reading from memory: {e}")
        return {}

    df = pd.merge(data[0], data[1], on='range_end', how='outer').fillna(0)
    log.debug("Merged Data range: {} - {}".format(df['range_end'].min(), df['range_end'].max()))

    now = pd.Timestamp.now()

    if selected_range == '1h':
        df_resampled = df.set_index('range_end').resample('1min').sum().reset_index()
        requested_df = df_resampled[df_resampled['range_end'] >= (now - pd.Timedelta(hours=1))]
    elif selected_range == '1d':
        df_resampled = df.set_index('range_end').resample('h').sum().reset_index()
        requested_df = df_resampled[df_resampled['range_end'] >= (now - pd.Timedelta(days=1))]
    elif selected_range == '7d':
        df_resampled = df.set_index('range_end').resample('D').sum().reset_index()
        requested_df = df_resampled[df_resampled['range_end'] >= (now - pd.Timedelta(days=7))]
    elif selected_range == '1m':
        df_resampled = df.set_index('range_end').resample('D').sum().reset_index()
        requested_df = df_resampled[df_resampled['range_end'] >= (now - pd.Timedelta(days=30))]

    log.info("Available data range for the requested period of {}: {} - {}".format(
        selected_range, requested_df['range_end'].min(), requested_df['range_end'].max(),
    ))

    # Cria o gráfico de linhas
    fig = px.line(
        requested_df,
        x='range_end', y=[topic.split("-")[-1] for topic in TOPICS],
        labels={
            'value': "{} count".format(_dt.now().strftime("%A, %H:%M").capitalize()),
            'range_end': 'Requests and responses timeline'
        },
    )

    return fig


def run():
    service_ip = fetch_host_ip() if cfg.BIND_HOST in ("127.0.0.1", "localhost") else cfg.BIND_HOST
    web.run_server(debug=True, host=service_ip, port=cfg.BIND_PORT)


if __name__ == "__main__":
    run()
