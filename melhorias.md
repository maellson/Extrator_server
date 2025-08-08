# Melhorias para o Sistema de Classificação de Documentos VoeTur

Vou detalhar as melhorias para seu sistema, focando nas opções internas sem necessidade de serviços de nuvem pagos adicionais.

## Benefícios do Tesseract 5.0+

O Tesseract 5.0+ traz melhorias significativas em relação à versão que você está usando:

- **Motor LSTM**: Usa redes neurais profundas para reconhecimento de texto, melhorando drasticamente a precisão
- **Melhor reconhecimento de layout**: Mais eficaz em documentos com formatação complexa como boletos e notas fiscais
- **Suporte avançado a múltiplos idiomas**: Importante para documentos que podem conter termos em português e inglês (comum em vouchers)
- **Melhor detecção de texto em imagens de baixa qualidade**: Crucial para documentos digitalizados

## 1. Melhorias no Pipeline de Extração de Texto (main3.py)

```python
# Adições ao seu código existente

# 1. Pré-processamento de imagens para melhorar OCR
def pre_processar_imagem(imagem_path):
    import cv2
    import numpy as np
    
    # Carrega a imagem
    img = cv2.imread(imagem_path)
    
    # Converte para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Binarização adaptativa
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Correção de inclinação (deskew)
    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    # Aumento de contraste
    processed = cv2.GaussianBlur(rotated, (3, 3), 0)
    
    # Salva a imagem processada
    processed_path = imagem_path.replace('.png', '_processed.png')
    cv2.imwrite(processed_path, processed)
    
    return processed_path

# 2. Extração de características específicas por tipo de documento
def extrair_caracteristicas_documento(texto, num_pagina):
    caracteristicas = {
        'num_pagina': num_pagina,
        'comprimento_texto': len(texto),
        'tem_cnpj': bool(re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)),
        'tem_cpf': bool(re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto)),
        'tem_codigo_barras': bool(re.search(r'[0-9]{44,48}', texto)),
        'tem_valor_rs': bool(re.search(r'R\$ [0-9]+,[0-9]{2}', texto)),
        'palavras_chave': {}
    }
    
    # Contagem de palavras-chave por tipo de documento
    palavras_chave = {
        'voucher': ['reserva', 'hóspede', 'quarto', 'check', 'arrival', 'chegada'],
        'boleto': ['valor', 'documento', 'juros', 'multa', 'boleto', 'pagador', 'cedente'],
        'nota_fiscal': ['nota fiscal', 'nfe', 'cnpj', 'tomador', 'prestador', 'serviço']
    }
    
    for tipo, palavras in palavras_chave.items():
        contagem = 0
        for palavra in palavras:
            contagem += len(re.findall(r'\b' + palavra + r'\b', texto.lower()))
        caracteristicas['palavras_chave'][tipo] = contagem
    
    return caracteristicas
```

## 2. Implementação de Classificadores Mais Simples

```python
# Implementação de classificadores básicos

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def treinar_classificadores(textos_paginas, labels_conhecidos):
    """
    Treina classificadores simples com os textos e labels disponíveis
    
    :param textos_paginas: Lista de tuples (num_pagina, texto)
    :param labels_conhecidos: Dicionário de {num_pagina: tipo_documento}
    :return: Dicionário com modelos treinados
    """
    # Preparar dados
    X = [texto for _, texto in textos_paginas if _ in labels_conhecidos]
    y = [labels_conhecidos[num] for num, _ in textos_paginas if num in labels_conhecidos]
    
    if len(X) < 10:  # Verificar se há dados suficientes
        print("Poucos dados para treinamento. Acumule mais exemplos rotulados.")
        return None
    
    # Divisão train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Extração de características TF-IDF
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    # Treinar Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train_tfidf, y_train)
    rf_score = rf.score(X_test_tfidf, y_test)
    
    # Treinar SVM
    svm = SVC(probability=True, kernel='linear')
    svm.fit(X_train_tfidf, y_train)
    svm_score = svm.score(X_test_tfidf, y_test)
    
    print(f"Random Forest score: {rf_score:.4f}")
    print(f"SVM score: {svm_score:.4f}")
    
    # Retornar modelos e vectorizer para uso posterior
    return {
        'vectorizer': vectorizer,
        'random_forest': rf,
        'svm': svm
    }

def classificar_com_ml(texto, modelos):
    """
    Classifica um texto usando os modelos ML treinados
    """
    if not modelos:
        return None, 0
        
    X = modelos['vectorizer'].transform([texto])
    
    # Predict com RF
    rf_probs = modelos['random_forest'].predict_proba(X)[0]
    rf_class = modelos['random_forest'].classes_[rf_probs.argmax()]
    rf_conf = rf_probs.max()
    
    # Predict com SVM
    svm_probs = modelos['svm'].predict_proba(X)[0]
    svm_class = modelos['svm'].classes_[svm_probs.argmax()]
    svm_conf = svm_probs.max()
    
    # Escolher o modelo com maior confiança
    if rf_conf > svm_conf:
        return rf_class, rf_conf
    else:
        return svm_class, svm_conf
```

