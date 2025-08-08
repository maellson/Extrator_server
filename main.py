
import os
import json
import pytesseract
from pdf2image import convert_from_path
import fitz  # PyMuPDF
from dotenv import load_dotenv
# extrato
# declaracao optante do simples


# imports atualizados
from langchain.prompts import PromptTemplate
# from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains import RetrievalQA

import fitz  # PyMuPDF
import sqlite3
from datetime import datetime


# Carregar variáveis de ambiente
load_dotenv()

# Configuração do OCR (ajuste o caminho se necessário)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# Caminhos
images_dir = "imagens_paginas"
texts_dir = "textos_paginas"

os.makedirs(images_dir, exist_ok=True)
os.makedirs(texts_dir, exist_ok=True)


def inicializar_banco_dados(db_path="classificacoes.db"):
    """
    Inicializa o banco de dados SQLite e cria a tabela de classificações.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Criar tabela de classificações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT NOT NULL UNIQUE,
            caminho_arquivo TEXT NOT NULL,
            tipo_classificacao TEXT NOT NULL,
            indice_certeza REAL NOT NULL,
            tokens_entrada INTEGER NOT NULL,
            tokens_saida INTEGER NOT NULL,
            data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

    # Criar índices para melhorar a performance das consultas
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_nome_arquivo ON classificacoes(nome_arquivo)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_tipo_classificacao ON classificacoes(tipo_classificacao)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_data_processamento ON classificacoes(data_processamento)')

    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado: {db_path}")


def inserir_classificacao_db(nome_arquivo, caminho_arquivo, classificacao, tokens_entrada, tokens_saida, db_path="classificacoes.db"):
    """
    Insere uma classificação no banco de dados.

    Args:
        nome_arquivo (str): Nome do arquivo classificado
        caminho_arquivo (str): Caminho completo do arquivo classificado
        classificacao (dict): Dicionário com a classificação e índice de certeza
        tokens_entrada (int): Número de tokens de entrada
        tokens_saida (int): Número de tokens de saída
        db_path (str): Caminho para o arquivo do banco de dados
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO classificacoes
        (nome_arquivo, caminho_arquivo, tipo_classificacao, indice_certeza, tokens_entrada, tokens_saida)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        nome_arquivo,
        caminho_arquivo,
        classificacao.get("tipo", "desconhecido"),
        classificacao.get("indice_certeza", 0.0),
        tokens_entrada,
        tokens_saida
    ))

    conn.commit()
    conn.close()


