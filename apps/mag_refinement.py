# -*- coding: utf-8 -*-

from typing import Dict, List
import pandas as pd
import dash_daq as daq
from dash import dcc, html
from dash.dash_table import DataTable
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame
import dash_bootstrap_components as dbc
from app import app
from plotly import graph_objects as go
import plotly.io as pio


from automappa.figures import (
    get_scatterplot_2d,
    taxonomy_sankey,
    get_scatterplot_3d,
    metric_boxplot,
)


pio.templates.default = "plotly_white"


########################################################################
# HIDDEN DIV to store refinement information
# ######################################################################

refinements_clusters_store = dcc.Store(
    id="refinements-clusters-store", storage_type="session"
)

########################################################################
# COMPONENTS: OFFCANVAS SETTINGS
# ######################################################################


color_by_col_dropdown = [
    html.Label("Contigs colored by:"),
    dcc.Dropdown(
        id="color-by-column",
        options=[],
        value="cluster",
        clearable=False,
    ),
]

scatterplot_2d_xaxis_dropdown = [
    html.Label("X-axis:"),
    dcc.Dropdown(
        id="x-axis-2d",
        options=[
            {"label": "X_1", "value": "x_1"},
            {"label": "Coverage", "value": "coverage"},
            {"label": "GC%", "value": "gc_content"},
            {"label": "Length", "value": "length"},
        ],
        value="x_1",
        clearable=False,
    ),
]

scatterplot_2d_yaxis_dropdown = [
    html.Label("Y-axis:"),
    dcc.Dropdown(
        id="y-axis-2d",
        options=[
            {"label": "X_2", "value": "x_2"},
            {"label": "Coverage", "value": "coverage"},
            {"label": "GC%", "value": "gc_content"},
            {"label": "Length", "value": "length"},
        ],
        value="x_2",
        clearable=False,
    ),
]

scatterplot_3d_zaxis_dropdown = [
    html.Label("Z-axis:"),
    dcc.Dropdown(
        id="scatterplot-3d-zaxis-dropdown",
        options=[
            {"label": "Coverage", "value": "coverage"},
            {"label": "GC%", "value": "gc_content"},
            {"label": "Length", "value": "length"},
        ],
        value="coverage",
        clearable=False,
    ),
]

taxa_rank_dropdown = [
    html.Label("Distribute taxa by rank:"),
    dcc.Dropdown(
        id="taxonomy-distribution-dropdown",
        options=[
            {"label": "Class", "value": "class"},
            {"label": "Order", "value": "order"},
            {"label": "Family", "value": "family"},
            {"label": "Genus", "value": "genus"},
            {"label": "Species", "value": "species"},
        ],
        value="species",
        clearable=False,
    ),
]

# add show-legend-toggle
scatterplot_2d_legend_toggle = daq.ToggleSwitch(
    id="show-legend-toggle",
    size=40,
    color="#c5040d",
    label="Legend",
    labelPosition="top",
    vertical=False,
    value=True,
)

# Tooltip for info on store selections behavior
hide_selections_tooltip = dbc.Tooltip(
    'Toggling this to the "on" state will hide your manually-curated MAG refinement groups',
    target="hide-selections-toggle",
    placement="left",
)

# add hide selection toggle
hide_selections_toggle = daq.ToggleSwitch(
    id="hide-selections-toggle",
    size=40,
    color="#c5040d",
    label="Hide MAG Refinements",
    labelPosition="left",
    vertical=False,
    value=False,
)

# Tooltip for info on store selections behavior
save_selections_tooltip = dbc.Tooltip(
    """Toggling this to the \"on\" state while selecting contigs (or while contigs are selected)
    will save the selected contigs to their own MAG refinement group
    """,
    target="save-selections-toggle",
    placement="left",
)

# add save selection toggle
save_selections_toggle = daq.ToggleSwitch(
    id="save-selections-toggle",
    size=40,
    color="#c5040d",
    label="Select MAG Refinements",
    labelPosition="left",
    vertical=False,
    value=False,
)

