# --- ESTÁGIO 1: Builder (Compilação) ---
FROM python:3.12-alpine AS builder

WORKDIR /app

# Impedir que o Python gere arquivos .pyc e garantir log em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências de compilação (apenas para o build)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    libffi-dev

# Instala as dependências do Python no diretório de usuário para facilitar a cópia
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt


# --- ESTÁGIO 2: Final (Produção) ---
FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala APENAS a biblioteca de runtime do PostgreSQL (essencial para rodar, mas leve)
RUN apk add --no-cache libpq

# Copia apenas as bibliotecas instaladas no estágio anterior
COPY --from=builder /root/.local /root/.local
# Garante que os binários instalados (como o gunicorn) fiquem no PATH
ENV PATH=/root/.local/bin:$PATH

# Copia o código do seu projeto SCARS
COPY . .

# Em produção, use Gunicorn em vez do runserver (mais estável e leve)
# Certifique-se de ter 'gunicorn' no seu requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "scars.wsgi:application"]