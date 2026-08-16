# Script legado (pré-refatoração). Toda a lógica aqui já foi portada e reorganizada
# em app/ (orquestração), services/ (regras de negócio) e ui/ (interface Tkinter).
# Mantido apenas como referência histórica; não é usado pela aplicação ativa (main.py).
# Precisa ser executado a partir da raiz do projeto (ex.: `python -m legacy.process_expenses`)
# para que os imports de scripts.* sejam resolvidos.
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from time import sleep
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import tkinter as tk
from tkinter import messagebox, ttk
from scripts.process_pdf import process_pdfs_by_name
from scripts.process_txt import read_txt_expenses_from_folder


all_expenses_df = pd.DataFrame()
nome_padrao = "Silvana"

def format_currency(value):
    return f"R$ {value:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

def analyze_cashflow(df):
    if df is not None:
        total_gains = df[df['tipo'] == 'ganho']['amount'].sum()
        total_expenses = df[df['tipo'] == 'despesa']['amount'].sum()
        balance = total_gains - total_expenses
        category_summary = df.groupby(['tipo', 'category'])['amount'].sum()
        return total_gains, total_expenses, balance, category_summary
    return None, None, None, None


METAS_CATEGORIAS_PADRAO = {
    'alimentação': 1800,
    'transporte': 900,
    'combustível': 1200,
    'marketing': 700,
    'estoque': 2500,
    'manutenção': 600,
    'outros': 500
}

def normalizar_colunas_padrao(df):
    if df is None or df.empty:
        return df

    aliases = {
        'data': ['data', 'date', 'Data', 'Date'],
        'amount': ['amount', 'valor', 'Valor', 'valor_total', 'total', 'montante'],
        'category': ['category', 'Category', 'categoria', 'Categoria', 'descricao', 'Descrição', 'description', 'Description'],
        'tipo': ['tipo', 'Tipo', 'type', 'Type', 'natureza', 'Natureza']
    }

    df = df.copy()
    for nome_padrao, nomes in aliases.items():
        for nome in nomes:
            if nome in df.columns and nome_padrao not in df.columns:
                df = df.rename(columns={nome: nome_padrao})
                break

    if 'tipo' in df.columns:
        df['tipo'] = df['tipo'].astype(str).str.strip().str.lower()
        df['tipo'] = df['tipo'].replace({
            'saida': 'despesa',
            'gasto': 'despesa',
            'expense': 'despesa',
            'expenses': 'despesa',
            'entrada': 'ganho',
            'receita': 'ganho',
            'income': 'ganho'
        })

    return df


def normalizar_categoria(categoria):
    if pd.isna(categoria):
        return 'outros'
    return str(categoria).strip().lower().replace('-', ' ').replace('_', ' ')


def obter_meta_categoria(categoria, metas=None):
    if metas is None:
        metas = METAS_CATEGORIAS_PADRAO

    nome = normalizar_categoria(categoria)
    for chave, valor in metas.items():
        if normalizar_categoria(chave) == nome:
            return valor
    return metas.get('outros', 0)


def calcular_metas_por_categoria(df, metas=None):
    if df is None or df.empty:
        return pd.DataFrame(columns=['category', 'gasto', 'meta', 'restante', 'percentual', 'status'])

    df = normalizar_colunas_padrao(df)
    if 'category' not in df.columns or 'amount' not in df.columns or 'data' not in df.columns:
        return pd.DataFrame(columns=['category', 'gasto', 'meta', 'restante', 'percentual', 'status'])

    if metas is None:
        metas = METAS_CATEGORIAS_PADRAO

    df = df.copy()
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['data_dt'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['amount', 'category', 'data_dt'])
    df = df[df['tipo'] == 'despesa']

    if df.empty:
        return pd.DataFrame(columns=['category', 'gasto', 'meta', 'restante', 'percentual', 'status'])

    mes_atual = df['data_dt'].max().to_period('M')
    df_mes = df[df['data_dt'].dt.to_period('M') == mes_atual]

    resumo = df_mes.groupby('category')['amount'].sum().reset_index().rename(columns={'amount': 'gasto'})
    resumo['meta'] = resumo['category'].apply(lambda categoria: obter_meta_categoria(categoria, metas))
    resumo['restante'] = resumo['meta'] - resumo['gasto']
    resumo['percentual'] = resumo.apply(
        lambda row: (row['gasto'] / row['meta'] * 100) if row['meta'] else 0,
        axis=1
    )

    def definir_status(row):
        if row['meta'] == 0:
            return 'sem meta'
        if row['gasto'] <= row['meta']:
            return 'dentro da meta'
        if row['percentual'] <= 120:
            return 'acima da meta'
        return 'alerta crítico'

    resumo['status'] = resumo.apply(definir_status, axis=1)
    return resumo.sort_values(['percentual', 'gasto'], ascending=[False, False]).reset_index(drop=True)


