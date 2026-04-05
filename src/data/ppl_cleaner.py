# -*- coding: utf-8 -*-
import re, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

_DATE    = re.compile(r"date|fecha|time|dt|timestamp|periodo|period", re.I)
_ID      = re.compile(r"\bid\b|_id$|^id_|invoice|order.?id|row.?id|customer.?id|sku", re.I)
_NUMERIC = re.compile(r"price|precio|sales|venta|revenue|ingreso|profit|ganancia|"
                       r"discount|descuento|quantity|cantidad|amount|monto|cost|costo|"
                       r"weight|peso|score|rate|tasa|total|subtotal", re.I)
_TEXT    = re.compile(r"name|nombre|description|descripcion|city|ciudad|country|pais|"
                       r"region|segment|industry|product|category|brand|contact|"
                       r"address|license|subregion", re.I)

NULL_STRINGS = {"nan", "none", "null", "n/a", "na", "", "-", "--", "?"}
DATE_FMT     = "%Y-%m-%d %H:%M:%S"


class DataFrameCleaner:
    def __init__(self, df, date_fmt=DATE_FMT, col_null=0.9, row_null=0.5, cat_fill="ffill"):
        self.df, self.raw = df.copy(), df.copy()
        self.date_fmt, self.col_null, self.row_null, self.cat_fill = date_fmt, col_null, row_null, cat_fill
        self.dates = self.nums = self.ids = self.texts = []
        self._log = []

    @classmethod
    def from_file(cls, path, **kw):
        path, ext = Path(path), Path(path).suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        elif ext == ".csv":
            try:
                df = pd.read_csv(path, sep=",", encoding="utf-8-sig")
                if df.shape[1] == 1:
                    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="latin-1")
        elif ext == ".parquet": df = pd.read_parquet(path)
        elif ext == ".json":    df = pd.read_json(path)
        else: raise ValueError("Extension no soportada: " + ext)
        return cls(df, **kw)

    def clean(self):
        for step in [self._prep, self._infer, self._cast, self._nulls, self._impute]:
            step()
        self._print_log()
        return self.df.reset_index(drop=True)

    def _prep(self):
        self.df.columns = self.df.columns.astype(str).str.lstrip("\ufeff").str.strip().str.replace(r"\s+", " ", regex=True)
        self.df = self.df.dropna(axis=1, how="all").drop_duplicates()
        for col in self.df.select_dtypes("object").columns:
            mask = self.df[col].astype(str).str.fullmatch(r"#+")
            if mask.any():
                self._log.append("'{}': {} valores '####' eliminados.".format(col, mask.sum()))
                self.df = self.df[~mask]

    def _infer(self):
        self.dates, self.nums, self.ids, self.texts = [], [], [], []
        for col in self.df.columns:
            if   _DATE.search(col):    self.dates.append(col)
            elif _ID.search(col):      self.ids.append(col)
            elif _NUMERIC.search(col): self.nums.append(col)
            elif _TEXT.search(col):    self.texts.append(col)
            else:
                s = self.df[col].dropna().head(50).astype(str)
                if pd.to_datetime(s, errors="coerce").notna().mean() > 0.7:
                    self.dates.append(col)
                elif pd.to_numeric(s.str.replace(r"[€$£, ]", "", regex=True), errors="coerce").notna().mean() > 0.7:
                    self.nums.append(col)
                else:
                    self.texts.append(col)

    def _cast(self):
        for col in self.dates:
            self.df[col] = pd.to_datetime(self.df[col], errors="coerce").dt.strftime(self.date_fmt)
        for col in self.nums:
            if self.df[col].dtype == object:
                self.df[col] = self.df[col].astype(str).str.replace(r"[€$£,\s]", "", regex=True)
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        for col in self.ids:
            s = self.df[col].dropna().astype(str).head(20)
            if pd.to_numeric(s, errors="coerce").notna().mean() > 0.8:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce").astype("Int64")
        for col in self.texts:
            self.df[col] = self.df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
            self.df[col] = self.df[col].where(~self.df[col].str.lower().isin(NULL_STRINGS), np.nan)

    def _nulls(self):
        to_drop = self.df.columns[self.df.isna().mean() > self.col_null].tolist()
        if to_drop:
            self.df.drop(columns=to_drop, inplace=True)
            self._log.append("Columnas con >{}% nulos eliminadas: {}".format(int(self.col_null*100), to_drop))
        mask = self.df.isna().mean(axis=1) > self.row_null
        if mask.any():
            self._log.append("Filas con >{}% nulos eliminadas: {}".format(int(self.row_null*100), int(mask.sum())))
            self.df = self.df[~mask]

    def _impute(self):
        for col in [c for c in self.nums if c in self.df.columns]:
            n = int(self.df[col].isna().sum())
            if not n: continue
            self.df[col] = self.df[col].interpolate(method="linear", limit_direction="both").fillna(self.df[col].median())
            self._log.append("'{}': {} nulos imputados (interpolacion).".format(col, n))

        for col in [c for c in self.texts + self.ids if c in self.df.columns]:
            n = int(self.df[col].isna().sum())
            if not n: continue
            if   self.cat_fill == "ffill":
                self.df[col] = self.df[col].ffill().bfill(); label = "ffill+bfill"
            elif self.cat_fill == "mode":
                mv = self.df[col].mode(); fill = mv.iloc[0] if not mv.empty else "Unknown"
                self.df[col] = self.df[col].fillna(fill); label = "moda ('{}')".format(fill)
            else:
                self.df[col] = self.df[col].fillna("Unknown"); label = "'Unknown'"
            self._log.append("'{}': {} nulos ({:.1f}%) imputados con {}.".format(col, n, n/len(self.df)*100, label))

    def _print_log(self):
        print("\n[pipeline] Resumen:")
        for l in self._log: print("  .", l)
        print("  . Shape final:", self.df.shape, "\n")

    def report(self):
        return pd.DataFrame([{
            "column": c, "dtype": str(self.df[c].dtype),
            "nulls": int(self.df[c].isna().sum()),
            "nulls_%": round(self.df[c].isna().mean()*100, 1),
            "unique": self.df[c].nunique(),
            "sample": self.df[c].dropna().iloc[0] if not self.df[c].dropna().empty else None,
        } for c in self.df.columns])


def run_pipeline(source, cat_fill="ffill", **kw):
    """run_pipeline("archivo.csv"|df, cat_fill="ffill"|"mode"|"unknown")"""
    if isinstance(source, pd.DataFrame):
        return DataFrameCleaner(source, cat_fill=cat_fill, **kw).clean()
    return DataFrameCleaner.from_file(source, cat_fill=cat_fill, **kw).clean()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: py -3.12 ppl_cleaner.py <archivo> [ffill|mode|unknown]"); sys.exit(1)
    path, strategy = Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "ffill"
    print("[pipeline] Archivo   :", path)
    print("[pipeline] Estrategia:", strategy)
    df_clean = run_pipeline(path, cat_fill=strategy)
    print(df_clean.head(10).to_string())
    out = path.with_name(path.stem + "_clean.parquet")
    df_clean.to_parquet(out, index=False)
    print("\n[pipeline] Guardado en:", out)