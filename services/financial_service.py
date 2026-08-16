import pandas as pd

from domain.enums import TransactionType
from domain.models import FinancialSummary
from domain.validators import clean_numeric_series, has_required_columns
from services.normalization_service import normalize_transaction_dataframe


METAS_CATEGORIAS_PADRAO = {
    "alimentação": 1800,
    "transporte": 900,
    "combustível": 1200,
    "marketing": 700,
    "estoque": 2500,
    "manutenção": 600,
    "outros": 500,
}


def analyze_cashflow(df):
    """Analisa o fluxo de caixa: ganhos totais, despesas totais e saldo."""
    if df is None or df.empty:
        return None

    normalized = normalize_transaction_dataframe(df)
    if not has_required_columns(normalized, ["tipo", "amount"]):
        return None

    total_gains = normalized[normalized["tipo"] == TransactionType.GAIN]["amount"].sum()
    total_expenses = normalized[normalized["tipo"] == TransactionType.EXPENSE]["amount"].sum()
    balance = total_gains - total_expenses
    category_summary = normalized.groupby(["tipo", "category"])["amount"].sum()
    return FinancialSummary(total_gains, total_expenses, balance, category_summary)


def build_dashboard_summary(df):
    """Retorna os KPIs principais para o dashboard central."""
    if df is None or df.empty:
        return {}

    normalized = normalize_transaction_dataframe(df).copy()
    if not has_required_columns(normalized, ["amount", "data", "tipo"]):
        return {}

    normalized["amount"] = clean_numeric_series(normalized["amount"])
    normalized["data_dt"] = pd.to_datetime(normalized["data"], format="%d-%m-%Y", errors="coerce")
    normalized = normalized.dropna(subset=["amount", "tipo", "data_dt"]).copy()
    normalized = normalized[normalized["amount"] > 0]

    total_ganhos = normalized[normalized["tipo"] == TransactionType.GAIN]["amount"].sum()
    total_despesas = normalized[normalized["tipo"] == TransactionType.EXPENSE]["amount"].sum()
    saldo_total = total_ganhos - total_despesas

    mes_atual = normalized["data_dt"].max().to_period("M")
    df_mes_atual = normalized[normalized["data_dt"].dt.to_period("M") == mes_atual]

    ganhos_mes = df_mes_atual[df_mes_atual["tipo"] == TransactionType.GAIN]["amount"].sum()
    despesas_mes = df_mes_atual[df_mes_atual["tipo"] == TransactionType.EXPENSE]["amount"].sum()
    saldo_mes = ganhos_mes - despesas_mes

    despesas_categorias = normalized[normalized["tipo"] == TransactionType.EXPENSE].groupby("category")["amount"].sum().sort_values(ascending=False)
    maior_categoria = despesas_categorias.idxmax() if not despesas_categorias.empty else "N/A"
    maior_categoria_valor = despesas_categorias.max() if not despesas_categorias.empty else 0

    saldo_por_mes = normalized.groupby(normalized["data_dt"].dt.to_period("M")).apply(
        lambda grupo: grupo[grupo["tipo"] == TransactionType.GAIN]["amount"].sum() - grupo[grupo["tipo"] == TransactionType.EXPENSE]["amount"].sum()
    )

    meses = sorted(normalized["data_dt"].dt.to_period("M").unique(), reverse=True)
    tendencia = "Em crescimento" if len(meses) > 1 and saldo_por_mes.iloc[-1] > saldo_por_mes.iloc[-2] else "Em ajuste"

    return {
        "total_ganhos": total_ganhos,
        "total_despesas": total_despesas,
        "saldo_total": saldo_total,
        "ganhos_mes": ganhos_mes,
        "despesas_mes": despesas_mes,
        "saldo_mes": saldo_mes,
        "maior_categoria": maior_categoria,
        "maior_categoria_valor": maior_categoria_valor,
        "total_transacoes": len(normalized),
        "tendencia": tendencia,
        "mes_atual": str(mes_atual),
        "saldo_por_mes": saldo_por_mes,
    }
