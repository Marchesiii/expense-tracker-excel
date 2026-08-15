import pandas as pd
import os

def parse_line_to_expense(line):
    """
    Extrai data, descrição, id da operação e valor separando em partes.
    Classifica corretamente como ganho ou despesa.
    """
    parts = line.strip().split()
    if len(parts) < 6:
        return None

    # 1. Data (primeira coluna)
    data = parts[0]

    # 2.1 Procura o saldo R$
    saldo_idx = None
    parts_reversed = parts[::-1]
    for i in range(len(parts_reversed)):
        if parts_reversed[i] == "R$":
            saldo_idx = len(parts) - i - 1
            break
    if saldo_idx is None or saldo_idx < 3:
        return None

    # 3. Descrição (do segundo elemento até o anterior ao id da operação)
    descricao = ' '.join(parts[1:saldo_idx])

    # 5. Valor (Antes do SALDO, deve ser "R$", valor, "R$", saldo)
    try:
        valor_idx = saldo_idx - 2
        if parts[valor_idx] == "R$":
            valor_str = parts[valor_idx + 1].replace('.', '').replace(',', '.')
            valor = float(valor_str)
        else:
            return None
    except Exception:
        return None

    tipo = 'despesa' if valor < 0 else 'ganho'
    amount = abs(valor)
    category = descricao
    return {'data': data, 'amount': amount, 'category': category, 'tipo': tipo}

def read_txt_expenses_from_folder(folder):
    """Lê todos os .txt da pasta e retorna DataFrame com data, amount, category, tipo."""
    data = []
    for filename in os.listdir(folder):
        if filename.lower().endswith('.txt'):
            with open(os.path.join(folder, filename), encoding='utf-8') as f:
                for line in f:
                    expense = parse_line_to_expense(line)
                    if expense:
                        data.append(expense)
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame(columns=['data', 'amount', 'category', 'tipo'])