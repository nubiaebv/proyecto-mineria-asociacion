"""
Módulo de limpieza de datos.
Eliminar duplicados, tratar nulos y estandarizar tipos.
"""
import pandas as pd


class DataCleaner:
    """
    Realiza la limpieza básica de un DataFrame.
    """

    def __init__(
        self,
        drop_duplicates: bool = True,
        null_strategy: str = "drop",
    ):
        self.drop_duplicates = drop_duplicates
        self.null_strategy = null_strategy
        self._report: dict = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica todas las transformaciones de limpieza y retorna el DataFrame."""
        df = df.copy()
        original_rows = len(df)

        # 1. Duplicados
        if self.drop_duplicates:
            n_dups = df.duplicated().sum()
            df = df.drop_duplicates()
            self._report["duplicados_eliminados"] = int(n_dups)
            print(f"[DataCleaner] Duplicados eliminados: {n_dups}")

        # 2. Nulos
        nulos_antes = int(df.isnull().sum().sum())
        df = self._handle_nulls(df)
        nulos_despues = int(df.isnull().sum().sum())
        self._report["nulos_antes"] = nulos_antes
        self._report["nulos_despues"] = nulos_despues
        print(f"[DataCleaner] Nulos antes={nulos_antes} | después={nulos_despues}")

        # 3. Espacios en columnas de texto
        str_cols = df.select_dtypes(include=["object", "str"]).columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()

        self._report["filas_originales"] = original_rows
        self._report["filas_finales"] = len(df)
        print(f"[DataCleaner] Filas: {original_rows} → {len(df)}")
        return df

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.null_strategy == "drop":
            return df.dropna()

        if self.null_strategy == "fill":
            for col in df.columns:
                if df[col].isnull().sum() == 0:
                    continue
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    moda = df[col].mode()
                    fill_val = moda.iloc[0] if not moda.empty else "UNKNOWN"
                    df[col] = df[col].fillna(fill_val)
            return df

        # 'none' – sin cambios
        return df

    @property
    def report(self) -> dict:
        return self._report
