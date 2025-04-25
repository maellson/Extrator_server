import json
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
import os
import pytesseract
from pdf2image import convert_from_path
import fitz  # PyMuPDF para páginas vetoriais
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do OCR
# ajuste o caminho se necessário
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# Caminhos
pdf_path = "arquivos_pdf/documento.pdf"
images_dir = "imagens_paginas"
texts_dir = "textos_paginas"

os.makedirs(images_dir, exist_ok=True)
os.makedirs(texts_dir, exist_ok=True)


def extrair_texto_via_ocr(pdf_path):
    paginas = convert_from_path(pdf_path, dpi=300)
    textos_paginas = []

    for num, pagina in enumerate(paginas, start=1):
        img_path = os.path.join(images_dir, f'pagina_{num}.png')
        pagina.save(img_path, 'PNG')

        texto = pytesseract.image_to_string(img_path, lang='por')
        textos_paginas.append((num, texto))

        with open(os.path.join(texts_dir, f'pagina_{num}.txt'), 'w', encoding='utf-8') as f:
            f.write(texto)

        print(f'Texto extraído da página {num}.')

    return textos_paginas


def extrair_texto_vetorial(pdf_path):
    doc = fitz.open(pdf_path)
    textos_paginas = []

    for num, page in enumerate(doc, start=1):
        texto = page.get_text()
        if texto.strip():
            textos_paginas.append((num, texto))
            with open(os.path.join(texts_dir, f'vetorial_pagina_{num}.txt'), 'w', encoding='utf-8') as f:
                f.write(texto)
            print(f'Texto vetorial extraído da página {num}.')

    return textos_paginas

# Combina OCR e vetorial, evita duplicação de página


def extrair_texto_completo(pdf_path):
    texto_ocr = dict(extrair_texto_via_ocr(pdf_path))
    texto_vetorial = dict(extrair_texto_vetorial(pdf_path))

    todas_paginas = {**texto_ocr, **texto_vetorial}
    paginas_texto = sorted(todas_paginas.items())
    return paginas_texto

# Construir vector store FAISS


def criar_vector_store(paginas_texto):
    documentos = []
    for num, texto in paginas_texto:
        documentos.append(f"Página {num}:\n{texto}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100)
    chunks = splitter.create_documents(documentos)

    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)

    vector_store = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True)
    print('Índice vetorial salvo localmente.')

# Consultar com LangChain e OpenAI


def consultar_vector_store(pergunta):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True)
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        retriever=vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 3}),
        return_source_documents=True
    )

    resposta = qa_chain({"query": pergunta})
    return resposta


# --------------------------------------


def classificar_documento(paginas_texto):
    conteudo = "\n\n".join(
        [f"Página {num}:\n{texto}" for num, texto in paginas_texto])

    prompt_template = PromptTemplate.from_template("""
Você está analisando um documento dividido por páginas, onde cada página começa com 'Página X:'.
Classifique as páginas de acordo com o conteúdo apresentado. Os tipos de conteúdo que devem ser detectados são:
- email
- boleto
- nota_fiscal

Considere:
- 'email' contém saudações, mensagens, assinaturas, ou linguagem de comunicação.
- 'boleto' contém código de barras, vencimento, valor, cedente ou banco.
- 'nota_fiscal' contém CNPJ, descrição de produtos/serviços, impostos, natureza da operação.

Responda apenas com um JSON, nesse formato:
{{
  "email": [1, 2],
  "boleto": [3],
  "nota_fiscal": [4, 5]
}}

Aqui está o conteúdo do documento:

{conteudo}
""")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    resposta = chain.run(conteudo=conteudo)

    try:
        return json.loads(resposta)
    except Exception:
        print("⚠️ Erro ao interpretar resposta do LLM como JSON:")
        print(resposta)
        return {"erro": "Formato inesperado", "resposta_bruta": resposta}


# Execução principal
if __name__ == "__main__":
    print("📄 Extraindo texto das páginas...")
    paginas_texto = extrair_texto_completo(pdf_path)

    print("🧠 Criando e salvando embeddings vetoriais...")
    criar_vector_store(paginas_texto)

    print("🤖 Classificando conteúdo...")
    classificacao = classificar_documento(paginas_texto)
    print(json.dumps(classificacao, indent=2))

    print("🤖 Consultando documento com agente RAG...")
    pergunta = ("Você está analisando um documento PDF que foi dividido por páginas. "
                "Cada página começa com o texto 'Página X:'. "
                "Seu objetivo é identificar em qual ou quais páginas aparece uma nota fiscal. "
                "Responda com o seguinte formato: 'nota_fiscal: [X]' ou 'nota_fiscal: [X-Y]'.")

    resultado = consultar_vector_store(pergunta)

    print("\n🔎 Resposta do Agente IA:")
    print(resultado["result"])

    print("\n📑 Documentos fontes usados na resposta:")
    for doc in resultado["source_documents"]:
        print(doc.page_content[:200], "...\n")