# Scatterplot 3D Legend Toggle
scatterplot_3d_legend_toggle = daq.ToggleSwitch(
    id="scatterplot-3d-legend-toggle",
    size=40,
    color="#c5040d",
    label="Legend",
    labelPosition="top",
    vertical=False,
    value=True,
)

# Download Refinements Button
binning_refinements_download_button = [
    dbc.Button(
        "Download Refinements",
        id="refinements-download-button",
        n_clicks=0,
        color="primary",
    ),
    Download(id="refinements-download"),
]

# Summarize Refinements Button
binning_refinements_summary_button = [
    dbc.Button(
        "Summarize Refinements",
        id="refinements-summary-button",
        n_clicks=0,
        color="primary",
    ),
]


refinement_settings_offcanvas = dbc.Offcanvas(
    [
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        dbc.Row(
                            [
                                dbc.Col(color_by_col_dropdown),
                                dbc.Col(scatterplot_2d_legend_toggle),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(scatterplot_2d_xaxis_dropdown),
                                dbc.Col(scatterplot_2d_yaxis_dropdown),
                            ]
                        ),
                    ],
                    title="Figure 1: 2D Metagenome Overview",
                ),
                dbc.AccordionItem(
                    [
                        dbc.Row(
                            [
                                dbc.Col(scatterplot_3d_zaxis_dropdown),
                                dbc.Col(scatterplot_3d_legend_toggle),
                            ]
                        ),
                    ],
                    title="Figure 2: 3D Metagenome Overview",
                ),
                dbc.AccordionItem(
                    [
                        dbc.Col(taxa_rank_dropdown),
                    ],
                    title="Figure 3: Taxonomic Distribution",
                ),
            ],
            start_collapsed=True,
            flush=True,
        ),
        dbc.Row(
            [
                dbc.Col([save_selections_tooltip, save_selections_toggle]),
                dbc.Col([hide_selections_tooltip, hide_selections_toggle]),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(binning_refinements_download_button),
                dbc.Col(binning_refinements_summary_button),
            ]
        ),
    ],
    id="refinement-settings-offcanvas",
    title="Refinement Settings",
    is_open=False,
    placement="end",
    scrollable=True,
)

refinement_settings_button = [
    dbc.Button("Refinement Settings", id="refinement-settings-button", n_clicks=0),
    refinement_settings_offcanvas,
]

########################################################################
# COMPONENTS: FIGURES AND TABLES
# ######################################################################

# Add metrics as alerts using MIMAG standards
# (success) alert --> passing thresholds (completeness >= 90%, contamination <= 5%)
# (warning) alert --> within 10% thresholds, e.g. (completeness >=80%, contam. <= 15%)
# (danger)  alert --> failing thresholds (completeness less than 80%, contam. >15%)

mag_metrics_table = [
    html.Label("Table 1. MAG Marker Metrics"),
    dcc.Loading(
        id="loading-mag-metrics-datatable",
        children=[html.Div(id="mag-metrics-datatable")],
        type="dot",
        color="#646569",
    ),
]

scatterplot_2d = [
    html.Label("Figure 1: 2D Metagenome Overview"),
    dcc.Loading(
        id="loading-scatterplot-2d",
        children=[
            dcc.Graph(
                id="scatterplot-2d",
                clear_on_unhover=True,
                config={"displayModeBar": True, "displaylogo": False},
            )
        ],
        type="graph",
    ),
]

scatterplot_3d = [
    html.Label("Figure 2: 3D Metagenome Overview"),
    dcc.Loading(
        id="loading-scatterplot-3d",
        children=[
            dcc.Graph(
                id="scatterplot-3d",
                clear_on_unhover=True,
                config={
                    "toImageButtonOptions": dict(
                        format="svg",
                        filename="scatter3dPlot.autometa.binning",
                    ),
                    "displayModeBar": True,
                    "displaylogo": False,
                },
            )
        ],
        type="graph",
    ),
]