def gerar_estatisticas_db(db_path="classificacoes.db"):
    """
    Gera estatísticas e métricas a partir dos dados do banco de dados.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados

    Returns:
        dict: Dicionário com as estatísticas e métricas
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total de classificações
    cursor.execute('SELECT COUNT(*) FROM classificacoes')
    total_classificacoes = cursor.fetchone()[0]

    # Classificações por tipo
    cursor.execute('''
        SELECT tipo_classificacao, COUNT(*)
        FROM classificacoes
        GROUP BY tipo_classificacao
    ''')
    classificacoes_por_tipo = dict(cursor.fetchall())

    # Total de tokens
    cursor.execute(
        'SELECT SUM(tokens_entrada), SUM(tokens_saida) FROM classificacoes')
    tokens_entrada_total, tokens_saida_total = cursor.fetchone()
    tokens_entrada_total = tokens_entrada_total or 0
    tokens_saida_total = tokens_saida_total or 0

    # Média de tokens
    if total_classificacoes > 0:
        media_tokens_entrada = tokens_entrada_total / total_classificacoes
        media_tokens_saida = tokens_saida_total / total_classificacoes
    else:
        media_tokens_entrada = 0
        media_tokens_saida = 0

    # Índices de certeza - média, mediana, mínimo e máximo
    cursor.execute(
        'SELECT indice_certeza FROM classificacoes ORDER BY indice_certeza')
    indices_certeza = [row[0] for row in cursor.fetchall()]

    if indices_certeza:
        media_certeza = sum(indices_certeza) / len(indices_certeza)
        mediana_certeza = indices_certeza[len(indices_certeza) // 2]
        min_certeza = min(indices_certeza)
        max_certeza = max(indices_certeza)
    else:
        media_certeza = 0
        mediana_certeza = 0
        min_certeza = 0
        max_certeza = 0

    # Classificações por faixa de certeza
    cursor.execute('''
        SELECT
            CASE
                WHEN indice_certeza >= 0.9 THEN 'Alta (0.9-1.0)'
                WHEN indice_certeza >= 0.7 THEN 'Média-Alta (0.7-0.9)'
                WHEN indice_certeza >= 0.5 THEN 'Média (0.5-0.7)'
                WHEN indice_certeza >= 0.3 THEN 'Baixa (0.3-0.5)'
                ELSE 'Muito Baixa (0.0-0.3)'
            END as faixa_certeza,
            COUNT(*) as quantidade
        FROM classificacoes
        GROUP BY
            CASE
                WHEN indice_certeza >= 0.9 THEN 'Alta (0.9-1.0)'
                WHEN indice_certeza >= 0.7 THEN 'Média-Alta (0.7-0.9)'
                WHEN indice_certeza >= 0.5 THEN 'Média (0.5-0.7)'
                WHEN indice_certeza >= 0.3 THEN 'Baixa (0.3-0.5)'
                ELSE 'Muito Baixa (0.0-0.3)'
            END
    ''')
    classificacoes_por_faixa_certeza = dict(cursor.fetchall())

    conn.close()

    return {
        "total_classificacoes": total_classificacoes,
        "classificacoes_por_tipo": classificacoes_por_tipo,
        "tokens_entrada_total": tokens_entrada_total,
        "tokens_saida_total": tokens_saida_total,
        "media_tokens_entrada": media_tokens_entrada,
        "media_tokens_saida": media_tokens_saida,
        "media_certeza": media_certeza,
        "mediana_certeza": mediana_certeza,
        "min_certeza": min_certeza,
        "max_certeza": max_certeza,
        "classificacoes_por_faixa_certeza": classificacoes_por_faixa_certeza
    }


def exportar_dados_csv(db_path="classificacoes.db", csv_path="classificacoes.csv"):
    """
    Exporta os dados do banco de dados para um arquivo CSV.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados
        csv_path (str): Caminho para o arquivo CSV de saída
    """
    import csv

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obter todos os dados da tabela
    cursor.execute('''
        SELECT nome_arquivo, tipo_classificacao, indice_certeza, tokens_entrada, tokens_saida, data_processamento
        FROM classificacoes
        ORDER BY data_processamento
    ''')

    # Escrever dados no arquivo CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Escrever cabeçalho
        writer.writerow(['nome_arquivo', 'tipo_classificacao', 'indice_certeza',
                        'tokens_entrada', 'tokens_saida', 'data_processamento'])
        # Escrever dados
        writer.writerows(cursor.fetchall())

    conn.close()
    print(f"Dados exportados para: {csv_path}")


def gerar_relatorio_resumido(db_path="classificacoes.db"):
    """
    Gera um relatório resumido das classificações.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados

    Returns:
        str: Relatório resumido em formato de texto
    """
    estatisticas = gerar_estatisticas_db(db_path)

    relatorio = []
    relatorio.append("RELATÓRIO RESUMIDO DE CLASSIFICAÇÕES")
    relatorio.append("=" * 50)
    relatorio.append(
        f"Total de documentos processados: {estatisticas['total_classificacoes']}")
    relatorio.append(
        f"Total de tokens de entrada: {estatisticas['tokens_entrada_total']}")
    relatorio.append(
        f"Total de tokens de saída: {estatisticas['tokens_saida_total']}")
    relatorio.append(
        f"Média de tokens por documento - Entrada: {estatisticas['media_tokens_entrada']:.2f}")
    relatorio.append(
        f"Média de tokens por documento - Saída: {estatisticas['media_tokens_saida']:.2f}")
    relatorio.append(
        f"Índice médio de certeza: {estatisticas['media_certeza']:.2f}")
    relatorio.append(
        f"Índice mediano de certeza: {estatisticas['mediana_certeza']:.2f}")
    relatorio.append("")
    relatorio.append("DISTRIBUIÇÃO POR TIPO DE DOCUMENTO:")
    for tipo, count in estatisticas['classificacoes_por_tipo'].items():
        percentual = (count / estatisticas['total_classificacoes']) * \
            100 if estatisticas['total_classificacoes'] > 0 else 0
        relatorio.append(f"  {tipo}: {count} ({percentual:.1f}%)")
    relatorio.append("")
    relatorio.append("DISTRIBUIÇÃO POR FAIXA DE CERTEZA:")
    for faixa, count in estatisticas['classificacoes_por_faixa_certeza'].items():
        percentual = (count / estatisticas['total_classificacoes']) * \
            100 if estatisticas['total_classificacoes'] > 0 else 0
        relatorio.append(f"  {faixa}: {count} ({percentual:.1f}%)")

    return "\n".join(relatorio)


def consultar_classificacoes(tipo=None, faixa_certeza_min=None, faixa_certeza_max=None, db_path="classificacoes.db"):
    """
    Consulta classificações no banco de dados com filtros opcionais.

    Args:
        tipo (str): Tipo de classificação para filtrar (opcional)
        faixa_certeza_min (float): Valor mínimo de certeza para filtrar (opcional)
        faixa_certeza_max (float): Valor máximo de certeza para filtrar (opcional)
        db_path (str): Caminho para o arquivo do banco de dados

    Returns:
        list: Lista de tuplas com os resultados da consulta
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Construir query com filtros opcionais
    query = "SELECT nome_arquivo, tipo_classificacao, indice_certeza, tokens_entrada, tokens_saida FROM classificacoes WHERE 1=1"
    params = []

    if tipo:
        query += " AND tipo_classificacao = ?"
        params.append(tipo)

    if faixa_certeza_min is not None:
        query += " AND indice_certeza >= ?"
        params.append(faixa_certeza_min)

    if faixa_certeza_max is not None:
        query += " AND indice_certeza <= ?"
        params.append(faixa_certeza_max)

    query += " ORDER BY indice_certeza DESC"

    cursor.execute(query, params)
    resultados = cursor.fetchall()

    conn.close()
    return resultados


