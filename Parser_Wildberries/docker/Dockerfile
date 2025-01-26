# Используем базовый образ с Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем зависимости проекта
COPY ../app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем файлы проекта в контейнер
COPY ../app /app

# Указываем команду для запуска приложения
CMD ["python", "/app/main.py"]