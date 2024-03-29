#!/usr/bin/env python

from typing import Dict, List, Tuple, Union
import numpy as np
import pandas as pd
from dash.exceptions import PreventUpdate
from plotly import graph_objects as go


def taxonomy_sankey(df: pd.DataFrame) -> go.Figure:
    ranks = df.columns.tolist()
    n_ranks = len(ranks)
    label = []
    for rank in ranks:
        label.extend(df[rank].unique().tolist())
    source = []
    target = []
    value = []
    for rank in ranks:
        for rank_name, rank_df in df.groupby(rank):
            source_index = label.index(rank_name)
            next_rank_i = ranks.index(rank) + 1
            if next_rank_i >= len(ranks[:n_ranks]):
                continue
            next_rank = ranks[next_rank_i]
            # all source is from label rank name index
            for rank_n in rank_df[next_rank].unique():
                target_index = label.index(rank_n)
                value_count = len(rank_df[rank_df[next_rank] == rank_n])
                label.append(source_index)
                source.append(source_index)
                target.append(target_index)
                value.append(value_count)
    return go.Figure(
        go.Sankey(
            node=dict(
                pad=8,
                thickness=13,
                line=dict(width=0.3),
                label=label,
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
            ),
        ),
    )


def metric_boxplot(
    data: List[Tuple[str, pd.Series]],
    horizontal: bool = False,
    boxmean: Union[bool, str] = True,
) -> go.Figure:
    """Generate go.Figure of go.Box traces for provided `metric`.

    Parameters
    ----------
    data : List[Tuple[str,pd.Series]]
        MAG annotations dataframe
    horizontal : bool, optional
        Whether to generate horizontal or vertical boxplot traces in the figure.
    boxmean : Union[bool,str], optional
        method to style mean and standard deviation or only to display quantiles with median.
        choices include False/True and 'sd'

    Returns
    -------
    go.Figure
        Figure of boxplot traces using provided parameters and aesthetics

    Raises
    ------
    PreventUpdate
        No metrics were provided to generate traces.
    """
    if not data:
        raise PreventUpdate
    traces = []
    for metric, series in data:
        if horizontal:
            trace = go.Box(x=series, name=metric, boxmean=boxmean)
        else:
            trace = go.Box(y=series, name=metric, boxmean=boxmean)
        traces.append(trace)
    return go.Figure(data=traces)


def metric_barplot(
    data: Tuple[str, List[float], List[float]],
    horizontal: bool = False,
) -> go.Figure:
    if not data:
        raise PreventUpdate
    name, x, y = data
    orientation = "h" if horizontal else "v"
    trace = go.Bar(x=x, y=y, orientation=orientation, name=name)
    return go.Figure([trace])


def format_axis_title(axis_title: str) -> str:
    """Format axis title depending on title text. Converts embed methods to uppercase then x_dim.

    Parameters
    ----------
    axis_title : str
        axis title to format (used from `xaxis_column` and `yaxis_column` in `scatterplot_2d_figure_callback`)

    Returns
    -------
    str
        formatted axis title
    """
    if "_x_" in axis_title:
        method_titles = {
            "bhsne": "BH-tSNE",
            "sksne": "(sklearn) BH-tSNE",
            "umap": "UMAP",
            "trimap": "TriMap",
            "densmap": "DensMap",
        }
        # {kmer_size}mers-{norm_method}-{embed_method}_x_{1,2}
        mers, norm_method, embed_method_embed_dim = axis_title.split("-")
        norm_method_titles = {"am_clr": "CLR", "ilr": "ILR"}
        norm_method = norm_method_titles.get(norm_method, norm_method.upper())
        embed_method, embed_dim = embed_method_embed_dim.split("_", 1)
        embed_method = method_titles.get(embed_method, embed_method.upper())
        kmer_size = mers.replace("mers", "")
        # formatted_axis_title = f"(k={kmer_size}, norm={norm_method}) {embed_method} {embed_dim}"
        formatted_axis_title = embed_dim
    elif "_" in axis_title:
        metagenome_metadata_titles = {"gc_content": "GC Content"}
        col_list = axis_title.split("_")
        metadata_title = " ".join(col.upper() for col in col_list)
        formatted_axis_title = metagenome_metadata_titles.get(
            axis_title, metadata_title
        )
    else:
        formatted_axis_title = axis_title.title()
    return formatted_axis_title


