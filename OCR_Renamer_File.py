import os
import cv2
from tesserocr import PyTessBaseAPI
import re
import streamlit as st
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from PIL import Image
from datetime import datetime

def ocr_image(image):
    with PyTessBaseAPI(lang='por') as api:
        api.SetImage(image)
        return api.GetUTF8Text()
# Função para extrair o ano da data do texto
def extract_year_from_text(text):
    padrao_data = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')
    datas_encontradas = padrao_data.findall(text)
    if datas_encontradas:
        data_extraida = datas_encontradas[0]
        return datetime.strptime(data_extraida, "%d/%m/%Y").year
    return None

# Função para renomear os arquivos e retornar um dicionário com os novos nomes e anos
def rename_files_and_get_names(directory, progress_bar, progress_text):
    padrao_nome = re.compile(r'\b(?:[A-Z][A-Z]*\s*){2,}\b')
    contador_nomes = {}
    novo_nomes = {}
    arquivos_por_ano = {}

    arquivos = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_arquivos = len(arquivos)

    for i, nome_arquivo in enumerate(arquivos):
        caminho_imagem_original = os.path.join(directory, nome_arquivo)
        imagem_original = cv2.imread(caminho_imagem_original)
        texto_completo = ocr_image(imagem_original)

        nomes_encontrados = padrao_nome.findall(texto_completo)
        ano = extract_year_from_text(texto_completo)

        if nomes_encontrados:
            nome_extraido = re.sub(r'[\\/:*?"<>|]', '_', nomes_encontrados[0][:30]).replace('\n', '')
            contador_nomes[nome_extraido] = contador_nomes.get(nome_extraido, 0) + 1
            novo_nome_arquivo = f"{nome_extraido}_{contador_nomes[nome_extraido]}.png" if contador_nomes[nome_extraido] > 1 else f"{nome_extraido}.png"

            novo_caminho_imagem_original = os.path.join(directory, novo_nome_arquivo)
            os.rename(caminho_imagem_original, novo_caminho_imagem_original)
            novo_nomes[nome_arquivo] = novo_nome_arquivo

            if ano:
                arquivos_por_ano.setdefault(ano, []).append(novo_nome_arquivo)

        # Atualizar barra de progresso
        progress_bar.progress((i + 1) / total_arquivos)
        progress_text.text(f"Processing file {i + 1} of {total_arquivos}")

    return novo_nomes, arquivos_por_ano

# Função para converter PNG para PDF
def convert_png_to_pdf(png_path, pdf_path):
    image = Image.open(png_path)
    aspect_ratio = image.width / image.height

    if aspect_ratio > 1:  # Paisagem
        pdf_width, pdf_height = 792, 792 / aspect_ratio
    else:  # Retrato ou quadrado
        pdf_height, pdf_width = 612, 612 * aspect_ratio

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
        ["LOTE 01", "LOTE 03", "LOTE 05", "LOTE 08", "BOTA FORA", "GERAL", "GENEBRA"]
    )

    if st.button("Process Files") and uploaded_files:
        temp_dir = tempfile.mkdtemp()
        for uploaded_file in uploaded_files:
            with open(os.path.join(temp_dir, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())

        progress_bar = st.progress(0)
        progress_text = st.empty()

        renamed_files, arquivos_por_ano = rename_files_and_get_names(temp_dir, progress_bar, progress_text)

        zip_file_name = f"{output_zip_name}.zip" if output_zip_name else "Processed_Files.zip"
        with zipfile.ZipFile(os.path.join(temp_dir, zip_file_name), "w") as zip_file:
            for ano, arquivos in arquivos_por_ano.items():
                for arquivo in arquivos:
                    caminho_arquivo = os.path.join(temp_dir, arquivo)
                    if convert_to_pdf:
                        pdf_path = caminho_arquivo.replace(".png", ".pdf")
                        convert_png_to_pdf(caminho_arquivo, pdf_path)
                        zip_file.write(pdf_path, arcname=os.path.join(str(ano), os.path.basename(pdf_path)))
                        os.remove(caminho_arquivo)
                    else:
                        zip_file.write(caminho_arquivo, arcname=os.path.join(str(ano), arquivo))

        st.download_button(
            label="Download Files",
            data=open(os.path.join(temp_dir, zip_file_name), "rb").read(),
            file_name=zip_file_name,
            mime="application/zip"
        )

if __name__ == "__main__":
    main()
