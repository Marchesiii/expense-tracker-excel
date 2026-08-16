import threading
import tkinter as tk
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from domain.enums import AlertStatus, TransactionType
from domain.validators import has_required_columns
from services.alert_service import build_alerts_table
from services.financial_service import analyze_cashflow
from services.forecast_service import forecast_next_month, recurring_expenses_forecast
from ui.dashboard_window import show_dashboard_window
from ui.styles import COLORS
from ui.widgets import create_button


def get_status_color(status):
    status_key = (status or "").strip().lower()
    colors = {
        AlertStatus.WITHIN_TARGET: COLORS["success"],
        AlertStatus.ABOVE_TARGET: COLORS["warning"],
        AlertStatus.CRITICAL: COLORS["danger"],
        "alerta_critico": COLORS["danger"],
        AlertStatus.NO_TARGET: COLORS["muted"],
    }
    return colors.get(status_key, COLORS["muted"])


def create_main_window(app):
    root = tk.Tk()
    root.title("Expense Tracker - Fluxo de Caixa")
    root.geometry("900x750")
    root.configure(bg=COLORS["light_bg"])

    header_frame = tk.Frame(root, bg=COLORS["primary"], height=80)
    header_frame.pack(fill=tk.X, side=tk.TOP)

    tk.Label(header_frame, text="💰 Expense Tracker", font=("Segoe UI", 20, "bold"), bg=COLORS["primary"], fg="white").pack(pady=15)
    tk.Label(header_frame, text="Gerenciador de Fluxo de Caixa - Silvana", font=("Segoe UI", 10), bg=COLORS["primary"], fg="#bdc3c7").pack()

    main_frame = tk.Frame(root, bg=COLORS["light_bg"])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    section1 = tk.LabelFrame(main_frame, text="📥 Importação de Dados", font=("Segoe UI", 11, "bold"), bg="white", fg=COLORS["primary"], padx=15, pady=12)
    section1.pack(fill=tk.X, pady=10)
    row1 = tk.Frame(section1, bg="white")
    row1.pack(fill=tk.X, pady=8)
    create_button(row1, "🔢 Processar PDFs", lambda: run_process_pdfs(app), COLORS["secondary"]).pack(side=tk.LEFT, padx=5)
    create_button(row1, "📥 Ler Dados", app.load_data, COLORS["success"]).pack(side=tk.LEFT, padx=5)

    section2 = tk.LabelFrame(main_frame, text="📊 Análise e Resumos", font=("Segoe UI", 11, "bold"), bg="white", fg=COLORS["primary"], padx=15, pady=12)
    section2.pack(fill=tk.X, pady=10)
    row2a = tk.Frame(section2, bg="white")
    row2a.pack(fill=tk.X, pady=8)
    create_button(row2a, "📄 Resumo Executivo", lambda: show_summary_dialog(app), COLORS["secondary"]).pack(side=tk.LEFT, padx=5)
    create_button(row2a, "Dashboard Central", lambda: show_dashboard_window(app.dataframe), COLORS["secondary"]).pack(side=tk.LEFT, padx=5)
    create_button(row2a, "📊 Categorias", lambda: show_categories_window(app.dataframe), COLORS["secondary"]).pack(side=tk.LEFT, padx=5)
    create_button(row2a, "📑 Relatórios", lambda: show_reports_window(app.dataframe), COLORS["warning"]).pack(side=tk.LEFT, padx=5)
    create_button(row2a, "⚠️ Metas e Alertas", lambda: show_alerts_window(app.dataframe), COLORS["warning"]).pack(side=tk.LEFT, padx=5)

    row2b = tk.Frame(section2, bg="white")
    row2b.pack(fill=tk.X, pady=8)
    create_button(row2b, "📈 Gráficos Mensais", lambda: show_monthly_chart_window(app.dataframe), COLORS["success"]).pack(side=tk.LEFT, padx=5)
    create_button(row2b, "📈 Previsão", lambda: show_forecast_window(app.dataframe), COLORS["success"]).pack(side=tk.LEFT, padx=5)

    section3 = tk.LabelFrame(main_frame, text="📋 Relatórios Detalhados", font=("Segoe UI", 11, "bold"), bg="white", fg=COLORS["primary"], padx=15, pady=12)
    section3.pack(fill=tk.X, pady=10)
    row3a = tk.Frame(section3, bg="white")
    row3a.pack(fill=tk.X, pady=8)
    create_button(row3a, "📊 Relatório Mensal", lambda: show_reports_window(app.dataframe), COLORS["secondary"]).pack(side=tk.LEFT, padx=5)
    create_button(row3a, "📊 Despesas Fixas", lambda: show_fixed_expenses_window(app.dataframe), COLORS["secondary"]).pack(side=tk.LEFT, padx=5)

    row3b = tk.Frame(section3, bg="white")
    row3b.pack(fill=tk.X, pady=8)
    create_button(row3b, "📅 Relatório Diário", lambda: show_daily_report_window(app.dataframe), COLORS["warning"]).pack(side=tk.LEFT, padx=5)
    create_button(row3b, "📊 Visualizar Dados", lambda: show_data_table_window(app.dataframe), COLORS["muted"]).pack(side=tk.LEFT, padx=5)

    footer_frame = tk.Frame(root, bg=COLORS["primary"], height=40)
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
    footer_left = tk.Frame(footer_frame, bg=COLORS["primary"])
    footer_left.pack(side=tk.LEFT, padx=20, pady=10)
    tk.Label(footer_left, text="✓ Aplicativo de Gerenciamento de Despesas", font=("Segoe UI", 9), bg=COLORS["primary"], fg="#bdc3c7").pack()

    footer_right = tk.Frame(footer_frame, bg=COLORS["primary"])
    footer_right.pack(side=tk.RIGHT, padx=20, pady=10)
    tk.Button(footer_right, text="❌ Sair", command=root.quit, bg=COLORS["danger"], fg="white", font=("Segoe UI", 9, "bold"), padx=20, pady=5, relief=tk.FLAT, cursor="hand2").pack()

    root.mainloop()


