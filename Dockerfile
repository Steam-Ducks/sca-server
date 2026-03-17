FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependências do sistema para PostgreSQL e compilação
RUN apk add --no-cache \
    postgresql-client \
    gcc \
    musl-dev \
    postgresql-dev

# Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Expõe porta
EXPOSE 8000

# Comando padrão (pode ser sobrescrito pelo docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]