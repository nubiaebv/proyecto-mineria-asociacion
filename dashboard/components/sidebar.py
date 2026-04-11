"""
sidebar.py – Sidebar lateral con controles interactivos y KPI cards.
"""
import pandas as pd
from dash import html, dcc


def create_sidebar(datasets: list[str], all_items: list[str]) -> html.Div:
    return html.Div(
        className="sidebar",
        children=[

            # ── Logo / título ─────────────────────────────────
            html.Div([
                html.Div("🛒  Reglas de Asociación",
                         style={"fontWeight": "700", "color": "#1a237e", "fontSize": "0.88rem"}),
                html.Div("BD162 · IC-2026 · CUC",
                         style={"fontSize": "0.70rem", "color": "#90a4ae", "marginTop": "2px"}),
            ]),

            html.Hr(className="sidebar-divider"),

            # ── Sección: Dataset ──────────────────────────────
            html.Div([
                html.Div("Fuente de datos", className="sidebar-section-title"),
                html.Label("📦 Dataset", className="control-label"),
                dcc.Dropdown(
                    id="dd-dataset",
                    options=[{"label": d, "value": d} for d in datasets],
                    value=datasets[0],
                    clearable=False,
                ),
            ]),

            html.Hr(className="sidebar-divider"),

            # ── Sección: Visualización ────────────────────────
            html.Div([
                html.Div("Visualización", className="sidebar-section-title"),

                html.Label("📊 Ordenar por", className="control-label"),
                dcc.RadioItems(
                    id="radio-metric",
                    options=[
                        {"label": "  Lift",       "value": "lift"},
                        {"label": "  Confianza",  "value": "confidence"},
                        {"label": "  Soporte",    "value": "support"},
                    ],
                    value="lift",
                    labelStyle={"display": "block", "marginBottom": "4px",
                                "fontSize": "0.80rem", "cursor": "pointer"},
                    inputStyle={"marginRight": "6px"},
                ),

                html.Div(style={"marginTop": "10px"}),
                html.Label("🏆 Top N reglas", className="control-label"),
                dcc.Dropdown(
                    id="dd-topn",
                    options=[{"label": str(n), "value": n} for n in [10, 15, 20, 30, 50]],
                    value=15,
                    clearable=False,
                ),
            ]),

            html.Hr(className="sidebar-divider"),

            # ── Sección: Filtros ──────────────────────────────
            html.Div([
                html.Div("Filtros de umbral", className="sidebar-section-title"),

                html.Label("🔎 Confianza mín.", className="control-label"),
                dcc.Slider(
                    id="slider-confidence",
                    min=0.0, max=1.0, step=0.05, value=0.3,
                    marks={0: "0", 0.5: "0.5", 1: "1"},
                    tooltip={"placement": "right", "always_visible": True},
                ),

                html.Div(style={"marginTop": "14px"}),
                html.Label("⚡ Lift mín.", className="control-label"),
                dcc.Slider(
                    id="slider-lift",
                    min=1.0, max=10.0, step=0.5, value=1.0,
                    marks={1: "1", 5: "5", 10: "10"},
                    tooltip={"placement": "right", "always_visible": True},
                ),

                html.Div(style={"marginTop": "14px"}),
                html.Label("📈 Soporte mín.", className="control-label"),
                dcc.Slider(
                    id="slider-support",
                    min=0.001, max=0.5, step=0.001, value=0.02,
                    marks={0.001: "0.001", 0.5: ".5"},
                    tooltip={"placement": "right", "always_visible": True},
                ),
            ]),

            html.Hr(className="sidebar-divider"),

            # ── Sección: KPIs reactivos ───────────────────────
            html.Div([
                html.Div("Métricas activas", className="sidebar-section-title"),
                html.Div(id="div-kpis"),   # se actualiza vía callback
            ]),
        ],
    )


def create_kpi_cards(rules: pd.DataFrame) -> html.Div:
    """Mini tarjetas KPI a partir del DataFrame de reglas filtradas."""
    def fmt(val, fmt_str):
        try:    return format(val, fmt_str)
        except: return "—"

    cards = [
        ("Total",      f"{len(rules):,}",                        "#3949ab"),
        ("Conf. med",  fmt(rules["confidence"].mean(), ".3f"),    "#00897b"),
        ("Lift máx",   fmt(rules["lift"].max(),        ".2f"),    "#e53935"),
        ("Sup. med",   fmt(rules["support"].mean(),    ".4f"),    "#fb8c00"),
    ]
    return html.Div(
        className="kpi-grid",
        children=[
            html.Div(
                className="kpi-card",
                style={"borderLeftColor": color},
                children=[
                    html.Div(value, className="kpi-value", style={"color": color}),
                    html.Div(label, className="kpi-label"),
                ],
            )
            for label, value, color in cards
        ],
    )
