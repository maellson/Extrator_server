
import os
import json
import pytesseract
from pdf2image import convert_from_path
import fitz  # PyMuPDF
from dotenv import load_dotenv


# imports atualizados
from langchain.prompts import PromptTemplate
# from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains import RetrievalQA

import fitz  # PyMuPDF


def gerar_highlighted_pdf(input_pdf: str,
                          output_pdf: str,
                          classificacao: dict,
                          termos_por_tipo: dict):
    doc = fitz.open(input_pdf)
    for tipo, paginas in classificacao.items():
        termos = termos_por_tipo.get(tipo, [])
        for pg in paginas:
            page = doc[pg - 1]
            # obtém o layout completo em dict
            pag_dict = page.get_text("dict")
            for block in pag_dict["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_span = span["text"]
                        # verifica cada termo dentro do texto do span
                        for termo in termos:
                            if termo.lower() in text_span.lower():
                                # bbox do span
                                r = fitz.Rect(span["bbox"])
                                # desenha amarelo sólido
                                page.draw_rect(r, fill=(1, 1, 0), width=0)
    # salva já com o destaque “queimado”
    doc.save(output_pdf, garbage=4, deflate=True)
    print(f"[Highlight] PDF anotado salvo em: {output_pdf}")


def exportar_paginas_com_highlight(highlighted_pdf: str, output_prefix: str):
    doc = fitz.open(highlighted_pdf)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(alpha=False)
        fn = f"{output_prefix}_page_{i}.png"
        pix.save(fn)
        print(f"[Export] Página {i} salva como: {fn}")


# Carregar variáveis de ambiente
load_dotenv()

# Configuração do OCR (ajuste o caminho se necessário)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# Caminhos
pdf_path = "arquivos_pdf/documento.pdf"
images_dir = "imagens_paginas"
texts_dir = "textos_paginas"
highlighted_pages = "highlighted_pages"

os.makedirs(images_dir, exist_ok=True)
os.makedirs(texts_dir, exist_ok=True)
# Add this line after the other os.makedirs calls
# os.makedirs(highlighted_pages, exist_ok=True)


def extrair_texto_via_ocr(pdf_path):
    paginas = convert_from_path(pdf_path, dpi=300)
    textos = []
    for num, pagina in enumerate(paginas, start=1):
        img_path = os.path.join(images_dir, f"pagina_{num}.png")
        pagina.save(img_path, "PNG")

        texto = pytesseract.image_to_string(img_path, lang="por")
        textos.append((num, texto))
        with open(os.path.join(texts_dir, f"pagina_{num}.txt"), "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"[OCR] Página {num} extraída.")
    return textos


def extrair_texto_vetorial(pdf_path):
    doc = fitz.open(pdf_path)
    textos = []
    for num, page in enumerate(doc, start=1):
        texto = page.get_text().strip()
        if texto:
            textos.append((num, texto))
            with open(os.path.join(texts_dir, f"vetorial_pagina_{num}.txt"), "w", encoding="utf-8") as f:
                f.write(texto)
            print(f"[Vetorial] Página {num} extraída.")
    return textos


def extrair_texto_completo(pdf_path):
    ocr = dict(extrair_texto_via_ocr(pdf_path))
    vet = dict(extrair_texto_vetorial(pdf_path))
    todas = {**ocr, **vet}
    return sorted(todas.items())


def classificar_documento(paginas_texto):
    conteudo = "\n\n".join(f"Página {n}:\n{t}" for n, t in paginas_texto)

    prompt_template = PromptTemplate.from_template("""
        Você está analisando um documento dividido por páginas, onde cada página começa com 'Página X:'.
        Classifique as páginas de acordo com o conteúdo apresentado. Os tipos de conteúdo que devem ser detectados são:
        - Voucher:"Número de reserva", "Hóspede", "Quarto:", "check in", "arrival", "chegada", "Quarto nº"
        - boleto: "Valor do Documento", "Juros/Multa", "Boleto", "Recibo do Pagador", "Local Pagamento", "Pagador"
        - nota_fiscal: "NOTA FISCAL DE SERVIÇO ELETRÔNICA", "NÚMERO DA NOTA", "TOMADOR DE SERVIÇOS", "PRESTADOR DE SERVIÇOS", "CNAE"

        Considere:
        - 'voucher' contém a descrição do agendamento, nome do cliente, data de check-in, quarto, valor, forma de pagamento, número do voucher.
        - 'boleto' contém código de barras, vencimento, valor, cedente ou banco, valor do documento.
        - 'nota_fiscal' contém CNPJ, descrição de produtos/serviços, impostos, natureza da operação, o tomardor e o prestador de serviços.
        - 'descarte' é qualquer página que não se encaixa em nenhum dos outros tipos.

        Responda apenas com um JSON, nesse formato:
        {{
        "voucher": [1, 2],
        "boleto": [3],
        "nota_fiscal": [4, 5]
        "descarte": [6, 7]
        }}

        Aqui está o conteúdo do documento:

        {conteudo}
""")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt_template | llm
    ai_message = chain.invoke({"conteudo": conteudo})

    # Extrai o texto puro do AIMessage
    text = ai_message.content if hasattr(
        ai_message, "content") else str(ai_message)

    # Limpeza de markdown/backticks
    resposta_limpa = text.strip().lstrip("```json").rstrip("```").strip()

    try:
        return json.loads(resposta_limpa)
    except json.JSONDecodeError:
        print("⚠️ Falha ao parsear JSON:")
        print(text)
        return {"erro": "formato inválido", "raw": text}


if __name__ == "__main__":
    print("📄 Extraindo texto...")
    paginas = extrair_texto_completo(pdf_path)

    print("🔖 Classificando páginas por tipo:")
    classificacao = classificar_documento(paginas)
    print(json.dumps(classificacao, indent=2))

    # --- dicionário de termos a buscar em cada tipo
    termos_por_tipo = {
        "nota_fiscal": ["NOTA FISCAL DE SERVIÇO ELETRÔNICA", "NÚMERO DA NOTA", "TOMADOR DE SERVIÇOS", "PRESTADOR DE SERVIÇOS", "CNAE"],
        "boleto": ["Valor do Documento", "Juros/Multa", "Boleto", "Recibo do Pagador", "Local Pagamento", "Pagador"],
        "voucher": ["Número de reserva", "Hóspede", "Quarto:", "check in", "arrival", "chegada", "Quarto nº"]
    }

    # 1) Gere um PDF anotado (com retângulos amarelos)
    """ highlighted_pdf = "documento_highlighted.pdf"
    gerar_highlighted_pdf(
        input_pdf=pdf_path,
        output_pdf=highlighted_pdf,
        classificacao=classificacao,
        termos_por_tipo=termos_por_tipo
    )

    # 2) Exporte cada página anotada em PNG
    exportar_paginas_com_highlight(
        highlighted_pdf=highlighted_pdf,
        output_prefix="highlighted"
    ) """
  # Cria o diretório highlight_pages
    os.makedirs(highlighted_pages, exist_ok=True)

    highlighted_pdf = "documento_highlighted.pdf"
    gerar_highlighted_pdf(pdf_path, highlighted_pdf,
                          classificacao, termos_por_tipo)
    exportar_paginas_com_highlight(highlighted_pdf, os.path.join(highlighted_pages, "highlighted"))
