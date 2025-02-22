FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN flake8 . --count --exit-zero
RUN bandit -ll -r app.py
RUN mypy --strict app.py

CMD ["python", "app.py"]
