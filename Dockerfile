FROM python:3.13-slim

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY bot.py config.py texts.py ./

# Создаём директорию для данных
RUN mkdir -p /app/data

# Запуск бота
CMD ["python", "bot.py"]
