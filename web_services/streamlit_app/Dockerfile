FROM python:3.12

WORKDIR /app
COPY requirements.txt .
COPY deps /deps
# RUN pip install --no-cache-dir -r requirements.txt \
#     --index-url https://pypi.tuna.tsinghua.edu.cn/simple
# Устанавливаем из локальной папки (без интернета)
RUN pip install --no-index --find-links=/deps -r requirements.txt
COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
