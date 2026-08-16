import pandas as pd

from domain.enums import AlertStatus, TransactionType
from domain.validators import clean_numeric_series, has_required_columns
from services.financial_service import METAS_CATEGORIAS_PADRAO
from services.forecast_service import forecast_next_month
from services.normalization_service import normalize_category, normalize_transaction_dataframe


def get_category_target(category, metas=None):
    if metas is None:
        metas = METAS_CATEGORIAS_PADRAO

    normalized_name = normalize_category(category)
    for key, value in metas.items():
        if normalize_category(key) == normalized_name:
            return value
    return metas.get("outros", 0)


def build_alerts_table(df, metas=None):
    """Cria tabela de metas por categoria e alertas financeiros."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["category", "gasto", "meta", "restante", "percentual", "status", "alerta"])

    normalized = normalize_transaction_dataframe(df)
    if not has_required_columns(normalized, ["category", "amount", "data"]):
        return pd.DataFrame(columns=["category", "gasto", "meta", "restante", "percentual", "status", "alerta"])

    if metas is None:
        metas = METAS_CATEGORIAS_PADRAO

    normalized = normalized.copy()
    normalized["amount"] = clean_numeric_series(normalized["amount"])
    normalized["data_dt"] = pd.to_datetime(normalized["data"], format="%d-%m-%Y", errors="coerce")
    normalized = normalized.dropna(subset=["amount", "category", "data_dt"])
    normalized = normalized[normalized["tipo"] == TransactionType.EXPENSE]

    if normalized.empty:
        return pd.DataFrame(columns=["category", "gasto", "meta", "restante", "percentual", "status", "alerta"])

    mes_atual = normalized["data_dt"].max().to_period("M")
    df_mes = normalized[normalized["data_dt"].dt.to_period("M") == mes_atual]

    resumo = df_mes.groupby("category")["amount"].sum().reset_index().rename(columns={"amount": "gasto"})
    resumo["meta"] = resumo["category"].apply(lambda categoria: get_category_target(categoria, metas))
    resumo["restante"] = resumo["meta"] - resumo["gasto"]
    resumo["percentual"] = resumo.apply(lambda row: (row["gasto"] / row["meta"] * 100) if row["meta"] else 0, axis=1)

    def definir_status(row):
        if row["meta"] == 0:
            return AlertStatus.NO_TARGET
        if row["gasto"] <= row["meta"]:
            return AlertStatus.WITHIN_TARGET
        if row["percentual"] <= 120:
            return AlertStatus.ABOVE_TARGET
        return AlertStatus.CRITICAL

    resumo["status"] = resumo.apply(definir_status, axis=1)
    resumo["alerta"] = resumo["status"].apply(lambda status: "SEM ALERTA" if status in [AlertStatus.WITHIN_TARGET, AlertStatus.NO_TARGET] else "META EXCEDIDA")

    previsao = forecast_next_month(normalized)
    if not previsao.empty:
        resumo = resumo.merge(previsao[["category", "previsao_proximo_mes"]], on="category", how="left")
        resumo["alerta"] = resumo.apply(
            lambda row: "PREVISÃO ACIMA DA META" if pd.notna(row.get("previsao_proximo_mes")) and row.get("meta", 0) and row.get("previsao_proximo_mes", 0) > row.get("meta", 0) else row.get("alerta", "SEM ALERTA"),
            axis=1,
        )

    return resumo.sort_values(["percentual", "gasto"], ascending=[False, False]).reset_index(drop=True)
