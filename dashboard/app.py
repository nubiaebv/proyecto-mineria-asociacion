"""
app.py – Punto de entrada del Interactive Dashboard con Plotly Dash.
Ejecutar:
    python dash_app/app.py
    # → http://localhost:8050
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dash import Dash

from dashboard.layout import create_layout
from dashboard.callbacks.charts_callbacks import register_chart_callbacks
from dashboard.callbacks.pipeline_callbacks import register_pipeline_callbacks

app = Dash(
    __name__,
    assets_folder="assets",
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    title="Dashboard · Reglas de Asociación | BD162",
)

app.layout = create_layout()
register_chart_callbacks(app)
register_pipeline_callbacks(app)

# Para despliegue con gunicorn: gunicorn dashboard.app:server
server = app.server

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
