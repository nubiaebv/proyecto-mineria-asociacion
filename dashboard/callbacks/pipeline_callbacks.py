"""
pipeline_callbacks.py – Callbacks para la pestaña Pipeline.
"""
from __future__ import annotations
import base64, io, sys, traceback, os
from pathlib import Path

import pandas as pd
from dash import html, dcc, Input, Output, State, no_update

# Asegurar path del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.config import RULES_TECH_FILE, RULES_RETAIL_FILE


# ── Mapeo destino → archivo ───────────────────────────────────────────────────
EXPORT_MAP = {
    "tech":   RULES_TECH_FILE,
    "retail": RULES_RETAIL_FILE,
}

# ── Mapeo destino → nombre del dataset en el sidebar ─────────────────────────
DATASET_NAME_MAP = {
    "tech":   "Tecnología / Software",
    "retail": "Retail (cadena detallista)",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode_upload(contents: str, filename: str) -> pd.DataFrame | None:
    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        ext = filename.rsplit(".", 1)[-1].lower()

        if ext in ("xlsx", "xls"):
            return pd.read_excel(io.BytesIO(decoded), engine="openpyxl")

        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                text = decoded.decode(enc)
                for sep in (",", ";", "\t"):
                    try:
                        df = pd.read_csv(io.StringIO(text), sep=sep, nrows=5,
                                         on_bad_lines="skip", engine="python")
                        if df.shape[1] > 1:
                            return pd.read_csv(io.StringIO(text), sep=sep,
                                               on_bad_lines="skip", engine="python")
                    except Exception:
                        continue
            except UnicodeDecodeError:
                continue

    except Exception as e:
        print(f"[_decode_upload] ERROR: {e}")
        return None


def _status_ok(msg: str) -> html.Div:
    return html.Div(msg, style={"color": "#2e7d32", "fontSize": "0.83rem",
                                 "marginTop": "6px", "fontWeight": "600"})


def _status_err(msg: str) -> html.Div:
    return html.Div(msg, style={"color": "#c62828", "fontSize": "0.83rem",
                                 "marginTop": "6px", "fontWeight": "600"})


def _kpi_summary(label: str, value: str, color: str) -> html.Div:
    return html.Div(className="kpi-card", style={"borderLeftColor": color}, children=[
        html.Div(value, className="kpi-value", style={"color": color}),
        html.Div(label, className="kpi-label"),
    ])


# ── Registro de callbacks ─────────────────────────────────────────────────────

def register_pipeline_callbacks(app) -> None:

    # ── 1. Procesar CSV subido → detectar columnas ────────────────────────────
    @app.callback(
        Output("upload-status",      "children"),
        Output("col-selector-wrapper","children"),
        Output("btn-run-pipeline",   "disabled"),
        Output("store-csv-columns",  "data"),
        Output("store-csv-content",  "data"),
        Input("upload-csv", "contents"),
        State("upload-csv", "filename"),
        prevent_initial_call=True,
    )
    def on_upload(contents, filename):
        if contents is None:
            return no_update, no_update, True, None, None

        df = _decode_upload(contents, filename)
        if df is None:
            return (
                _status_err(f"❌ No se pudo leer '{filename}'. Verifica que sea un CSV válido."),
                no_update, True, None, None,
            )

        cols = df.columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "str"]).columns.tolist()

        status = _status_ok(
            f"✅ '{filename}' cargado · {df.shape[0]:,} filas × {df.shape[1]} columnas"
        )

        selector = html.Div([
            html.Div(
                "Selecciona las columnas que formarán cada transacción "
                "(déjalas vacías para usar todas las categóricas automáticamente):",
                className="pipe-hint",
            ),
            dcc.Checklist(
                id="pipe-col-checklist",
                options=[{"label": f"  {c}  [{df[c].dtype}]", "value": c} for c in cols],
                value=cat_cols,          # preseleccionar las categóricas
                labelStyle={"display": "inline-block", "marginRight": "14px",
                             "marginBottom": "6px", "fontSize": "0.81rem",
                             "cursor": "pointer"},
                inputStyle={"marginRight": "5px"},
                className="col-checklist",
            ),
            html.Div(
                f"💡 {len(cat_cols)} columnas categóricas preseleccionadas de {len(cols)} totales.",
                style={"fontSize":"0.74rem","color":"#90a4ae","marginTop":"6px"},
            ),
        ])

        return status, selector, False, cols, contents

    # ── 2. Ejecutar el pipeline ───────────────────────────────────────────────
    @app.callback(
        Output("pipe-log",             "children"),
        Output("pipe-run-status",      "children"),
        Output("pipe-results-summary", "children"),
        Output("store-pipeline-ran",   "data"),
        Input("btn-run-pipeline",  "n_clicks"),
        State("store-csv-content", "data"),
        State("upload-csv",        "filename"),
        State("pipe-col-checklist","value"),
        State("pipe-sup-apriori",  "value"),
        State("pipe-conf-apriori", "value"),
        State("pipe-sup-eclat",    "value"),
        State("pipe-conf-eclat",   "value"),
        State("pipe-null-strategy","value"),
        State("pipe-export-dataset","value"),
        prevent_initial_call=True,
    )
    def run_pipeline(n_clicks, csv_contents, filename,
                     rule_columns,
                     sup_apriori, conf_apriori,
                     sup_eclat,   conf_eclat,
                     null_strategy, export_dest):

        if not n_clicks or csv_contents is None:
            return no_update, no_update, no_update, no_update

        log_lines: list[str] = []

        def log(msg: str):
            log_lines.append(msg)

        try:
            # ── Decodificar CSV ──────────────────────────────────────────────
            log(f"📂 Leyendo archivo: {filename}")
            df_raw = _decode_upload(csv_contents, filename)
            if df_raw is None:
                raise ValueError("No se pudo decodificar el CSV.")
            log(f"   → {df_raw.shape[0]:,} filas × {df_raw.shape[1]} columnas")

            # ── Importar pipeline ────────────────────────────────────────────
            log("\n⚙️  Iniciando MiningPipeline…")
            from src.pipeline.data_cleaner    import DataCleaner
            from src.pipeline.data_transformer import DataTransformer
            from src.pipeline.eda_analyzer    import EDAAnalyzer
            from src.models.apriori_model     import AprioriModel
            from src.models.eclat_model       import ECLATModel
            from src.models.recommender       import Recommender

            # ── Paso 2: Limpieza ─────────────────────────────────────────────
            log("\n── PASO 1/5 · Limpieza de datos ──")
            STRATEGY_MAP = {
                "Eliminar filas con nulos": "drop",
                "Rellenar (mediana / moda)": "fill",
                "Sin cambios": "none",
            }
            cleaner = DataCleaner(null_strategy=STRATEGY_MAP.get(null_strategy, "drop"))
            df_clean = cleaner.clean(df_raw)
            r = cleaner.report
            log(f"   Duplicados eliminados : {r.get('duplicados_eliminados', 0)}")
            log(f"   Nulos antes / después : {r.get('nulos_antes',0)} / {r.get('nulos_despues',0)}")
            log(f"   Filas resultantes     : {r.get('filas_finales',0):,}")

            # ── Paso 3: Transformación ───────────────────────────────────────
            # ── Paso 2/5 · Transformación de datos ──
            invoice_col = next((c for c in df_clean.columns if "invoice" in c.lower()), None)
            desc_col = next((c for c in df_clean.columns if "descri" in c.lower()), None)

            if invoice_col and desc_col:
                sep_used = "|"
                top_products = (
                    df_clean[desc_col]
                    .value_counts()
                    .head(150)
                    .index.tolist()
                )
                df_filtered = df_clean[df_clean[desc_col].isin(top_products)]
                df_grouped = (
                    df_filtered.groupby(invoice_col)[desc_col]
                    .apply(lambda x: sep_used.join(x.astype(str).str.strip().str.lower().unique()))
                    .reset_index()
                    .rename(columns={desc_col: "Reglas"})
                )
                df_transformed = df_grouped
                log(f"   Modo retail: top {len(top_products)} productos, {len(df_transformed):,} transacciones")
            else:
                sep_used = ","
                cols_to_use = rule_columns if rule_columns else None
                transformer = DataTransformer(rule_columns=cols_to_use)
                df_transformed = transformer.transform(df_clean)
                log(f"   Columnas usadas: {cols_to_use or 'inferidas automáticamente'}")
            # ── Paso 4: EDA básico (sin plots) ───────────────────────────────
            log("\n── PASO 3/5 · Estadísticas básicas ──")
            num_cols = df_clean.select_dtypes(include=["int64","float64"]).columns
            cat_cols_eda = df_clean.select_dtypes(include=["object","str"]).columns
            log(f"   Columnas numéricas   : {len(num_cols)}")
            log(f"   Columnas categóricas : {len(cat_cols_eda)}")

            # ── Paso 5: Apriori ──────────────────────────────────────────────
            log(f"\n── PASO 4/5 · Modelo Apriori  (soporte≥{sup_apriori}, confianza≥{conf_apriori}) ──")
            import matplotlib
            matplotlib.use("Agg")   # sin pantalla
            apriori_model = AprioriModel(
                min_support=sup_apriori,
                min_confidence=conf_apriori,
                separator=sep_used,
            ).fit(df_transformed)
            n_ap = len(apriori_model.rules_) if apriori_model.rules_ is not None else 0
            log(f"   Itemsets frecuentes : {len(apriori_model.frequent_itemsets_)}")
            log(f"   Reglas generadas    : {n_ap}")
            if n_ap > 0:
                top = apriori_model.rules_.nlargest(3, "lift")
                log("   Top 3 por lift:")
                for _, r in top.iterrows():
                    ant = " + ".join(sorted(r["antecedents"]))
                    con = " + ".join(sorted(r["consequents"]))
                    log(f"     {ant} → {con}  [lift={r['lift']:.3f}, conf={r['confidence']:.3f}]")

            # ── Paso 6: ECLAT ────────────────────────────────────────────────
            log(f"\n── PASO 5/5 · Modelo ECLAT  (soporte≥{sup_eclat}, confianza≥{conf_eclat}) ──")
            eclat_model = ECLATModel(
                min_support=sup_eclat,
                min_confidence=conf_eclat,
                separator=sep_used,
            ).fit(df_transformed)
            n_ec = len(eclat_model.df_rules_) if eclat_model.df_rules_ is not None else 0
            log(f"   Itemsets frecuentes : {len(eclat_model.frequent_itemsets_)}")
            log(f"   Reglas generadas    : {n_ec}")

            # ── Exportar al dashboard ────────────────────────────────────────
            log(f"\n💾 Exportando reglas → dataset '{DATASET_NAME_MAP.get(export_dest)}'…")
            rules_to_export = None
            if n_ap > 0:
                rules_to_export = apriori_model.rules_.copy()
                log("   Fuente: Apriori")
            elif n_ec > 0:
                rules_to_export = eclat_model.df_rules_.copy()
                log("   Fuente: ECLAT (Apriori no generó reglas con esos umbrales)")
            else:
                log("   ⚠️  Ningún modelo generó reglas. Baja los umbrales e intenta de nuevo.")

            export_path = EXPORT_MAP[export_dest]
            if rules_to_export is not None and not rules_to_export.empty:
                rules_to_export["antecedents"] = rules_to_export["antecedents"].apply(lambda x: str(set(x)))
                rules_to_export["consequents"] = rules_to_export["consequents"].apply(lambda x: str(set(x)))
                os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
                rules_to_export[["antecedents","consequents","support","confidence","lift"]].to_csv(
                    export_path, index=False, encoding="utf-8"
                )
                log(f"   ✅ {len(rules_to_export)} reglas guardadas en:")
                log(f"      {export_path}")

            log("\n★ Pipeline finalizado con éxito ★")
            log("→ Ve a cualquier pestaña y selecciona el dataset para ver los resultados.")

            # ── Status badge ─────────────────────────────────────────────────
            status = html.Span("✅ Completado", style={
                "background":"#e8f5e9","color":"#2e7d32",
                "padding":"4px 14px","borderRadius":"20px",
                "fontWeight":"700","fontSize":"0.82rem",
            })

            # ── Tarjetas de resumen ───────────────────────────────────────────
            summary = html.Div([
                html.Hr(style={"margin":"18px 0","borderColor":"#e8eaf6"}),
                html.Div("📊 Resumen del pipeline", className="pipe-section-title",
                         style={"marginBottom":"12px"}),
                html.Div(className="kpi-grid", style={"gridTemplateColumns":"repeat(4,1fr)","gap":"10px"}, children=[
                    _kpi_summary("Filas procesadas", f"{len(df_transformed):,}", "#3949ab"),
                    _kpi_summary("Reglas Apriori",   str(n_ap),                 "#00897b"),
                    _kpi_summary("Reglas ECLAT",     str(n_ec),                 "#e53935"),
                    _kpi_summary("Dataset destino",
                                 DATASET_NAME_MAP.get(export_dest,"?"),         "#fb8c00"),
                ]),
                html.Div(
                    f"🔄 Cambia a cualquier pestaña y selecciona "
                    f"'{DATASET_NAME_MAP.get(export_dest)}' para ver los nuevos resultados.",
                    style={"marginTop":"12px","fontSize":"0.83rem","color":"#546e7a",
                           "background":"#e8eaf6","padding":"10px 14px","borderRadius":"8px"},
                ),
            ])

            return "\n".join(log_lines), status, summary, True

        except Exception as exc:
            log(f"\n❌ ERROR: {exc}")
            log(traceback.format_exc())
            status = html.Span("❌ Error", style={
                "background":"#ffebee","color":"#c62828",
                "padding":"4px 14px","borderRadius":"20px",
                "fontWeight":"700","fontSize":"0.82rem",
            })
            return "\n".join(log_lines), status, no_update, False

    # ── 3. Invalidar cache del data_loader al terminar el pipeline ────────────
    @app.callback(
        Output("dd-dataset", "options"),
        Input("store-pipeline-ran", "data"),
        prevent_initial_call=True,
    )
    def refresh_dataset_options(ran):
        """Al terminar el pipeline limpia el cache para que el dashboard recargue las reglas."""
        if ran:
            from dashboard import data_loader as dl
            dl._cache.clear()
        from dashboard.data_loader import get_dataset_names
        datasets = get_dataset_names()
        return [{"label": d, "value": d} for d in datasets]
