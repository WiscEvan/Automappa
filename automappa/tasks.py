#!/usr/bin/env python


import tempfile
import random

# import time
from typing import List
import pandas as pd

from geom_median.numpy import compute_geometric_median

from celery import Celery, group
from celery.utils.log import get_task_logger
from celery.result import AsyncResult

from Bio import SeqIO

from autometa.common import kmers

from automappa import settings

from automappa.utils.markers import get_marker_symbols
from automappa.utils.serializers import (
    get_metagenome_seqrecords,
    get_table,
    table_to_db,
)


queue = Celery(
    __name__, backend=settings.celery.backend_url, broker=settings.celery.broker_url
)
queue.config_from_object("automappa.conf.celeryconfig")

logger = get_task_logger(__name__)

if settings.server.debug:
    logger.debug(
        f"celery config:\n{queue.conf.humanize(with_defaults=False, censored=True)}"
    )


def get_job(job_id):
    """
    To be called from automappa web app.
    The job ID is passed and the celery job is returned.
    """
    return AsyncResult(job_id, app=queue)


@queue.task(bind=True)
def preprocess_marker_symbols(self, binning_table: str, markers_table: str) -> str:
    bin_df = get_table(binning_table, index_col="contig")
    markers_df = get_table(markers_table, index_col="contig")
    marker_symbols_df = get_marker_symbols(bin_df, markers_df).set_index("contig")
    marker_symbols_table = markers_table.replace("-markers", "-marker-symbols")
    table_to_db(marker_symbols_df, marker_symbols_table, index=True)
    return marker_symbols_table


# TODO: STRETCH GOALS
# Data loader [stretch...]
# CheckM annotation

# TODO
# Create 2d-scatterplot figure
# Marker symbols table
# kmer freq. analysis pipeline
# scatterplot 2-d embedding views


@queue.task(bind=True)
def count_kmer(self, metagenome_table: str, size: int = 5, cpus: int = None) -> str:
    records = get_metagenome_seqrecords(metagenome_table)
    # Uncomment next line to speed-up debugging...
    # FIXME: Comment out below:
    # records = random.sample(records, k=1_000)
    with tempfile.NamedTemporaryFile(mode="w") as tmp:
        SeqIO.write(records, tmp.name, "fasta")
        tmp.seek(0)
        counts = kmers.count(
            assembly=tmp.name,
            size=size,
            out=None,
            force=False,
            verbose=False,
            cpus=cpus,
        )
    logger.info("count finished")
    # Strip sample name of -metagenome tag (will append the rest for kmer-pipeline)
    counts_table = metagenome_table.replace("-metagenome", f"-{size}mers")
    table_to_db(counts, name=counts_table, index=True)
    return counts_table


@queue.task(bind=True)
def normalize_kmer(self, counts_table: str, norm_method: str) -> str:
    counts = get_table(counts_table, index_col="contig")
    norm_df = kmers.normalize(counts, method=norm_method)
    norm_table = f"{counts_table}-{norm_method}"
    table_to_db(norm_df, name=norm_table, index=True)
    return norm_table


@queue.task(bind=True)
def embed_kmer(self, norm_table: str, embed_method: str, n_jobs: int = 1) -> str:
    norm_df = get_table(norm_table, index_col="contig")
    # FIXME: Refactor renaming of embed_df.columns
    prev_kmer_params = norm_table.split("-", 1)[-1]
    embed_df = kmers.embed(
        # TODO: (on autometa[2.0.4] release): norm_df, method=embed_method, embed_dimensions=2, n_jobs=n_jobs
        norm_df,
        method=embed_method,
        embed_dimensions=2,
    ).rename(
        columns={
            "x_1": f"{prev_kmer_params}-{embed_method}_x_1",
            "x_2": f"{prev_kmer_params}-{embed_method}_x_2",
        }
    )
    embed_table = f"{norm_table}-{embed_method}"
    table_to_db(embed_df, name=embed_table, index=True)
    return embed_table


@queue.task(bind=True)
def aggregate_embeddings(self, embed_tables: List[str], table_name: str) -> str:
    df = pd.concat(
        [get_table(embed_table, index_col="contig") for embed_table in embed_tables],
        axis=1,
    )
    table_to_db(df, table_name, index=True)
    return table_name


def preprocess_embeddings(
    metagenome_table: str,
    cpus: int = 1,
    kmer_size: int = 5,
    norm_method: str = "am_clr",
    embed_methods: List[str] = ["bhsne", "densmap", "trimap", "umap"],
):
    embeddings_table = metagenome_table.replace("-metagenome", "-embeddings")
    kmer_pipeline = (
        count_kmer.s(metagenome_table, kmer_size, cpus)
        | normalize_kmer.s(norm_method)
        | group(embed_kmer.s(embed_method, cpus) for embed_method in embed_methods)
        | aggregate_embeddings.s(embeddings_table)
    )
    result = kmer_pipeline()
    # while not result.ready():
    #     time.sleep(1)
    # with open('graph.dot', 'w') as fh:
    #     result.parent.parent.parent.graph.to_dot(fh)
    logger.debug(result)
    return result


@queue.task
def preprocess_clusters_geom_medians(
    binning_table: str, cluster_col: str = "cluster", weight_col: str = "length"
) -> str:
    """Compute each cluster's (`cluster_col`) geometric median weighted by contig length (`weight_col`)

    Parameters
    ----------
    df : pd.DataFrame
        Table containing x_1 and x_2 coordinates and `cluster_col` from embedding
    cluster_col : str, optional
        Value to use for cluster column, by default "cluster"
    weight_col : str, optional
        Column to use for weighting the geometric median computation, by default 'length'

    Returns
    -------
    pd.DataFrame
        index=range(cluster_1, cluster_n), cols=[cluster_col, x_1, x_2, termination, weighted]
        `x_1` and `x_2` correspond to the computed geometric median values corresponding to the respective cluster.
        `termination` is the reason of termination passed from the `compute_geometric_median` function
        `weighted` denotes the value that was used for weighting the cluster's geometric median (`weight_col`)

    """
    df = get_table(binning_table, index_col="contig")
    medians = []
    for cluster, dff in df.groupby(cluster_col):
        points = dff[["x_1", "x_2"]].to_numpy()
        if weight_col:
            weights = dff[weight_col].to_numpy()
        out = compute_geometric_median(points=points, weights=weights)
        median = out.median
        medians.append(
            {
                cluster_col: cluster,
                "x_1": median[0],
                "x_2": median[1],
                "termination": out.termination,
                "weighted": weight_col,
            }
        )
    medians_df = pd.DataFrame(medians)
    medians_table = binning_table.replace("-binning", f"{cluster_col}-gmedians")
    table_to_db(medians_df, medians_table)
    return medians_table


@queue.task
def get_embedding_traces_df(embeddings_table: str) -> pd.DataFrame:
    # 1. Compute all embeddings for assembly...
    # 2. groupby cluster
    # 3. Extract k-mer size, norm method, embed method

    embed_traces = []
    for embed_method in ["trimap", "densmap", "bhsne", "umap", "sksne"]:
        traces_df = get_scattergl_traces(
            df, f"{embed_method}_x_1", f"{embed_method}_x_2", "cluster"
        )
        traces_df.rename(columns={"trace": embed_method}, inplace=True)
        embed_traces.append(traces_df)
    embed_traces_df = pd.concat(embed_traces, axis=1)
    return embed_traces_df


if __name__ == "__main__":
    pass