taxonomy_figure = [
    html.Label("Figure 3: Taxonomic Distribution"),
    dcc.Loading(
        id="loading-taxonomy-distribution",
        children=[
            dcc.Graph(
                id="taxonomy-distribution",
                config={
                    "displayModeBar": False,
                    "displaylogo": False,
                    "staticPlot": True,
                },
            )
        ],
        type="graph",
    ),
]

mag_refinement_coverage_boxplot = [
    html.Label("Figure 4: MAG Refinement Coverage Boxplot"),
    dcc.Loading(
        id="loading-mag-refinement-coverage-boxplot",
        children=[
            dcc.Graph(
                id="mag-refinement-coverage-boxplot",
                config={"displayModeBar": False, "displaylogo": False},
            )
        ],
        type="dot",
        color="#646569",
    ),
]

mag_refinement_gc_content_boxplot = [
    html.Label("Figure 5: MAG Refinement GC Content Boxplot"),
    dcc.Loading(
        id="loading-mag-refinement-gc-content-boxplot",
        children=[
            dcc.Graph(
                id="mag-refinement-gc-content-boxplot",
                config={"displayModeBar": False, "displaylogo": False},
            )
        ],
        type="dot",
        color="#0479a8",
    ),
]

mag_refinement_length_boxplot = [
    html.Label("Figure 6: MAG Refinement Length Boxplot"),
    dcc.Loading(
        id="loading-mag-refinement-length-boxplot",
        children=[
            dcc.Graph(
                id="mag-refinement-length-boxplot",
                config={"displayModeBar": False, "displaylogo": False},
            )
        ],
        type="dot",
        color="#0479a8",
    ),
]


refinements_table = dcc.Loading(
    id="loading-refinements-table",
    children=[html.Div(id="refinements-table")],
    type="circle",
    color="#646569",
)


########################################################################
# LAYOUT
# ######################################################################

# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/layout/
# For best results, make sure you adhere to the following two rules when constructing your layouts:
#
# 1. Only use Row and Col inside a Container.
# 2. The immediate children of any Row component should always be Col components.
# 3. Your content should go inside the Col components.

layout = dbc.Container(
    children=[
        dbc.Row([dbc.Col(refinements_clusters_store)]),
        dbc.Row([dbc.Col(refinement_settings_button, width=4)]),
        dbc.Row([dbc.Col(scatterplot_2d, width=9), dbc.Col(mag_metrics_table, width=3)]),
        # TODO: Add MAG assembly metrics table
        dbc.Row([dbc.Col(taxonomy_figure, width=9), dbc.Col(scatterplot_3d)]),
        dbc.Row(
            [
                dbc.Col(mag_refinement_coverage_boxplot),
                dbc.Col(mag_refinement_gc_content_boxplot),
                dbc.Col(mag_refinement_length_boxplot),
            ]
        ),
        dbc.Row([dbc.Col(refinements_table, width=12)]),
    ],
    fluid=True,
)


########################################################################
# CALLBACKS
# ######################################################################


@app.callback(
    Output("refinement-settings-offcanvas", "is_open"),
    Input("refinement-settings-button", "n_clicks"),
    [State("refinement-settings-offcanvas", "is_open")],
)
def toggle_offcanvas(n1: int, is_open: bool) -> bool:
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("color-by-column", "options"), [Input("metagenome-annotations", "children")]
)
def color_by_column_options_callback(annotations_json: "str | None"):
    df = pd.read_json(annotations_json, orient="split")
    return [
        {"label": col.title().replace("_", " "), "value": col}
        for col in df.columns
        if df[col].dtype.name not in {"float64", "int64"} and col != "contig"
    ]


