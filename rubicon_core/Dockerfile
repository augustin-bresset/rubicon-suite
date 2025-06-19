FROM python:3.12-slim
WORKDIR /app
COPY rubicon_core/requirements.txt .
RUN pip install -r requirements.txt alembic psycopg2-binary
COPY . .
