import os

import pandas as pd

from scripts.process_pdf import process_pdfs_by_name
from scripts.process_txt import read_txt_expenses_from_folder


def load_data_from_txt_folder(folder_path):
    if not os.path.exists(folder_path):
        return pd.DataFrame(columns=["data", "amount", "category", "tipo"])
    return read_txt_expenses_from_folder(folder_path)


def load_all_expenses(business_name="Silvana"):
    pdf_txt_folder = os.path.join("data", "pdf", business_name)
    pdf_df = load_data_from_txt_folder(pdf_txt_folder)

    if pdf_df.empty:
        return pd.DataFrame(columns=["data", "amount", "category", "tipo"])

    return pdf_df


def process_pdf_files(business_name="Silvana"):
    process_pdfs_by_name(business_name)
    return load_all_expenses(business_name)
