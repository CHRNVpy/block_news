import sqlite3

# Connect to database
conn = sqlite3.connect('/root/block/news.db')
c = conn.cursor()

# Create table if not exists
# c.execute('''CREATE TABLE IF NOT EXISTS news (
# id INTEGER PRIMARY KEY, 
# title TEXT,
# article_id INTEGER,
# date TIMESTAMP,
# url TEXT
# )''')


def save_to_db(title, article_id, date, url):
    # Insert data into table
    c.execute("INSERT INTO news (title, article_id, date, url) VALUES (?, ?, ?, ?)", (title, article_id, date, url))

    # Count rows in table
    c.execute("SELECT COUNT(*) FROM news")
    num_rows = c.fetchone()[0]

    # Delete last row if there are more than 50 rows
    if num_rows > 50:
        c.execute("DELETE FROM news WHERE id = (SELECT MIN(id) FROM news)")

    # Commit changes to database
    conn.commit()


def in_db(article_id):
    # Check if the post title already exists in the table
    c.execute("SELECT id FROM news WHERE article_id=?", (article_id,))
    result = c.fetchone()
    # If the post title does not exist, insert the new post
    if not result:
        return False
    else:
        return True
