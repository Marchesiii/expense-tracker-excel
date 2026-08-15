import pandas as pd

def read_expenses(file_path):
    """Lê as despesas do arquivo Excel."""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return None
    
if __name__ == "__main__":
    read_expenses()