def previsao_proximo_mes(df, meses_considerados=3):
    if df is None or df.empty:
        return pd.DataFrame(columns=['category', 'media_historica', 'previsao_proximo_mes', 'status'])

    df = normalizar_colunas_padrao(df)
    if 'category' not in df.columns or 'amount' not in df.columns or 'data' not in df.columns:
        return pd.DataFrame(columns=['category', 'media_historica', 'previsao_proximo_mes', 'status'])

    df = df.copy()
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['data_dt'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['amount', 'category', 'data_dt'])
    df = df[df['tipo'] == 'despesa']

    if df.empty:
        return pd.DataFrame(columns=['category', 'media_historica', 'previsao_proximo_mes', 'status'])

    df['mes'] = df['data_dt'].dt.to_period('M')
    historico = df.groupby(['category', 'mes'], as_index=False)['amount'].sum()
    historico = historico.sort_values(['category', 'mes']).reset_index(drop=True)

    historico_ultimos_meses = historico.groupby('category', group_keys=False).tail(meses_considerados)
    media_por_categoria = (
        historico_ultimos_meses
        .groupby('category', as_index=False)['amount']
        .mean()
        .rename(columns={'amount': 'media_historica'})
    )

    ultima_data = historico['mes'].max()
    ultimo_mes = historico[historico['mes'] == ultima_data].rename(columns={'amount': 'gasto_ultimo_mes'})

    previsao = media_por_categoria.merge(ultimo_mes[['category', 'gasto_ultimo_mes']], on='category', how='left')
    previsao['previsao_proximo_mes'] = previsao['media_historica'].round(2)
    previsao['status'] = previsao.apply(
        lambda row: 'acima da média' if row['previsao_proximo_mes'] > row['gasto_ultimo_mes'] else 'estável',
        axis=1
    )

    return previsao[['category', 'media_historica', 'previsao_proximo_mes', 'status']].sort_values('previsao_proximo_mes', ascending=False).reset_index(drop=True)


def dashboard_central(df):
    if df is None or df.empty:
        return {}

    df = df.copy()
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['data_dt'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['amount', 'tipo', 'data_dt']).copy()
    df = df[df['amount'] > 0]

    total_ganhos = df[df['tipo'] == 'ganho']['amount'].sum()
    total_despesas = df[df['tipo'] == 'despesa']['amount'].sum()
    saldo_total = total_ganhos - total_despesas

    mes_atual = df['data_dt'].max().to_period('M')
    df_mes_atual = df[df['data_dt'].dt.to_period('M') == mes_atual]

    ganhos_mes = df_mes_atual[df_mes_atual['tipo'] == 'ganho']['amount'].sum()
    despesas_mes = df_mes_atual[df_mes_atual['tipo'] == 'despesa']['amount'].sum()
    saldo_mes = ganhos_mes - despesas_mes

    despesas_categorias = df[df['tipo'] == 'despesa'].groupby('category')['amount'].sum().sort_values(ascending=False)
    maior_categoria = despesas_categorias.idxmax() if not despesas_categorias.empty else 'N/A'
    maior_categoria_valor = despesas_categorias.max() if not despesas_categorias.empty else 0

    resumo_mensal = df.groupby(df['data_dt'].dt.to_period('M'))['amount'].sum()
    saldo_por_mes = df.groupby(df['data_dt'].dt.to_period('M')).apply(
        lambda grupo: grupo[grupo['tipo'] == 'ganho']['amount'].sum() - grupo[grupo['tipo'] == 'despesa']['amount'].sum()
    )

    meses = sorted(df['data_dt'].dt.to_period('M').unique(), reverse=True)
    tendencia = 'Em crescimento' if len(meses) > 1 and saldo_por_mes.iloc[-1] > saldo_por_mes.iloc[-2] else 'Em ajuste'

    return {
        'total_ganhos': total_ganhos,
        'total_despesas': total_despesas,
        'saldo_total': saldo_total,
        'ganhos_mes': ganhos_mes,
        'despesas_mes': despesas_mes,
        'saldo_mes': saldo_mes,
        'maior_categoria': maior_categoria,
        'maior_categoria_valor': maior_categoria_valor,
        'total_transacoes': len(df),
        'tendencia': tendencia,
        'mes_atual': str(mes_atual),
        'saldo_por_mes': saldo_por_mes,
        'resumo_mensal': resumo_mensal,
    }


def criar_dashboard_card(parent, titulo, valor, descricao, cor='#3498db'):
    card = tk.Frame(parent, bg='white', bd=1, relief=tk.FLAT, highlightbackground='#dfe6e9', highlightthickness=1)
    card.pack_propagate(False)
    card.configure(width=220, height=120)

    tk.Label(card, text=titulo, bg='white', fg='#4a627a', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(12, 0))
    tk.Label(card, text=valor, bg='white', fg=cor, font=('Segoe UI', 16, 'bold')).pack(anchor='w', padx=12, pady=(6, 0))
    tk.Label(card, text=descricao, bg='white', fg='#6c7a89', font=('Segoe UI', 9)).pack(anchor='w', padx=12, pady=(6, 8))
    return card


