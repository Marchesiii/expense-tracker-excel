import pandas as pd

data = {
    'data': ['01-01-2024', '02-01-2024', '03-01-2024', '04-01-2024', '05-01-2024'],
    'amount': [100.0, -50.0, 200.0, -30.0, 150.0],
    'category': ['Salário', 'Alimentação', 'Freelance', 'Transporte', 'Investimentos'],
    'tipo': ['ganho', 'despesa', 'ganho', 'despesa', 'ganho']
}

df = pd.DataFrame(data)
df.to_excel('.\data\expenses.xlsx', index=False)
print("Arquivo de teste criado com sucesso!")