import sqlite3

conn = sqlite3.connect("news.db")
cursor = conn.cursor()

cursor.execute("""
SELECT users.username,
       predictions.news_text,
       predictions.prediction,
       predictions.timestamp
FROM predictions
JOIN users
ON users.id = predictions.user_id
ORDER BY predictions.id DESC
""")

rows = cursor.fetchall()

print("\n===== USER PREDICTIONS =====\n")

for row in rows:
    print(row)

conn.close()