## 3. Implementação de Métricas de Confiança

```python
def classificar_com_confianca(paginas_texto, modelos_ml=None):
    """
    Combina classificação por LLM e ML com métricas de confiança
    """
    conteudo = "\n\n".join(f"Página {n}:\n{t}" for n, t in paginas_texto)
    
    # Classificação por LLM (seu código existente melhorado)
    prompt_template = PromptTemplate.from_template("""
        Você está analisando um documento dividido por páginas, onde cada página começa com 'Página X:'.
        Classifique as páginas de acordo com o conteúdo apresentado. Os tipos de conteúdo que devem ser detectados são:
        - Voucher:"Número de reserva", "Hóspede", "Quarto:", "check in", "arrival", "chegada", "Quarto nº"
        - boleto: "Valor do Documento", "Juros/Multa", "Boleto", "Recibo do Pagador", "Local Pagamento", "Pagador"
        - nota_fiscal: "NOTA FISCAL DE SERVIÇO ELETRÔNICA", "NÚMERO DA NOTA", "TOMADOR DE SERVIÇOS", "PRESTADOR DE SERVIÇOS", "CNAE"
        - descarte: qualquer página que não se encaixa nas categorias acima

        Para cada página classificada, também atribua um score de confiança entre 0 e 1, onde:
        - 0.9-1.0: Certeza quase absoluta (contém múltiplos indicadores claros do tipo)
        - 0.7-0.9: Alta confiança (contém alguns indicadores claros)
        - 0.5-0.7: Confiança moderada (contém pelo menos um indicador)
        - 0.3-0.5: Baixa confiança (há indícios, mas não são conclusivos)
        - 0.0-0.3: Muito baixa confiança (quase sem indicadores)

        Responda apenas com um JSON, nesse formato:
        {{
        "classificacoes": [
            {{"pagina": 1, "tipo": "voucher", "confianca": 0.95}},
            {{"pagina": 2, "tipo": "boleto", "confianca": 0.85}},
            {{"pagina": 3, "tipo": "nota_fiscal", "confianca": 0.65}},
            {{"pagina": 4, "tipo": "descarte", "confianca": 0.40}}
          ]
        }}

        Aqui está o conteúdo do documento:

        {conteudo}
    """)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt_template | llm
    ai_message = chain.invoke({"conteudo": conteudo})
    
    # Extrai o texto e processa o JSON
    text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
    resposta_limpa = text.strip().lstrip("```json").rstrip("```").strip()
    
    try:
        resultados_llm = json.loads(resposta_limpa)
    except json.JSONDecodeError:
        print("⚠️ Falha ao parsear JSON:")
        print(text)
        return {"erro": "formato inválido", "raw": text}
    
    # Se tivermos modelos ML treinados, vamos combinar as classificações
    if modelos_ml:
        resultados_combinados = []
        for classificacao in resultados_llm.get("classificacoes", []):
            pagina = classificacao["pagina"]
            texto_pagina = next((t for n, t in paginas_texto if n == pagina), "")
            
            # Obter classificação e confiança do ML
            ml_tipo, ml_conf = classificar_com_ml(texto_pagina, modelos_ml)
            
            # Se LLM e ML concordam, aumentar a confiança
            if ml_tipo == classificacao["tipo"]:
                confianca_final = min(1.0, classificacao["confianca"] + 0.1)
                fonte = "llm+ml_concordam"
            # Se discordam, usar a classificação de maior confiança
            elif ml_conf > classificacao["confianca"]:
                tipo_final = ml_tipo
                confianca_final = ml_conf
                fonte = "ml_maior_confianca"
            else:
                tipo_final = classificacao["tipo"]
                confianca_final = classificacao["confianca"]
                fonte = "llm_maior_confianca"
                
            resultados_combinados.append({
                "pagina": pagina,
                "tipo": tipo_final,
                "confianca": confianca_final,
                "fonte": fonte,
                "llm_tipo": classificacao["tipo"],
                "llm_confianca": classificacao["confianca"],
                "ml_tipo": ml_tipo,
                "ml_confianca": ml_conf
            })
            
        # Convertemos para o formato anterior para compatibilidade
        classificacao_final = {}
        for res in resultados_combinados:
            tipo = res["tipo"]
            pagina = res["pagina"]
            if tipo not in classificacao_final:
                classificacao_final[tipo] = []
            classificacao_final[tipo].append(pagina)
            
        # Também retornamos os detalhes de confiança para análise
        return {
            "classificacao": classificacao_final,
            "detalhes": resultados_combinados
        }
    
    # Se não temos modelos ML, apenas reorganizar o resultado do LLM
    else:
        classificacao_final = {}
        for classificacao in resultados_llm.get("classificacoes", []):
            tipo = classificacao["tipo"]
            pagina = classificacao["pagina"]
            if tipo not in classificacao_final:
                classificacao_final[tipo] = []
            classificacao_final[tipo].append(pagina)
            
        return {
            "classificacao": classificacao_final,
            "detalhes": resultados_llm.get("classificacoes", [])
        }
```

