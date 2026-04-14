"""
visualizacion_notebook.py – Visualizaciones para explorar reglas de asociación
en el notebook, separadas por algoritmo.
Métodos disponibles: scatter, bar, heatmap, hist, top_rules
"""
import plotly.express as px

# ECLAT


class VisualizacionECLAT:

    def __init__(self, pipeline):
        self.rules = pipeline.eclat_.df_rules_.copy()

    def _prepare(self, min_support=0.02, min_confidence=0.2):
        return self.rules[
            (self.rules["support"]    >= min_support) &
            (self.rules["confidence"] >= min_confidence)
        ].copy()

    def _to_display(self, df):
        d = df.copy()
        d["Antecedente"] = d["antecedents"].apply(lambda x: " + ".join(sorted(x)))
        d["Consecuente"] = d["consequents"].apply(lambda x: " + ".join(sorted(x)))
        return d[["Antecedente", "Consecuente", "support", "confidence", "lift"]].round(4)

    def scatter(self, min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin reglas con esos filtros.")
            return
        d = self._to_display(df)
        px.scatter(
            d, x="support", y="confidence",
            color="lift", size="lift", size_max=22,
            hover_data=["Antecedente", "Consecuente"],
            color_continuous_scale="YlOrRd",
            template="plotly_white",
            title="ECLAT – Soporte vs Confianza",
            labels={"support": "Soporte", "confidence": "Confianza", "lift": "Lift"},
        ).show()

    def bar(self, top_n=15, metric="lift", min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin reglas con esos filtros.")
            return
        d = self._to_display(df.nlargest(top_n, metric))
        d["Regla"] = d["Antecedente"] + "  →  " + d["Consecuente"]
        px.bar(
            d, x=metric, y="Regla", orientation="h",
            color="confidence", color_continuous_scale="Blues",
            text=metric,
            template="plotly_white",
            title=f"ECLAT – Top {top_n} reglas por {metric}",
            labels={metric: metric.capitalize(), "Regla": ""},
        ).update_traces(
            texttemplate="%{text:.3f}", textposition="outside"
        ).update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin={"t": 30, "b": 40, "l": 280, "r": 60},
        ).show()

    def heatmap(self, top_n=20, min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin reglas con esos filtros.")
            return
        top = df.nlargest(top_n, "lift").copy()
        top["ant_str"] = top["antecedents"].apply(lambda x: " + ".join(sorted(x)))
        top["con_str"] = top["consequents"].apply(lambda x: " + ".join(sorted(x)))
        pivot = top.pivot_table(
            index="ant_str", columns="con_str", values="lift", aggfunc="max"
        ).fillna(0)
        px.imshow(
            pivot, color_continuous_scale="Blues", aspect="auto",
            template="plotly_white",
            title="ECLAT – Heatmap de Lift",
            labels={"x": "Consecuente", "y": "Antecedente", "color": "Lift"},
        ).update_layout(
            margin={"t": 30, "b": 80, "l": 180, "r": 20},
            xaxis_tickangle=-35,
        ).show()

    def hist(self, metric="lift", min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin datos con esos filtros.")
            return
        px.histogram(
            df, x=metric, nbins=30,
            color_discrete_sequence=["#3949ab"],
            template="plotly_white",
            title=f"ECLAT – Distribución de {metric}",
            labels={metric: metric.capitalize()},
        ).show()

    def top_rules(self, n=10, min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        return self._to_display(df.sort_values("lift", ascending=False).head(n))



# APRIORI

class VisualizacionApriori:

    def __init__(self, pipeline):
        self.rules = pipeline.apriori_.rules_.copy()

    def _prepare(self, min_support=0.02, min_confidence=0.2):
        return self.rules[
            (self.rules["support"]    >= min_support) &
            (self.rules["confidence"] >= min_confidence)
        ].copy()

    def _to_display(self, df):
        d = df.copy()
        d["Antecedente"] = d["antecedents"].apply(lambda x: " + ".join(sorted(x)))
        d["Consecuente"] = d["consequents"].apply(lambda x: " + ".join(sorted(x)))
        return d[["Antecedente", "Consecuente", "support", "confidence", "lift"]].round(4)

    def scatter(self, min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin reglas con esos filtros.")
            return
        d = self._to_display(df)
        px.scatter(
            d, x="support", y="confidence",
            color="lift", size="lift", size_max=22,
            hover_data=["Antecedente", "Consecuente"],
            color_continuous_scale="YlOrRd",
            template="plotly_white",
            title="Apriori – Soporte vs Confianza",
            labels={"support": "Soporte", "confidence": "Confianza", "lift": "Lift"},
        ).show()

    def bar(self, top_n=15, metric="lift", min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin reglas con esos filtros.")
            return
        d = self._to_display(df.nlargest(top_n, metric))
        d["Regla"] = d["Antecedente"] + "  →  " + d["Consecuente"]
        px.bar(
            d, x=metric, y="Regla", orientation="h",
            color="confidence", color_continuous_scale="Blues",
            text=metric,
            template="plotly_white",
            title=f"Apriori – Top {top_n} reglas por {metric}",
            labels={metric: metric.capitalize(), "Regla": ""},
        ).update_traces(
            texttemplate="%{text:.3f}", textposition="outside"
        ).update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin={"t": 30, "b": 40, "l": 280, "r": 60},
        ).show()

    def heatmap(self, top_n=20, min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin reglas con esos filtros.")
            return
        top = df.nlargest(top_n, "lift").copy()
        top["ant_str"] = top["antecedents"].apply(lambda x: " + ".join(sorted(x)))
        top["con_str"] = top["consequents"].apply(lambda x: " + ".join(sorted(x)))
        pivot = top.pivot_table(
            index="ant_str", columns="con_str", values="lift", aggfunc="max"
        ).fillna(0)
        px.imshow(
            pivot, color_continuous_scale="Blues", aspect="auto",
            template="plotly_white",
            title="Apriori – Heatmap de Lift",
            labels={"x": "Consecuente", "y": "Antecedente", "color": "Lift"},
        ).update_layout(
            margin={"t": 30, "b": 80, "l": 180, "r": 20},
            xaxis_tickangle=-35,
        ).show()

    def hist(self, metric="lift", min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        if df.empty:
            print("Sin datos con esos filtros.")
            return
        px.histogram(
            df, x=metric, nbins=30,
            color_discrete_sequence=["#3949ab"],
            template="plotly_white",
            title=f"Apriori – Distribución de {metric}",
            labels={metric: metric.capitalize()},
        ).show()

    def top_rules(self, n=10, min_support=0.02, min_confidence=0.2):
        df = self._prepare(min_support, min_confidence)
        return self._to_display(df.sort_values("lift", ascending=False).head(n))