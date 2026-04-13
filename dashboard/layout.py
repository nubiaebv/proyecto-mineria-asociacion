"""
layout.py – Layout full-height con 5 pestañas principales.
"""
from dash import html, dcc, dash_table

from dashboard.components.navbar import create_navbar
from dashboard.components.sidebar import create_sidebar
from dashboard.components.pipeline_tab import create_pipeline_tab
from dashboard.data_loader import get_dataset_names, get_all_items


# ── Helpers de pestaña ────────────────────────────────────────────────────────

def _panel(children) -> html.Div:
    """Wrapper con clase tab-panel para altura gestionada por CSS."""
    return html.Div(className="tab-panel", children=children)


# ── Definición de pestañas ────────────────────────────────────────────────────

def _tab_exploracion() -> dcc.Tab:
    return dcc.Tab(
        label="📊 Exploración",
        value="tab-exploracion",
        children=_panel([
            html.Div(
                className="grid-2col",
                children=[
                    # Scatter soporte vs confianza
                    html.Div(className="inner-card", children=[
                        html.P("Soporte vs Confianza",
                               style={"fontWeight": "600", "color": "#1a237e",
                                      "marginBottom": "8px", "fontSize": "0.84rem"}),
                        dcc.Graph(
                            id="graph-scatter",
                            className="graph-full",
                            config={"displayModeBar": True, "responsive": True},
                            style={"height": "100%"},
                        ),
                    ]),
                    # Histograma distribución de Lift
                    html.Div(className="inner-card", children=[
                        html.P("Distribución de Lift",
                               style={"fontWeight": "600", "color": "#1a237e",
                                      "marginBottom": "8px", "fontSize": "0.84rem"}),
                        dcc.Graph(
                            id="graph-hist-lift",
                            className="graph-full",
                            config={"responsive": True},
                            style={"height": "100%"},
                        ),
                    ]),
                ],
            )
        ]),
    )


def _tab_top_reglas() -> dcc.Tab:
    return dcc.Tab(
        label="🏆 Top Reglas",
        value="tab-top",
        children=_panel([
            dcc.Graph(
                id="graph-bar",
                className="graph-full",
                config={"displayModeBar": True, "responsive": True},
                style={"height": "calc(100vh - 220px)"},
            ),
        ]),
    )


def _tab_heatmap() -> dcc.Tab:
    return dcc.Tab(
        label="🔥 Heatmap Lift",
        value="tab-heatmap",
        children=_panel([
            dcc.Graph(
                id="graph-heatmap",
                className="graph-full",
                config={"displayModeBar": True, "responsive": True},
                style={"height": "calc(100vh - 220px)"},
            ),
        ]),
    )


def _tab_tabla() -> dcc.Tab:
    return dcc.Tab(
        label="📋 Tabla de Reglas",
        value="tab-tabla",
        children=_panel([
            dash_table.DataTable(
                id="tbl-rules",
                page_size=14,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": "#e8eaf6",
                    "fontWeight": "700",
                    "color": "#1a237e",
                    "fontSize": "0.80rem",
                },
                style_cell={
                    "textAlign": "left",
                    "padding": "9px 12px",
                    "fontSize": "0.81rem",
                    "whiteSpace": "normal",
                    "height": "auto",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#f5f6fd"},
                    {"if": {"filter_query": "{lift} > 3"},
                     "backgroundColor": "#fff9c4", "color": "#e65100"},
                ],
                export_format="csv",
                export_headers="display",
            ),
        ]),
    )


# ── Layout principal ──────────────────────────────────────────────────────────

def create_layout() -> html.Div:
    datasets  = get_dataset_names()
    all_items = get_all_items(datasets[0]) if datasets else []

    return html.Div(
        className="app-shell",
        children=[

            # ── Navbar fijo ───────────────────────────────────
            create_navbar(),

            # ── Cuerpo: sidebar + área de tabs ────────────────
            html.Div(
                className="main-content",
                children=[

                    # Sidebar con controles y KPIs
                    create_sidebar(datasets, all_items),

                    # Área de pestañas principales
                    html.Div(
                        className="tab-area",
                        children=[
                            dcc.Tabs(
                                id="main-tabs",
                                value="tab-exploracion",
                                className="main-tabs",
                                vertical=False,
                                mobile_breakpoint=0,
                                children=[
                                    _tab_exploracion(),
                                    _tab_top_reglas(),
                                    _tab_heatmap(),
                                    _tab_tabla(),
                                    create_pipeline_tab(),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
