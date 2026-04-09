"""
Módulo del modelo Apriori.
"""
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


class AprioriModel:

    def __init__(
        self,
        min_support: float = 0.1,
        min_confidence: float = 0.5,
        rules_col: str = "Reglas",
        separator: str = ",",
    ):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.rules_col = rules_col
        self.separator = separator
        self.frequent_itemsets_: pd.DataFrame | None = None
        self.rules_: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "AprioriModel":
        """Entrena el modelo sobre el DataFrame transformado."""
        transactions = list(
            df[self.rules_col].apply(
                lambda x: [i.strip() for i in str(x).split(self.separator)]
            )
        )

        te = TransactionEncoder()
        te_array = te.fit(transactions).transform(transactions)
        df_encoded = pd.DataFrame(te_array, columns=te.columns_).replace(False, 0)

        self.frequent_itemsets_ = apriori(
            df_encoded, min_support=self.min_support, use_colnames=True, verbose=0
        )
        self.rules_ = association_rules(
            self.frequent_itemsets_,
            metric="confidence",
            min_threshold=self.min_confidence,
        )
        print(
            f"[AprioriModel] Itemsets frecuentes: {len(self.frequent_itemsets_)} | "
            f"Reglas generadas: {len(self.rules_)}"
        )
        return self

    def get_top_rules(self, n: int = 10) -> pd.DataFrame:
        """Retorna las n mejores reglas ordenadas por lift."""
        self._check_fitted()
        return self.rules_.sort_values("lift", ascending=False).head(n)

    def plot_confidence_lift(self, save_path: str | None = None):
        """Scatter plot Confidence vs Lift."""
        self._check_fitted()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(
            self.rules_["confidence"],
            self.rules_["lift"],
            alpha=0.7,
            color="steelblue",
            edgecolors="k",
            s=60,
        )
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Lift")
        ax.set_title("Apriori – Confidence vs Lift")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120, bbox_inches="tight")
            print(f"[AprioriModel] Plot guardado: {save_path}")
        plt.show()

    def plot_network(self, save_path: str | None = None):
        """Grafo de reglas de asociación."""
        self._check_fitted()
        G = nx.DiGraph()
        for _, row in self.rules_.iterrows():
            G.add_edge(
                tuple(row["antecedents"]),
                tuple(row["consequents"]),
                weight=row["confidence"],
            )
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, with_labels=True, node_color="lightblue",
                edge_color="gray", node_size=3000, font_size=9, arrows=True)
        edge_labels = {
            (tuple(r["antecedents"]), tuple(r["consequents"])): f"{r['confidence']:.2f}"
            for _, r in self.rules_.iterrows()
        }
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        plt.title("Apriori – Red de Reglas de Asociación")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120, bbox_inches="tight")
            print(f"[AprioriModel] Grafo guardado: {save_path}")
        plt.show()

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    def _check_fitted(self):
        if self.rules_ is None:
            raise RuntimeError("Ejecute fit() antes de llamar este método.")
