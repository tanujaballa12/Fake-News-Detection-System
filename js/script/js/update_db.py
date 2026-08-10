import sqlite3

conn = sqlite3.connect("news.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS predictions")

cursor.execute("""
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    news_text TEXT,
    prediction TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Predictions table updated successfully!")
