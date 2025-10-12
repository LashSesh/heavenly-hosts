FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN adduser --disabled-password --gecos '' hhp \
    && apt-get update \
    && apt-get install -y --no-install-recommends libcap2-bin \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src/ /app/src/
RUN pip install --no-cache-dir /app
USER hhp
EXPOSE 8080/tcp 4444/udp
CMD ["uvicorn", "hhp.api:app", "--host", "0.0.0.0", "--port", "8080"]
