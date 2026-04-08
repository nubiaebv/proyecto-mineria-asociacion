"""
navbar.py – Barra de navegación superior (compacta, altura fija).
"""
from dash import html


def create_navbar() -> html.Div:
    return html.Div(
        className="navbar",
        children=[
            html.Div([
                html.Div("🛒  Dashboard · Reglas de Asociación", className="navbar-title"),
                html.Div("Minería de Datos II · BD162 · IC-2026 · Colegio Universitario de Cartago",
                         className="navbar-subtitle"),
            ]),
            html.Div("Grupo #2 · Nubia Brenes Valerín & Gilary Granados Calvo",
                     className="navbar-badge"),
        ],
    )
