FROM python:3.12

WORKDIR /app
COPY requirements.txt .
COPY deps /deps
# RUN pip install --no-cache-dir -r requirements.txt \
#     --index-url https://pypi.tuna.tsinghua.edu.cn/simple
# Устанавливаем из локальной папки (без интернета)
RUN pip install --no-index --find-links=/deps -r requirements.txt
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
