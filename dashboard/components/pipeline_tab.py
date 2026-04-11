"""
pipeline_tab.py – Pestaña Pipeline dentro del dashboard.
"""
from dash import html, dcc


# ─── Helpers de sección ───────────────────────────────────────────────────────

def _section(title: str, children) -> html.Div:
    return html.Div(className="pipe-section", children=[
        html.Div(title, className="pipe-section-title"),
        *children,
    ])


def _row(*cols) -> html.Div:
    return html.Div(className="pipe-row", children=list(cols))


def _col(children, flex="1") -> html.Div:
    return html.Div(style={"flex": flex, "minWidth": "0"}, children=children)


def _label(text: str) -> html.Label:
    return html.Label(text, className="control-label", style={"marginBottom": "4px"})


# ─── Pestaña completa ─────────────────────────────────────────────────────────

def create_pipeline_tab() -> dcc.Tab:
    return dcc.Tab(
        label="⚙️ Pipeline",
        value="tab-pipeline",
        children=html.Div(className="tab-panel pipe-panel", children=[

            # ── 1. Upload ────────────────────────────────────────────────────
            _section("📂 1. Cargar archivo CSV", [
                dcc.Upload(
                    id="upload-csv",
                    children=html.Div([
                        html.Span("⬆️  Arrastra tu CSV aquí o "),
                        html.A("selecciona un archivo", style={"color": "#3949ab", "cursor": "pointer"}),
                    ]),
                    className="upload-zone",
                    multiple=False,
                    accept=".csv,.xlsx,.xls",
                ),
                html.Div(id="upload-status", className="upload-status"),
            ]),

            # ── 2. Columnas de transacción ───────────────────────────────────
            _section("🔗 2. Columnas para las transacciones", [
                html.Div(
                    id="col-selector-wrapper",
                    children=html.Div(
                        "Sube un CSV primero para ver las columnas disponibles.",
                        className="pipe-hint",
                    ),
                ),
            ]),

            # ── 3. Parámetros ────────────────────────────────────────────────
            _section("⚙️ 3. Parámetros del pipeline", [
                _row(
                    _col([
                        html.Div("— Apriori —", className="pipe-algo-title"),
                        _label("Soporte mín."),
                        dcc.Slider(id="pipe-sup-apriori",  min=0.001, max=0.5,  step=0.001, value=0.05,
                                   marks={0.001:"0.001", 0.1:"0.1", 0.5:"0.5", 1:"1"},
                                   tooltip={"placement":"right","always_visible":True}),
                        html.Div(style={"height":"10px"}),
                        _label("Confianza mín."),
                        dcc.Slider(id="pipe-conf-apriori", min=0.1,  max=1.0,  step=0.05, value=0.5,
                                   marks={0.1:"0.1", 0.5:"0.5", 1:"1"},
                                   tooltip={"placement":"right","always_visible":True}),
                    ]),
                    _col([
                        html.Div("— ECLAT —", className="pipe-algo-title"),
                        _label("Soporte mín."),
                        dcc.Slider(id="pipe-sup-eclat",   min=0.001, max=0.5,  step=0.001, value=0.2,
                                   marks={0.001:"0.001", 0.1:"0.1", 0.5:"0.5", 1:"1"},
                                   tooltip={"placement":"right","always_visible":True}),
                        html.Div(style={"height":"10px"}),
                        _label("Confianza mín."),
                        dcc.Slider(id="pipe-conf-eclat",  min=0.1,  max=1.0,  step=0.05, value=0.5,
                                   marks={0.1:"0.1", 0.5:"0.5", 1:"1"},
                                   tooltip={"placement":"right","always_visible":True}),
                    ]),
                    _col([
                        html.Div("— Limpieza —", className="pipe-algo-title"),
                        _label("Estrategia de nulos"),
                        dcc.RadioItems(
                            id="pipe-null-strategy",
                            options=[
                                {"label": "  Eliminar filas con nulos",  "value": "drop"},
                                {"label": "  Rellenar (mediana / moda)", "value": "fill"},
                                {"label": "  Sin cambios",               "value": "none"},
                            ],
                            value="drop",
                            labelStyle={"display":"block","marginBottom":"6px","fontSize":"0.80rem"},
                            inputStyle={"marginRight":"6px"},
                        ),
                        html.Div(style={"height":"10px"}),
                        _label("Exportar como dataset"),
                        dcc.Dropdown(
                            id="pipe-export-dataset",
                            options=[
                                {"label": "Tecnología / Software",      "value": "tech"},
                                {"label": "Retail (cadena detallista)", "value": "retail"},
                            ],
                            value="tech",
                            clearable=False,
                        ),
                    ], flex="0.9"),
                ),
            ]),

            # ── 4. Ejecutar ──────────────────────────────────────────────────
            _section("🚀 4. Ejecutar", [
                html.Div(className="pipe-run-row", children=[
                    html.Button(
                        "▶  Ejecutar Pipeline",
                        id="btn-run-pipeline",
                        className="btn-run",
                        n_clicks=0,
                        disabled=True,
                    ),
                    html.Div(id="pipe-run-status", className="pipe-run-status"),
                ]),
            ]),

            # ── 5. Resumen de resultados ─────────────────────────────────────
            _section("📊 6. Resumen de resultados", [
                html.Div(id="pipe-results-summary"),
            ]),

            # ── 6. Log de ejecución ──────────────────────────────────────────
            _section("📋 5. Log de ejecución", [
                html.Pre(
                    id="pipe-log",
                    className="pipe-log",
                    children="El log aparecerá aquí al ejecutar el pipeline...",
                ),
            ]),

            # Store para guardar columnas detectadas
            dcc.Store(id="store-csv-columns"),
            dcc.Store(id="store-csv-content"),
            dcc.Store(id="store-pipeline-ran", data=False),
        ]),
    )
