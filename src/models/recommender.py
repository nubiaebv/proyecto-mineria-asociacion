"""
Módulo de recomendaciones de negocio.
"""
from __future__ import annotations
import pandas as pd


class Recommender:
    """
    Sistema de recomendación basado en reglas de asociación.

    """

    def __init__(self, top_n: int = 5, min_lift: float = 1.0):
        self.top_n = top_n
        self.min_lift = min_lift
        self._rules: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def fit(self, rules_df: pd.DataFrame) -> "Recommender":
        """
        Carga las reglas de asociación.

        """
        required = {"antecedents", "consequents", "confidence", "lift"}
        if not required.issubset(rules_df.columns):
            raise ValueError(f"El DataFrame de reglas debe tener: {required}")
        self._rules = rules_df.copy()
        print(f"[Recommender] {len(self._rules)} reglas cargadas.")
        return self

    def recommend(self, items: list[str]) -> pd.DataFrame:
        """
        Dado un set de ítems (ej. ['Software', 'LATAM']),
        retorna las recomendaciones más relevantes.
        """
        self._check_fitted()
        items_set = frozenset(i.strip() for i in items)

        # Filtrar reglas cuyo antecedente esté contenido en los ítems dados
        mask = self._rules["antecedents"].apply(
            lambda ant: bool(frozenset(ant) & items_set)
        )
        candidates = self._rules[mask & (self._rules["lift"] >= self.min_lift)]

        if candidates.empty:
            print(f"[Recommender] Sin recomendaciones para: {items}")
            return pd.DataFrame()

        top = candidates.sort_values(
            ["lift", "confidence"], ascending=False
        ).head(self.top_n)

        result = top[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
        result["propuesta"] = result.apply(self._build_proposal, axis=1)
        return result.reset_index(drop=True)

    def business_proposals(self, top_n: int | None = None) -> pd.DataFrame:
        """
        Genera las top N propuestas de negocio globales (sin filtro de ítem).
        """
        self._check_fitted()
        n = top_n or self.top_n
        top = self._rules.sort_values(
            ["lift", "confidence"], ascending=False
        ).head(n).copy()
        top["propuesta"] = top.apply(self._build_proposal, axis=1)
        return top[["antecedents", "consequents", "support", "confidence", "lift", "propuesta"]].reset_index(drop=True)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    @staticmethod
    def _build_proposal(row) -> str:
        ant = ", ".join(sorted(row["antecedents"]))
        con = ", ".join(sorted(row["consequents"]))
        conf = row["confidence"]
        lift = row["lift"]
        return (
            f"Clientes que adquieren [{ant}] tienen un {conf*100:.1f}% de probabilidad "
            f"de también adquirir [{con}] (lift={lift:.2f}). "
            f"Se recomienda crear un bundle o campaña cruzada entre estos productos/segmentos."
        )

    def _check_fitted(self):
        if self._rules is None:
            raise RuntimeError("Ejecute fit() antes de llamar este método.")


class AssociationRecommender(Recommender):
    """
    Alias del Recommender con la API que espera el dashboard.
    """

    def __init__(self, rules_df: pd.DataFrame, min_lift: float = 1.0):
        super().__init__(min_lift=min_lift)
        if not rules_df.empty:
            self.fit(rules_df)

    def recommend(self, items: list[str], top_n: int = 8) -> pd.DataFrame:  # type: ignore[override]
        """
        Retorna recomendaciones con columna 'item_recomendado' para el dashboard.

        """
        self.top_n = top_n
        base = super().recommend(items)
        if base.empty:
            return base

        rows = []
        for _, row in base.iterrows():
            for item in sorted(row["consequents"]):
                rows.append({
                    "item_recomendado": item,
                    "support":    round(row["support"],    4),
                    "confidence": round(row["confidence"], 4),
                    "lift":       round(row["lift"],       4),
                })
        result = pd.DataFrame(rows).drop_duplicates("item_recomendado")
        return result.head(top_n).reset_index(drop=True)
