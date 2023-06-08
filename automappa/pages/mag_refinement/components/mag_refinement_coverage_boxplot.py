#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, Input, Output, dcc, html
from plotly import graph_objects as go

from automappa.data.source import SampleTables
from automappa.utils.figures import (
    metric_boxplot,
)

from automappa.components import ids


def render(app: DashProxy) -> html.Div:
    @app.callback(
        Output(ids.MAG_REFINEMENT_COVERAGE_BOXPLOT, "figure"),
        [
            Input(ids.SELECTED_TABLES_STORE, "data"),
            Input(ids.SCATTERPLOT_2D, "selectedData"),
        ],
    )
    def subset_coverage_boxplot_by_scatterplot_selection(
        sample: SampleTables,
        selected_data: Dict[str, List[Dict[str, str]]],
    ) -> go.Figure:
        if not selected_data:
            raise PreventUpdate
        df = sample.binning.table
        contigs = {point["text"] for point in selected_data["points"]}
        df = df.loc[df.index.isin(contigs)]
        fig = metric_boxplot(df, metrics=["coverage"], boxmean="sd")
        return fig

    return html.Div(
        [
            html.Label("Figure 4: MAG Refinement Coverage Boxplot"),
            dcc.Loading(
                id=ids.LOADING_MAG_REFINEMENT_COVERAGE_BOXPLOT,
                children=[
                    dcc.Graph(
                        id=ids.MAG_REFINEMENT_COVERAGE_BOXPLOT,
                        config={"displayModeBar": False, "displaylogo": False},
                    )
                ],
                type="dot",
                color="#646569",
            ),
        ]
    )
