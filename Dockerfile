FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
