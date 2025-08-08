# Sistema de Classificação de Documentos VoeTur - Visão Completa do Projeto

Desenvolvi uma série de diagramas que representam visualmente o sistema de classificação de documentos proposto para a VoeTur. Estes diagramas ilustram a arquitetura, fluxos de processo, interações entre componentes e uma interface de validação.

## Arquitetura do Sistema

O primeiro diagrama apresenta a arquitetura completa do sistema, dividida em quatro grandes blocos:

1. **Entrada e Processamento**: Responsável pela ingestão de PDFs e extração de texto usando técnicas complementares (OCR e vetorial)
2. **Classificação Híbrida**: Combina a abordagem atual baseada em LLM com classificadores de ML para melhorar a assertividade
3. **Validação Iterativa**: Implementa o processo de feedback humano para melhorar continuamente os modelos
4. **Saída e Integração**: Formata e entrega os resultados para integração com a API da VoeTur

Este design modular permite que cada componente seja aprimorado independentemente, mantendo a interoperabilidade do sistema.

## Fluxo do Processo Iterativo

O segundo diagrama detalha o fluxo completo do processo, mostrando como funciona o ciclo iterativo de classificação e validação:

1. Documentos são processados por lotes
2. Cada página recebe uma classificação com nível de confiança
3. Páginas com baixa confiança (<70%) são enviadas para validação humana
4. Os feedbacks coletados são utilizados para treinar modelos ML
5. Esses modelos aprimorados são aplicados aos próximos documentos

Este ciclo de melhoria contínua é o coração da solução, permitindo que o sistema evolua rapidamente de 70% para potencialmente 85-90% de assertividade.

## Interação entre Componentes

O terceiro diagrama mostra a sequência de interações entre todos os componentes do sistema durante um ciclo completo de processamento:

- Como o usuário interage com o pipeline
- O fluxo de dados entre extratores de texto, classificadores e modelos ML
- A intervenção humana no processo de validação
- A realimentação do sistema com dados validados

Este diagrama ajuda a entender como os diferentes componentes trabalham juntos em tempo de execução.

## Interface de Validação

Incluí um mockup interativo da interface de validação para demonstrar como seria a experiência do operador humano no processo de validação manual. Esta interface:

- Exibe o documento e o texto extraído lado a lado
- Mostra a classificação sugerida com seu nível de confiança
- Permite confirmação rápida ou alteração da classificação
- Acompanha o progresso do lote sendo validado

Uma interface intuitiva é crucial para garantir que a validação manual seja eficiente e precisa.

## Integração com o Sistema VoeTur

O último diagrama ilustra como a solução se integra ao ambiente existente da VoeTur:

1. Os documentos são recebidos do armazenamento de arquivos da VoeTur
2. O processamento ocorre em nossa solução autônoma 
3. Os resultados são retornados à API da VoeTur em formato JSON
4. A base de dados da VoeTur é atualizada com as classificações

Esta arquitetura mantém uma clara separação de responsabilidades enquanto garante uma integração fluida com os sistemas existentes.

---

Esta abordagem combina o melhor dos dois mundos: aproveita a eficácia da sua solução atual baseada em LLM (que já alcança 70% de assertividade) e adiciona classificadores mais simples treinados de forma iterativa com feedback humano. Ao focar a validação manual apenas nos documentos com baixa confiança, otimizamos o esforço humano enquanto continuamente melhoramos o sistema.

Gostaria que eu detalhasse algum aspecto específico desta proposta ou explique melhor algum dos componentes apresentados?