def run_process_pdfs(app):
    window = tk.Toplevel()
    window.title("Processar PDFs")
    window.geometry("380x140")
    window.resizable(False, False)
    window.configure(bg=COLORS["light_bg"])

    tk.Label(
        window,
        text=f"Processando PDFs de '{app.business_name}'...",
        bg=COLORS["light_bg"],
        fg=COLORS["text"],
        font=("Segoe UI", 11, "bold"),
        wraplength=320,
    ).pack(pady=(28, 10))
    progress = ttk.Progressbar(window, mode="indeterminate")
    progress.pack(fill=tk.X, padx=24)
    progress.start(12)
    window.update_idletasks()

    def finish_success():
        progress.stop()
        window.destroy()
        from tkinter import messagebox
        messagebox.showinfo(
            "PDFs",
            f"PDFs processados para '{app.business_name}' com sucesso.\nClique em 'Ler Dados' para carregar as novas transações.",
        )

    def finish_error(exc):
        progress.stop()
        window.destroy()
        from tkinter import messagebox
        messagebox.showerror("Erro ao processar PDFs", str(exc))

    def worker():
        # A extração de PDF (PyPDF2) é pesada; roda fora da thread principal do Tkinter.
        try:
            app.process_pdfs()
        except Exception as exc:
            window.after(0, lambda: finish_error(exc))
            return
        window.after(0, finish_success)

    threading.Thread(target=worker, daemon=True).start()


def show_summary_dialog(app):
    summary = analyze_cashflow(app.dataframe)
    if summary is None:
        from tkinter import messagebox
        messagebox.showwarning("Resumo", "Nenhum dado encontrado para gerar o resumo.")
        return

    from tkinter import messagebox
    messagebox.showinfo(
        "Resumo",
        f"Ganhos: R$ {summary.total_gains:,.2f}\n"
        f"Despesas: R$ {summary.total_expenses:,.2f}\n"
        f"Saldo: R$ {summary.balance:,.2f}",
    )


