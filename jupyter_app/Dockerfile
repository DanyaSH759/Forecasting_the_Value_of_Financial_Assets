FROM python:3.12

# Устанавливаем все зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Jupyter
RUN pip install notebook

# Создаем папку для Jupyter
WORKDIR /app

# Открываем порт
EXPOSE 8888

# Команда запуска Jupyter
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root"]
