import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    role VARCHAR(10),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
cur.close()
conn.close()

print("Table created successfully ✅")
