import sqlite3

conn = sqlite3.connect('bazi_pro.db')
cursor = conn.execute("SELECT id, pattern, day_master FROM analyses WHERE pattern LIKE '%化木%'")
rows = cursor.fetchall()
print(f"Found {len(rows)} records with 化木 in pattern")
for r in rows:
    print(r)
conn.close()
