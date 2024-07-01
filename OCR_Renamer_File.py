import os
import cv2
import pytesseract
import re
import streamlit as st
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from datetime import datetime

# Configurar o caminho do Tesseract OCR
caminho_tesseract = r"C:\Users\User\AppData\Local\Programs\Tesseract-OCR"
pytesseract.pytesseract.tesseract_cmd = os.path.join(caminho_tesseract, 'tesseract.exe')

# Função para extrair o ano da data do texto
def extract_year_from_text(text):
    padrao_data = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')
    datas_encontradas = padrao_data.findall(text)
    if datas_encontradas:
        data_extraida = datas_encontradas[0]
        ano = datetime.strptime(data_extraida, "%d/%m/%Y").year
        return ano
    return None

# Função para determinar a categoria (EPI ou Ferramentas) com base no texto
def categorize_file(text):
    if re.search(r'\b(EPI|UNIFORMES)\b', text, re.IGNORECASE):
        return 'EPI'
    return 'FERRAMENTA'

# Função para renomear os arquivos e retornar um dicionário com os novos nomes, anos e categorias
def rename_files_and_get_names(directory, progress_bar, progress_text):
    padrao_nome = re.compile(r'\b(?:[A-Z][A-Z]*\s*){2,}\b')
    contador_nomes = {}
    novo_nomes = {}
    arquivos_por_ano_e_categoria = {}

    arquivos = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_arquivos = len(arquivos)

    for i, nome_arquivo in enumerate(arquivos):
        caminho_imagem_original = os.path.join(directory, nome_arquivo)
        imagem_original = cv2.imread(caminho_imagem_original)
        texto_completo = pytesseract.image_to_string(imagem_original, lang="por")
        
        nomes_encontrados = padrao_nome.findall(texto_completo)
        ano = extract_year_from_text(texto_completo)
        categoria = categorize_file(texto_completo)
        
        if nomes_encontrados:
            nome_extraido = nomes_encontrados[0][:30]
            nome_extraido = re.sub(r'[\\/:*?"<>|]', '_', nome_extraido)
            nome_extraido = nome_extraido.replace('\n', '')

            if nome_extraido in contador_nomes:
                contador_nomes[nome_extraido] += 1
                novo_nome_arquivo = f"{nome_extraido}_{contador_nomes[nome_extraido]}.png"
            else:
                contador_nomes[nome_extraido] = 1
                novo_nome_arquivo = f"{nome_extraido}.png"

            novo_caminho_imagem_original = os.path.join(directory, novo_nome_arquivo)
            os.rename(caminho_imagem_original, novo_caminho_imagem_original)
            novo_nomes[nome_arquivo] = novo_nome_arquivo
            
            if ano:
                if ano not in arquivos_por_ano_e_categoria:
                    arquivos_por_ano_e_categoria[ano] = {'EPI': [], 'FERRAMENTA': []}
                arquivos_por_ano_e_categoria[ano][categoria].append(novo_nome_arquivo)

        # Atualizar barra de progresso
        progress_bar.progress((i + 1) / total_arquivos)
        progress_text.text(f"Processing file {i + 1} of {total_arquivos}")

    return novo_nomes, arquivos_por_ano_e_categoria

# Função para converter PNG para PDF em modo paisagem
def convert_png_to_pdf(png_path, pdf_path):
    image = Image.open(png_path)
    width, height = image.size
    aspect_ratio = width / height

    # Definir o tamanho da página do PDF com base na proporção da imagem
    if (aspect_ratio > 1):  # Paisagem
        pdf_width = 792  # 11 polegadas em pontos (1 polegada = 72 pontos)
        pdf_height = pdf_width / aspect_ratio
    else:  # Retrato ou quadrado
        pdf_height = 612  # 8,5 polegadas em pontos (1 polegada = 72 pontos)
        pdf_width = pdf_height * aspect_ratio

    pdf = canvas.Canvas(pdf_path, pagesize=(pdf_width, pdf_height))
    pdf.drawImage(png_path, 0, 0, width=pdf_width, height=pdf_height)
    pdf.showPage()
    pdf.save()

def main():
    st.title("OCR File Renamer and PNG to PDF Converter")

    uploaded_files = st.file_uploader("Upload your image files", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    convert_to_pdf = st.checkbox("Convert to PDF")
    output_zip_name = st.selectbox(
        "Select the name for the output ZIP file",
        ["LOTE 01 EPI", "LOTE 01 FERRAMENTAS", "LOTE 03 EPI", "LOTE 03 FERRAMENTAS", "LOTE 05 EPI", "LOTE 05 FERRAMENTAS", "LOTE 08 EPI", "LOTE 08 FERRAMENTAS", "BOTA FORA EPI", "BOTA FORA FERRAMENTAS", "GERAL FERRAMENTAS", "GERAL EPI", "GENEBRA EPI", "GENEBRA FERRAMENTAS"]
    )

    # Estado da página para rastrear se o botão de download foi clicado
    if 'download_clicked' not in st.session_state:
        st.session_state['download_clicked'] = False

    if st.button("Process Files"):
        if uploaded_files:
            temp_dir = tempfile.mkdtemp()
            for uploaded_file in uploaded_files:
                with open(os.path.join(temp_dir, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Configurar barra de progresso
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            renamed_files, arquivos_por_ano_e_categoria = rename_files_and_get_names(temp_dir, progress_bar, progress_text)
            
            # Criar um arquivo zip com os arquivos renomeados
            zip_file_name = output_zip_name + ".zip" if output_zip_name else "Processed_Files.zip"
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                with zipfile.ZipFile(os.path.join(temp_dir, zip_file_name), "w") as zip_file:
                    for ano, categorias in arquivos_por_ano_e_categoria.items():
                        for categoria, arquivos in categorias.items():
                            for arquivo in arquivos:
                                caminho_arquivo = os.path.join(temp_dir, arquivo)
                                if convert_to_pdf:
                                    pdf_path = caminho_arquivo.replace(".png", ".pdf")
                                    convert_png_to_pdf(caminho_arquivo, pdf_path)
                                    zip_file.write(pdf_path, arcname=os.path.join(str(ano), categoria, os.path.basename(pdf_path)))
                                    os.remove(caminho_arquivo)
                                else:
                                    zip_file.write(caminho_arquivo, arcname=os.path.join(str(ano), categoria, arquivo))

                st.session_state['download_clicked'] = True
                st.download_button(
                    label="Download Files",
                    data=open(os.path.join(temp_dir, zip_file_name), "rb").read(),
                    file_name=zip_file_name,
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()
