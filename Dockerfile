FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости и обновляем pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip

# Устанавливаем зависимости приложения
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем non-root пользователя
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Копируем исходный код
COPY --chown=appuser:appuser . .

# Проверки кода
RUN flake8 . --count --exit-zero \
    && bandit -ll -r app.py -c pyproject.toml \
    && mypy --strict app.py

CMD ["python", "app.py"]
