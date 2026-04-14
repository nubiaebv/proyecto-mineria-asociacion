"""
data_loader.py – Carga y filtrado de reglas de asociación para el dashboard Dash.
"""
import pandas as pd
from pathlib import Path
import sys

# Asegurar que el raíz del proyecto está en el path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RULES_RETAIL_FILE, RULES_TECH_FILE

# ── Mapeo dataset → archivo ──────────────────────────────────────────────────
DATASET_PATHS = {
    "Retail (cadena detallista)": RULES_RETAIL_FILE,
    "Tecnología / Software":      RULES_TECH_FILE,
}

# ── Cache en memoria ─────────────────────────────────────────────────────────
_cache: dict[str, pd.DataFrame] = {}


def _parse_frozenset(value: str) -> frozenset:
    """Convierte la representación textual de un frozenset a frozenset real."""
    try:
        return frozenset(eval(value))
    except Exception:
        return frozenset({str(value)})


def load_rules_for_dataset(dataset_name: str) -> pd.DataFrame:
    """
    Carga las reglas del dataset indicado (con cache en memoria).

    """
    if dataset_name in _cache:
        return _cache[dataset_name]

    path = DATASET_PATHS.get(dataset_name)
    if path is None or not Path(path).exists():
        # Retornar DataFrame vacío para no romper callbacks
        empty = pd.DataFrame(columns=["antecedents", "consequents",
                                       "support", "confidence", "lift"])
        return empty

    df = pd.read_csv(path)
    df["antecedents"] = df["antecedents"].apply(_parse_frozenset)
    df["consequents"] = df["consequents"].apply(_parse_frozenset)

    _cache[dataset_name] = df
    return df


def filter_rules(
    rules: pd.DataFrame,
    min_confidence: float = 0.3,
    min_lift: float = 1.0,
    min_support: float = 0.0,
) -> pd.DataFrame:
    """Filtra el DataFrame de reglas según los umbrales indicados."""
    if rules.empty:
        return rules
    mask = (
        (rules["confidence"] >= min_confidence) &
        (rules["lift"]       >= min_lift)       &
        (rules["support"]    >= min_support)
    )
    return rules[mask].reset_index(drop=True)


def get_all_items(dataset_name: str) -> list[str]:
    """Retorna todos los ítems únicos presentes en los antecedentes."""
    rules = load_rules_for_dataset(dataset_name)
    if rules.empty:
        return []
    items = sorted({item for fset in rules["antecedents"] for item in fset})
    return items


def get_dataset_names() -> list[str]:
    """Lista de nombres de datasets disponibles."""
    return list(DATASET_PATHS.keys())
