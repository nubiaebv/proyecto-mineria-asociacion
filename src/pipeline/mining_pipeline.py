"""
Pipeline principal de Minería de Datos.
Orquestar todos los pasos: carga → limpieza → transformación → EDA → modelos → recomendaciones.

"""
from __future__ import annotations
from pathlib import Path

import pandas as pd

from src.pipeline.data_loader import DataLoader
from src.pipeline.data_cleaner import DataCleaner
from src.pipeline.data_transformer import DataTransformer
from src.pipeline.eda_analyzer import EDAAnalyzer
from src.models.apriori_model import AprioriModel
from src.models.eclat_model import ECLATModel
from src.models.recommender import Recommender


class MiningPipeline:
    """
    Orquestador del pipeline completo de minería de asociación.
    """

    def __init__(
        self,
        csv_path: str | Path,
        rule_columns: list[str] | None = None,
        min_support_apriori: float = 0.1,
        min_confidence_apriori: float = 0.5,
        min_support_eclat: float = 0.2,
        min_confidence_eclat: float = 0.5,
        null_strategy: str = "drop",
        save_plots: bool = False,
        reports_path: str | None = None,
    ):
        self.csv_path = Path(csv_path)
        self.rule_columns = rule_columns
        self.min_support_apriori = min_support_apriori
        self.min_confidence_apriori = min_confidence_apriori
        self.min_support_eclat = min_support_eclat
        self.min_confidence_eclat = min_confidence_eclat
        self.null_strategy = null_strategy
        self.save_plots = save_plots
        self.reports_path = reports_path or str(self.csv_path.parent.parent / "reports")

        # Resultados accesibles tras ejecutar run()
        self.df_raw_: pd.DataFrame | None = None
        self.df_clean_: pd.DataFrame | None = None
        self.df_transformed_: pd.DataFrame | None = None
        self.eda_summary_: dict = {}
        self.apriori_: AprioriModel | None = None
        self.eclat_: ECLATModel | None = None
        self.recommender_apriori_: Recommender | None = None
        self.recommender_eclat_: Recommender | None = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def run(self) -> "MiningPipeline":
        """Ejecuta el pipeline completo de principio a fin."""
        print("\n" + "★" * 60)
        print("  PIPELINE DE MINERÍA DE DATOS – INICIO")
        print("★" * 60)

        self._step_load()
        self._step_clean()
        self._step_transform()
        self._step_eda()
        self._step_apriori()
        self._step_eclat()
        self._step_recommender()

        print("\n" + "★" * 60)
        print("  PIPELINE FINALIZADO CON ÉXITO")
        print("★" * 60)
        return self

    def recommend(self, items: list[str], model: str = "apriori") -> pd.DataFrame:
        """
        Genera recomendaciones para los ítems dados.
        """
        rec = self.recommender_apriori_ if model == "apriori" else self.recommender_eclat_
        if rec is None:
            raise RuntimeError("Ejecute run() antes de pedir recomendaciones.")
        return rec.recommend(items)

    def top_proposals(self, model: str = "apriori", n: int = 10) -> pd.DataFrame:
        """Retorna las top N propuestas de negocio globales."""
        rec = self.recommender_apriori_ if model == "apriori" else self.recommender_eclat_
        if rec is None:
            raise RuntimeError("Ejecute run() antes de pedir propuestas.")
        return rec.business_proposals(top_n=n)

    # ------------------------------------------------------------------
    # Pasos privados del pipeline
    # ------------------------------------------------------------------
    def _step_load(self):
        print("\n── PASO 1: Carga de datos ──")
        loader = DataLoader(self.csv_path)
        self.df_raw_ = loader.load()

    def _step_clean(self):
        print("\n── PASO 2: Limpieza de datos ──")
        cleaner = DataCleaner(null_strategy=self.null_strategy)
        self.df_clean_ = cleaner.clean(self.df_raw_)

    def _step_transform(self):
        print("\n── PASO 3: Transformación de datos ──")
        transformer = DataTransformer(rule_columns=self.rule_columns)
        self.df_transformed_ = transformer.transform(self.df_clean_)

        # Guardar CSV procesado
        processed_path = self.csv_path.parent.parent / "data" / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        out_file = processed_path / self.csv_path.name
        self.df_transformed_.to_csv(out_file, index=False, encoding="utf-8")
        print(f"[Pipeline] CSV procesado guardado: {out_file}")

    def _step_eda(self):
        print("\n── PASO 4: Análisis Exploratorio (EDA) ──")
        Path(self.reports_path).mkdir(parents=True, exist_ok=True)
        eda = EDAAnalyzer(save_plots=self.save_plots, reports_path=self.reports_path)
        self.eda_summary_ = eda.analyze(self.df_clean_)

    def _step_apriori(self):
        print("\n── PASO 5: Modelo Apriori ──")
        self.apriori_ = AprioriModel(
            min_support=self.min_support_apriori,
            min_confidence=self.min_confidence_apriori,
        ).fit(self.df_transformed_)

        ap_path = f"{self.reports_path}/apriori_scatter.png" if self.save_plots else None
        an_path = f"{self.reports_path}/apriori_network.png" if self.save_plots else None
        if len(self.apriori_.rules_) > 0:
            self.apriori_.plot_confidence_lift(save_path=ap_path)
            self.apriori_.plot_network(save_path=an_path)
        else:
            print("[Pipeline] Apriori: sin reglas con los umbrales actuales. "
                  "Pruebe reducir min_support o min_confidence.")

    def _step_eclat(self):
        print("\n── PASO 6: Modelo ECLAT ──")
        self.eclat_ = ECLATModel(
            min_support=self.min_support_eclat,
            min_confidence=self.min_confidence_eclat,
        ).fit(self.df_transformed_)

        es_path = f"{self.reports_path}/eclat_scatter.png" if self.save_plots else None
        en_path = f"{self.reports_path}/eclat_network.png" if self.save_plots else None
        if self.eclat_.df_rules_ is not None and len(self.eclat_.df_rules_) > 0:
            self.eclat_.plot_confidence_lift(save_path=es_path)
            self.eclat_.plot_network(save_path=en_path)
        else:
            print("[Pipeline] ECLAT: sin reglas con los umbrales actuales. "
                  "Pruebe reducir min_support o min_confidence.")

    def _step_recommender(self):
        print("\n── PASO 7: Sistema de Recomendación ──")
        if self.apriori_.rules_ is not None and len(self.apriori_.rules_) > 0:
            self.recommender_apriori_ = Recommender().fit(self.apriori_.rules_)

        if (self.eclat_.df_rules_ is not None
                and len(self.eclat_.df_rules_) > 0):
            self.recommender_eclat_ = Recommender().fit(self.eclat_.df_rules_)

    def export_rules_for_dashboard(self, output_path: str) -> None:
        """
        Exporta las reglas Apriori (o ECLAT si no hay Apriori) a un CSV
        listo para que el dashboard lo consuma.
        """
        import os
        rules = None
        if self.apriori_ is not None and self.apriori_.rules_ is not None \
                and len(self.apriori_.rules_) > 0:
            rules = self.apriori_.rules_.copy()
        elif self.eclat_ is not None and self.eclat_.df_rules_ is not None \
                and len(self.eclat_.df_rules_) > 0:
            rules = self.eclat_.df_rules_.copy()

        if rules is None or rules.empty:
            print(f"[Pipeline] Sin reglas para exportar → {output_path}")
            return

        rules["antecedents"] = rules["antecedents"].apply(lambda x: str(set(x)))
        rules["consequents"] = rules["consequents"].apply(lambda x: str(set(x)))
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        rules[["antecedents", "consequents", "support", "confidence", "lift"]].to_csv(
            output_path, index=False, encoding="utf-8"
        )
        print(f"[Pipeline] Reglas exportadas → {output_path}  ({len(rules)} reglas)")
