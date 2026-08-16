import pandas as pd
import os

def parse_line_to_expense(line):
    """
    Extrai data, categoria, id da operação e valor separando em partes.
    Classifica corretamente como ganho ou despesa.
    """
    parts = line.strip().split()
    if len(parts) < 6:
        return None

    data = parts[0]
    r_values = [idx for idx, part in enumerate(parts) if part == "R$"]
    if len(r_values) < 2:
        return None

    amount_idx = r_values[-2]
    amount_token = parts[amount_idx + 1] if amount_idx + 1 < len(parts) else None
    if amount_token is None:
        return None

    descricao_tokens = parts[1:amount_idx]
    if descricao_tokens and descricao_tokens[-1].isdigit() and len(descricao_tokens[-1]) >= 6:
        descricao_tokens = descricao_tokens[:-1]

    descricao = ' '.join(descricao_tokens).strip()
    if not descricao:
        return None

    try:
        valor = float(amount_token.replace('.', '').replace(',', '.'))
    except ValueError:
        return None

    tipo = 'despesa' if valor < 0 else 'ganho'
    amount = abs(valor)
    return {'data': data, 'amount': amount, 'category': descricao, 'tipo': tipo}

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