FROM python:3.12-slim

RUN pip install -U pip ; pip install --no-cache-dir uv

COPY . /app

WORKDIR /app

CMD ["uv", "run", "streamlit", "run", "main.py"]