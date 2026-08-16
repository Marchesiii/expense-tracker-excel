import pandas as pd

from domain.enums import TransactionType
from domain.validators import clean_numeric_series


DEFAULT_ALIASES = {
    "data": ["data", "date", "Data", "Date"],
    "amount": ["amount", "valor", "Valor", "valor_total", "total", "montante"],
    "category": ["category", "Category", "categoria", "Categoria", "descricao", "Descrição", "description", "Description"],
    "tipo": ["tipo", "Tipo", "type", "Type", "natureza", "Natureza"],
}


def normalize_transaction_dataframe(df):
    """Padroniza nomes e valores das colunas transacionais."""
    if df is None or df.empty:
        return df

    normalized = df.copy()

    for canonical_name, aliases in DEFAULT_ALIASES.items():
        for alias in aliases:
            if alias in normalized.columns and canonical_name not in normalized.columns:
                normalized = normalized.rename(columns={alias: canonical_name})
                break

    if "tipo" in normalized.columns:
        normalized["tipo"] = (
            normalized["tipo"]
            .astype(str)
            .str.strip()
            .str.lower()
            .replace({
                "saida": TransactionType.EXPENSE,
                "gasto": TransactionType.EXPENSE,
                "expense": TransactionType.EXPENSE,
                "expenses": TransactionType.EXPENSE,
                "entrada": TransactionType.GAIN,
                "receita": TransactionType.GAIN,
                "income": TransactionType.GAIN,
            })
        )

    if "amount" in normalized.columns:
        normalized["amount"] = clean_numeric_series(normalized["amount"]).abs()

    if "category" in normalized.columns:
        normalized["category"] = normalized["category"].fillna("Outros").astype(str)

    return normalized


def normalize_category(category):
    if pd.isna(category):
        return "outros"
    return str(category).strip().lower().replace("-", " ").replace("_", " ")