def show_categories_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Categorias", "Nenhum dado disponível para gerar o relatório de categorias.")
        return

    if not has_required_columns(df, ["category", "amount", "tipo"]):
        from tkinter import messagebox
        messagebox.showwarning("Categorias", "Os dados carregados não possuem as colunas necessárias para este relatório.")
        return

    window = tk.Toplevel()
    window.title("Categorias")
    window.geometry("850x420")
    window.configure(bg=COLORS["light_bg"])

    header = tk.Frame(window, bg=COLORS["primary"], height=72)
    header.pack(fill=tk.X)
    tk.Label(header, text="📊 Relatório por Categorias", bg=COLORS["primary"], fg="white", font=("Segoe UI", 18, "bold")).pack(pady=18)

    loading = tk.Frame(window, bg=COLORS["light_bg"])
    loading.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    tk.Label(loading, text="Carregando categorias...", bg=COLORS["light_bg"], fg=COLORS["text"], font=("Segoe UI", 11, "bold")).pack(pady=(20, 8))
    progress = ttk.Progressbar(loading, mode="indeterminate")
    progress.pack(fill=tk.X, padx=20)
    progress.start(12)
    window.update_idletasks()

    def build_category_report():
        category_df = df.copy()
        category_df["amount"] = pd.to_numeric(category_df["amount"], errors="coerce")
        category_df = category_df.dropna(subset=["amount", "category", "tipo"])

        by_category = (
            category_df[category_df["tipo"] == TransactionType.EXPENSE].groupby("category")["amount"].sum().reset_index(name="Despesas")
            .merge(
                category_df[category_df["tipo"] == TransactionType.GAIN].groupby("category")["amount"].sum().reset_index(name="Ganhos"),
                on="category",
                how="outer",
            )
            .fillna({"Despesas": 0, "Ganhos": 0})
        )
        by_category["Saldo"] = by_category["Ganhos"] - by_category["Despesas"]
        return by_category.sort_values("Despesas", ascending=False).reset_index(drop=True)

    def show_report(by_category):
        progress.stop()
        loading.destroy()

        if by_category.empty:
            from tkinter import messagebox
            messagebox.showwarning("Categorias", "Não há dados suficientes para compor o relatório de categorias.")
            window.destroy()
            return

        body = tk.Frame(window, bg=COLORS["light_bg"], padx=16, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(body, columns=("Categoria", "Ganhos", "Despesas", "Saldo"), show="headings")
        tree.pack(fill=tk.BOTH, expand=True)
        for column in ("Categoria", "Ganhos", "Despesas", "Saldo"):
            tree.heading(column, text=column)
            tree.column(column, anchor="center", width=180)

        for _, row in by_category.iterrows():
            tree.insert(
                "",
                "end",
                values=(
                    row["category"],
                    f"R$ {row.get('Ganhos', 0):,.2f}",
                    f"R$ {row.get('Despesas', 0):,.2f}",
                    f"R$ {row.get('Saldo', 0):,.2f}",
                ),
            )

    def show_error(exc):
        progress.stop()
        loading.destroy()
        from tkinter import messagebox
        messagebox.showerror("Categorias", f"Não foi possível montar o relatório de categorias:\n{exc}")
        window.destroy()

    def worker():
        # Só o pandas roda na thread; widgets do Tkinter só podem ser tocados na thread principal.
        try:
            result = build_category_report()
        except Exception as exc:
            window.after(0, lambda: show_error(exc))
            return
        window.after(0, lambda: show_report(result))

    threading.Thread(target=worker, daemon=True).start()


def show_reports_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Relatórios", "Nenhum dado disponível para gerar relatórios.")
        return

    if not has_required_columns(df, ["category", "amount", "tipo", "data"]):
        from tkinter import messagebox
        messagebox.showwarning("Relatórios", "Os dados carregados não possuem as colunas necessárias para compor os relatórios.")
        return

    report_df = df.copy()
    report_df["data_dt"] = pd.to_datetime(report_df["data"], format="%d-%m-%Y", errors="coerce")
    report_df = report_df.dropna(subset=["data_dt", "amount"])
    report_df["mes"] = report_df["data_dt"].dt.to_period("M").astype(str)
    summary = report_df.groupby(["mes", "tipo"], as_index=False)["amount"].sum()
    summary = summary.pivot(index="mes", columns="tipo", values="amount").fillna(0).reset_index()
    summary["Saldo"] = summary.get(TransactionType.GAIN, 0) - summary.get(TransactionType.EXPENSE, 0)

    window = tk.Toplevel()
    window.title("Relatórios")
    window.geometry("840x420")
    window.configure(bg=COLORS["light_bg"])

    header = tk.Frame(window, bg=COLORS["primary"], height=72)
    header.pack(fill=tk.X)
    tk.Label(header, text="📑 Relatórios Mensais e Financeiros", bg=COLORS["primary"], fg="white", font=("Segoe UI", 18, "bold")).pack(pady=18)

    body = tk.Frame(window, bg=COLORS["light_bg"], padx=18, pady=18)
    body.pack(fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(body, columns=("Mês", "Ganhos", "Despesas", "Saldo"), show="headings")
    tree.pack(fill=tk.BOTH, expand=True)

    for column in ("Mês", "Ganhos", "Despesas", "Saldo"):
        tree.heading(column, text=column)
        tree.column(column, anchor="center", width=180)

    for _, row in summary.sort_values("mes", ascending=True).iterrows():
        tree.insert(
            "",
            "end",
            values=(
                row.get("mes", "-"),
                f"R$ {row.get(TransactionType.GAIN, 0):,.2f}",
                f"R$ {row.get(TransactionType.EXPENSE, 0):,.2f}",
                f"R$ {row.get('Saldo', 0):,.2f}",
            ),
        )


def show_monthly_chart_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Gráficos Mensais", "Nenhum dado disponível para montar os gráficos.")
        return

    if not has_required_columns(df, ["amount", "tipo", "data"]):
        from tkinter import messagebox
        messagebox.showwarning("Gráficos Mensais", "Os dados carregados não possuem as colunas necessárias para montar o gráfico.")
        return

    chart_df = df.copy()
    chart_df["amount"] = pd.to_numeric(chart_df["amount"], errors="coerce")
    chart_df["data_dt"] = pd.to_datetime(chart_df["data"], format="%d-%m-%Y", errors="coerce")
    chart_df = chart_df.dropna(subset=["amount", "data_dt"])
    chart_df["mes"] = chart_df["data_dt"].dt.to_period("M").astype(str)

    summary = chart_df.groupby(["mes", "tipo"], as_index=False)["amount"].sum()
    summary = summary.pivot(index="mes", columns="tipo", values="amount").fillna(0).reset_index()
    if summary.empty:
        from tkinter import messagebox
        messagebox.showwarning("Gráficos Mensais", "Não há dados suficientes para gerar o gráfico mensal.")
        return

    window = tk.Toplevel()
    window.title("Gráficos Mensais")
    window.geometry("980x520")
    window.configure(bg=COLORS["light_bg"])

    header = tk.Frame(window, bg=COLORS["primary"], height=72)
    header.pack(fill=tk.X)
    tk.Label(header, text="📈 Gráficos Mensais", bg=COLORS["primary"], fg="white", font=("Segoe UI", 18, "bold")).pack(pady=18)

    fig = Figure(figsize=(10, 5), dpi=100)
    ax = fig.add_subplot(111)
    months = list(summary["mes"])
    gains = summary.get(TransactionType.GAIN, pd.Series(0, index=summary.index)).tolist()
    expenses = summary.get(TransactionType.EXPENSE, pd.Series(0, index=summary.index)).tolist()

    x = range(len(months))
    ganho_bars = ax.bar([i - 0.2 for i in x], gains, width=0.35, label="Ganhos", color=COLORS["success"])
    despesa_bars = ax.bar([i + 0.2 for i in x], expenses, width=0.35, label="Despesas", color=COLORS["danger"])

    ax.set_title("Ganhos e Despesas por Mês")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Valor (R$)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=30)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    ax.legend()

    for bars in (ganho_bars, despesa_bars):
        for bar in bars:
            height = bar.get_height()
            if height == 0:
                continue
            ax.annotate(
                f"R$ {height:,.0f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#2c3e50",
            )

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=16, pady=16)


