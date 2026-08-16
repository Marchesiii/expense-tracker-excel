from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    data: str
    amount: float
    category: str
    tipo: str


@dataclass
class FinancialSummary:
    total_gains: float
    total_expenses: float
    balance: float
    category_summary: dict


@dataclass
class AlertRow:
    category: str
    gasto: float
    meta: float
    restante: float
    percentual: float
    status: str
    alerta: str
    previsao_proximo_mes: Optional[float] = None
