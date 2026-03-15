FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p logs ai_evaluate/archive
EXPOSE 8001
CMD ["python", "main.py"]
