#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, Protocol

from dash.exceptions import PreventUpdate
from dash_extensions.enrich import DashProxy, Input, Output, dcc, html

import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd

from automappa.components import ids


class RefinementsDownloadButtonDataSource(Protocol):
    def get_refinements_dataframe(self, metagenome_id: int) -> pd.DataFrame:
        ...

    def has_user_refinements(self, metagenome_id: int) -> bool:
        ...


def render(app: DashProxy, source: RefinementsDownloadButtonDataSource) -> html.Div:
    @app.callback(
        Output(ids.REFINEMENTS_DOWNLOAD, "data"),
        [
            Input(ids.REFINEMENTS_DOWNLOAD_BUTTON, "n_clicks"),
            Input(ids.METAGENOME_ID_STORE, "data"),
        ],
    )
    def download_refinements(
        n_clicks: int,
        metagenome_id: int,
    ) -> Dict[str, "str | bool"]:
        if not n_clicks:
            raise PreventUpdate
        df = source.get_refinements_dataframe(metagenome_id)
        return dcc.send_data_frame(df.to_csv, "refinements.csv", index=False)

    @app.callback(
        Output(ids.REFINEMENTS_DOWNLOAD_BUTTON, "disabled"),
        Input(ids.METAGENOME_ID_STORE, "data"),
        Input(ids.MAG_REFINEMENTS_SAVE_BUTTON, "n_clicks"),
        Input(ids.REFINEMENTS_CLEARED_NOTIFICATION, "children"),
    )
    def disable_download_button(
        metagenome_id: int, save_btn: int, clear_btn_notification
    ) -> bool:
        return not source.has_user_refinements(metagenome_id)

    # Download Refinements Button
    return html.Div(
        [
            dmc.Button(
                "Download Refinements",
                id=ids.REFINEMENTS_DOWNLOAD_BUTTON,
                leftIcon=[DashIconify(icon="line-md:download-loop", height=25)],
                n_clicks=0,
                color="dark",
                variant="outline",
                fullWidth=False,
            ),
            dcc.Download(id=ids.REFINEMENTS_DOWNLOAD),
        ]
    )