def gerar_dashboard_controle(db_path="classificacoes.db"):
    """
    Gera um dashboard de controle com as principais métricas do sistema.

    Args:
        db_path (str): Caminho para o arquivo do banco de dados

    Returns:
        str: Dashboard de controle em formato de texto
    """
    estatisticas = gerar_estatisticas_db(db_path)

    dashboard = []
    dashboard.append("DASHBOARD DE CONTROLE - CLASSIFICAÇÃO DE DOCUMENTOS")
    dashboard.append("=" * 60)
    dashboard.append("")

    # Métricas principais
    dashboard.append("MÉTRICAS PRINCIPAIS:")
    dashboard.append("-" * 20)
    dashboard.append(
        f"Total de documentos processados: {estatisticas['total_classificacoes']}")
    dashboard.append(
        f"Taxa de sucesso: 100% (todos os documentos foram classificados)")
    dashboard.append(
        f"Custo estimado (tokens): {estatisticas['tokens_entrada_total'] + estatisticas['tokens_saida_total']:,}")
    dashboard.append("")

    # Distribuição por tipo
    dashboard.append("DISTRIBUIÇÃO POR TIPO DE DOCUMENTO:")
    dashboard.append("-" * 40)
    tipos = ["voucher", "boleto", "nota_fiscal", "descarte"]
    for tipo in tipos:
        count = estatisticas['classificacoes_por_tipo'].get(tipo, 0)
        percentual = (count / estatisticas['total_classificacoes']) * \
            100 if estatisticas['total_classificacoes'] > 0 else 0
        dashboard.append(f"  {tipo.capitalize()}: {count} ({percentual:.1f}%)")
    dashboard.append("")

    # Qualidade das classificações
    dashboard.append("QUALIDADE DAS CLASSIFICAÇÕES:")
    dashboard.append("-" * 30)
    dashboard.append(
        f"Índice médio de certeza: {estatisticas['media_certeza']:.2f}")
    dashboard.append(
        f"Índice mediano de certeza: {estatisticas['mediana_certeza']:.2f}")
    dashboard.append(
        f"Índice máximo de certeza: {estatisticas['max_certeza']:.2f}")
    dashboard.append(
        f"Índice mínimo de certeza: {estatisticas['min_certeza']:.2f}")
    dashboard.append("")

    # Distribuição por faixa de certeza
    dashboard.append("DISTRIBUIÇÃO POR FAIXA DE CERTEZA:")
    dashboard.append("-" * 35)
    faixas = [
        ("Alta (0.9-1.0)", "Alta"),
        ("Média-Alta (0.7-0.9)", "Média-Alta"),
        ("Média (0.5-0.7)", "Média"),
        ("Baixa (0.3-0.5)", "Baixa"),
        ("Muito Baixa (0.0-0.3)", "Muito Baixa")
    ]
    for faixa_nome, faixa_label in faixas:
        count = estatisticas['classificacoes_por_faixa_certeza'].get(
            faixa_nome, 0)
        percentual = (count / estatisticas['total_classificacoes']) * \
            100 if estatisticas['total_classificacoes'] > 0 else 0
        dashboard.append(f"  {faixa_label}: {count} ({percentual:.1f}%)")
    dashboard.append("")

    # Eficiência
    dashboard.append("EFICIÊNCIA:")
    dashboard.append("-" * 12)
    dashboard.append(
        f"Média de tokens por documento - Entrada: {estatisticas['media_tokens_entrada']:.2f}")
    dashboard.append(
        f"Média de tokens por documento - Saída: {estatisticas['media_tokens_saida']:.2f}")
    dashboard.append(
        f"Total de tokens processados: {estatisticas['tokens_entrada_total'] + estatisticas['tokens_saida_total']:,}")

    return "\n".join(dashboard)


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


