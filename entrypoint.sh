#!/bin/bash
set -e

echo "=== 1. ממתין לעליית מסד הנתונים ==="
python3 -c "
import time, psycopg2, os
host = os.getenv('DB_HOST', 'postgres')
db = os.getenv('POSTGRES_DB', 'timlul_db')
user = os.getenv('POSTGRES_USER', 'timlul_user')
password = os.getenv('POSTGRES_PASSWORD', 'timlul_password')
port = os.getenv('DB_PORT', '5432')

while True:
    try:
        conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
        conn.close()
        break
    except Exception:
        time.sleep(1)
"

echo "=== 2. אימות מבנה מסד הנתונים ==="
python3 init_db.py

echo "=== 3. טעינת קבצים קיימים ==="
python3 ingest_json.py

echo "=== 4. הפעלת מנגנון ניטור זמן אמת ברקע ==="
python3 file_watcher.py &

echo "=== 5. הפעלת הדשבורד ==="
streamlit run app.py --server.port 8501 --server.address 0.0.0.0