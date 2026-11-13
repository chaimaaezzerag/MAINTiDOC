FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY prompts ./prompts
COPY config ./config
COPY ui ./ui
RUN useradd --uid 10001 --create-home maintidoc
USER maintidoc
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
