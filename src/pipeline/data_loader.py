"""
Módulo de carga de datos.
Leer cualquier archivo CSV y retornar un DataFrame limpio.
"""
import pandas as pd
from pathlib import Path


class DataLoader:
    """
    Carga un archivo CSV desde cualquier ruta y lo expone como DataFrame.
    """

    def __init__(
        self,
        filepath: str | Path,
        delimiter: str = ",",
        encoding: str = "utf-8",
        decimal: str = ".",
    ):
        self.filepath = Path(filepath)
        self.delimiter = delimiter
        self.encoding = encoding
        self.decimal = decimal
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def load(self) -> pd.DataFrame:
        """Lee el CSV y retorna el DataFrame crudo."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {self.filepath}")

        self._df = pd.read_csv(
            self.filepath,
            delimiter=self.delimiter,
            decimal=self.decimal,
            encoding=self.encoding,
        )
        print(f"[DataLoader] Cargado '{self.filepath.name}': "
              f"{self._df.shape[0]} filas × {self._df.shape[1]} columnas")
        return self._df

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._df is None:
            raise RuntimeError("Ejecute load() primero.")
        return self._df
