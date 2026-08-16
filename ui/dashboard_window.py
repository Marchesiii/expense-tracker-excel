import tkinter as tk

import pandas as pd

from services.financial_service import build_dashboard_summary


def show_dashboard_window(df):
    if df is None or df.empty:
        from tkinter import messagebox
        messagebox.showwarning("Dashboard", "Nenhum dado disponível para montar o dashboard.")
        return

    summary = build_dashboard_summary(df)
    if not summary:
        from tkinter import messagebox
        messagebox.showwarning("Dashboard", "Não foi possível montar o dashboard com os dados atuais.")
        return

    janela = tk.Toplevel()
    janela.title("Dashboard Central")
    janela.geometry("1100x650")
    janela.configure(bg="#f0f2f5")

    top = tk.Frame(janela, bg="#2c3e50", height=70)
    top.pack(fill=tk.X)
    tk.Label(top, text="📊 Dashboard Central", bg="#2c3e50", fg="white", font=("Segoe UI", 18, "bold")).pack(pady=18)

    metricas = tk.Frame(janela, bg="#f0f2f5")
    metricas.pack(fill=tk.X, padx=20, pady=20)

    cards = [
        ("Ganhos Totais", format_currency(summary["total_ganhos"]), f"Mês atual: {summary['mes_atual']}", "#27ae60"),
        ("Despesas Totais", format_currency(summary["total_despesas"]), "Gasto consolidado", "#e74c3c"),
        ("Saldo Total", format_currency(summary["saldo_total"]), "Resultado geral", "#3498db"),
        ("Saldo do Mês", format_currency(summary["saldo_mes"]), f"Tendência: {summary['tendencia']}", "#8e44ad"),
    ]

    for idx, (titulo, valor, detalhe, cor) in enumerate(cards):
        card = create_dashboard_card(metricas, titulo, valor, detalhe, cor)
        card.grid(row=0, column=idx, padx=10, pady=5, sticky="nsew")

    metricas.grid_columnconfigure((0, 1, 2, 3), weight=1)

    body = tk.Frame(janela, bg="#f0f2f5")
    body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    left = tk.LabelFrame(body, text="Resumo Operacional", bg="white", fg="#2c3e50", font=("Segoe UI", 11, "bold"), padx=12, pady=12)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    resumo = [
        ("Ganhos no mês", format_currency(summary["ganhos_mes"])),
        ("Despesas no mês", format_currency(summary["despesas_mes"])),
        ("Categoria mais relevante", summary["maior_categoria"]),
        ("Maior gasto", format_currency(summary["maior_categoria_valor"])),
        ("Transações registradas", str(summary["total_transacoes"])),
    ]

    for titulo, valor in resumo:
        row = tk.Frame(left, bg="white")
        row.pack(fill=tk.X, pady=6)
        tk.Label(row, text=f"{titulo}:", bg="white", fg="#2c3e50", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(row, text=str(valor), bg="white", fg="#4a627a", font=("Segoe UI", 10)).pack(side=tk.RIGHT)

    right = tk.LabelFrame(body, text="Evolução por Mês", bg="white", fg="#2c3e50", font=("Segoe UI", 11, "bold"), padx=12, pady=12)
    right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    saldo = summary.get("saldo_por_mes")
    if saldo is not None and not saldo.empty:
        chart = tk.Canvas(right, width=420, height=220, bg="white", highlightthickness=0)
        chart.pack(fill=tk.BOTH, expand=True)

        meses_ordenados = [str(period) for period in saldo.index]
        valores = list(saldo.values)
        max_valor = max(abs(v) for v in valores) if valores else 1

        chart_w = 400
        chart_h = 180
        margin = 25
        step_x = (chart_w - 2 * margin) / max(len(valores), 1)

        for i, valor in enumerate(valores):
            x0 = margin + i * step_x
            x1 = x0 + step_x * 0.7
            y0 = chart_h - margin
            altura = (abs(valor) / max_valor) * (chart_h - 2 * margin)
            y_top = y0 - altura if valor >= 0 else y0
            cor_bar = "#27ae60" if valor >= 0 else "#e74c3c"
            chart.create_rectangle(x0, y_top, x1, y0, fill=cor_bar, outline="")
            chart.create_text(x0 + (x1 - x0) / 2, y0 + 15, text=f"{valor:,.0f}", fill="#2c3e50", font=("Segoe UI", 8))

        for idx, label in enumerate(meses_ordenados[-8:]):
            x = margin + idx * (chart_w - 2 * margin) / max(len(meses_ordenados[-8:]), 1)
            chart.create_text(x, chart_h - 8, text=label[-2:], fill="#2c3e50", font=("Segoe UI", 7))
    else:
        tk.Label(right, text="Sem dados suficientes para exibir evolução.", bg="white", fg="#6c7a89", font=("Segoe UI", 10)).pack(pady=60)


def create_dashboard_card(parent, titulo, valor, descricao, cor="#3498db"):
    card = tk.Frame(parent, bg="white", bd=1, relief=tk.FLAT, highlightbackground="#dfe6e9", highlightthickness=1)
    card.pack_propagate(False)
    card.configure(width=220, height=120)

    tk.Label(card, text=titulo, bg="white", fg="#4a627a", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12, 0))
    tk.Label(card, text=valor, bg="white", fg=cor, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=12, pady=(6, 0))
    tk.Label(card, text=descricao, bg="white", fg="#6c7a89", font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(6, 8))
    return card


def format_currency(value):
    return f"R$ {value:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")
