import os
import json
import pytesseract
from pdf2image import convert_from_path
import fitz  # PyMuPDF
from dotenv import load_dotenv


# imports atualizados
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do OCR (ajuste o caminho se necessário)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# Caminhos
pdf_path = "arquivos_pdf/documento.pdf"
images_dir = "imagens_paginas"
texts_dir = "textos_paginas"

os.makedirs(images_dir, exist_ok=True)
os.makedirs(texts_dir, exist_ok=True)


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


def criar_vector_store(paginas_texto):
    docs = [f"Página {num}:\n{txt}" for num, txt in paginas_texto]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100)
    chunks = splitter.create_documents(docs)

    emb = OpenAIEmbeddings()
    store = FAISS.from_documents(chunks, emb)
    store.save_local("faiss_index")
    print("[FAISS] Índice salvo em ./faiss_index")


def consultar_vector_store(pergunta: str):
    emb = OpenAIEmbeddings()
    store = FAISS.load_local(
        "faiss_index", emb, allow_dangerous_deserialization=True
    )
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        retriever=store.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
    )
    # usa .invoke() em v0.2+
    return qa.invoke({"query": pergunta})


def classificar_documento(paginas_texto):
    conteudo = "\n\n".join(f"Página {n}:\n{t}" for n, t in paginas_texto)

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

    print("🧠 Criando embeddings e FAISS index...")
    criar_vector_store(paginas)

    print("🔖 Classificando páginas por tipo:")
    classificacao = classificar_documento(paginas)
    print(json.dumps(classificacao, indent=2))

    print("🤖 Fazendo consulta RAG:")
    query = (
        "Você está analisando um documento PDF dividido por páginas. "
        "Cada página começa com 'Página X:'. "
        "Em qual(is) página(s) aparece uma nota fiscal? "
        "Responda como: nota_fiscal: [X-Y]"
    )
    resultado = consultar_vector_store(query)

    print("\n🔎 Resposta RAG:")
    print(resultado["result"])
    print("\n📑 Fontes:")
    for doc in resultado["source_documents"]:
        print(doc.page_content[:200], "...\n")
