"""
Módulo del modelo ECLAT.
"""
from __future__ import annotations
from collections import defaultdict
from itertools import combinations
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx


class ECLATModel:

    def __init__(
        self,
        min_support: float = 0.2,
        min_confidence: float = 0.5,
        rules_col: str = "Reglas",
        separator: str = ",",
    ):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.rules_col = rules_col
        self.separator = separator
        self.frequent_itemsets_: dict = {}
        self.df_itemsets_: pd.DataFrame | None = None
        self.rules_: list[dict] = []
        self.df_rules_: pd.DataFrame | None = None
        self._n_transactions: int = 0

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "ECLATModel":
        """Ejecuta ECLAT sobre el DataFrame transformado."""
        transactions = list(
            df[self.rules_col].apply(
                lambda x: [i.strip() for i in str(x).split(self.separator)]
            )
        )
        self._n_transactions = len(transactions)
        min_count = max(1, int(self.min_support * self._n_transactions))

        vertical_db = self._build_vertical_db(transactions)
        freq1 = {item: tids for item, tids in vertical_db.items() if len(tids) >= min_count}

        self.frequent_itemsets_ = {
            item: {"support_count": len(tids),
                   "support_pct": round(len(tids) / self._n_transactions, 4)}
            for item, tids in freq1.items()
        }

        items_list = sorted(freq1.items(), key=lambda x: str(sorted(x[0])))
        self._eclat_recursive(frozenset(), items_list, min_count)

        self.rules_ = self._generate_rules()
        self.df_itemsets_, self.df_rules_ = self._to_dataframes()

        print(
            f"[ECLATModel] Itemsets frecuentes: {len(self.frequent_itemsets_)} | "
            f"Reglas generadas: {len(self.rules_)}"
        )
        return self

    def get_top_rules(self, n: int = 10) -> pd.DataFrame:
        """Retorna las n mejores reglas ordenadas por lift."""
        self._check_fitted()
        return self.df_rules_.sort_values("lift", ascending=False).head(n)

    def plot_confidence_lift(self, save_path: str | None = None):
        """Scatter plot Confidence vs Lift."""
        self._check_fitted()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(
            self.df_rules_["confidence"],
            self.df_rules_["lift"],
            alpha=0.6,
            c="steelblue",
            edgecolors="k",
            s=60,
        )
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Lift")
        ax.set_title("ECLAT – Confidence vs Lift")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120, bbox_inches="tight")
            print(f"[ECLATModel] Plot guardado: {save_path}")
        plt.show()

    def plot_network(self, save_path: str | None = None):
        """Grafo de reglas de asociación."""
        self._check_fitted()
        G = nx.DiGraph()
        for _, row in self.df_rules_.iterrows():
            ant = ", ".join(sorted(row["antecedents"]))
            con = ", ".join(sorted(row["consequents"]))
            G.add_edge(ant, con, weight=row["lift"])

        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, node_size=2000, node_color="steelblue", alpha=0.8)
        nx.draw_networkx_labels(G, pos, font_size=9, font_color="white", font_weight="bold")
        nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=20)
        edge_labels = {(u, v): f"lift={d['weight']:.2f}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
        plt.title("ECLAT – Red de Reglas de Asociación")
        plt.axis("off")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120, bbox_inches="tight")
            print(f"[ECLATModel] Grafo guardado: {save_path}")
        plt.show()

    # ------------------------------------------------------------------
    # Algoritmo ECLAT (implementación recursiva)
    # ------------------------------------------------------------------
    @staticmethod
    def _build_vertical_db(transactions: list[list[str]]) -> dict:
        vertical_db: dict = defaultdict(set)
        for tid, transaction in enumerate(transactions):
            for item in transaction:
                vertical_db[frozenset([item])].add(tid)
        return dict(vertical_db)

    def _eclat_recursive(self, prefix, items, min_support):
        while items:
            item, tid_set = items.pop(0)
            new_prefix = prefix | item
            support = len(tid_set)
            if support >= min_support:
                self.frequent_itemsets_[new_prefix] = {
                    "support_count": support,
                    "support_pct": round(support / self._n_transactions, 4),
                }
                suffix = [
                    (other_item, tid_set & other_tid_set)
                    for other_item, other_tid_set in items
                    if len(tid_set & other_tid_set) >= min_support
                ]
                if suffix:
                    self._eclat_recursive(new_prefix, suffix, min_support)

    def _generate_rules(self) -> list[dict]:
        rules = []
        for itemset, stats in self.frequent_itemsets_.items():
            if len(itemset) < 2:
                continue
            for size in range(1, len(itemset)):
                for antecedent in combinations(sorted(itemset), size):
                    antecedent = frozenset(antecedent)
                    consequent = itemset - antecedent
                    if antecedent in self.frequent_itemsets_:
                        ant_sup = self.frequent_itemsets_[antecedent]["support_count"]
                        confidence = round(stats["support_count"] / ant_sup, 4)
                        if confidence >= self.min_confidence:
                            con_sup_pct = self.frequent_itemsets_.get(
                                consequent, {}
                            ).get("support_pct")
                            lift = round(confidence / con_sup_pct, 4) if con_sup_pct else None
                            rules.append({
                                "antecedents": set(antecedent),
                                "consequents": set(consequent),
                                "support": stats["support_pct"],
                                "confidence": confidence,
                                "lift": lift,
                            })
        return sorted(rules, key=lambda r: r["confidence"], reverse=True)

    def _to_dataframes(self):
        df_items = pd.DataFrame([
            {
                "itemset": ", ".join(sorted(k)),
                "tamaño": len(k),
                "support_count": v["support_count"],
                "support": v["support_pct"],
            }
            for k, v in self.frequent_itemsets_.items()
        ]).sort_values(["tamaño", "support_count"], ascending=[True, False])

        df_rules = pd.DataFrame([
            {
                "antecedents": frozenset(r["antecedents"]),
                "consequents": frozenset(r["consequents"]),
                "support": r["support"],
                "confidence": r["confidence"],
                "lift": r["lift"],
            }
            for r in self.rules_
        ])
        return df_items, df_rules

    # ------------------------------------------------------------------
    def _check_fitted(self):
        if self.df_rules_ is None:
            raise RuntimeError("Ejecute fit() antes de llamar este método.")