def mostrar_dashboard_central():
    if all_expenses_df is None or all_expenses_df.empty:
        messagebox.showwarning('Dashboard', 'Nenhum dado disponível para montar o dashboard.')
        return
    
    dados = dashboard_central(all_expenses_df)
    if not dados:
        messagebox.showwarning('Dashboard', 'Não foi possível montar o dashboard com os dados atuais.')
        return

    janela = tk.Toplevel()
    janela.title('Dashboard Central')
    janela.geometry('1100x650')
    janela.configure(bg='#f0f2f5')

    top = tk.Frame(janela, bg='#2c3e50', height=70)
    top.pack(fill=tk.X)
    tk.Label(top, text='📊 Dashboard Central', bg='#2c3e50', fg='white', font=('Segoe UI', 18, 'bold')).pack(pady=18)

    metricas = tk.Frame(janela, bg='#f0f2f5')
    metricas.pack(fill=tk.X, padx=20, pady=20)

    cards = [
        ('Ganhos Totais', format_currency(dados['total_ganhos']), f'Mês atual: {dados["mes_atual"]}', '#27ae60'),
        ('Despesas Totais', format_currency(dados['total_despesas']), 'Gasto consolidado', '#e74c3c'),
        ('Saldo Total', format_currency(dados['saldo_total']), 'Resultado geral', '#3498db'),
        ('Saldo do Mês', format_currency(dados['saldo_mes']), f'Tendência: {dados["tendencia"]}', '#8e44ad'),
    ]

    for idx, (titulo, valor, detalhe, cor) in enumerate(cards):
        card = criar_dashboard_card(metricas, titulo, valor, detalhe, cor)
        card.grid(row=0, column=idx, padx=10, pady=5, sticky='nsew')

    metricas.grid_columnconfigure((0, 1, 2, 3), weight=1)

    body = tk.Frame(janela, bg='#f0f2f5')
    body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    left = tk.LabelFrame(body, text='Resumo Operacional', bg='white', fg='#2c3e50', font=('Segoe UI', 11, 'bold'), padx=12, pady=12)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    resumo = [
        ('Ganhos no mês', format_currency(dados['ganhos_mes'])),
        ('Despesas no mês', format_currency(dados['despesas_mes'])),
        ('Categoria mais relevante', dados['maior_categoria']),
        ('Maior gasto', format_currency(dados['maior_categoria_valor'])),
        ('Transações registradas', str(dados['total_transacoes'])),
    ]

    for titulo, valor in resumo:
        row = tk.Frame(left, bg='white')
        row.pack(fill=tk.X, pady=6)
        tk.Label(row, text=f'{titulo}:', bg='white', fg='#2c3e50', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(row, text=str(valor), bg='white', fg='#4a627a', font=('Segoe UI', 10)).pack(side=tk.RIGHT)

    right = tk.LabelFrame(body, text='Evolução por Mês', bg='white', fg='#2c3e50', font=('Segoe UI', 11, 'bold'), padx=12, pady=12)
    right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    if not dados['saldo_por_mes'].empty:
        chart = tk.Canvas(right, width=420, height=220, bg='white', highlightthickness=0)
        chart.pack(fill=tk.BOTH, expand=True)

        meses_ordenados = [str(period) for period in dados['saldo_por_mes'].index]
        saldos = list(dados['saldo_por_mes'].values)

        max_valor = max(abs(v) for v in saldos) if saldos else 1
        chart_w = 400
        chart_h = 180
        margin = 25
        step_x = (chart_w - 2 * margin) / max(len(saldos), 1)

        for i, valor in enumerate(saldos):
            x0 = margin + i * step_x
            x1 = x0 + step_x * 0.7
            y0 = chart_h - margin
            altura = (abs(valor) / max_valor) * (chart_h - 2 * margin)
            y_top = y0 - altura if valor >= 0 else y0
            cor_bar = '#27ae60' if valor >= 0 else '#e74c3c'
            chart.create_rectangle(x0, y_top, x1, y0, fill=cor_bar, outline='')
            chart.create_text(x0 + (x1 - x0) / 2, y0 + 15, text=f'{valor:,.0f}', fill='#2c3e50', font=('Segoe UI', 8))

        for idx, label in enumerate(meses_ordenados[-8:]):
            x = margin + idx * (chart_w - 2 * margin) / max(len(meses_ordenados[-8:]), 1)
            chart.create_text(x, chart_h - 8, text=label[-2:], fill='#2c3e50', font=('Segoe UI', 7))
    else:
        tk.Label(right, text='Sem dados suficientes para exibir evolução.', bg='white', fg='#6c7a89', font=('Segoe UI', 10)).pack(pady=60)


def gerar_dashboard_central():
    try:
        mostrar_dashboard_central()
    except Exception as e:
        messagebox.showerror('Erro no dashboard', str(e))


def mostrar_alertas_financeiros():
    try:
        if all_expenses_df is None or all_expenses_df.empty:
            messagebox.showwarning('Alertas', 'Nenhum dado disponível para avaliar metas.')
            return

        df = normalizar_colunas_padrao(all_expenses_df)
        colunas_necessarias = {'data', 'tipo', 'category', 'amount'}
        faltando = colunas_necessarias - set(df.columns)
        if faltando:
            messagebox.showwarning('Alertas', f'Os dados carregados não têm as colunas necessárias: {sorted(faltando)}')
            return

        df = df.copy()
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['amount', 'category', 'tipo', 'data'])
        df = df[df['tipo'].isin(['despesa', 'ganho'])]

        if df.empty:
            messagebox.showwarning('Alertas', 'Não há lançamentos válidos para gerar alertas.')
            return

        metas = calcular_metas_por_categoria(df)
        previsao = previsao_proximo_mes(df)

        if metas.empty and previsao.empty:
            messagebox.showwarning('Alertas', 'Não há dados suficientes para gerar alertas.')
            return

        if not metas.empty:
            tabela = metas.copy()
            if not previsao.empty:
                tabela = tabela.merge(previsao[['category', 'previsao_proximo_mes']], on='category', how='left')
            tabela['alerta'] = tabela.apply(
                lambda row: 'META EXCEDIDA' if row.get('status') in ['acima da meta', 'alerta crítico'] else 'SEM ALERTA',
                axis=1
            )
            if 'previsao_proximo_mes' in tabela.columns:
                tabela['alerta'] = tabela.apply(
                    lambda row: 'PREVISÃO ACIMA DA META' if pd.notna(row.get('previsao_proximo_mes')) and row.get('meta', 0) and row.get('previsao_proximo_mes', 0) > row.get('meta', 0) else row.get('alerta', 'SEM ALERTA'),
                    axis=1
                )
        else:
            tabela = previsao.copy()
            tabela['meta'] = 0
            tabela['gasto'] = 0
            tabela['restante'] = 0
            tabela['percentual'] = 0
            tabela['status'] = 'sem histórico'
            tabela['alerta'] = 'PREVISÃO ACIMA DA META' if (tabela['previsao_proximo_mes'] > 0).any() else 'SEM ALERTA'

        janela = tk.Toplevel()
        janela.title('Metas e Alertas')
        janela.geometry('980x420')
        janela.configure(bg='#f0f2f5')

        cabecalho = tk.Frame(janela, bg='#2c3e50', height=60)
        cabecalho.pack(fill=tk.X)
        tk.Label(cabecalho, text='⚠️ Metas por Categoria e Alertas', bg='#2c3e50', fg='white', font=('Segoe UI', 16, 'bold')).pack(pady=14)

        tree = ttk.Treeview(janela, columns=('Categoria', 'Gasto Atual', 'Meta', 'Restante', 'Previsão Próx. Mês', 'Status', 'Alerta'), show='headings')
        tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        for col in ('Categoria', 'Gasto Atual', 'Meta', 'Restante', 'Previsão Próx. Mês', 'Status', 'Alerta'):
            tree.heading(col, text=col)
            tree.column(col, anchor='center', width=120)

        for idx, (_, row) in enumerate(tabela.iterrows()):
            cor = '#e74c3c' if row.get('alerta', 'SEM ALERTA') != 'SEM ALERTA' else '#27ae60'
            tag = f'alerta_{idx}'
            tree.insert('', 'end', values=(
                row.get('category', 'N/A'),
                format_currency(row.get('gasto', 0)),
                format_currency(row.get('meta', 0)),
                format_currency(row.get('restante', 0)),
                format_currency(row.get('previsao_proximo_mes', 0)),
                row.get('status', 'sem histórico'),
                row.get('alerta', 'SEM ALERTA')
            ))

            tree.item(tree.get_children()[-1], tags=(tag,))
            tree.tag_configure(tag, background='white', foreground=cor)

        if tabela.empty:
            tk.Label(janela, text='Sem registros suficientes.', fg='#6c7a89', font=('Segoe UI', 10)).pack(pady=30)

        rodape = tk.Label(janela, text='Atenção: alertas aparecem em vermelho quando a categoria ultrapassa a meta ou a previsão do próximo mês supera o limite.', bg='#f0f2f5', fg='#2c3e50', font=('Segoe UI', 9))
        rodape.pack(pady=(0, 12))
    except Exception as e:
        messagebox.showerror('Erro em Metas e Alertas', f'Não foi possível abrir a tela de alertas:\n{e}')

