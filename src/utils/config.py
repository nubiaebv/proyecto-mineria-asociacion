"""
config.py – Rutas y constantes globales del proyecto.
"""
from pathlib import Path

# ── Raíz del proyecto ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Directorios de datos ─────────────────────────────────────────────────────
DATA_RAW_DIR       = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR        = PROJECT_ROOT / "reports"

# ── Archivos de reglas generados por el pipeline ─────────────────────────────
# El pipeline exporta los resultados en estos CSV; el dashboard los lee.
RULES_RETAIL_FILE = str(DATA_PROCESSED_DIR / "rules_retail.csv")
RULES_TECH_FILE   = str(DATA_PROCESSED_DIR / "rules_tech.csv")

# ── Asegurar que los directorios existen ─────────────────────────────────────
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
