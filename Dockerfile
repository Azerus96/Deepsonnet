FROM python:3.11-slim

WORKDIR /app

# Создаем non-root пользователя
RUN useradd -m appuser && chown -R appuser /app
USER appuser

COPY requirements.txt .

# Обновляем pip перед установкой
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --user

COPY . .

# Запускаем проверки с игнорированием ошибок стиля
RUN flake8 . --count --exit-zero
RUN bandit -ll -r app.py -c pyproject.toml
RUN mypy --strict app.py

CMD ["python", "app.py"]