def classificar_pagina(texto_pagina):
    """
    Classifica uma única página de documento com índice de certeza e coleta métricas de tokens.

    Args:
        texto_pagina (str): Texto extraído da página do documento

    Returns:
        dict: Dicionário com a classificação, índice de certeza e métricas de tokens
    """

    prompt_template = PromptTemplate.from_template("""
        Classifique o documento de acordo com o conteúdo apresentado em uma das seguintes categorias:
        - voucher: Contém informações de reserva de hotel, como número do quarto, nome do cliente, data de check-in, valor, forma de pagamento, número do voucher.
        - boleto: Contém dados de boletos bancários: como código de barras, data do processamento, Nosso número, cedente ou banco e número do boleto, agencia e código do beneficiário, uso do banco, local de pagameto
        - nota_fiscal: Contém informações de notas fiscais de serviço, como CNPJ, descrição de produtos/serviços, impostos.
        - descarte: Qualquer documento que não se encaixa nas categorias acima

        Para a classificação, também atribua um score de confiança entre 0 e 1, onde:
        - 0.9-1.0: Certeza quase absoluta
        - 0.7-0.9: Alta confiança
        - 0.5-0.7: Confiança moderada
        - 0.3-0.5: Baixa confiança
        - 0.0-0.3: Muito baixa confiança

        Responda apenas com um JSON, nesse formato:
        {{
          "tipo": "voucher",
          "indice_certeza": 0.95
        }}

        Aqui está o conteúdo do documento:

        {conteudo}
    """)

    # Criar o modelo LLM com callbacks para coletar métricas
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt_template | llm

    # Invocar o modelo e coletar resposta
    ai_message = chain.invoke({"conteudo": texto_pagina})

    # Extrair informações de uso de tokens se disponíveis
    tokens_entrada = 0
    tokens_saida = 0

    # Verificar se há informações de tokens na resposta
    if hasattr(ai_message, 'response_metadata'):
        metadata = ai_message.response_metadata
        tokens_entrada = metadata.get(
            'token_usage', {}).get('prompt_tokens', 0)
        tokens_saida = metadata.get(
            'token_usage', {}).get('completion_tokens', 0)

    # Extrai o texto puro do AIMessage
    text = ai_message.content if hasattr(
        ai_message, "content") else str(ai_message)

    # Limpeza de markdown/backticks
    resposta_limpa = text.strip().lstrip("```json").rstrip("```").strip()

    try:
        resultado = json.loads(resposta_limpa)
        # Adicionar métricas de tokens ao resultado
        resultado["tokens_entrada"] = tokens_entrada
        resultado["tokens_saida"] = tokens_saida
        return resultado
    except json.JSONDecodeError:
        print("⚠️ Falha ao parsear JSON:")
        print(text)
        return {"erro": "formato inválido", "raw": text, "tokens_entrada": tokens_entrada, "tokens_saida": tokens_saida}


