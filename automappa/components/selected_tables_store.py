# -*- coding: utf-8 -*-

import itertools
import logging
from typing import Literal
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import Input, Output, DashProxy, Serverside, dcc
from automappa.data.source import SampleTables
from automappa.components import ids
from automappa.tasks import (
    preprocess_clusters_geom_medians,
    preprocess_embeddings,
    preprocess_marker_symbols,
)

logger = logging.getLogger(__name__)


def render(
    app: DashProxy,
    storage_type: Literal["memory", "session", "local"] = "session",
    clear_data: bool = False,
) -> dcc.Store:
    @app.callback(
        Output(ids.SELECTED_TABLES_STORE, "data"),
        [
            Input(ids.REFINE_MAGS_BUTTON, "n_clicks"),
            Input(ids.BINNING_SELECT, "value"),
            Input(ids.MARKERS_SELECT, "value"),
            Input(ids.METAGENOME_SELECT, "value"),
        ],
    )
    def on_refine_mags_button_click(
        n, binning_select_value, markers_select_value, metagenome_select_value
    ):
        if n is None:
            raise PreventUpdate
        tables_dict = {}
        if metagenome_select_value is not None:
            tables_dict["metagenome"] = {"id": metagenome_select_value}
        if binning_select_value is not None:
            tables_dict.update(
                {
                    "binning": {"id": binning_select_value},
                    "refinements": {
                        "id": binning_select_value.replace("-binning", "-refinement")
                    },
                }
            )
        if markers_select_value is not None:
            tables_dict["markers"] = {"id": markers_select_value}
        sample = SampleTables(**tables_dict)
        # BEGIN Queueing tasks from annotations...
        # TODO: Refactor to separate bg-task submission?
        # Show table of running tasks for user to monitor...
        if sample.binning and sample.markers:
            marker_symbols_task = preprocess_marker_symbols.delay(
                sample.binning.id, sample.markers.id
            )
        if sample.metagenome:
            embedding_tasks = []
            # kmer_sizes = set([kmer_table.size for kmer_table in sample.kmers])
            kmer_sizes = set([5])
            # norm_methods = set([kmer_table.norm_method for kmer_table in sample.kmers])
            norm_methods = set(["am_clr"])
            embed_methods = set(
                [kmer_table.embed_method for kmer_table in sample.kmers]
            )
            embed_methods = ["umap", "densmap", "bhsne"]
            for kmer_size, norm_method in itertools.product(kmer_sizes, norm_methods):
                embeddings_task = preprocess_embeddings(
                    metagenome_table=sample.metagenome.id,
                    kmer_size=kmer_size,
                    norm_method=norm_method,
                    embed_methods=embed_methods,
                )
                embedding_tasks.append(embeddings_task)
        if sample.binning:
            clusters_geom_medians_task = preprocess_clusters_geom_medians.delay(
                sample.binning.id, "cluster"
            )
        # df = pd.DataFrame([get_task(t.id) for t in [marker_symbols_task, clusters_geom_medians_task, *embedding_tasks]])
        # TODO: Monitor tasks progress with dcc.Interval in another callback...
        # logger.debug(df)
        return Serverside(sample)

    return dcc.Store(
        id=ids.SELECTED_TABLES_STORE,
        storage_type=storage_type,
        clear_data=clear_data,
    )