@app.callback(
    Output("mag-metrics-datatable", "children"),
    [
        Input("kingdom-markers", "children"),
        Input("scatterplot-2d", "selectedData"),
    ],
)
def update_mag_metrics_datatable_callback(
    markers_json: "str | None", selected_contigs: Dict[str, List[Dict[str, str]]]
) -> DataTable:
    markers_df = pd.read_json(markers_json, orient="split").set_index("contig")
    if selected_contigs:
        contigs = {point["text"] for point in selected_contigs["points"]}
        selected_contigs_count = len(contigs)
        markers_df = markers_df.loc[markers_df.index.isin(contigs)]

    expected_markers_count = markers_df.shape[1]

    pfam_counts = markers_df.sum()
    if pfam_counts.empty:
        total_markers = 0
        single_copy_marker_count = 0
        markers_present_count = 0
        redundant_markers_count = 0
        marker_set_count = 0
        completeness = "NA"
        purity = "NA"
    else:
        total_markers = pfam_counts.sum()
        single_copy_marker_count = pfam_counts.eq(1).sum()
        markers_present_count = pfam_counts.ge(1).sum()
        redundant_markers_count = pfam_counts.gt(1).sum()
        completeness = markers_present_count / expected_markers_count * 100
        purity = single_copy_marker_count / markers_present_count * 100
        marker_set_count = total_markers / expected_markers_count

    marker_contig_count = markers_df.sum(axis=1).ge(1).sum()
    single_marker_contig_count = markers_df.sum(axis=1).eq(1).sum()
    multi_marker_contig_count = markers_df.sum(axis=1).gt(1).sum()
    metrics_data = {
        "Expected Markers": expected_markers_count,
        "Total Markers": total_markers,
        "Redundant-Markers": redundant_markers_count,
        "Markers Count": markers_present_count,
        "Marker Sets (Total / Expected)": marker_set_count,
        "Marker-Containing Contigs": marker_contig_count,
        "Multi-Marker Contigs": multi_marker_contig_count,
        "Single-Marker Contigs": single_marker_contig_count,
    }
    if selected_contigs:
        metrics_data.update(
            {
                "Contigs": selected_contigs_count,
                "Completeness (%)": completeness,
                "Purity (%)": purity,
            }
        )

    metrics_df = pd.DataFrame([metrics_data]).T
    metrics_df.rename(columns={0: "Value"}, inplace=True)
    metrics_df.index.name = "MAG Metric"
    metrics_df.reset_index(inplace=True)
    metrics_df = metrics_df.round(2)
    return DataTable(
        data=metrics_df.to_dict("records"),
        columns=[{"name": col, "id": col} for col in metrics_df.columns],
        style_cell={"textAlign": "center"},
        # TODO: style completeness and purity cells to MIMAG standards as mentioned above
        style_cell_conditional=[{"if": {"column_id": "contig"}, "textAlign": "right"}],
    )


@app.callback(
    Output("taxonomy-distribution", "figure"),
    [
        Input("metagenome-annotations", "children"),
        Input("scatterplot-2d", "selectedData"),
        Input("taxonomy-distribution-dropdown", "value"),
    ],
)
def taxonomy_distribution_figure_callback(
    annotations: "str | None",
    selected_contigs: Dict[str, List[Dict[str, str]]],
    selected_rank: str,
) -> go.Figure:
    df = pd.read_json(annotations, orient="split")
    if selected_contigs:
        ctg_list = {point["text"] for point in selected_contigs["points"]}
        df = df[df.contig.isin(ctg_list)]
    fig = taxonomy_sankey(df, selected_rank=selected_rank)
    return fig


