from flask import Flask
import pymysql
import boto3
import json
import os

# PyMySQL を MySQLdb として使う
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# ===== Secrets Manager から DB 認証情報を取得 =====
def load_db_credentials():
    secret_name = os.environ.get("DB_SECRET_NAME", "customer-info-app-credentials")
    region_name = os.environ.get("AWS_REGION", "ap-northeast-2")
    client = boto3.client("secretsmanager", region_name=region_name)
    secret_value = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value["SecretString"])

# 起動時にキャッシュ
DB_CREDS = load_db_credentials()   # {"username":"app_user","password":"..."}
DB_HOST  = os.environ["DB_HOST"]   # 例: customer-info.xxxxxx.ap-northeast-1.rds.amazonaws.com
DB_NAME  = os.environ.get("DB_NAME", "customer_info")

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_CREDS["username"],
        password=DB_CREDS["password"],
        database=DB_NAME,
        port=int(DB_CREDS.get("port", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        autocommit=True,
    )

@app.route("/")
def index():
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, age, email, created_at
                FROM customers
                ORDER BY id ASC
            """)
            rows = cur.fetchall()

        html = [
            "<!doctype html><meta charset='utf-8'>",
            "<h1>顧客一覧（customers）</h1>",
            "<table border='1' cellpadding='6' cellspacing='0'>",
            "<tr><th>ID</th><th>名前</th><th>年齢</th><th>Email</th><th>登録日時</th></tr>"
        ]
        for r in rows:
            html.append(
                f"<tr><td>{r['id']}</td><td>{r['name']}</td><td>{r['age']}</td>"
                f"<td>{r['email']}</td><td>{r['created_at']}</td></tr>"
            )
        html.append("</table>")
        return "\n".join(html)

    except Exception as e:
        return f"<pre>DB接続エラー：{e}</pre>", 500

@app.route("/healthcheck")
def healthcheck():
    return "OK", 200

