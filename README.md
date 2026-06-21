# FitStock - Gestor de Estoque (Streamlit)

Este repositório contém um app Streamlit para gerenciamento de estoque de academia com reconciliação entre "Estoque do Sistema", "Quartinho" e "Recepção".

Como rodar localmente:

1. (Recomendado) crie um virtualenv:

   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\activate      # Windows

2. Instale dependências:

   pip install -r requirements.txt

3. Rode a aplicação:

   streamlit run app.py

Deploy com Docker (geral):

1. Build: docker build -t fitstock .
2. Run: docker run -p 8501:8501 fitstock
3. O app estará disponível em http://localhost:8501

Opções de deploy:
- Streamlit Cloud: simples e direto (recomendado para apps Streamlit).
- Render / Railway: suportam Python e são fáceis de configurar.
- Vercel: possível via Docker/container; exige configuração de projeto para usar uma imagem/container.
