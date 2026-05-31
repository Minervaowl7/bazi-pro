import sqlite3
conn = sqlite3.connect('bazi_pro.db')
cursor = conn.execute("UPDATE analyses SET pattern='月劫格，透正官' WHERE pattern='化木格'")
print(f"Updated {cursor.rowcount} records from 化木格 to 月劫格，透正官")
conn.commit()
conn.close()