def build_summary_df(df, group_cols, value_col='amount', tipo_col='tipo', extrai_func=None, aggfunc='sum'):
    if df is None or df.empty:
        print("Nenhum dado disponível para o relatório.")
        return pd.DataFrame()

    df = df.copy()

    if 'category' in df.columns:
        df['category'] = df['category'].fillna('Outros')

    resumo   = df.groupby(group_cols)[value_col].agg(aggfunc).unstack(fill_value=0)

    resultados = []
    for grupo, row in resumo.iterrows():
        resultado = {}

        if isinstance(grupo, tuple):
            for i, col in enumerate(group_cols):
                if i < len(grupo):
                    valor = grupo[i]
                    if col == 'category' and extrai_func:
                        valor = ' '.join(extrai_func(valor))
                    resultado[col] = valor
        else:
            valor = grupo
            if group_cols[0] == 'category' and extrai_func:
                valor = ' '.join(extrai_func(valor))
            resultado[group_cols[0]] = valor

        resultado['ganhos'] = row.get('ganho', 0)
        resultado['despesas'] = row.get('despesa', 0)
        resultado['saldo'] = resultado['ganhos'] - resultado['despesas']

        resultados.append(resultado)

    return pd.DataFrame(resultados)

def category_report(df):
    if df is None or df.empty:
        print("Nenhum dado disponível para o relatório mensal.")
        return

    resumo = build_summary_df(df, group_cols=['category', 'tipo'], extrai_func=extraiCategoria)

    df_agrupado = resumo.groupby('category').agg({
        'ganhos': 'sum',
        'despesas': 'sum',
        'saldo': 'sum'
    }).reset_index()

    df_agrupado = contaCategorias(df, df_agrupado)

    return df_agrupado

