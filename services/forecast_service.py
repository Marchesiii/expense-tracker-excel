import pandas as pd

from domain.enums import AlertStatus, TransactionType
from domain.validators import clean_numeric_series, has_required_columns
from services.normalization_service import normalize_transaction_dataframe


def forecast_next_month(df, months_considered=3):
    """Calcula a previsão do próximo mês por categoria com base no histórico recente."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["category", "media_historica", "previsao_proximo_mes", "status"])

    normalized = normalize_transaction_dataframe(df)
    if not has_required_columns(normalized, ["category", "amount", "data"]):
        return pd.DataFrame(columns=["category", "media_historica", "previsao_proximo_mes", "status"])

    normalized = normalized.copy()
    normalized["amount"] = clean_numeric_series(normalized["amount"])
    normalized["data_dt"] = pd.to_datetime(normalized["data"], format="%d-%m-%Y", errors="coerce")
    normalized = normalized.dropna(subset=["amount", "category", "data_dt"])
    normalized = normalized[normalized["tipo"] == TransactionType.EXPENSE]

    if normalized.empty:
        return pd.DataFrame(columns=["category", "media_historica", "previsao_proximo_mes", "status"])

    normalized["mes"] = normalized["data_dt"].dt.to_period("M")
    historico = normalized.groupby(["category", "mes"], as_index=False)["amount"].sum()
    historico = historico.sort_values(["category", "mes"]).reset_index(drop=True)

    historico_ultimos_meses = historico.groupby("category", group_keys=False).tail(months_considered)
    media_por_categoria = (
        historico_ultimos_meses.groupby("category", as_index=False)["amount"]
        .mean()
        .rename(columns={"amount": "media_historica"})
    )

    ultima_data = historico["mes"].max()
    ultimo_mes = historico[historico["mes"] == ultima_data].rename(columns={"amount": "gasto_ultimo_mes"})

    previsao = media_por_categoria.merge(ultimo_mes[["category", "gasto_ultimo_mes"]], on="category", how="left")
    previsao["previsao_proximo_mes"] = previsao["media_historica"].round(2)
    previsao["status"] = previsao.apply(
        lambda row: AlertStatus.ABOVE_AVERAGE if row["previsao_proximo_mes"] > row.get("gasto_ultimo_mes", 0) else AlertStatus.STABLE,
        axis=1,
    )

    return previsao[["category", "media_historica", "previsao_proximo_mes", "status"]].sort_values("previsao_proximo_mes", ascending=False).reset_index(drop=True)


def _strip_category_suffix(category):
    """Remove os últimos tokens (normalmente nome de quem recebeu o pagamento) do texto da categoria."""
    tokens = str(category).strip().split()
    if len(tokens) > 1:
        tokens = tokens[:-3]
    return " ".join(tokens) if tokens else "Outros"


def recurring_expenses_forecast(df, min_occurrences=10, min_months=2):
    """Identifica categorias de despesa recorrentes (fixas/mistas/variáveis) com base na frequência mensal."""
    columns = ["category", "previsao_mensal", "qtd_ocorrencias", "tipo_categoria"]
    if df is None or df.empty:
        return pd.DataFrame(columns=columns)

    normalized = normalize_transaction_dataframe(df)
    if not has_required_columns(normalized, ["category", "amount", "data"]):
        return pd.DataFrame(columns=columns)

    normalized = normalized.copy()
    normalized["amount"] = clean_numeric_series(normalized["amount"])
    normalized["data_dt"] = pd.to_datetime(normalized["data"], format="%d-%m-%Y", errors="coerce")
    normalized = normalized.dropna(subset=["amount", "category", "data_dt"])
    normalized = normalized[normalized["tipo"] == TransactionType.EXPENSE]
    if normalized.empty:
        return pd.DataFrame(columns=columns)

    normalized["category"] = normalized["category"].apply(_strip_category_suffix)
    normalized["mes"] = normalized["data_dt"].dt.to_period("M")

    ocorrencias_mensais = normalized.groupby(["category", "mes"]).agg(
        soma_despesas=("amount", "sum"),
        qtd_ocorrencias=("amount", "count"),
    ).reset_index()
    ocorrencias_mensais = ocorrencias_mensais[ocorrencias_mensais["qtd_ocorrencias"] > min_occurrences]
    if ocorrencias_mensais.empty:
        return pd.DataFrame(columns=columns)

    frequencia_mensal = ocorrencias_mensais.groupby("category")["mes"].nunique().reset_index()
    frequencia_mensal.rename(columns={"mes": "meses_com_recorrencia"}, inplace=True)

    categorias_consistentes = frequencia_mensal[frequencia_mensal["meses_com_recorrencia"] >= min_months]["category"]
    ocorrencias_consistentes = ocorrencias_mensais[ocorrencias_mensais["category"].isin(categorias_consistentes)]

    resumo_categoria = ocorrencias_consistentes.groupby("category").agg(
        media_despesas=("soma_despesas", "mean"),
        qtd_ocorrencias=("qtd_ocorrencias", "mean"),
    ).reset_index()
    resumo_categoria["previsao_mensal"] = resumo_categoria["media_despesas"].round(2)
    resumo_categoria = resumo_categoria.merge(frequencia_mensal, on="category", how="left")
    resumo_categoria["tipo_categoria"] = resumo_categoria["meses_com_recorrencia"].apply(
        lambda meses: "fixa" if meses >= 5 else ("mista" if meses >= 3 else "variável")
    )

    return resumo_categoria[columns].sort_values("previsao_mensal", ascending=False).reset_index(drop=True)
