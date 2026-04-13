"""
Módulo de Análisis Exploratorio de Datos (EDA).
 Calcular y mostrar estadísticas descriptivas básicas.
"""
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")


class EDAAnalyzer:
    """
    Realiza el análisis exploratorio completo sobre un DataFrame.

    """

    def __init__(
        self,
        figsize: tuple = (14, 5),
        save_plots: bool = False,
        reports_path: str | None = None,
    ):
        self.figsize = figsize
        self.save_plots = save_plots
        self.reports_path = reports_path
        self._summary: dict = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def analyze(self, df: pd.DataFrame) -> dict:
        """Ejecuta el EDA completo y retorna un diccionario con el resumen."""
        print("\n" + "=" * 60)
        print("  ANÁLISIS EXPLORATORIO DE DATOS")
        print("=" * 60)

        self._dimensiones(df)
        self._tipos_datos(df)
        self._estadisticas_numericas(df)
        self._estadisticas_categoricas(df)
        self._duplicados(df)
        self._nulos(df)
        self._plots_sin_outliers(df)

        print("\n[EDAAnalyzer] Análisis completo.\n")
        return self._summary

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    def _dimensiones(self, df: pd.DataFrame):
        print(f"\n📐 Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")
        self._summary["shape"] = df.shape

    def _tipos_datos(self, df: pd.DataFrame):
        print("\n🔤 Tipos de datos:")
        print(df.dtypes.to_string())
        self._summary["dtypes"] = df.dtypes.to_dict()

    def _estadisticas_numericas(self, df: pd.DataFrame):
        num_cols = df.select_dtypes(include=["int64", "float64"]).columns
        if len(num_cols) == 0:
            return
        print("\n📊 Estadísticas numéricas:")
        desc = df[num_cols].describe().T
        print(desc.to_string())
        extras = {}
        for col in num_cols:
            extras[col] = {
                "media": round(df[col].mean(), 4),
                "mediana": round(df[col].median(), 4),
                "moda": df[col].mode().iloc[0] if not df[col].mode().empty else None,
                "std": round(df[col].std(), 4),
                "skewness": round(df[col].skew(), 4),
                "kurtosis": round(df[col].kurtosis(), 4),
            }
        self._summary["numeric_stats"] = extras

    def _estadisticas_categoricas(self, df: pd.DataFrame):
        cat_cols = df.select_dtypes(include=["object", "str"]).columns
        if len(cat_cols) == 0:
            return
        print("\n🏷️  Estadísticas categóricas:")
        cat_stats = {}
        for col in cat_cols:
            n_unique = df[col].nunique()
            most_freq = df[col].mode().iloc[0] if not df[col].mode().empty else None
            top5 = df[col].value_counts().head(5).to_dict()
            print(f"  {col}: {n_unique} únicos | más frecuente: '{most_freq}'")
            cat_stats[col] = {"n_unique": n_unique, "most_frequent": most_freq, "top5": top5}
        self._summary["categorical_stats"] = cat_stats

    def _duplicados(self, df: pd.DataFrame):
        n_dups = df.duplicated().sum()
        pct = round(n_dups / len(df) * 100, 2) if len(df) > 0 else 0
        print(f"\n🔁 Duplicados: {n_dups} ({pct}%)")
        self._summary["duplicados"] = {"cantidad": int(n_dups), "porcentaje": pct}

    def _nulos(self, df: pd.DataFrame):
        total_nulos = df.isnull().sum().sum()
        pct = round(total_nulos / df.size * 100, 2)
        print(f"\n⚠️  Nulos totales: {total_nulos} ({pct}%)")
        por_col = df.isnull().sum()
        por_col = por_col[por_col > 0]
        if len(por_col):
            print(por_col.to_string())
        self._summary["nulos"] = {"total": int(total_nulos), "porcentaje": pct}

    def _plots_sin_outliers(self, df: pd.DataFrame):
        num_cols = df.select_dtypes(include=["int64", "float64"]).columns
        if len(num_cols) == 0:
            return

        df_plot = df.copy()
        for col in num_cols:
            Q1 = df_plot[col].quantile(0.25)
            Q3 = df_plot[col].quantile(0.75)
            IQR = Q3 - Q1
            df_plot[col] = df_plot[col].where(
                (df_plot[col] >= Q1 - 1.5 * IQR) &
                (df_plot[col] <= Q3 + 1.5 * IQR)
            )

        n_cols = 3
        n_rows = (len(num_cols) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(self.figsize[0], 4 * n_rows))
        axes = axes.flatten() if len(num_cols) > 1 else [axes]

        for idx, col in enumerate(num_cols):
            axes[idx].boxplot(df_plot[col].dropna(), vert=True)
            axes[idx].set_title(f"Boxplot – {col}", fontweight="bold")
            axes[idx].grid(alpha=0.3)

        for idx in range(len(num_cols), len(axes)):
            axes[idx].set_visible(False)

        plt.suptitle("Boxplots sin outliers extremos", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if self.save_plots and self.reports_path:
            path = f"{self.reports_path}/eda_boxplots_sin_outliers.png"
            plt.savefig(path, dpi=120, bbox_inches="tight")
            print(f"[EDAAnalyzer] Plot guardado: {path}")
        plt.show()