def contaCategorias(df, df_agrupado):
    df['count'] = 1

    df['categoria_limpa'] = df['category'].apply(lambda x: ' '.join(extraiCategoria(x)))

    contagem = df.groupby('categoria_limpa')['count'].sum().reset_index()
    contagem.rename(columns={'categoria_limpa': 'category'}, inplace=True)
    df_agrupado = df_agrupado.merge(contagem, on='category', how='left').sort_values(by='count', ascending=False).reset_index(drop=True)
    return df_agrupado

def extraiCategoria(categoria):
    categoriasplit = categoria.strip().split()
    if len(categoriasplit) > 1:
        categoriasplit = categoriasplit[:-3]
    else:
        categoriasplit = [categoria]
    if len(categoriasplit) == 0:
        categoriasplit = ['Outros']
    elif len(categoriasplit) == 1:
        categoriasplit = [categoriasplit[0], '']
    elif len(categoriasplit) == 2:
        categoriasplit = [categoriasplit[0], categoriasplit[1]]
    return categoriasplit

def monthly_report(df):
    if df is None or df.empty:
        print("Nenhum dado disponível para o relatório mensal.")
        return

    df = df.copy()
    df['mês'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce').dt.to_period('M')

    resumo = build_summary_df(df, group_cols=['mês', 'tipo'])

    return resumo

def previsao_mensal_por_ocorrencia(df):
    df = df.copy()
    df['mes'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce').dt.to_period('M')
 
    resumo = build_summary_df(df, group_cols=['category', 'mes', 'tipo' ], extrai_func=extraiCategoria)
    
    df_despesas = resumo[['category', 'mes', 'despesas']]
    df_despesas = df_despesas[df_despesas['despesas'] > 0]

    df_despesas = contaCategorias(df, df_despesas)

    ocorrencias_mensais = df_despesas.groupby(['category', 'mes']).agg(
        soma_despesas=('despesas', 'sum'),
        qtd_ocorrencias=('despesas', 'count')
    ).reset_index()

    ocorrencias_mensais_filtradas = ocorrencias_mensais[ocorrencias_mensais['qtd_ocorrencias'] > 10]

    frequencia_mensal = ocorrencias_mensais_filtradas.groupby('category')['mes'].nunique().reset_index()
    frequencia_mensal.rename(columns={'mes': 'meses_com_recorrencia'}, inplace=True)

    # Define categorias consistentes (ex: pelo menos 2 meses com recorrência)
    categorias_consistentes = frequencia_mensal[frequencia_mensal['meses_com_recorrencia'] >= 2]['category']

    ocorrencias_mensais_consistentes = ocorrencias_mensais_filtradas[
        ocorrencias_mensais_filtradas['category'].isin(categorias_consistentes)
    ]
    ocorrencias_mensais_consistentes.rename(columns={'soma_despesas': 'media_despesas'}, inplace=True)
    resumo_categoria = ocorrencias_mensais_consistentes.groupby('category').agg({
        'media_despesas': 'mean',
        'qtd_ocorrencias': 'mean'
    }).reset_index()

    resumo_categoria['previsao_mensal'] = resumo_categoria['media_despesas'].round(2)

    resumo_categoria = resumo_categoria.merge(frequencia_mensal, on='category', how='left')

    def classificar_categoria(meses):
        if meses >= 5:
            return 'fixa'
        elif meses >= 3:
            return 'mista'
        else:
            return 'variável'

    resumo_categoria['tipo_categoria'] = resumo_categoria['meses_com_recorrencia'].apply(classificar_categoria)

    return resumo_categoria[['category', 'previsao_mensal', 'qtd_ocorrencias', 'tipo_categoria']]

def categoriasFixas(df):
    df = df.copy()
    resumo = build_summary_df(df, group_cols=['category', 'tipo'], extrai_func=extraiCategoria)

    df_agrupado = resumo.groupby('category').agg({
        'ganhos': 'mean',
        'despesas': 'mean',
        'saldo': 'mean',
        'count': 'sum'
    }).reset_index()

    df_agrupado = df_agrupado.sort_values(by='count', ascending=False).reset_index(drop=True)

    return df_agrupado


def daily_report(df, diaIn=None):
    if df is None or df.empty:
        return None, []

    df = df.copy()
    df['dia'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce').dt.date

    if diaIn:
        detalhes = []
        transacoes_dia = df[df['dia'].dt.day.astype(str) == diaIn]
        transacoes_dia["ganho"] = transacoes_dia['tipo'] == 'ganho'
        transacoes_dia["despesa"] = transacoes_dia['tipo'] == 'despesa'
        
        return transacoes_dia
    else:
         resumo = build_summary_df(df, group_cols=['dia', 'tipo'])

    resumo['dia'] = resumo['dia'].apply(lambda d: d.strftime('%d/%m/%Y'))
    return resumo

def gerar_graficos():
    try:
        geraGraficos(all_expenses_df)
        messagebox.showinfo("Gráficos", "Gráficos gerados com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro nos gráficos", str(e))

def mostrar_dataframe(df):
    janela = tk.Toplevel()
    janela.title("Dados")
    janela.geometry("1000x600")

    from tkinter import ttk
    
    estilo = ttk.Style()
    estilo.theme_use('clam')
    estilo.configure("Treeview",
                     background="#f0f2f5",
                     foreground="#2c3e50",
                     rowheight=25,
                     font=("Segoe UI", 9))
    estilo.configure("Treeview.Heading",
                     background="#3498db",
                     foreground="white",
                     borderwidth=1,
                     font=("Segoe UI", 10, "bold"))
    estilo.map('Treeview', background=[('selected', '#2980b9')])
    
    title_frame = tk.Frame(janela, bg="#2c3e50", height=50)
    title_frame.pack(fill=tk.X)
    
    tk.Label(
        title_frame,
        text="📊 Visualização de Dados",
        font=("Segoe UI", 14, "bold"),
        bg="#2c3e50",
        fg="white"
    ).pack(pady=12)
    
    tree_frame = tk.Frame(janela, bg="#f0f2f5")
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    scrollbar_y = ttk.Scrollbar(tree_frame)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    tree = ttk.Treeview(
        tree_frame,
        yscrollcommand=scrollbar_y.set,
        xscrollcommand=scrollbar_x.set
    )
    tree.pack(fill=tk.BOTH, expand=True)
    
    scrollbar_y.config(command=tree.yview)
    scrollbar_x.config(command=tree.xview)

    if df is not None and not df.empty:
        tree["columns"] = list(df.columns)
        tree["show"] = "tree headings"
        tree.column("#0", width=0, stretch=tk.NO)

        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=100)

        for idx, (_, row) in enumerate(df.iterrows()):
            tag = "oddrow" if idx % 2 == 0 else "evenrow"
            tree.insert("", "end", values=list(row), tags=(tag,))
        
        tree.tag_configure("oddrow", background="#ecf0f1")
        tree.tag_configure("evenrow", background="white")
    else:
        tree.insert("", "end", values=("Nenhum dado disponível",))
    
    footer_frame = tk.Frame(janela, bg="#2c3e50", height=40)
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    tk.Label(
        footer_frame,
        text=f"Total de registros: {len(df) if df is not None else 0}",
        font=("Segoe UI", 9),
        bg="#2c3e50",
        fg="#bdc3c7"
    ).pack(pady=8)

def geraGraficos(df):

    if df is None or df.empty:
        print("Nenhum dado disponível para gerar gráficos.")
        return

    plt.close('all')

    df = df.copy()
    df['mês'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce').dt.to_period('M')

    resumo = df.groupby(['mês', 'tipo'])['amount'].sum().unstack(fill_value=0)
    resumo = resumo.reset_index()
    resumo['mês'] = resumo['mês'].astype(str)

    sns.set_style("white")

    fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.4
    x = range(len(resumo))

    ganhos = resumo.get('ganho', 0)
    despesas = resumo.get('despesa', 0)

    rects1 = ax.bar(x, ganhos, width=bar_width, label='Ganhos', color='skyblue')
    rects2 = ax.bar([i + bar_width for i in x], despesas, width=bar_width, label='Despesas', color='salmon')

    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.set_xticks([i + bar_width / 2 for i in x])
    ax.set_xticklabels(resumo['mês'], rotation=45)
    ax.set_title('Ganhos vs Despesas Mensais', fontsize=16, weight='bold')
    ax.set_xlabel('Mês', fontsize=12)
    ax.set_ylabel('Valor (R$)', fontsize=12)

    resumo['saldo'] = resumo['ganho'] - resumo['despesa']
    ax.plot(x, resumo['saldo'], marker='o', linestyle='--', color='gray', label='Saldo')

    for i, saldo in enumerate(resumo['saldo']):
        cor = 'green' if saldo >= 0 else 'red'
        ax.text(i, saldo + 500, f'R$ {saldo:,.2f}', ha='center', fontsize=9, color=cor)

    ax.legend()

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'R$ {height:,.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height / 2),
                        ha='center', va='center',
                        color='black', fontsize=9)

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    plt.show()

def gerar_relatorios():
    try:
        mostrar_dataframe(monthly_report(all_expenses_df))
        resumodia = daily_report(all_expenses_df)
        mostrar_dataframe(resumodia)
        messagebox.showinfo("Relatórios", "Relatórios mensal e diário gerados.")
    except Exception as e:
        messagebox.showerror("Erro nos relatórios", str(e))

def gerar_resumo():
    try:
        gains, expenses, balance, summary = analyze_cashflow(all_expenses_df)
        if gains is not None:
            messagebox.showinfo("Resumo",
                f"Ganhos: {format_currency(gains)}\n"
                f"Despesas: {format_currency(expenses)}\n"
                f"Saldo: {format_currency(balance)}"
            )
        else:
            messagebox.showwarning("Resumo", "Nenhum dado encontrado para gerar o resumo.")
    except Exception as e:
        messagebox.showerror("Erro no resumo", str(e))

def limpar_dados():
    global all_expenses_df
    try:
        all_expenses_df = all_expenses_df.dropna(subset=['amount', 'tipo', 'data'])
        all_expenses_df = all_expenses_df[all_expenses_df['tipo'].isin(['ganho', 'despesa'])]
        all_expenses_df['amount'] = pd.to_numeric(all_expenses_df['amount'], errors='coerce')
        all_expenses_df = all_expenses_df[all_expenses_df['amount'] != 0]
        messagebox.showinfo("Limpeza", "Dados limpos com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro na limpeza", str(e))

def ler_dados():
    global all_expenses_df
    try:
        expenses_df = None

        pdf_txt_folder = os.path.join('data', 'pdf', nome_padrao)
        pdf_expenses_df = read_txt_expenses_from_folder(pdf_txt_folder)

        if expenses_df is not None and not expenses_df.empty:
            all_expenses_df = pd.concat([expenses_df, pdf_expenses_df], ignore_index=True)
        else:
            all_expenses_df = pdf_expenses_df

        messagebox.showinfo("Leitura", "Dados lidos e combinados com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro na leitura", str(e))

def processar_pdfs():
    try:
        process_pdfs_by_name(nome_padrao)
        messagebox.showinfo("PDFs", f"PDFs processados para '{nome_padrao}' com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro ao processar PDFs", str(e))

def verificar_totais():
    try:
        total_ganhos = all_expenses_df[all_expenses_df['tipo'] == 'ganho']['amount'].sum()
        total_despesas = all_expenses_df[all_expenses_df['tipo'] == 'despesa']['amount'].sum()
        total_geral = total_ganhos - total_despesas

        all_expenses_df['mês'] = pd.to_datetime(all_expenses_df['data'], format='%d-%m-%Y', errors='coerce').dt.to_period('M')
        resumo_mensal = all_expenses_df.groupby(['mês', 'tipo'])['amount'].sum().unstack(fill_value=0)
        total_mensal = (resumo_mensal.get('ganho', 0) - resumo_mensal.get('despesa', 0)).sum()

        resultado = (
            f"Total geral: {format_currency(total_geral)}\n"
            f"Total mensal: {format_currency(total_mensal)}"
        )

        if abs(total_geral - total_mensal) > 0.01:
            resultado += "\n⚠️ Diferença entre total geral e mensal detectada."

        messagebox.showinfo("Totais", resultado)

    except Exception as e:
        messagebox.showerror("Erro nos totais", str(e))

def mostrar_detalhes_treeview(detalhes):
    if not detalhes:
        return

    janela = tk.Toplevel()
    janela.title("Detalhes das Transações")

    tree = tk.Treeview(janela, columns=("Data", "Tipo", "Categoria", "Valor"), show="headings")
    tree.pack(fill="both", expand=True)

    for col in ("Data", "Tipo", "Categoria", "Valor"):
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    for item in detalhes:
        tree.insert("", "end", values=(item["Data"], item["Tipo"], item["Categoria"], item["Valor"]))

def gerar_relatorio_dia():
    dia = None
    resumo_df = daily_report(all_expenses_df, dia)

    if resumo_df is not None and not resumo_df.empty:
        mostrar_dataframe(resumo_df)
    else:
        messagebox.showinfo("Relatório", "Nenhum dado encontrado para o dia informado.")

def criar_interface():
    root = tk.Tk()
    root.title("Expense Tracker - Fluxo de Caixa")
    root.geometry("900x750")
    root.configure(bg="#f0f2f5")
    
    estilo_titulo = ("Segoe UI", 20, "bold")
    
    cor_primaria = "#2c3e50"
    cor_secundaria = "#3498db"
    cor_sucesso = "#27ae60"
    cor_atencao = "#e74c3c"

    header_frame = tk.Frame(root, bg=cor_primaria, height=80)
    header_frame.pack(fill=tk.X, side=tk.TOP)
    
    tk.Label(
        header_frame,
        text="💰 Expense Tracker",
        font=estilo_titulo,
        bg=cor_primaria,
        fg="white"
    ).pack(pady=15)
    
    tk.Label(
        header_frame,
        text="Gerenciador de Fluxo de Caixa - Silvana",
        font=("Segoe UI", 10),
        bg=cor_primaria,
        fg="#bdc3c7"
    ).pack()
    
    main_frame = tk.Frame(root, bg="#f0f2f5")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    section1 = tk.LabelFrame(
        main_frame,
        text="📥 Importação de Dados",
        font=("Segoe UI", 11, "bold"),
        bg="white",
        fg=cor_primaria,
        padx=15,
        pady=12,
        relief=tk.FLAT,
        borderwidth=1
    )
    section1.pack(fill=tk.X, pady=10)
    
    row1 = tk.Frame(section1, bg="white")
    row1.pack(fill=tk.X, pady=8)
    
    criar_botao(row1, "🔢 Processar PDFs", processar_pdfs, cor_secundaria).pack(side=tk.LEFT, padx=5)
    criar_botao(row1, "📥 Ler Dados", ler_dados, cor_sucesso).pack(side=tk.LEFT, padx=5)
    criar_botao(row1, "🧹 Limpar Dados", limpar_dados, cor_atencao).pack(side=tk.LEFT, padx=5)
    
    section2 = tk.LabelFrame(
        main_frame,
        text="📊 Análise e Resumos",
        font=("Segoe UI", 11, "bold"),
        bg="white",
        fg=cor_primaria,
        padx=15,
        pady=12,
        relief=tk.FLAT,
        borderwidth=1
    )
    section2.pack(fill=tk.X, pady=10)
    
    row2a = tk.Frame(section2, bg="white")
    row2a.pack(fill=tk.X, pady=8)
    
    criar_botao(row2a, "📄 Resumo Executivo", gerar_resumo, cor_secundaria).pack(side=tk.LEFT, padx=5)
    criar_botao(row2a, "🧮 Verificar Totais", verificar_totais, "#16a085").pack(side=tk.LEFT, padx=5)
    criar_botao(row2a, "Dashboard Central", gerar_dashboard_central, "#1abc9c").pack(side=tk.LEFT, padx=5)
    criar_botao(row2a, "📈 Gráficos Mensais", gerar_graficos, "#8e44ad").pack(side=tk.LEFT, padx=5)
    
    row2b = tk.Frame(section2, bg="white")
    row2b.pack(fill=tk.X, pady=8)
    
    criar_botao(row2b, "📊 Categorias", lambda: mostrar_dataframe(category_report(all_expenses_df)), cor_secundaria).pack(side=tk.LEFT, padx=5)
    criar_botao(row2b, "⚠️ Metas e Alertas", mostrar_alertas_financeiros, "#f39c12").pack(side=tk.LEFT, padx=5)
    criar_botao(row2b, "📑 Relatórios", gerar_relatorios, "#f39c12").pack(side=tk.LEFT, padx=5)
    
    section3 = tk.LabelFrame(
        main_frame,
        text="📋 Relatórios Detalhados",
        font=("Segoe UI", 11, "bold"),
        bg="white",
        fg=cor_primaria,
        padx=15,
        pady=12,
        relief=tk.FLAT,
        borderwidth=1
    )
    section3.pack(fill=tk.X, pady=10)
    
    row3a = tk.Frame(section3, bg="white")
    row3a.pack(fill=tk.X, pady=8)
    
    criar_botao(row3a, "📊 Relatório Mensal", lambda: mostrar_dataframe(monthly_report(all_expenses_df)), cor_secundaria).pack(side=tk.LEFT, padx=5)
    criar_botao(row3a, "📊 Despesas Fixas", lambda: mostrar_dataframe(previsao_mensal_por_ocorrencia(all_expenses_df)), "#2980b9").pack(side=tk.LEFT, padx=5)
    
    row3b = tk.Frame(section3, bg="white")
    row3b.pack(fill=tk.X, pady=8)
    
    criar_botao(row3b, "📅 Relatório Diário", gerar_relatorio_dia, "#d35400").pack(side=tk.LEFT, padx=5)
    criar_botao(row3b, "📊 Visualizar Dados", lambda: mostrar_dataframe(all_expenses_df), "#34495e").pack(side=tk.LEFT, padx=5)
    
    footer_frame = tk.Frame(root, bg=cor_primaria, height=40)
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    footer_left = tk.Frame(footer_frame, bg=cor_primaria)
    footer_left.pack(side=tk.LEFT, padx=20, pady=10)
    
    tk.Label(
        footer_left,
        text="✓ Aplicativo de Gerenciamento de Despesas",
        font=("Segoe UI", 9),
        bg=cor_primaria,
        fg="#bdc3c7"
    ).pack()
    
    footer_right = tk.Frame(footer_frame, bg=cor_primaria)
    footer_right.pack(side=tk.RIGHT, padx=20, pady=10)
    
    tk.Button(
        footer_right,
        text="❌ Sair",
        command=root.quit,
        bg=cor_atencao,
        fg="white",
        font=("Segoe UI", 9, "bold"),
        padx=20,
        pady=5,
        relief=tk.FLAT,
        cursor="hand2"
    ).pack()
    
    root.mainloop()

def criar_botao(parent, texto, comando, cor_fundo):
    botao = tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=cor_fundo,
        fg="white",
        font=("Segoe UI", 9, "bold"),
        padx=12,
        pady=8,
        relief=tk.FLAT,
        cursor="hand2",
        activebackground=ajustar_cor(cor_fundo, -20),
        activeforeground="white",
        bd=0
    )
    
    def on_enter(event):
        botao.config(bg=ajustar_cor(cor_fundo, -15))
    
    def on_leave(event):
        botao.config(bg=cor_fundo)
    
    botao.bind("<Enter>", on_enter)
    botao.bind("<Leave>", on_leave)
    
    return botao

def ajustar_cor(cor_hex, ajuste):
    """Ajusta o brilho de uma cor hexadecimal."""
    cor_hex = cor_hex.lstrip('#')
    rgb = tuple(int(cor_hex[i:i+2], 16) for i in (0, 2, 4))
    rgb_ajustado = tuple(max(0, min(255, c + ajuste)) for c in rgb)
    return f"#{rgb_ajustado[0]:02x}{rgb_ajustado[1]:02x}{rgb_ajustado[2]:02x}"


def main():
    criar_interface()

if __name__ == "__main__":
    main()