@app.callback(
    Output("scatterplot-3d", "figure"),
    [
        Input("metagenome-annotations", "children"),
        Input("scatterplot-3d-zaxis-dropdown", "value"),
        Input("scatterplot-3d-legend-toggle", "value"),
        Input("color-by-column", "value"),
        Input("scatterplot-2d", "selectedData"),
    ],
)
def scatterplot_3d_figure_callback(
    annotations: "str | None",
    z_axis: str,
    show_legend: bool,
    color_by_col: str,
    selected_contigs: Dict[str, List[Dict[str, str]]],
) -> go.Figure:
    df = pd.read_json(annotations, orient="split")
    color_by_col = "phylum" if color_by_col not in df.columns else color_by_col
    if not selected_contigs:
        contigs = df.contig.tolist()
    else:
        contigs = {point["text"] for point in selected_contigs["points"]}
    # Subset DataFrame by selected contigs
    df = df[df.contig.isin(contigs)]
    if color_by_col == "cluster":
        # Categoricals for binning
        df[color_by_col] = df[color_by_col].fillna("unclustered")
    else:
        # Other possible categorical columns all relate to taxonomy
        df[color_by_col] = df[color_by_col].fillna("unclassified")
    fig = get_scatterplot_3d(
        df=df,
        x_axis="x_1",
        y_axis="x_2",
        z_axis=z_axis,
        show_legend=show_legend,
        color_by_col=color_by_col,
    )
    return fig


@app.callback(
    Output("scatterplot-2d", "figure"),
    [
        Input("metagenome-annotations", "children"),
        Input("refinements-clusters-store", "data"),
        Input("x-axis-2d", "value"),
        Input("y-axis-2d", "value"),
        Input("show-legend-toggle", "value"),
        Input("color-by-column", "value"),
        Input("hide-selections-toggle", "value"),
    ],
)
def scatterplot_2d_figure_callback(
    annotations: "str | None",
    refinement: "str | None",
    xaxis_column: str,
    yaxis_column: str,
    show_legend: bool,
    color_by_col: str,
    hide_selection_toggle: bool,
) -> go.Figure:
    df = pd.read_json(annotations, orient="split").set_index("contig")
    color_by_col = "phylum" if color_by_col not in df.columns else color_by_col
    # Subset metagenome-annotations by selections iff selections have been made
    df[color_by_col] = df[color_by_col].fillna("unclustered")
    if hide_selection_toggle:
        refine_df = pd.read_json(refinement, orient="split").set_index("contig")
        refine_cols = [col for col in refine_df.columns if "refinement" in col]
        if refine_cols:
            refine_col = refine_cols.pop()
            # Retrieve only contigs that have already been refined...
            refined_contigs_index = refine_df[
                refine_df[refine_col].str.contains("refinement")
            ].index
            df.drop(refined_contigs_index, axis="index", inplace=True, errors="ignore")
    fig = get_scatterplot_2d(
        df,
        x_axis=xaxis_column,
        y_axis=yaxis_column,
        show_legend=show_legend,
        color_by_col=color_by_col,
    )
    return fig


@app.callback(
    Output("mag-refinement-coverage-boxplot", "figure"),
    [
        Input("metagenome-annotations", "children"),
        Input("scatterplot-2d", "selectedData"),
    ],
)
def mag_summary_coverage_boxplot_callback(
    df_json: "str | None", selected_data: Dict[str, List[Dict[str, str]]]
) -> go.Figure:
    df = pd.read_json(df_json, orient="split")
    if not selected_data:
        raise PreventUpdate
    contigs = {point["text"] for point in selected_data["points"]}
    df = df.loc[df.contig.isin(contigs)]
    fig = metric_boxplot(df, metrics=["coverage"], boxmean="sd")
    fig.update_layout(hovermode="y")
    return fig


@app.callback(
    Output("mag-refinement-gc-content-boxplot", "figure"),
    [
        Input("metagenome-annotations", "children"),
        Input("scatterplot-2d", "selectedData"),
    ],
)
def mag_summary_gc_content_boxplot_callback(
    df_json: "str | None", selected_data: Dict[str, List[Dict[str, str]]]
) -> go.Figure:
    df = pd.read_json(df_json, orient="split")
    if not selected_data:
        raise PreventUpdate
    contigs = {point["text"] for point in selected_data["points"]}
    df = df.loc[df.contig.isin(contigs)]
    fig = metric_boxplot(df, metrics=["gc_content"], boxmean="sd")
    return fig


