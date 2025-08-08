# Plano de Implementação - Sistema de Classificação de Documentos

## Visão Geral

Este documento descreve as etapas detalhadas para implementar melhorias no sistema de classificação de documentos, incluindo a adição de métricas de confiança, coleta de consumo de tokens, processamento em lote e otimização do sistema.

O sistema atual funciona lendo um arquivo com diversas páginas e classificando cada página individualmente. Agora, os arquivos já estão separados individualmente (cada arquivo PDF representa uma página única), então vamos processar cada arquivo individualmente e classificar seu conteúdo.

## Etapas de Implementação

### 1. Definir estrutura do arquivo de saída JSON

**Objetivo**: Criar uma estrutura padronizada para armazenar todas as métricas coletadas de cada documento processado.

**Detalhes**:
- Nome do arquivo: Identificador do documento PDF processado
- Classificação: 
  - tipo: Tipo de documento classificado (voucher, boleto, nota_fiscal, descarte)
  - indice_certeza: Índice de certeza da classificação (0-1)
- Tokens de entrada: Número total de tokens usados na entrada do modelo
- Tokens de saída: Número total de tokens gerados pelo modelo

**Formato JSON**:
```json
{
  "nome_arquivo": "page_0_17468174577783681508214.pdf",
  "classificacao": {
    "tipo": "voucher",
    "indice_certeza": 0.95
  },
  "tokens_entrada": 1250,
  "tokens_saida": 150
}
```

### 2. Implementar função para calcular e retornar o índice de certeza do modelo LLM

**Objetivo**: Modificar o prompt e a função de classificação para que o modelo retorne índices de certeza para cada classificação.

**Detalhes**:
- Atualizar o template do prompt para solicitar um índice de certeza (0-1) para a classificação
- Modificar a função `classificar_documento` para processar os índices de certeza retornados pelo modelo
- Adicionar validação para garantir que os índices de certeza estejam no formato correto

**Exemplo de modificação no prompt**:
```
Classifique o documento de acordo com o conteúdo apresentado em uma das seguintes categorias:
- voucher: Contém informações de reserva de hotel
- boleto: Contém dados de boletos bancários
- nota_fiscal: Contém informações de notas fiscais de serviço
- descarte: Qualquer documento que não se encaixa nas categorias acima

Para a classificação, também atribua um score de confiança entre 0 e 1, onde:
- 0.9-1.0: Certeza quase absoluta
- 0.7-0.9: Alta confiança
- 0.5-0.7: Confiança moderada
- 0.3-0.5: Baixa confiança
- 0.0-0.3: Muito baixa confiança

Responda apenas com um JSON, nesse formato:
{
  "tipo": "voucher",
  "indice_certeza": 0.95
}
```

### 3. Adicionar coleta de métricas de consumo de tokens

**Objetivo**: Implementar mecanismos para coletar e registrar o número de tokens de entrada e saída usados em cada chamada ao modelo.

**Detalhes**:
- Utilizar as APIs do LangChain ou OpenAI para obter informações de consumo de tokens
- Adicionar contadores para tokens de entrada e saída em cada chamada ao modelo
- Armazenar essas métricas no arquivo de saída JSON

### 4. Modificar o sistema para processar todos os arquivos em "amostragem/Parte 1"

**Objetivo**: Atualizar o código para iterar por todos os subdiretórios e arquivos PDF em `amostragem/Parte 1/` e processá-los individualmente.

**Detalhes**:
- Implementar uma função para percorrer recursivamente o diretório `amostragem/Parte 1/`
- Para cada arquivo PDF encontrado, executar o processo de classificação
- Coletar todas as métricas para cada arquivo processado

### 5. Remover geração de highlighted_pages

**Objetivo**: Eliminar a parte do código que gera os PDFs com highlights e as imagens exportadas para reduzir consumo de recursos.

**Detalhes**:
- Remover as funções `gerar_highlighted_pdf` e `exportar_paginas_com_highlight`
- Eliminar a geração de imagens e PDFs com highlights
- Remover a criação do diretório `highlighted_pages`

### 6. Criar diretório de saída e salvar resultados em arquivos JSON

**Objetivo**: Implementar a criação do diretório de saída `amostragem/Parte 1/OUTPUT/` e salvar os resultados de cada documento em arquivos JSON separados.

**Detalhes**:
- Criar o diretório `amostragem/Parte 1/OUTPUT/` se não existir
- Para cada documento processado, salvar um arquivo JSON com as métricas coletadas
- Nomear os arquivos JSON com o mesmo nome do arquivo PDF original, mas com extensão `.json`

### 7. Atualizar formato da saída

**Objetivo**: Modificar o formato da saída do console para incluir todas as informações solicitadas.

**Detalhes**:
- Atualizar a saída do console para mostrar o nome do arquivo e a classificação com índice de certeza
- Manter um formato legível e organizado para fácil acompanhamento do processo
- Mostrar informações de consumo de tokens na saída

## Ordem de Implementação Recomendada

1. Definir estrutura do arquivo de saída JSON
2. Implementar função para calcular e retornar o índice de certeza do modelo LLM
3. Adicionar coleta de métricas de consumo de tokens
4. Modificar o sistema para processar todos os arquivos em "amostragem/Parte 1"
5. Remover geração de highlighted_pages
6. Criar diretório de saída e salvar resultados em arquivos JSON
7. Atualizar formato da saída

## Critérios de Sucesso

- Todos os arquivos em `amostragem/Parte 1/` são processados com sucesso
- Cada arquivo gera um JSON de saída correspondente no diretório `OUTPUT/`
- As métricas de confiança são coletadas e armazenadas corretamente
- O consumo de tokens é registrado para cada chamada ao modelo
- O sistema não gera mais arquivos de highlighted_pages desnecessários
- A saída do console mostra informações relevantes de forma organizada