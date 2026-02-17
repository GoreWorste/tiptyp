# TipTyp — тест набора, запуск в локальной сети
FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Код приложения
COPY app.py word_generator.py word_model.py train_word_model.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY scripts/ ./scripts/

# Каталог для БД и моделей (volume)
ENV TIPTYP_DATA=/data
RUN mkdir -p /data/instance

# Порт и хост для доступа из локальной сети
ENV FLASK_APP=app.py
EXPOSE 5000

# Gunicorn: привязка к 0.0.0.0 для доступа с других устройств в сети
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "app:app"]
