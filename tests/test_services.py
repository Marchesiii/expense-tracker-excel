import unittest

import pandas as pd

from scripts.process_txt import parse_line_to_expense
from services.alert_service import build_alerts_table
from services.financial_service import analyze_cashflow
from services.forecast_service import forecast_next_month
from services.normalization_service import normalize_transaction_dataframe
from ui.main_window import get_status_color


class TestFinancialServices(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            {"data": "01-01-2025", "amount": 100, "category": "alimentação", "tipo": "despesa"},
            {"data": "05-01-2025", "amount": 200, "category": "alimentação", "tipo": "despesa"},
            {"data": "10-01-2025", "amount": 300, "category": "transporte", "tipo": "despesa"},
            {"data": "15-01-2025", "amount": 500, "category": "vendas", "tipo": "ganho"},
            {"data": "20-01-2025", "amount": 150, "category": "combustível", "tipo": "despesa"},
        ])

    def test_normalize_transaction_dataframe(self):
        raw = pd.DataFrame([
            {"Date": "01-01-2025", "Valor": 100, "Categoria": "alimentação", "Type": "expense"},
        ])

        normalized = normalize_transaction_dataframe(raw)

        self.assertIn("data", normalized.columns)
        self.assertIn("amount", normalized.columns)
        self.assertIn("category", normalized.columns)
        self.assertIn("tipo", normalized.columns)
        self.assertEqual(normalized.loc[0, "tipo"], "despesa")

    def test_analyze_cashflow(self):
        summary = analyze_cashflow(self.df)

        self.assertEqual(summary.total_gains, 500)
        self.assertEqual(summary.total_expenses, 750)
        self.assertEqual(summary.balance, -250)
        self.assertIn("alimentação", summary.category_summary.index.get_level_values("category").tolist())

    def test_forecast_next_month(self):
        forecast = forecast_next_month(self.df, months_considered=2)

        self.assertIn("category", forecast.columns)
        self.assertIn("previsao_proximo_mes", forecast.columns)
        self.assertGreater(len(forecast), 0)

    def test_alerts_table(self):
        alerts = build_alerts_table(self.df)

        self.assertIn("category", alerts.columns)
        self.assertIn("alerta", alerts.columns)
        self.assertGreater(len(alerts), 0)

    def test_status_color_mapping(self):
        self.assertEqual(get_status_color("dentro da meta"), "#27ae60")
        self.assertEqual(get_status_color("acima da meta"), "#f39c12")
        self.assertEqual(get_status_color("alerta crítico"), "#e74c3c")
        self.assertEqual(get_status_color("sem meta"), "#6c7a89")

    def test_parse_line_strips_transaction_id_and_currency_label_from_category(self):
        line = "01-05-2025 Pagamento Comercialorlando 109622212631 R$ -54,15 R$ 1.023,97"
        parsed = parse_line_to_expense(line)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["amount"], 54.15)
        self.assertEqual(parsed["tipo"], "despesa")
        self.assertEqual(parsed["category"], "Pagamento Comercialorlando")

    def test_negative_amounts_are_normalized_for_totals(self):
        df = pd.DataFrame([
            {"data": "01-01-2025", "amount": -100, "category": "alimentação", "tipo": "despesa"},
            {"data": "02-01-2025", "amount": 300, "category": "vendas", "tipo": "ganho"},
        ])

        normalized = normalize_transaction_dataframe(df)
        self.assertEqual(normalized.loc[0, "amount"], 100)
        self.assertEqual(normalized.loc[1, "amount"], 300)

        summary = analyze_cashflow(normalized)
        self.assertEqual(summary.total_gains, 300)
        self.assertEqual(summary.total_expenses, 100)
        self.assertEqual(summary.balance, 200)


if __name__ == "__main__":
    unittest.main()
