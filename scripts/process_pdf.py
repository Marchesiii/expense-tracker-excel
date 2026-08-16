import PyPDF2
import re
import os

def convert_pdf_to_text(pdf_file, output_txt_file):
    """Converte PDF para TXT, juntando todos os blocos de movimentação e reconstruindo linhas quebradas."""
    try:
        with open(pdf_file, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'

        lines = text.splitlines()
        mov_lines = []
        inside_block = False
        for line in lines:
            if "Data Descrição ID da operação Valor Saldo" in line:
                inside_block = True
                continue
            if inside_block:
               
                if (
                    line.strip() == "" or
                    "Data Descrição ID da operação Valor Saldo" in line or
                    line.strip().startswith("Saldo final:") or
                    line.strip().startswith("Data de geração:")
                ):
                    inside_block = False
                    continue

                if re.match(r'\d{2}-\d{2}-\d{4}Você tem alguma dúvida\?!', line.replace(' ', '')):
                    continue
                mov_lines.append(line)

        reconstructed = []
        buffer = ""
        for line in mov_lines:
            if re.match(r'\d{2}-\d{2}-\d{4}', line) or re.search(r'\d+/\d+\d{2}-\d{2}-\d{4}', line):
                if buffer:
                    reconstructed.append(buffer.strip())
                buffer = ""\

                match = re.search(r'(\d{2}-\d{2}-\d{4})(.*)', line)
                if match:
                    data = match.group(1)
                    restante = match.group(2).lstrip()
                    buffer = data + " " + restante
                else:
                    buffer = line.strip()  # fallback, caso não encontre a data
            else:
                buffer += line.lstrip()

        if buffer:
            reconstructed.append(buffer.strip())

        
        final_lines = []
        for line in reconstructed:
            line = re.sub(r'(\D)(\d{8,})', r'\1 \2', line, count=1)
            final_lines.append(line)

        filtered_text = '\n'.join(final_lines)

        with open(output_txt_file, 'w', encoding='utf-8') as output_file:
            output_file.write(filtered_text)
        print(f"Conteúdo do PDF salvo em {output_txt_file}")
    except Exception as e:
        print(f"Erro ao processar o arquivo PDF: {e}")

def process_pdfs_by_name(nome):
    """Processa todos os PDFs em data/pdf/<nome>, pulando se o .txt já existir."""
    pdf_folder = os.path.join('data', 'pdf', nome)
    if not os.path.exists(pdf_folder):
        print(f"Pasta não encontrada: {pdf_folder}")
        return
    for filename in os.listdir(pdf_folder):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder, filename)
            output_txt = os.path.splitext(pdf_path)[0] + '.txt'
            if os.path.exists(output_txt):
                print(f"Arquivo já processado, pulando: {output_txt}")
                continue
            convert_pdf_to_text(pdf_path, output_txt)

        