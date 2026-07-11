FROM python:3.12-slim

WORKDIR /app
COPY app.py /app/app.py

EXPOSE 8000

CMD ["python3", "/app/app.py", "--port", "8000"]
