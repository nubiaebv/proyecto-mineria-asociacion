"""
Módulo de transformación de datos.
Construir la columna 'Reglas' que alimenta los modelos
de minería de asociación.
"""
import pandas as pd


class DataTransformer:
    """
    Transforma el DataFrame crudo en uno listo para minería de asociación.
    """

    def __init__(
        self,
        rule_columns: list[str] | None = None,
        separator: str = ",",
        output_col: str = "Reglas",
    ):
        self.rule_columns = rule_columns
        self.separator = separator
        self.output_col = output_col

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrega la columna 'Reglas' y retorna el DataFrame enriquecido."""
        df = df.copy()

        cols = self._resolve_columns(df)
        print(f"[DataTransformer] Columnas usadas para Reglas: {cols}")

        df[self.output_col] = df[cols].apply(
            lambda row: self.separator.join(row.astype(str).str.strip()), axis=1
        )
        print(f"[DataTransformer] Columna '{self.output_col}' creada. "
              f"Ejemplo: {df[self.output_col].iloc[0]}")
        return df

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    def _resolve_columns(self, df: pd.DataFrame) -> list[str]:
        if self.rule_columns:
            missing = [c for c in self.rule_columns if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Columnas no encontradas en el DataFrame: {missing}\n"
                    f"Columnas disponibles: {df.columns.tolist()}"
                )
            return self.rule_columns

        # Inferencia automática: usa todas las columnas categóricas
        inferred = df.select_dtypes(include=["object", "str"]).columns.tolist()
        if not inferred:
            raise ValueError(
                "No se encontraron columnas categóricas. "
                "Especifique 'rule_columns' manualmente."
            )
        print(f"[DataTransformer] Columnas inferidas automáticamente: {inferred}")
        return inferred
