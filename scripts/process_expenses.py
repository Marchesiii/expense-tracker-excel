from time import sleep
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import tkinter as tk
from tkinter import messagebox
from process_pdf import process_pdfs_by_name
from process_txt import read_txt_expenses_from_folder

all_expenses_df = pd.DataFrame()
nome_padrao = "Silvana"

def format_currency(value):
    """Formata o valor para o padrão R$ xx,xx."""
    return f"R$ {value:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')

def analyze_cashflow(df):
    """Analisa o fluxo de caixa: ganhos totais, despesas totais e saldo."""
    if df is not None:
        total_gains = df[df['tipo'] == 'ganho']['amount'].sum()
        total_expenses = df[df['tipo'] == 'despesa']['amount'].sum()
        balance = total_gains - total_expenses
        category_summary = df.groupby(['tipo', 'category'])['amount'].sum()
        return total_gains, total_expenses, balance, category_summary
    return None, None, None, None

def build_summary_df(df, group_cols, value_col='amount', tipo_col='tipo', extrai_func=None, aggfunc='sum'):
    """
    Gera um DataFrame resumo agrupado por colunas dinâmicas.

    Parâmetros:
    - df: DataFrame original
    - group_cols: lista de colunas para agrupar (ex: ['category', 'tipo'])
    - value_col: coluna de valores numéricos (default: 'amount')
    - tipo_col: coluna que separa 'ganho' e 'despesa'
    - extrai_func: função opcional para tratar nomes de categoria (aplicada apenas se 'category' estiver em group_cols)
    - aggfunc: função de agregação (default: 'sum')

    Retorna:
    - DataFrame agrupado com colunas de agrupamento + ganhos, despesas e saldo
    """
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
    """Gera um relatório de categorias de despesas e ganhos."""
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
    """Gera um relatório de ganhos e despesas por mês."""
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
    """Gera um relatório de ganhos e despesas por dia, com detalhes."""
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
    
    # Criar estilo
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
    
    # Frame para título
    title_frame = tk.Frame(janela, bg="#2c3e50", height=50)
    title_frame.pack(fill=tk.X)
    
    tk.Label(
        title_frame,
        text="📊 Visualização de Dados",
        font=("Segoe UI", 14, "bold"),
        bg="#2c3e50",
        fg="white"
    ).pack(pady=12)
    
    # Frame para o Treeview
    tree_frame = tk.Frame(janela, bg="#f0f2f5")
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Scrollbars
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
    
    # Frame para rodapé
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
    """Gera gráficos de ganhos e despesas por mês."""

    if df is None or df.empty:
        print("Nenhum dado disponível para gerar gráficos.")
        return

    df = df.copy()
    df['mês'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce').dt.to_period('M')

    resumo = df.groupby(['mês', 'tipo'])['amount'].sum().unstack(fill_value=0)

    resumo = resumo.reset_index()
    resumo['mês'] = resumo['mês'].astype(str)

    sns.set_style("white")
    plt.grid(axis='y', linestyle='--', alpha=0.3)


    plt.figure(figsize=(10, 6))
    bar_width = 0.4
    x = range(len(resumo))

    ganhos = resumo.get('ganho', 0)
    despesas = resumo.get('despesa', 0)

    rects1 = plt.bar(x, ganhos, width=bar_width, label='Ganhos', color='skyblue')
    rects2 = plt.bar([i + bar_width for i in x], despesas, width=bar_width, label='Despesas', color='salmon')

    plt.xticks([i + bar_width / 2 for i in x], resumo['mês'], rotation=45)
    plt.title('Ganhos vs Despesas Mensais', fontsize=16, weight='bold')
    plt.xlabel('Mês', fontsize=12)
    plt.ylabel('Valor (R$)', fontsize=12)
    resumo['saldo'] = resumo['ganho'] - resumo['despesa']
    plt.plot(x, resumo['saldo'], marker='o', linestyle='--', color='gray', label='Saldo')
    for i, saldo in enumerate(resumo['saldo']):
        cor = 'green' if saldo >= 0 else 'red'
        plt.text(i, saldo + 500, f'R$ {saldo:,.2f}', ha='center', fontsize=9, color=cor)
    plt.legend()

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            plt.annotate(f'R$ {height:,.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height / 2),
                        ha='center', va='center',
                        color='black', fontsize=9)


    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
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
    
    # Configurar estilo
    estilo_titulo = ("Segoe UI", 20, "bold")
    estilo_subtitulo = ("Segoe UI", 11, "")
    estilo_botao = ("Segoe UI", 10, "")
    
    # Cores do tema
    cor_primaria = "#2c3e50"
    cor_secundaria = "#3498db"
    cor_sucesso = "#27ae60"
    cor_atencao = "#e74c3c"
    cor_fundo_claro = "#ecf0f1"
    cor_texto = "#2c3e50"
    
    # ===== HEADER =====
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
    
    # ===== MAIN CONTENT =====
    main_frame = tk.Frame(root, bg="#f0f2f5")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # ===== SEÇÃO 1: IMPORTAÇÃO DE DADOS =====
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
    
    # ===== SEÇÃO 2: ANÁLISE E RESUMOS =====
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
    criar_botao(row2a, "📈 Gráficos Mensais", gerar_graficos, "#8e44ad").pack(side=tk.LEFT, padx=5)
    
    row2b = tk.Frame(section2, bg="white")
    row2b.pack(fill=tk.X, pady=8)
    
    criar_botao(row2b, "📊 Categorias", lambda: mostrar_dataframe(category_report(all_expenses_df)), cor_secundaria).pack(side=tk.LEFT, padx=5)
    criar_botao(row2b, "📑 Relatórios", gerar_relatorios, "#f39c12").pack(side=tk.LEFT, padx=5)
    
    # ===== SEÇÃO 3: RELATÓRIOS DETALHADOS =====
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
    
    # ===== FOOTER =====
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
    """Cria um botão com estilo moderno."""
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
    
    # Efeito hover
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