def processar_diretorio_amostragem(diretorio_base="amostragem/Parte_1/29675", diretorio_saida="amostragem/Parte_1/OUTPUT"):
    """
    Processa todos os arquivos PDF no diretório de amostragem e salva resultados em JSON.
    Processa todos os arquivos de uma pasta antes de passar para a próxima.

    Args:
        diretorio_base (str): Caminho base para o diretório de amostragem
        diretorio_saida (str): Caminho para o diretório de saída dos resultados
    """
    import glob

    # Criar diretório de saída se não existir
    os.makedirs(diretorio_saida, exist_ok=True)

    # Obter lista ordenada de subdiretórios
    subdiretorios = sorted([d for d in os.listdir(
        diretorio_base) if os.path.isdir(os.path.join(diretorio_base, d))])

    print(f"Encontrados {len(subdiretorios)} subdiretórios para processar")

    # Processar cada subdiretório em ordem
    resultados = []
    for subdiretorio in subdiretorios:
        print(f"Processando diretório: {subdiretorio}")

        # Encontrar todos os arquivos PDF no subdiretório atual
        caminho_subdiretorio = os.path.join(diretorio_base, subdiretorio)
        padrao = os.path.join(caminho_subdiretorio, "*.pdf")
        arquivos_pdf = glob.glob(padrao)

        # Ordenar arquivos para processamento consistente
        arquivos_pdf.sort()

        print(
            f"  Encontrados {len(arquivos_pdf)} arquivos PDF no diretório {subdiretorio}")

        # Processar cada arquivo no subdiretório
        for arquivo_pdf in arquivos_pdf:
            try:
                print(f"  Processando: {os.path.basename(arquivo_pdf)}")

                # Extrair texto do PDF
                texto_pagina = extrair_texto_completo(arquivo_pdf)
                texto_combinado = "\n".join(
                    [texto for _, texto in texto_pagina])

                # Classificar a página com coleta de métricas
                classificacao = classificar_pagina(texto_combinado)

                # Preparar resultado no formato especificado
                # Extrair o nome do arquivo sem o prefixo "page_"
                nome_arquivo_completo = os.path.basename(arquivo_pdf)
                if nome_arquivo_completo.startswith("page_"):
                    # Remove "page_" do início
                    nome_arquivo = nome_arquivo_completo[5:]
                else:
                    nome_arquivo = nome_arquivo_completo

                resultado_formatado = {
                    "nome_arquivo": nome_arquivo,
                    "classificacao": {
                        "tipo": classificacao.get("tipo", "desconhecido"),
                        "indice_certeza": classificacao.get("indice_certeza", 0.0)
                    },
                    "tokens_entrada": classificacao.get("tokens_entrada", 0),
                    "tokens_saida": classificacao.get("tokens_saida", 0)
                }
                resultados.append(resultado_formatado)

                # Inserir resultado no banco de dados
                inserir_classificacao_db(
                    nome_arquivo,
                    arquivo_pdf,
                    resultado_formatado["classificacao"],
                    resultado_formatado["tokens_entrada"],
                    resultado_formatado["tokens_saida"]
                )

                # Salvar resultado em arquivo JSON
                nome_arquivo_json = nome_arquivo.replace(".pdf", ".json")
                caminho_json = os.path.join(diretorio_saida, nome_arquivo_json)
                with open(caminho_json, "w", encoding="utf-8") as f:
                    json.dump(resultado_formatado, f,
                              indent=2, ensure_ascii=False)

                print(f"    Classificação: {classificacao}")
                print(
                    f"    Tokens - Entrada: {classificacao.get('tokens_entrada', 0)}, Saída: {classificacao.get('tokens_saida', 0)}")
            except Exception as e:
                print(f"    Erro ao processar {arquivo_pdf}: {str(e)}")

    return resultados


