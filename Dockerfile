FROM arm64v8/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists for CSV logging
RUN mkdir -p data

CMD ["python", "-u", "main.py"]
