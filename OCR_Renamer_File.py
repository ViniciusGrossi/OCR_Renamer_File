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

# Configurar o caminho do Tesseract OCR
caminho_tesseract = r"C:\Users\User\AppData\Local\Programs\Tesseract-OCR"
pytesseract.pytesseract.tesseract_cmd = os.path.join(caminho_tesseract, 'tesseract.exe')

# Função para renomear os arquivos e retornar um dicionário com os novos nomes
def rename_files_and_get_names(directory, progress_bar, progress_text):
    padrao_nome = re.compile(r'\b(?:[A-Z][A-Z]*\s*){2,}\b')
    contador_nomes = {}
    novo_nomes = {}

    arquivos = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_arquivos = len(arquivos)

    for i, nome_arquivo in enumerate(arquivos):
        caminho_imagem_original = os.path.join(directory, nome_arquivo)
        imagem_original = cv2.imread(caminho_imagem_original)
        texto_completo = pytesseract.image_to_string(imagem_original, lang="por")
        nomes_encontrados = padrao_nome.findall(texto_completo)
        
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

        # Atualizar barra de progresso
        progress_bar.progress((i + 1) / total_arquivos)
        progress_text.text(f"Processing file {i + 1} of {total_arquivos}")

    return novo_nomes

# Função para converter PNG para PDF em modo paisagem
def convert_png_to_pdf(png_path, pdf_path):
    image = Image.open(png_path)
    width, height = image.size
    aspect_ratio = width / height

    # Definir o tamanho da página do PDF com base na proporção da imagem
    if aspect_ratio > 1:  # Paisagem
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
        ["LOTE 01 EPI", "LOTE 01 FERRAMENTAS", "LOTE 03 EPI", "LOTE 03 FERRAMENTAS", "LOTE 05 EPI", "LOTE 05 FERRAMENTAS", "LOTE 08 EPI", "LOTE 08 FERRAMENTAS","BOTA FORA EPI", "BOTA FORA FERRAMENTAS", "GERAL FERRAMENTAS", "GERAL EPI","GENEBRA EPI", "GENEBRA FERRAMENTAS"]
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
            
            renamed_files = rename_files_and_get_names(temp_dir, progress_bar, progress_text)
            
            # Criar um arquivo zip com os arquivos renomeados
            zip_file_name = output_zip_name + ".zip" if output_zip_name else "Processed_Files.zip"
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                with zipfile.ZipFile(os.path.join(temp_dir, zip_file_name), "w") as zip_file:
                    total_files = len(renamed_files)
                    for i, (original_name, new_name) in enumerate(renamed_files.items()):
                        png_path = os.path.join(temp_dir, new_name)
                        
                        if convert_to_pdf:
                            pdf_path = png_path.replace(".png", ".pdf")
                            convert_png_to_pdf(png_path, pdf_path)
                            zip_file.write(pdf_path, arcname=os.path.basename(pdf_path))
                            os.remove(png_path)
                        else:
                            zip_file.write(png_path, arcname=new_name)
                        
                        # Atualizar barra de progresso
                        progress_bar.progress((i + 1) / total_files)
                        progress_text.text(f"Zipping file {i + 1} of {total_files}")

                st.session_state['download_clicked'] = True
                st.download_button(
                    label="Download Files", 
                    data=open(os.path.join(temp_dir, zip_file_name), "rb").read(), 
                    file_name=zip_file_name, 
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()
