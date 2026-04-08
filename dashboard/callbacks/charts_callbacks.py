"""
charts_callbacks.py – Callbacks reactivos para el dashboard Plotly Dash.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, Input, Output

from dashboard.data_loader import load_rules_for_dataset, filter_rules
from dashboard.components.sidebar import create_kpi_cards


# ── Helpers de figura ─────────────────────────────────────────────────────────

def _to_display(rules: pd.DataFrame) -> pd.DataFrame:
    d = rules.copy()
    d["Antecedente"] = d["antecedents"].apply(lambda x: " + ".join(sorted(x)))
    d["Consecuente"] = d["consequents"].apply(lambda x: " + ".join(sorted(x)))
    return d[["Antecedente", "Consecuente", "support", "confidence", "lift"]].round(4)


def _empty_fig(msg: str = "Sin datos con los filtros actuales") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font={"size": 16, "color": "#90a4ae"},
    )
    fig.update_layout(
        plot_bgcolor="#f8f9fd", paper_bgcolor="#f8f9fd",
        xaxis={"visible": False}, yaxis={"visible": False},
    )
    return fig


def _scatter(rules: pd.DataFrame) -> go.Figure:
    if rules.empty:
        return _empty_fig()
    d = _to_display(rules)
    return px.scatter(
        d, x="support", y="confidence",
        color="lift", size="lift", size_max=22,
        hover_data=["Antecedente", "Consecuente"],
        color_continuous_scale="YlOrRd",
        labels={"support": "Soporte", "confidence": "Confianza", "lift": "Lift"},
        template="plotly_white",
    ).update_layout(
        margin={"t": 30, "b": 40, "l": 40, "r": 20},
        coloraxis_colorbar={"thickness": 12, "len": 0.7},
    )


def _bar(rules: pd.DataFrame, top_n: int, metric: str) -> go.Figure:
    if rules.empty:
        return _empty_fig()
    d = _to_display(rules.nlargest(top_n, metric))
    d["Regla"] = d["Antecedente"] + "  →  " + d["Consecuente"]
    return px.bar(
        d, x=metric, y="Regla", orientation="h",
        color="confidence", color_continuous_scale="Blues",
        text=metric,
        labels={metric: metric.capitalize(), "Regla": ""},
        template="plotly_white",
    ).update_traces(
        texttemplate="%{text:.3f}", textposition="outside"
    ).update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin={"t": 30, "b": 40, "l": 280, "r": 60},
        coloraxis_colorbar={"thickness": 12},
    )


def _heatmap(rules: pd.DataFrame, top_n: int) -> go.Figure:
    if rules.empty:
        return _empty_fig()
    top = rules.nlargest(top_n, "lift").copy()
    top["ant_str"] = top["antecedents"].apply(lambda x: " + ".join(sorted(x)))
    top["con_str"] = top["consequents"].apply(lambda x: " + ".join(sorted(x)))
    pivot = top.pivot_table(
        index="ant_str", columns="con_str", values="lift", aggfunc="max"
    ).fillna(0)
    return px.imshow(
        pivot, color_continuous_scale="Blues", aspect="auto",
        labels={"x": "Consecuente", "y": "Antecedente", "color": "Lift"},
        template="plotly_white",
    ).update_layout(
        margin={"t": 30, "b": 80, "l": 180, "r": 20},
        xaxis_tickangle=-35,
    )


def _hist(rules: pd.DataFrame, metric: str) -> go.Figure:
    if rules.empty:
        return _empty_fig()
    return px.histogram(
        rules, x=metric, nbins=30,
        color_discrete_sequence=["#3949ab"],
        labels={metric: metric.capitalize()},
        template="plotly_white",
    ).update_layout(margin={"t": 30, "b": 40, "l": 50, "r": 20})


# ── Registro de callbacks ─────────────────────────────────────────────────────

def register_chart_callbacks(app) -> None:
    """Registra todos los callbacks en la instancia Dash recibida."""

    # ── Inputs comunes (sidebar) ──────────────────────────────
    _common_inputs = [
        Input("dd-dataset",        "value"),
        Input("slider-confidence", "value"),
        Input("slider-lift",       "value"),
        Input("slider-support",    "value"),
        Input("radio-metric",      "value"),
        Input("dd-topn",           "value"),
    ]

    # ── 1. KPIs en sidebar ────────────────────────────────────
    @app.callback(
        Output("div-kpis", "children"),
        *_common_inputs,
    )
    def update_kpis(dataset, min_conf, min_lift, min_sup, metric, top_n):
        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        return create_kpi_cards(rules)

    # ── 2. Pestaña Exploración: scatter + histograma ──────────
    @app.callback(
        Output("graph-scatter",   "figure"),
        Output("graph-hist-lift", "figure"),
        *_common_inputs,
    )
    def update_exploracion(dataset, min_conf, min_lift, min_sup, metric, top_n):
        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        return _scatter(rules), _hist(rules, "lift")

    # ── 3. Pestaña Top Reglas: barras ─────────────────────────
    @app.callback(
        Output("graph-bar", "figure"),
        *_common_inputs,
    )
    def update_bar(dataset, min_conf, min_lift, min_sup, metric, top_n):
        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        return _bar(rules, top_n, metric)

    # ── 4. Pestaña Heatmap ────────────────────────────────────
    @app.callback(
        Output("graph-heatmap", "figure"),
        *_common_inputs,
    )
    def update_heatmap(dataset, min_conf, min_lift, min_sup, metric, top_n):
        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        return _heatmap(rules, min(top_n, 20))

    # ── 5. Pestaña Tabla ──────────────────────────────────────
    @app.callback(
        Output("tbl-rules", "data"),
        Output("tbl-rules", "columns"),
        *_common_inputs,
    )
    def update_tabla(dataset, min_conf, min_lift, min_sup, metric, top_n):
        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        d = _to_display(rules.nlargest(top_n, metric) if not rules.empty else rules)
        columns = [{"name": c, "id": c} for c in d.columns]
        return d.to_dict("records"), columns

    # ── 6. Pestaña Recomendaciones: ítems recomendados ────────
    @app.callback(
        Output("div-recommendations", "children"),
        Input("dd-rec-items",      "value"),
        Input("dd-dataset",        "value"),
        Input("slider-confidence", "value"),
        Input("slider-lift",       "value"),
        Input("slider-support",    "value"),
    )
    def update_recommendations(selected_items, dataset, min_conf, min_lift, min_sup):
        if not selected_items:
            return html.Div(className="placeholder-msg", children=[
                html.Div("🎯", className="placeholder-icon"),
                html.Div("Selecciona ítems arriba para ver recomendaciones"),
            ])

        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        if rules.empty:
            return html.P("Sin reglas con los filtros actuales.",
                          style={"color": "#e53935", "fontSize": "0.85rem"})

        from src.models.recommender import AssociationRecommender
        recs = AssociationRecommender(rules).recommend(selected_items, top_n=8)

        if recs.empty:
            return html.P("No se encontraron recomendaciones para esos ítems.",
                          style={"color": "#fb8c00", "fontSize": "0.85rem"})

        return [
            html.Div(className="rec-card", children=[
                html.Div(f"🎯 {row['item_recomendado'].title()}", className="rec-item"),
                html.Div(
                    f"Soporte: {row['support']}  ·  Confianza: {row['confidence']}  ·  Lift: {row['lift']}",
                    className="rec-metrics",
                ),
            ])
            for _, row in recs.iterrows()
        ]

    # ── 7. Pestaña Recomendaciones: propuestas de negocio ─────
    @app.callback(
        Output("div-proposals", "children"),
        Input("dd-dataset",        "value"),
        Input("slider-confidence", "value"),
        Input("slider-lift",       "value"),
        Input("slider-support",    "value"),
    )
    def update_proposals(dataset, min_conf, min_lift, min_sup):
        rules = filter_rules(load_rules_for_dataset(dataset), min_conf, min_lift, min_sup)
        if rules.empty:
            return html.Div(className="placeholder-msg", children=[
                html.Div("📌", className="placeholder-icon"),
                html.Div("Sin reglas disponibles con los filtros actuales"),
            ])

        from src.models.recommender import AssociationRecommender
        props = AssociationRecommender(rules).business_proposals(top_n=10)

        return [
            html.Div(className="proposal-card", children=[
                html.Div(
                    f"📌 {' + '.join(sorted(row['antecedents']))} → "
                    f"{' + '.join(sorted(row['consequents']))}  "
                    f"[lift {row['lift']:.2f}]",
                    className="proposal-rule",
                ),
                html.Div(row["propuesta"]),
            ])
            for _, row in props.iterrows()
        ]