def get_hovertemplate_and_customdata_cols(
    x_axis: str, y_axis: str
) -> Tuple[str, List[str]]:
    # Hovertemplate
    x_hover_title = format_axis_title(x_axis)
    y_hover_title = format_axis_title(y_axis)
    text_hover_label = "Contig: %{text}"
    coverage_label = "Coverage: %{customdata[0]:.2f}"
    gc_content_label = "GC%: %{customdata[1]:.2f}"
    length_label = "Length: %{customdata[2]:,} bp"
    x_hover_label = f"{x_hover_title}: " + "%{x:.2f}"
    y_hover_label = f"{y_hover_title}: " + "%{y:.2f}"
    hovertemplate = "<br>".join(
        [
            text_hover_label,
            coverage_label,
            gc_content_label,
            length_label,
            x_hover_label,
            y_hover_label,
        ]
    )
    metadata_cols = ["coverage", "gc_content", "length"]
    return hovertemplate, metadata_cols


def get_scattergl_traces(
    df: pd.DataFrame,
    x_axis: str,
    y_axis: str,
    color_by_col: str = "cluster",
    fillna: str = "unclustered",
) -> pd.DataFrame:
    """Generate scattergl 2D traces from `df` with index of `contig`, x and y corresponding to `x_axis` and `y_axis`, respectively with traces
    being grouped by the `color_by_col`. If there exists `nan` values in the `color_by_col`, these may be filled with the value used in `fillna`.

    Parameters
    ----------
    df : pd.DataFrame
        * `index` = `contigs`

        binning table of columns:

        * f`{embed_method}_x_1`
        * f`{embed_method}_x_2`
        * `gc_content`
        * `coverage`
        * `length`
        * `colory_by_col` (commonly used column is `cluster`)

    x_axis : str
        column to use to supply to the `x` argument in `Scattergl(x=...)`
    y_axis : str
        column to use to supply to the `y` argument in `Scattergl(y=...)`
    color_by_col : str, by default "cluster"
        Column with which to group the traces
    fillna : str, optional
        value to replace `nan` in `color_by_col`, by default "unclustered"

    Returns
    -------
    pd.DataFrame
        index=`color_by_col`, column=`trace`
    """
    hovertemplate, metadata_cols = get_hovertemplate_and_customdata_cols(
        x_axis=x_axis, y_axis=y_axis
    )
    traces = []
    metadata_cols = [col for col in metadata_cols if col in df.columns]
    df = df.fillna(value={color_by_col: fillna})
    for color_col_name in df[color_by_col].unique():
        dff = df.loc[df[color_by_col].eq(color_col_name)]
        customdata = dff[metadata_cols] if metadata_cols else []
        trace = go.Scattergl(
            x=dff[x_axis],
            y=dff[y_axis],
            customdata=customdata,
            text=dff.index,
            mode="markers",
            opacity=0.85,
            hovertemplate=hovertemplate,
            name=color_col_name,
        )
        traces.append({color_by_col: color_col_name, "trace": trace})
    return pd.DataFrame(traces).set_index(color_by_col)


def get_embedding_traces_df(df: pd.DataFrame) -> pd.DataFrame:
    embed_traces = []
    for embed_method in ["trimap", "densmap", "bhsne", "umap", "sksne"]:
        traces_df = get_scattergl_traces(
            df, f"{embed_method}_x_1", f"{embed_method}_x_2", "cluster"
        )
        traces_df.rename(columns={"trace": embed_method}, inplace=True)
        embed_traces.append(traces_df)
    embed_traces_df = pd.concat(embed_traces, axis=1)
    return embed_traces_df