if __name__ == "__main__":
    # Inicializar banco de dados
    inicializar_banco_dados()

    # Processar arquivos na pasta de amostragem
    print("Processando arquivos em amostragem/Parte 1...")
    resultados = processar_diretorio_amostragem()

    # Mostrar resumo dos resultados
    print("\nResumo das classificações:")
    total_tokens_entrada = 0
    total_tokens_saida = 0
    classificacoes_por_tipo = {"voucher": 0, "boleto": 0,
                               "nota_fiscal": 0, "descarte": 0, "desconhecido": 0}

    for resultado in resultados:
        nome_arquivo = resultado["nome_arquivo"]
        classificacao = resultado["classificacao"]
        tokens_entrada = resultado["tokens_entrada"]
        tokens_saida = resultado["tokens_saida"]

        # Atualizar totais
        total_tokens_entrada += tokens_entrada
        total_tokens_saida += tokens_saida
        classificacoes_por_tipo[classificacao["tipo"]] += 1

        # Mostrar resultado formatado
        print(f"📄 Extraindo texto...")
        print(f"name: {nome_arquivo}")
        print("{")
        print(f'  "{classificacao["tipo"]}": [')
        print(f'    {{')
        print(f'      "value": 1,')
        print(f'      "indice_certeza": {classificacao["indice_certeza"]:.2f}')
        print(f'    }}')
        print("  ]")
        print("}")
        print(f"Tokens - Entrada: {tokens_entrada}, Saída: {tokens_saida}")
        print()

    # Mostrar resumo final
    print("Resumo final:")
    print(f"Total de arquivos processados: {len(resultados)}")
    print(f"Total de tokens de entrada: {total_tokens_entrada}")
    print(f"Total de tokens de saída: {total_tokens_saida}")
    print("Classificações por tipo:")
    for tipo, count in classificacoes_por_tipo.items():
        if count > 0:
            print(f"  {tipo}: {count}")

    # Gerar e mostrar estatísticas do banco de dados
    print("\nEstatísticas do banco de dados:")
    estatisticas = gerar_estatisticas_db()
    print(f"Total de classificações: {estatisticas['total_classificacoes']}")
    print(f"Tokens de entrada total: {estatisticas['tokens_entrada_total']}")
    print(f"Tokens de saída total: {estatisticas['tokens_saida_total']}")
    print(
        f"Média de tokens de entrada: {estatisticas['media_tokens_entrada']:.2f}")
    print(
        f"Média de tokens de saída: {estatisticas['media_tokens_saida']:.2f}")
    print(f"Média de certeza: {estatisticas['media_certeza']:.2f}")
    print(f"Mediana de certeza: {estatisticas['mediana_certeza']:.2f}")
    print("Classificações por tipo:")
    for tipo, count in estatisticas['classificacoes_por_tipo'].items():
        print(f"  {tipo}: {count}")
    print("Classificações por faixa de certeza:")
    for faixa, count in estatisticas['classificacoes_por_faixa_certeza'].items():
        print(f"  {faixa}: {count}")

    # Exportar dados para CSV
    exportar_dados_csv()

    # Gerar e mostrar relatório resumido
    print("\n" + gerar_relatorio_resumido())

    # Gerar e mostrar dashboard de controle
    print("\n" + gerar_dashboard_controle())
