import pandas as pd


def has_required_columns(df, required_columns):
    if df is None or df.empty:
        return False
    return set(required_columns).issubset(set(df.columns))


def clean_numeric_series(series):
    return pd.to_numeric(series, errors="coerce")