@app.callback(
    Output("mag-refinement-length-boxplot", "figure"),
    [
        Input("metagenome-annotations", "children"),
        Input("scatterplot-2d", "selectedData"),
    ],
)
def mag_summary_length_boxplot_callback(
    df_json: "str | None", selected_data: Dict[str, List[Dict[str, str]]]
) -> go.Figure:
    df = pd.read_json(df_json, orient="split")
    if not selected_data:
        raise PreventUpdate
    contigs = {point["text"] for point in selected_data["points"]}
    df = df.loc[df.contig.isin(contigs)]
    fig = metric_boxplot(df, metrics=["length"])
    return fig


@app.callback(
    Output("refinements-table", "children"),
    [Input("refinements-clusters-store", "data")],
)
def refinements_table_callback(df: "str | None") -> DataTable:
    df = pd.read_json(df, orient="split")
    return DataTable(
        id="refinements-datatable",
        data=df.to_dict("records"),
        columns=[{"name": col, "id": col} for col in df.columns],
        style_cell={"textAlign": "center"},
        style_cell_conditional=[{"if": {"column_id": "contig"}, "textAlign": "right"}],
        virtualization=True,
    )


@app.callback(
    Output("refinements-datatable", "data"),
    [
        Input("scatterplot-2d", "selectedData"),
        Input("refinements-clusters-store", "data"),
    ],
)
def update_refinements_table(
    selected_data: Dict[str, List[Dict[str, str]]], refinements: "str | None"
) -> "str | None":
    df = pd.read_json(refinements, orient="split")
    if not selected_data:
        return df.to_dict("records")
    contigs = {point["text"] for point in selected_data["points"]}
    return df[df.contig.isin(contigs)].to_dict("records")


@app.callback(
    Output("refinements-download", "data"),
    [
        Input("refinements-download-button", "n_clicks"),
        Input("refinements-clusters-store", "data"),
    ],
)
def download_refinements(
    n_clicks: int, curated_mags: "str | None"
) -> Dict[str, "str | bool"]:
    if not n_clicks:
        raise PreventUpdate
    df = pd.read_json(curated_mags, orient="split")
    return send_data_frame(df.to_csv, "refinements.csv", index=False)


@app.callback(
    Output("refinements-clusters-store", "data"),
    [
        Input("scatterplot-2d", "selectedData"),
        Input("refinement-data", "children"),
        Input("save-selections-toggle", "value"),
    ],
    [State("refinements-clusters-store", "data")],
)
def store_binning_refinement_selections(
    selected_data: Dict[str, List[Dict[str, str]]],
    refinement_data: "str | None",
    save_toggle: bool,
    intermediate_selections: "str | None",
) -> "str | None":
    if not selected_data and not intermediate_selections:
        # We first load in our binning information for refinement
        # Note: this callback should trigger on initial load
        # TODO: Could also remove and construct dataframes from selected contigs
        # Then perform merge when intermediate selections are downloaded.
        bin_df = pd.read_json(refinement_data, orient="split")
        if "cluster" not in bin_df.columns:
            bin_df["cluster"] = "unclustered"
        else:
            bin_df["cluster"].fillna("unclustered", inplace=True)
        return bin_df.to_json(orient="split")
    if not save_toggle or not selected_data:
        raise PreventUpdate
    contigs = {point["text"] for point in selected_data["points"]}
    pdf = pd.read_json(intermediate_selections, orient="split").set_index("contig")
    refinement_cols = [col for col in pdf.columns if "refinement" in col]
    refinement_num = len(refinement_cols) + 1
    group_name = f"refinement_{refinement_num}"
    pdf.loc[contigs, group_name] = group_name
    pdf = pdf.fillna(axis="columns", method="ffill")
    pdf.reset_index(inplace=True)
    return pdf.to_json(orient="split")
