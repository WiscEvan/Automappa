#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

from app import app
from apps import explorer, summary

tab_style = {
    "borderTop": "3px solid white",
    "borderBottom": "0px",
    "borderLeft": "0px",
    "borderRight": "0px",
    "backgroundColor": "#9b0000",
}

tab_selected_style = {
    "borderTop": "3px solid #c5040d",
    "borderBottom": "0px",
    "borderLeft": "0px",
    "borderRight": "0px",
    "fontWeight": "bold",
    "color": "white",
    "backgroundColor": "#c5040d",
}


def layout(df, cluster_columns):
    app.layout = html.Div(
        [
            # Hidden div that saves dataframe for each tab
            html.Div(
                df.to_json(orient="split"), id="binning_df", style={"display": "none"}
            ),
            html.Div(
                df[cluster_columns].to_json(orient="split"),
                id="refinement-data",
                style={"display": "none"},
            ),
            html.Link(
                href="https://use.fontawesome.com/releases/v5.2.0/css/all.css",
                rel="stylesheet",
            ),
            html.Link(
                href="https://fonts.googleapis.com/css?family=Dosis", rel="stylesheet"
            ),
            html.Link(
                href="https://fonts.googleapis.com/css?family=Open+Sans",
                rel="stylesheet",
            ),
            html.Link(
                href="https://fonts.googleapis.com/css?family=Ubuntu", rel="stylesheet"
            ),
            html.Link(href="static/dash_crm.css", rel="stylesheet"),
            html.Link(href="static/stylesheet.css", rel="stylesheet"),
            # header
            html.Div(
                [
                    html.Label(
                        "Automappa Dashboard", className="three columns app-title"
                    ),
                    html.Div(
                        [
                            dcc.Tabs(
                                id="tabs",
                                style={"height": "10", "verticalAlign": "middle"},
                                children=[
                                    dcc.Tab(
                                        label="Bin Exploration",
                                        value="explorer_tab",
                                        style=tab_style,
                                        selected_style=tab_selected_style,
                                    ),
                                    dcc.Tab(
                                        id="bin_summary",
                                        label="Binning Summary",
                                        value="summary_tab",
                                        style=tab_style,
                                        selected_style=tab_selected_style,
                                    ),
                                ],
                                value="explorer_tab",
                            ),
                        ],
                        className="seven columns row header",
                    ),
                    html.Div(
                        html.Img(src="static/UWlogo.png", height="100%"),
                        style={"float": "right", "height": "100%"},
                        className="two columns",
                    ),
                ],
                className="row header",
            ),
            # Tab content
            html.Div(id="tab_content", className="row", style={"margin": "0.5% 0.5%"}),
        ],
        className="row",
        style={"margin": "0%"},
    )


@app.callback(Output("tab_content", "children"), [Input("tabs", "value")])
def render_content(tab):
    if tab == "explorer_tab":
        return explorer.layout
    elif tab == "summary_tab":
        return summary.layout
    else:
        return explorer.layout


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Automappa: An interactive interface for exploration of metagenomes"
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Path to recursive_dbscan.tab or ML_recruitment.tab",
        required=True,
    )
    parser.add_argument(
        "--port",
        help="port to expose",
        default="8050",
        type=int,
    )
    parser.add_argument(
        "--host",
        help="host ip address to expose",
        default="0.0.0.0",
    )
    parser.add_argument(
        "--debug",
        help="Turn on debug mode",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    df = pd.read_csv(args.input, sep="\t")
    cols = [
        col
        for col in df.columns
        if "refinement_" in col or "cluster" in col or "contig" in col
    ]
    layout(df, cluster_columns=cols)
    try:
        app.run_server(host=args.host, port=args.port, debug=args.debug)
    except OSError as exc:
        print(exc)
        print("It looks like Automappa is having trouble starting...")
        print(
            f"""Is port {args.port} available?
\nAre you running Automappa in another terminal?
\nPerhaps you are running another server on docker?
\tYou can check using `docker ps -a`.
\tYou can stop your container using `docker container stop <container-hash>`
\tYou can also remove your stopped containers with `docker rm <container-hash>`"""
        )
        exit(1)
