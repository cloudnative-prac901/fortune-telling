# app.py
from flask import Flask, render_template_string, url_for, redirect, request
from datetime import datetime, timezone, timedelta
import os, json
import pymysql
import boto3

# PyMySQL を MySQLdb として使う
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# ===== 設定 =====
AWS_REGION     = os.getenv("AWS_REGION", "ap-northeast-2")
DB_HOST        = os.getenv("DB_HOST")  # 例: xxxxxx.ap-northeast-1.rds.amazonaws.com
DB_NAME        = os.getenv("DB_NAME", "fortune_telling")
DB_SECRET_NAME = os.getenv("DB_SECRET_NAME", "fortune-telling-app-credentials")
TZ_JST         = timezone(timedelta(hours=9))

# ===== Secrets Manager から DB 認証情報を取得（起動時キャッシュ）=====
_sm = boto3.client("secretsmanager", region_name=AWS_REGION)
_secret = _sm.get_secret_value(SecretId=DB_SECRET_NAME)
_creds  = json.loads(_secret["SecretString"])  # {"username": "...", "password": "..."}

def get_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=_creds["username"],
        password=_creds["password"],
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

# ===== HTML（トップ＆結果）=====
TOP_HTML = """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>今日の運勢</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; }
    .card { max-width: 560px; margin: 0 auto; padding: 2rem; border: 1px solid #eee; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,.06); }
    h1 { font-size: 1.8rem; margin: 0 0 1rem; }
    .date { color: #555; margin-bottom: 1.5rem; }
    button { font-size: 1.1rem; padding: .8rem 1.2rem; border: 0; border-radius: 10px; cursor: pointer; }
    .primary { background:#0ea5e9; color:#fff; }
  </style>
</head>
<body>
  <div class="card">
    <h1>今日の運勢</h1>
    <div class="date">{{ date_text }}</div>
    <form method="post" action="{{ url_for('result') }}">
      <button class="primary" type="submit">占う</button>
    </form>
  </div>
</body>
</html>
"""

RESULT_HTML = """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>今日の運勢 - 結果</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; }
    .card { max-width: 560px; margin: 0 auto; padding: 2rem; border: 1px solid #eee; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,.06); }
    h1 { font-size: 1.8rem; margin: 0 0 1rem; }
    .label { color:#6b7280; font-size:.9rem; }
    .value { font-size:1.3rem; margin-bottom:.8rem; }
    button { display:inline-block; margin-top:1.2rem; font-size:1.05rem; padding:.7rem 1.1rem; border-radius:10px; border:0; cursor:pointer; }
    .ghost { background:#f3f4f6; color:#111827; }
  </style>
</head>
<body>
  <div class="card">
    <h1>今日の運勢（結果）</h1>
    <div class="label">おみくじ番号：</div>
    <div class="value">{{ number }}番</div>
    <div class="label">今日の運勢：</div>
    <div class="value">{{ fortune_rank }}</div>
    <div class="label">開運の一言：</div>
    <div class="value">{{ message }}</div>
    <form action="{{ url_for('fortune') }}" method="get">
      <button class="ghost" type="submit">Topに戻る</button>
    </form>
  </div>
</body>
</html>
"""

# ===== ルーティング =====

# / はヘルスチェック用
@app.get("/")
def health():
    return {"status": "ok"}, 200

# /fortune はトップ画面
@app.get("/fortune")
def fortune():
    today = datetime.now(TZ_JST)
    date_text = f"{today.month}月{today.day}日の運勢"
    return render_template_string(TOP_HTML, date_text=date_text)

# /result は結果画面（ボタンクリックでPOST想定／GETも許可）
@app.route("/result", methods=["GET", "POST"])
def result():
    sql = "SELECT number, fortune_rank, message FROM results ORDER BY RAND() LIMIT 1"
    row = None
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
    except Exception:
        # DB未準備時のフォールバック
        row = {"number": "11", "fortune_rank": "中吉", "message": "深呼吸してペースを整えよう。"}

    # テーブルが空のときのフォールバック
    if not row:
        row = {"number": "11", "fortune_rank": "中吉", "message": "深呼吸してペースを整えよう。"}

    return render_template_string(
        RESULT_HTML,
        number=row["number"],
        fortune_rank=row["fortune_rank"],
        message=row["message"],
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