## 4. Implementação da Abordagem Iterativa

Aqui está um fluxo completo para a abordagem iterativa:

```python
def processo_iterativo_classificacao(diretorio_pdfs):
    """
    Implementa o processo iterativo de classificação, validação e melhoria
    """
    # Estrutura para armazenar labels validados
    labels_validados = {}  # {arquivo_pdf: {pagina: tipo}}
    
    # Ciclo iterativo de melhoria
    modelos_ml = None
    paginas_para_validar = []
    
    # Loop por cada arquivo PDF no diretório
    for arquivo_pdf in os.listdir(diretorio_pdfs):
        if not arquivo_pdf.endswith('.pdf'):
            continue
            
        caminho_pdf = os.path.join(diretorio_pdfs, arquivo_pdf)
        print(f"Processando: {arquivo_pdf}")
        
        # Extração de texto
        paginas_texto = extrair_texto_completo(caminho_pdf)
        
        # Classificação com confiança
        resultados = classificar_com_confianca(paginas_texto, modelos_ml)
        
        # Identificar páginas com baixa confiança para validação manual
        for detalhe in resultados["detalhes"]:
            if detalhe["confianca"] < 0.7:  # Limiar de confiança para revisão
                paginas_para_validar.append({
                    "arquivo": arquivo_pdf,
                    "pagina": detalhe["pagina"],
                    "tipo_sugerido": detalhe["tipo"],
                    "confianca": detalhe["confianca"]
                })
        
        # A cada 5 PDFs processados ou quando atingir 20 páginas para validação:
        # 1. Realizar validação manual (implementar interface simples ou CSV)
        # 2. Atualizar labels_validados com as correções
        # 3. Treinar modelos ML com dados validados
        if len(paginas_para_validar) >= 20:
            # Aqui você implementaria a interface de validação
            # Por simplicidade, vamos simular com um prompt:
            print(f"⚠️ {len(paginas_para_validar)} páginas precisam de validação manual")
            
            # Gerar CSV para validação
            with open('validacao_manual.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['arquivo', 'pagina', 'tipo_sugerido', 'confianca', 'tipo_correto'])
                for item in paginas_para_validar:
                    writer.writerow([
                        item['arquivo'], 
                        item['pagina'], 
                        item['tipo_sugerido'],
                        item['confianca'],
                        ''  # Coluna a ser preenchida manualmente
                    ])
            
            print("Arquivo 'validacao_manual.csv' gerado. Preencha a coluna 'tipo_correto' e reinicie o processo.")
            
            # Após validação manual, simularíamos a leitura do CSV preenchido
            # E atualizaríamos labels_validados
            
            # Agora podemos treinar os modelos ML com dados validados
            modelos_ml = treinar_classificadores(todas_paginas_texto, todas_labels_validados)
            
            # Reiniciar a lista de páginas para validar
            paginas_para_validar = []
    
    return {
        "labels_validados": labels_validados,
        "modelos_ml": modelos_ml
    }
```

