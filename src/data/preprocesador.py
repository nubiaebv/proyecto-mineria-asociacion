import pandas as pd
from mlxtend.preprocessing import TransactionEncoder


class Preprocesador:
    """
    Transforma el DataFrame limpio del EDA en una matriz binaria
    de transacciones lista para Apriori y ECLAT.

    Estrategia: cada factura (Invoice) es una transacción compuesta
    por los productos (Description) que contiene.
    """

    def __init__(self, df: pd.DataFrame):
        self.df     = df.copy()
        self.te     = TransactionEncoder()
        self.df_bin = None
        self.transacciones = None

    def _extraer_transacciones(self) -> list[list[str]]:
        """Agrupa por Invoice y devuelve lista de listas de productos."""
        transacciones = (
            self.df.groupby("Invoice")["Description"]
            .apply(lambda x: x.dropna().astype(str).unique().tolist())
            .tolist()
        )
        return transacciones

    def transformar(self) -> pd.DataFrame:
        """Devuelve DataFrame binario (True/False) por producto."""
        self.transacciones = self._extraer_transacciones()
        matriz = self.te.fit_transform(self.transacciones)
        self.df_bin = pd.DataFrame(matriz, columns=self.te.columns_)
        print(f"[Preprocesador] {len(self.transacciones)} transacciones, "
              f"{self.df_bin.shape[1]} productos únicos.")
        return self.df_bin

    def get_transacciones(self) -> list[list[str]]:
        """Devuelve las transacciones en formato lista (para ECLAT)."""
        if self.transacciones is None:
            self.transacciones = self._extraer_transacciones()
        return self.transacciones

