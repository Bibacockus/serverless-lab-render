from flask import Flask, request, jsonify
import psycopg2
import os
from urllib.parse import urlparse
import sys

app = Flask(__name__)

# Подключение к БД с обработкой ошибок
DATABASE_URL = os.environ.get('DATABASE_URL')
conn = None

if DATABASE_URL:
    try:
        url = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        print("✅ Database connected successfully")
        
        # Создание таблицы при старте
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            print("✅ Table 'messages' ready")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        conn = None
else:
    print("⚠️ DATABASE_URL not set, running without database")

@app.route('/')
def hello():
    return "Hello, Serverless! 🚀\n", 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health():
    return "OK", 200

@app.route('/save', methods=['POST'])
def save_message():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        data = request.get_json()
        message = data.get('message', '') if data else ''
        
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
            
        return jsonify({"status": "saved", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/messages')
def get_messages():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        
        messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)