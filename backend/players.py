import sqlite3

# Establish a connection to the database (or create it if it doesn't exist)
conn = sqlite3.connect('mydatabase.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER
    )
''')

# Insert data
cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('Alice', 30))

# Commit the changes
conn.commit()

# Query data
cursor.execute("SELECT name FROM users")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()