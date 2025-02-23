FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install types-python-dateutil gradio-stubs

RUN useradd -m appuser && chown -R appuser /app
USER appuser

COPY --chown=appuser:appuser . .

RUN flake8 . --count --exit-zero \
    && bandit -ll -r app.py -c pyproject.toml \
    && mypy --strict --ignore-missing-imports app.py

CMD ["python", "app.py"]
