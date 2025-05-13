import os
import cv2
import pytesseract
import re
import streamlit as st
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from PIL import Image

# Configurar o caminho do Tesseract OCR
caminho_tesseract = r"C:\Users\User\AppData\Local\Programs\Tesseract-OCR"
pytesseract.pytesseract.tesseract_cmd = os.path.join(caminho_tesseract, 'tesseract.exe')

# Função para identificar o lote do arquivo
def identify_lot(text):
    text = text.upper()
    
    # Verificar Lote 01
    if re.search(r'\bLOTE\s*0*1\b', text):
        return "Lote 01"
    
    # Verificar Bota Fora
    if re.search(r'\bBOTA\s*FORA\b', text):
        return "Bota Fora"
    
    # Verificar Jardim Genebra
    if re.search(r'\bJARDIM\s*GENEBRA\b', text) or re.search(r'\bGENEBRA\b', text):
        return "Jardim Genebra"
    
    # Verificar Grama e seus lotes
    if re.search(r'\bGRAMA\b', text):
        # Verificar lotes específicos de Grama
        if re.search(r'\bGRAMA\s*0*2\b', text) or re.search(r'\bLOTE\s*0*2\b', text):
            return "Grama/Grama 02"
        elif re.search(r'\bGRAMA\s*0*3\b', text) or re.search(r'\bLOTE\s*0*3\b', text):
            return "Grama/Grama 03"
        elif re.search(r'\bGRAMA\s*0*4\b', text) or re.search(r'\bLOTE\s*0*4\b', text):
            return "Grama/Grama 04"
        elif re.search(r'\bGRAMA\s*0*5\b', text) or re.search(r'\bLOTE\s*0*5\b', text):
            return "Grama/Grama 05"
        else:
            return "Grama"
    
    # Se não identificou nenhum lote específico
    return "Gerais"

# Função para extrair nomes próprios do texto
def extract_proper_names(text):
    # Padrão para encontrar nomes próprios (duas ou mais palavras iniciadas com maiúscula)
    padrao_nome = re.compile(r'\b(?:[A-Z][A-Za-z]*\s+){1,}[A-Z][A-Za-z]*\b')
    
    # Padrão alternativo para um nome próprio único
    padrao_nome_unico = re.compile(r'\b[A-Z][A-Za-z]{2,}\b')
    
    nomes_encontrados = padrao_nome.findall(text)
    
    # Se não encontrou nomes com o padrão principal, tenta o padrão alternativo
    if not nomes_encontrados:
        nomes_encontrados = padrao_nome_unico.findall(text)
        # Filtra palavras comuns que não são nomes próprios
        palavras_comuns = ['LOTE', 'BOTA', 'FORA', 'JARDIM', 'GENEBRA', 'GRAMA']
        nomes_encontrados = [nome for nome in nomes_encontrados if nome not in palavras_comuns]
    
    if nomes_encontrados:
        # Limita o tamanho do nome e limpa caracteres especiais
        nome_extraido = re.sub(r'[\\/:*?"<>|]', '_', nomes_encontrados[0][:30]).replace('\n', '')
        return nome_extraido
    
    return None

# Função para renomear os arquivos e organizá-los por lotes
def rename_files_and_organize_by_lot(directory, progress_bar, progress_text):
    contador_nomes = {}
    arquivos_por_lote = {}
    novo_nomes = {}

    arquivos = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_arquivos = len(arquivos)

    for i, nome_arquivo in enumerate(arquivos):
        caminho_imagem_original = os.path.join(directory, nome_arquivo)
        imagem_original = cv2.imread(caminho_imagem_original)
        texto_completo = pytesseract.image_to_string(imagem_original, lang="por")

        # Extrair nome próprio
        nome_extraido = extract_proper_names(texto_completo)
        if not nome_extraido:
            nome_extraido = "Documento"
            
        # Identificar lote
        lote = identify_lot(texto_completo)
        
        # Criar nome único para o arquivo
        contador_nomes[nome_extraido] = contador_nomes.get(nome_extraido, 0) + 1
        novo_nome_arquivo = f"{nome_extraido}_{contador_nomes[nome_extraido]}.png" if contador_nomes[nome_extraido] > 1 else f"{nome_extraido}.png"
        
        novo_caminho_imagem_original = os.path.join(directory, novo_nome_arquivo)
        os.rename(caminho_imagem_original, novo_caminho_imagem_original)
        novo_nomes[nome_arquivo] = novo_nome_arquivo
        
        # Adicionar à estrutura de arquivos por lote
        arquivos_por_lote.setdefault(lote, []).append(novo_nome_arquivo)

        # Atualizar barra de progresso
        progress_bar.progress((i + 1) / total_arquivos)
        progress_text.text(f"Processando arquivo {i + 1} de {total_arquivos}")

    return novo_nomes, arquivos_por_lote

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
    st.title("OCR File Renamer and Lot Organizer")

    uploaded_files = st.file_uploader("Upload your image files", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    convert_to_pdf = st.checkbox("Convert to PDF")
    output_zip_name = st.text_input("Enter the name for the output ZIP file", "Processed_Files")

    if st.button("Process Files") and uploaded_files:
        with st.spinner("Processing files..."):
            temp_dir = tempfile.mkdtemp()
            for uploaded_file in uploaded_files:
                with open(os.path.join(temp_dir, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

            progress_bar = st.progress(0)
            progress_text = st.empty()

            renamed_files, arquivos_por_lote = rename_files_and_organize_by_lot(temp_dir, progress_bar, progress_text)

            # Criar arquivo ZIP com a estrutura de pastas por lote
            zip_file_name = f"{output_zip_name}.zip" if output_zip_name else "Processed_Files.zip"
            with zipfile.ZipFile(os.path.join(temp_dir, zip_file_name), "w") as zip_file:
                for lote, arquivos in arquivos_por_lote.items():
                    for arquivo in arquivos:
                        caminho_arquivo = os.path.join(temp_dir, arquivo)
                        if convert_to_pdf:
                            pdf_path = caminho_arquivo.replace(".png", ".pdf").replace(".jpg", ".pdf").replace(".jpeg", ".pdf")
                            convert_png_to_pdf(caminho_arquivo, pdf_path)
                            zip_file.write(pdf_path, arcname=os.path.join(lote, os.path.basename(pdf_path)))
                        else:
                            zip_file.write(caminho_arquivo, arcname=os.path.join(lote, arquivo))

            st.success("Files processed successfully!")
            st.download_button(
                label="Download Files",
                data=open(os.path.join(temp_dir, zip_file_name), "rb").read(),
                file_name=zip_file_name,
                mime="application/zip"
            )

if __name__ == "__main__":
    main()