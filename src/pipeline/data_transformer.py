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
        """
        Agrega la columna 'Reglas' y retorna el DataFrame transformado.
        Soporta:
        1) Dataset ya por transacción (una fila = una compra)
        2) Dataset transaccional clásico (múltiples filas por factura)
        """
        df = df.copy()

        cols = self._resolve_columns(df)
        print(f"[DataTransformer] Columnas usadas para Reglas: {cols}")

        #  Caso 1: Dataset transaccional clásico (Factura + Producto)
        if self.rule_columns and len(self.rule_columns) == 2: # para cuando se definen manualmente 2 columnas, si no, va al caso 2
            invoice_col, item_col = self.rule_columns

            if df[invoice_col].duplicated().any():
                print("[DataTransformer] Dataset transaccional detectado. Agrupando por factura...")

                grouped = (
                    df.groupby(invoice_col)[item_col]
                    .apply(lambda x: self.separator.join(
                        x.astype(str).str.strip().unique()
                    ))
                    .reset_index()
                )

                grouped = grouped.rename(columns={item_col: self.output_col})
                return grouped

        # Caso 2: Ya viene una fila = una transacción
        df[self.output_col] = df[cols].apply(
            lambda row: self.separator.join(
                row.astype(str).str.strip().unique()
            ),
            axis=1
        )

        print(
            f"[DataTransformer] Columna '{self.output_col}' creada. "
            f"Ejemplo: {df[self.output_col].iloc[0]}"
        )

        return df

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    def _resolve_columns(self, df: pd.DataFrame) -> list[str]:
        if self.rule_columns:
            missing = [c for c in self.rule_columns if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Columnas no encontradas: {missing}\n"
                    f"Disponibles: {df.columns.tolist()}"
                )
            return self.rule_columns

        # Inferencia automática: columnas categóricas
        inferred = df.select_dtypes(include=["object", "string"]).columns.tolist()

        if not inferred:
            raise ValueError(
                "No se encontraron columnas categóricas. "
                "Defina 'rule_columns' manualmente."
            )
        print(f"[DataTransformer] Columnas inferidas automáticamente: {inferred}")
        return inferred