def show_daily_report_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Relatório Diário", "Nenhum dado disponível para gerar o relatório diário.")
        return

    if not has_required_columns(df, ["amount", "tipo", "data"]):
        from tkinter import messagebox
        messagebox.showwarning("Relatório Diário", "Os dados carregados não possuem as colunas necessárias para este relatório.")
        return

    report_df = df.copy()
    report_df["amount"] = pd.to_numeric(report_df["amount"], errors="coerce")
    report_df["data_dt"] = pd.to_datetime(report_df["data"], format="%d-%m-%Y", errors="coerce")
    report_df = report_df.dropna(subset=["amount", "data_dt"])
    report_df["dia"] = report_df["data_dt"].dt.strftime("%d/%m/%Y")

    summary = report_df.groupby(["dia", "tipo"], as_index=False)["amount"].sum()
    summary = summary.pivot(index="dia", columns="tipo", values="amount").fillna(0).reset_index()
    if summary.empty:
        from tkinter import messagebox
        messagebox.showwarning("Relatório Diário", "Não há dados suficientes para gerar o relatório diário.")
        return

    summary["Saldo"] = summary.get(TransactionType.GAIN, 0) - summary.get(TransactionType.EXPENSE, 0)
    summary["_dia_ordenacao"] = pd.to_datetime(summary["dia"], format="%d/%m/%Y")

    window = tk.Toplevel()
    window.title("Relatório Diário")
    window.geometry("850x420")
    window.configure(bg=COLORS["light_bg"])

    header = tk.Frame(window, bg=COLORS["primary"], height=72)
    header.pack(fill=tk.X)
    tk.Label(header, text="📅 Relatório Diário", bg=COLORS["primary"], fg="white", font=("Segoe UI", 18, "bold")).pack(pady=18)

    body = tk.Frame(window, bg=COLORS["light_bg"], padx=16, pady=16)
    body.pack(fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(body, columns=("Data", "Ganhos", "Despesas", "Saldo"), show="headings")
    tree.pack(fill=tk.BOTH, expand=True)

    for column in ("Data", "Ganhos", "Despesas", "Saldo"):
        tree.heading(column, text=column)
        tree.column(column, anchor="center", width=180)

    for _, row in summary.sort_values("_dia_ordenacao", ascending=True).iterrows():
        tree.insert(
            "",
            "end",
            values=(
                row.get("dia", "-"),
                f"R$ {row.get(TransactionType.GAIN, 0):,.2f}",
                f"R$ {row.get(TransactionType.EXPENSE, 0):,.2f}",
                f"R$ {row.get('Saldo', 0):,.2f}",
            ),
        )


def show_alerts_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Alertas", "Nenhum dado disponível para avaliar metas.")
        return

    alerts = build_alerts_table(df)
    if alerts.empty:
        from tkinter import messagebox
        messagebox.showwarning("Alertas", "Não há dados suficientes para gerar alertas.")
        return

    new_window = tk.Toplevel()
    new_window.title("Metas e Alertas")
    new_window.geometry("980x420")

    cabecalho = tk.Frame(new_window, bg=COLORS["primary"], height=60)
    cabecalho.pack(fill=tk.X)
    tk.Label(cabecalho, text="⚠️ Metas por Categoria e Alertas", bg=COLORS["primary"], fg="white", font=("Segoe UI", 16, "bold")).pack(pady=14)

    tree = ttk.Treeview(new_window, columns=("Categoria", "Gasto Atual", "Meta", "Restante", "Status", "Alerta"), show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    for column in ("Categoria", "Gasto Atual", "Meta", "Restante", "Status", "Alerta"):
        tree.heading(column, text=column)
        tree.column(column, anchor="center", width=130)

    for _, row in alerts.iterrows():
        status = row.get("status", "sem histórico")
        tag_name = f"status_{_}"
        tree.insert(
            "",
            "end",
            values=(
                row.get("category", "N/A"),
                f"R$ {row.get('gasto', 0):,.2f}",
                f"R$ {row.get('meta', 0):,.2f}",
                f"R$ {row.get('restante', 0):,.2f}",
                status,
                row.get("alerta", "SEM ALERTA"),
            ),
            tags=(tag_name,),
        )
        tree.tag_configure(tag_name, foreground=get_status_color(status), background="white")


def show_forecast_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Previsão", "Nenhum dado disponível para gerar previsão.")
        return

    forecast = forecast_next_month(df)
    if forecast.empty:
        from tkinter import messagebox
        messagebox.showwarning("Previsão", "Não há histórico suficiente para gerar previsão.")
        return

    new_window = tk.Toplevel()
    new_window.title("Previsão do Próximo Mês")
    new_window.geometry("700x420")

    tree = ttk.Treeview(new_window, columns=("Categoria", "Média Histórica", "Previsão", "Status"), show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    for column in ("Categoria", "Média Histórica", "Previsão", "Status"):
        tree.heading(column, text=column)
        tree.column(column, anchor="center", width=160)

    for _, row in forecast.iterrows():
        tree.insert(
            "",
            "end",
            values=(
                row["category"],
                f"R$ {row.get('media_historica', 0):,.2f}",
                f"R$ {row.get('previsao_proximo_mes', 0):,.2f}",
                row.get("status", "estável"),
            ),
        )


def show_fixed_expenses_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Despesas Fixas", "Nenhum dado disponível para identificar despesas fixas.")
        return

    recorrentes = recurring_expenses_forecast(df)
    if recorrentes.empty:
        from tkinter import messagebox
        messagebox.showwarning("Despesas Fixas", "Não há histórico suficiente para identificar despesas recorrentes.")
        return

    window = tk.Toplevel()
    window.title("Despesas Fixas")
    window.geometry("780x420")
    window.configure(bg=COLORS["light_bg"])

    header = tk.Frame(window, bg=COLORS["primary"], height=72)
    header.pack(fill=tk.X)
    tk.Label(header, text="📊 Despesas Fixas e Recorrentes", bg=COLORS["primary"], fg="white", font=("Segoe UI", 18, "bold")).pack(pady=18)

    body = tk.Frame(window, bg=COLORS["light_bg"], padx=16, pady=16)
    body.pack(fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(body, columns=("Categoria", "Previsão Mensal", "Ocorrências Médias", "Tipo"), show="headings")
    tree.pack(fill=tk.BOTH, expand=True)

    for column in ("Categoria", "Previsão Mensal", "Ocorrências Médias", "Tipo"):
        tree.heading(column, text=column)
        tree.column(column, anchor="center", width=180)

    for _, row in recorrentes.iterrows():
        tree.insert(
            "",
            "end",
            values=(
                row["category"],
                f"R$ {row.get('previsao_mensal', 0):,.2f}",
                f"{row.get('qtd_ocorrencias', 0):.1f}",
                row.get("tipo_categoria", "variável"),
            ),
        )


def show_data_table_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Visualizar Dados", "Nenhum dado disponível para exibir.")
        return

    window = tk.Toplevel()
    window.title("Visualizar Dados")
    window.geometry("1000x600")
    window.configure(bg=COLORS["light_bg"])

    header = tk.Frame(window, bg=COLORS["primary"], height=60)
    header.pack(fill=tk.X)
    tk.Label(header, text="📊 Visualização de Dados", bg=COLORS["primary"], fg="white", font=("Segoe UI", 16, "bold")).pack(pady=14)

    tree_frame = tk.Frame(window, bg=COLORS["light_bg"])
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar_y = ttk.Scrollbar(tree_frame)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

    tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    tree.pack(fill=tk.BOTH, expand=True)
    scrollbar_y.config(command=tree.yview)
    scrollbar_x.config(command=tree.xview)

    tree["columns"] = list(df.columns)
    tree["show"] = "headings"
    for column in df.columns:
        tree.heading(column, text=column)
        tree.column(column, anchor="center", width=100)

    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))

    footer = tk.Frame(window, bg=COLORS["primary"], height=40)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    tk.Label(footer, text=f"Total de registros: {len(df)}", font=("Segoe UI", 9), bg=COLORS["primary"], fg="#bdc3c7").pack(pady=8)
