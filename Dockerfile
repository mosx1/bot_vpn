# Этап сборки зависимостей
FROM python:3.13-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Финальный образ
FROM python:3.13-slim

WORKDIR /bot_vpn

# Копируем только нужные файлы из builder
COPY --from=builder /root/.local /home/bot/.local
COPY --chown=bot:bot . .


CMD ["python3", "bot_vpn.py"]
