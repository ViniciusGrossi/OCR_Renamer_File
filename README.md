## **Visão Geral**

Este projeto foi desenvolvido para atender a uma demanda de digitalização em uma empresa, onde o processo manual de organização de arquivos consumia muito tempo. O encarregado pela tarefa precisava passar o dia todo separando os arquivos em ordem alfabética, por ano e por categoria de produtos. Este aplicativo, construído com Streamlit, automatiza todos esses processos, oferecendo uma solução eficiente para a renomeação e categorização de arquivos. Além disso, o aplicativo pode converter arquivos de imagem (PNG, JPG, JPEG) em PDF.

## **Funcionalidades**

1. **Renomeação Automática de Arquivos**:
    - Utiliza OCR (Reconhecimento Óptico de Caracteres) para extrair nomes e datas dos arquivos de imagem.
    - Renomeia os arquivos com base nos nomes extraídos e garante que os nomes sejam únicos.
2. **Organização por Ano e Categoria**:
    - Extrai o ano a partir das datas nos arquivos e os organiza em pastas por ano.
    - Classifica os arquivos em duas categorias: "EPI" e "Ferramentas", com base em palavras-chave encontradas no texto.
3. **Conversão de Imagens para PDF**:
    - Oferece a opção de converter imagens para PDF em modo paisagem ou retrato, dependendo da proporção da imagem.
4. **Download de Arquivos Organizados**:
    - Permite o download de todos os arquivos organizados em um arquivo ZIP.

## **Tecnologias Utilizadas**

- **Streamlit**: Para criar a interface do usuário.
- **Pytesseract**: Para OCR e extração de texto das imagens.
- **OpenCV**: Para manipulação de imagens.
- **ReportLab**: Para criar PDFs a partir de imagens.
- **Python**: Para a lógica do aplicativo e manipulação de arquivos.

# Uso
Inicie o aplicativo:

sh
Copiar código
streamlit run app.py
Upload de Arquivos:

Faça o upload dos arquivos de imagem (PNG, JPG, JPEG) através da interface do aplicativo.
Configurações de Conversão:

Selecione se deseja converter os arquivos para PDF.
Escolha o nome para o arquivo ZIP de saída.
Processamento de Arquivos:

Clique no botão "Process Files" para iniciar o processamento.
Acompanhe o progresso através da barra de progresso e do texto de status.
Download dos Arquivos:

Após o processamento, clique no botão "Download Files" para baixar o arquivo ZIP com os arquivos organizados.