## 5. Script de Interface Simples para Validação Manual

Para facilitar a validação manual, você pode implementar uma interface simples baseada em console ou uma interface web básica usando Flask:

```python
def interface_validacao_console(paginas_para_validar, diretorio_imagens):
    """
    Interface simples de console para validação manual
    """
    resultados_validacao = []
    
    print("=== INTERFACE DE VALIDAÇÃO MANUAL ===")
    print(f"Total de {len(paginas_para_validar)} páginas para validar\n")
    
    for idx, item in enumerate(paginas_para_validar):
        arquivo = item['arquivo']
        pagina = item['pagina']
        tipo_sugerido = item['tipo_sugerido']
        confianca = item['confianca']
        
        # Mostrar informações da página
        print(f"\n[{idx+1}/{len(paginas_para_validar)}] Arquivo: {arquivo}, Página: {pagina}")
        print(f"Tipo sugerido: {tipo_sugerido} (confiança: {confianca:.2f})")
        
        # Mostrar opções
        print("\nOpções de tipo:")
        print("1. voucher")
        print("2. boleto")
        print("3. nota_fiscal")
        print("4. descarte")
        print("5. Outro (especificar)")
        print("x. Pular esta página")
        
        # Obter input do usuário
        escolha = input("\nEscolha o tipo correto (enter para aceitar sugestão): ").strip()
        
        if escolha == "":
            tipo_correto = tipo_sugerido
        elif escolha == "x":
            continue
        elif escolha == "1":
            tipo_correto = "voucher"
        elif escolha == "2":
            tipo_correto = "boleto"
        elif escolha == "3":
            tipo_correto = "nota_fiscal"
        elif escolha == "4":
            tipo_correto = "descarte"
        elif escolha == "5":
            tipo_correto = input("Especifique o tipo: ").strip()
        else:
            print("Opção inválida, mantendo sugestão.")
            tipo_correto = tipo_sugerido
        
        resultados_validacao.append({
            "arquivo": arquivo,
            "pagina": pagina,
            "tipo_original": tipo_sugerido,
            "tipo_correto": tipo_correto
        })
        
        print(f"✓ Página classificada como: {tipo_correto}")
    
    return resultados_validacao
```

## Implementação do Processo Completo

Finalmente, aqui está o fluxo completo do processo recomendado:

