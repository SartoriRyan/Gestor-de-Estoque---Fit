# Imagem base
FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema (para xlsxwriter/openpyxl etc.)
RUN apt-get update && apt-get install -y build-essential libpq-dev --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia o app
COPY app.py ./

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.enableCORS", "false"]
