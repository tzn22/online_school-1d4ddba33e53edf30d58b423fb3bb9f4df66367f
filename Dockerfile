# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as builder

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Основной stage
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование виртуального окружения из builder stage
COPY --from=builder /opt/venv /opt/venv

# Установка PATH для виртуального окружения
ENV PATH="/opt/venv/bin:$PATH"

# Создание директорий для приложения
WORKDIR /app

# Копирование исходного кода
COPY . .

# Создание директорий для статических файлов и медиа
RUN mkdir -p staticfiles media logs

# Установка прав на выполнение скриптов
RUN chmod +x scripts/*.sh 2>/dev/null || echo "Нет скриптов для chmod"

# Создание пользователя для безопасности
RUN groupadd -r django && useradd --no-log-init -r -g django django
RUN chown -R django:django /app
USER django

# Открытие порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Команда по умолчанию
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]