```python
def pipeline_completo(diretorio_pdfs, salvar_modelo=True, carregar_modelo=None):
    """
    Pipeline completo de classificação de documentos
    """
    # 1. Inicializar estruturas de dados
    labels_validados = {}
    todas_paginas_texto = []
    
    # Carregar modelo existente se disponível
    modelos_ml = None
    if carregar_modelo and os.path.exists(carregar_modelo):
        import pickle
        with open(carregar_modelo, 'rb') as f:
            modelos_ml = pickle.load(f)
        print(f"Modelo carregado de: {carregar_modelo}")
    
    # 2. Loop principal
    for batch_idx, batch_pdfs in enumerate(chunks(os.listdir(diretorio_pdfs), 5)):
        print(f"\n=== Processando batch {batch_idx+1} ===")
        
        paginas_para_validar = []
        
        for arquivo_pdf in batch_pdfs:
            if not arquivo_pdf.endswith('.pdf'):
                continue
                
            caminho_pdf = os.path.join(diretorio_pdfs, arquivo_pdf)
            print(f"Processando: {arquivo_pdf}")
            
            # Extração de texto com pré-processamento melhorado
            paginas_texto = extrair_texto_completo(caminho_pdf)
            todas_paginas_texto.extend([(f"{arquivo_pdf}_{num}", texto) for num, texto in paginas_texto])
            
            # Classificação com confiança
            resultados = classificar_com_confianca(paginas_texto, modelos_ml)
            
            # Salvar resultados
            with open(f"resultados_{arquivo_pdf}.json", 'w') as f:
                json.dump(resultados, f, indent=2)
            
            # Identificar páginas com baixa confiança para validação
            for detalhe in resultados["detalhes"]:
                if detalhe["confianca"] < 0.7:
                    paginas_para_validar.append({
                        "arquivo": arquivo_pdf,
                        "pagina": detalhe["pagina"],
                        "tipo_sugerido": detalhe["tipo"],
                        "confianca": detalhe["confianca"]
                    })
        
        # 3. Validação manual das páginas com baixa confiança
        if paginas_para_validar:
            resultados_validacao = interface_validacao_console(paginas_para_validar)
            
            # Atualizar labels validados
            for res in resultados_validacao:
                arquivo = res["arquivo"]
                pagina = res["pagina"]
                tipo = res["tipo_correto"]
                
                if arquivo not in labels_validados:
                    labels_validados[arquivo] = {}
                    
                labels_validados[arquivo][pagina] = tipo
                
            # 4. Treinar/atualizar modelos ML com dados validados
            todas_labels = {}
            for arquivo, paginas in labels_validados.items():
                for pagina, tipo in paginas.items():
                    id_pagina = f"{arquivo}_{pagina}"
                    todas_labels[id_pagina] = tipo
                    
            if len(todas_labels) >= 20:  # Só treinar se tivermos dados suficientes
                modelos_ml = treinar_classificadores(todas_paginas_texto, todas_labels)
                
                # Salvar modelo
                if salvar_modelo:
                    import pickle
                    with open('modelo_classificador.pkl', 'wb') as f:
                        pickle.dump(modelos_ml, f)
                    print("Modelo salvo como: modelo_classificador.pkl")
    
    # 5. Relatório final
    print("\n=== RELATÓRIO FINAL ===")
    print(f"Total de documentos processados: {len(os.listdir(diretorio_pdfs))}")
    print(f"Total de páginas com labels validados: {sum(len(p) for p in labels_validados.values())}")
    
    if modelos_ml:
        print("\nPerformance dos modelos ML:")
        # Aqui você poderia adicionar métricas de avaliação
    
    return {
        "labels_validados": labels_validados,
        "modelos_ml": modelos_ml
    }

# Função auxiliar para processar em batches
def chunks(lst, n):
    """Divide uma lista em chunks de tamanho n"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
```

## Resumo das Melhorias Implementadas

1. **Melhoria na extração de texto**:
   - Pré-processamento de imagens para melhorar o OCR
   - Detecção e correção de rotação de documentos
   - Extração estruturada de características específicas por tipo

2. **Classificadores ML simples**:
   - TF-IDF com Random Forest e SVM 
   - Fusão de classificadores LLM + ML para melhor performance

3. **Métricas de confiança**:
   - Scores de probabilidade para cada classificação
   - Detecção de páginas com classificação ambígua
   - Sistema de identificação de necessidade de validação manual

4. **Abordagem iterativa**:
   - Processo semi-automático com validação manual inteligente
   - Interface simples para revisão humana das classificações duvidosas
   - Pipeline escalável que melhora com o tempo

Com estas implementações, você poderá aumentar a assertividade significativamente além dos 70% atuais, possivelmente chegando a 85-90% após algumas iterações de melhoria.

Deseja que eu detalhe mais alguma parte específica ou forneça exemplos adicionais para algum desses componentes?