def get_scatterplot_2d(
    df: pd.DataFrame,
    x_axis: str,
    y_axis: str,
    # embed_method: str,
    color_by_col: str = "cluster",
    fillna: str = "unclustered",
) -> go.Figure:
    """Generate `go.Figure` of scattergl 2D traces

    Parameters
    ----------
    df : pd.DataFrame
        _description_
    x_axis : str
        _description_
    y_axis : str
        _description_
    embed_method : str
        _description_
    color_by_col : str, optional
        _description_, by default "cluster"
    fillna : str, optional
        _description_, by default "unclustered"

    Returns
    -------
    go.Figure
        _description_
    """
    layout = go.Layout(
        legend=dict(x=1, y=1),
        margin=dict(r=50, b=50, l=50, t=50),
        hovermode="closest",
        clickmode="event+select",
        height=600,
        width="100%",
    )
    fig = go.Figure(layout=layout)
    traces_df = get_scattergl_traces(
        df,
        x_axis=x_axis,
        y_axis=y_axis,
        color_by_col=color_by_col,
        fillna=fillna,
    )
    # TODO: Update function to use embed_traces_df...
    fig.add_traces(traces_df.trace.tolist())
    return fig


def get_scatterplot_3d(
    df: pd.DataFrame,
    x_axis: str,
    y_axis: str,
    z_axis: str,
    color_by_col: str,
) -> go.Figure:
    """Create go.Figure from `df`

    Parameters
    ----------
    df : pd.DataFrame
        index_col=[contig], cols=[`x_axis`, `y_axis`, `z_axis`]
    x_axis : str
        continuous column for x-axis
    y_axis : str
        continuous column for y-axis
    z_axis : str
        continuous column for z-axis
    color_by_col : str
        categorical column for color-by-col

    Returns
    -------
    go.Figure
        _description_
    """

    def marker_size_scaler(x: pd.DataFrame, scale_by: str = "length") -> int:
        x_min_scaler = x[scale_by] - x[scale_by].min()
        x_max_scaler = x[scale_by].max() - x[scale_by].min()
        if not x_max_scaler:
            # Protect Division by 0
            x_ceil = np.ceil(x_min_scaler / x_max_scaler + 1)
        else:
            x_ceil = np.ceil(x_min_scaler / x_max_scaler)
        x_scaled = x_ceil * 2 + 4
        return x_scaled

    x_axis_title = format_axis_title(x_axis)
    y_axis_title = format_axis_title(y_axis)
    z_axis_title = format_axis_title(z_axis)
    fig = go.Figure(
        layout=go.Layout(
            scene=dict(
                xaxis=dict(title=x_axis_title),
                yaxis=dict(title=y_axis_title),
                zaxis=dict(title=z_axis_title),
            ),
            legend={"x": 1, "y": 1},
            autosize=True,
            margin=dict(r=0, b=0, l=0, t=25),
            hovermode="closest",
        )
    )
    x_hover_label = f"{x_axis_title}: " + "%{x:.2f}"
    y_hover_label = f"{y_axis_title}: " + "%{y:.2f}"
    z_hover_label = f"{z_axis_title}: " + "%{z:.2f}"
    text_hover_label = "Contig: %{text}"
    hovertemplate = "<br>".join(
        [text_hover_label, z_hover_label, x_hover_label, y_hover_label]
    )
    for color_by_col_val, dff in df.groupby(color_by_col):
        trace = go.Scatter3d(
            x=dff[x_axis],
            y=dff[y_axis],
            z=dff[z_axis],
            text=dff.index,
            mode="markers",
            marker={
                "size": df.assign(normLen=marker_size_scaler)["normLen"],
                "line": {"width": 0.1, "color": "black"},
            },
            opacity=0.45,
            hoverinfo="all",
            hovertemplate=hovertemplate,
            name=color_by_col_val,
        )
        fig.add_trace(trace)
    fig.update_layout(legend_title_text=color_by_col.title())
    return fig


if __name__ == "__main__":
    pass
