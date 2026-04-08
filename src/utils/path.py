"""
Utilidad para manejo de rutas del proyecto.
"""
import os
from pathlib import Path


def obtener_ruta_local() -> str:
    """Retorna la ruta raíz del proyecto."""
    # Sube hasta encontrar la raíz del proyecto (donde está src/)
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "src").exists():
            return str(parent)
    return str(Path(__file__).resolve().parents[3])


def get_data_path(subfolder: str = "raw") -> Path:
    """Retorna el path a la carpeta de datos."""
    root = Path(obtener_ruta_local())
    return root / "data" / subfolder


def get_reports_path() -> Path:
    """Retorna el path a la carpeta de reportes."""
    root = Path(obtener_ruta_local())
    path = root / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path
