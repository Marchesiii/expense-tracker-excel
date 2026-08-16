import os
import sys
from pathlib import Path

import pandas as pd
import tkinter as tk
from tkinter import messagebox

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.data_loader import load_all_expenses
from services.normalization_service import normalize_transaction_dataframe
from services.financial_service import analyze_cashflow
from services.alert_service import build_alerts_table
from services.forecast_service import forecast_next_month
from scripts.process_pdf import process_pdfs_by_name
from ui.main_window import create_main_window


class ExpenseTrackerApp:
    def __init__(self):
        self.dataframe = pd.DataFrame()
        self.business_name = "Silvana"

    def process_pdfs(self):
        process_pdfs_by_name(self.business_name)

    def load_data(self):
        self.dataframe = load_all_expenses(self.business_name)
        if self.dataframe.empty:
            messagebox.showwarning("Dados", "Nenhum dado foi carregado.")
            return

        self.dataframe = normalize_transaction_dataframe(self.dataframe)
        messagebox.showinfo("Leitura", "Dados lidos e normalizados com sucesso.")

    def open_main_window(self):
        create_main_window(self)

    def summarize(self):
        return analyze_cashflow(self.dataframe)

    def get_alerts(self):
        return build_alerts_table(self.dataframe)

    def get_forecast(self):
        return forecast_next_month(self.dataframe)


if __name__ == "__main__":
    app = ExpenseTrackerApp()
    root = tk.Tk()
    root.withdraw()
    app.load_data()
    app.open_main_window()
    root.mainloop()
