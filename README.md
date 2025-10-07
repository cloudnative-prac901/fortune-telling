# customer-info

Flask + Nginx + Gunicorn のサンプルアプリ。  

# ローカル起動
```bash
docker build -t customer-info:dev .
docker run -p 8080:80 \
  -e DB_HOST=localhost -e DB_USER=user -e DB_PASSWORD=pass -e DB_NAME=sample \
  customer-info:dev
# http://localhost:8080 へアクセス
