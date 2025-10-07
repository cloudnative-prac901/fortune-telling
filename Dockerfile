# ランタイム
FROM python:3.12-slim

# OSパッケージ（MySQL, curl など）
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends \
      build-essential default-libmysqlclient-dev ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体
COPY app/app.py /app/app.py
ENV PORT=80
EXPOSE 80

# Gunicornで起動（0.0.0.0:80）
CMD ["gunicorn", "-b", "0.0.0.0:80", "--workers", "2", "app:app"]
