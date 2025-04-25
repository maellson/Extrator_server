# Extrator Server

Projeto para extração inteligente de informações de documentos PDF, utilizando OCR, embeddings e agentes IA.

## Pré-requisitos

- **Python >= 3.11**
- [Poetry](https://python-poetry.org/docs/#installation)

## Instalação do Poetry

Para instalar o Poetry no seu sistema, rode o seguinte comando:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Após a instalação, adicione o Poetry ao PATH do seu sistema (caso necessário):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verifique a instalação do Poetry:

```bash
poetry --version
```

## Instalação do Projeto

Clone o repositório e acesse o diretório:

```bash
git clone <url-do-seu-repositorio>
cd extrator_server
```

Instale as dependências usando Poetry:

```bash
poetry install
```

Se ocorrer o aviso:

```
Warning: The current project could not be installed: No file/folder found for package extrator-server
```

Edite o arquivo `pyproject.toml` e adicione:

```toml
[tool.poetry]
package-mode = false
```

E rode novamente:

```bash
poetry install
```

## Ativação do Ambiente Virtual

Para ativar o ambiente Poetry criado:

```bash
poetry shell
```

Alternativamente (se houver problema com o comando acima):

```bash
source $(poetry env info --path)/bin/activate
```

## Estrutura do Projeto

```plaintext
extrator_server
├── arquivos_pdf
├── imagens_paginas
├── textos_paginas
├── main.py
├── pyproject.toml
└── README.md
```

## Executar o Projeto

Para executar o script principal:

```bash
python main.py
```

Certifique-se de configurar corretamente suas variáveis de ambiente, como chaves API do OpenAI, no arquivo `.env`:

```env
OPENAI_API_KEY=sua-chave-api-openai
```

## Dependências Principais

- Flask
- pytesseract
- pdf2image
- PyMuPDF
- LangChain
- OpenAI
- FAISS
- python-dotenv

## Testes

Para rodar testes (se aplicável):

```bash
pytest
```

---

Agora seu projeto está configurado corretamente e pronto para uso!

