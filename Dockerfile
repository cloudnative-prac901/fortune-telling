# ランタイム
FROM python:3.12-slim

# OSパッケージ（MySQL接続やtz、必要最小限）
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 依存関係
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体
COPY app/app.py /app/app.py
ENV PORT=8080
EXPOSE 8080

# Gunicornで起動（マルチワーカー対応）
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "2", "app:app"]
