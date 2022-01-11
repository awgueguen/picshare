import sqlite3

DATABASE = 'app.db'
db = sqlite3.connect(DATABASE)

cursor = db.cursor()

# Creation of table "categories".
# If it existed already, we delete the table and create a new one
cursor.execute('DROP TABLE IF EXISTS categories')
cursor.execute("""CREATE TABLE categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(200) NOT NULL)""")


cursor.execute('DROP TABLE IF EXISTS pictures')
cursor.execute("""CREATE TABLE pictures (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            upload_date TEXT,
                            filename VARCHAR(200),
                            name VARCHAR(20),
                            description VARCHAR(200),
                            category_id INTEGER,
                                CONSTRAINT fk_categories
                                FOREIGN KEY (category_id)
                                REFERENCES categories(id))""")


cursor.execute('DROP TABLE IF EXISTS comments')
cursor.execute("""CREATE TABLE comments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            upload_date TEXT NOT NULL,
                            author VARCHAR(200) NOT NULL,
                            content VARCHAR(200) NOT NULL,
                            picture_id INTEGER NOT NULL,
                                CONSTRAINT fk_pictures
                                FOREIGN KEY (picture_id)
                                REFERENCES pictures(id))""")

# --------------------------------------------------------------------------- #
# we create some dummy data                                                   #
# --------------------------------------------------------------------------- #

# categories ---------------------------------------------------------------- #
for name in ["Cats", "Dogs", "People", "Backgrounds"]:
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))

# pictures ------------------------------------------------------------------ #
for data in [
        ("2022-08-12 10:12:21", "cat.jpg", "Cat", "Hello", 1),
        ("2022-08-10 10:12:21", "dog.jpg", "Dog", "Hello", 2),
        ("2022-07-12 10:12:21", "guy.jpg", "A guy", "Hello", 3),
        ("2021-08-12 10:12:21", "woman.jpg", "A woman", "Hello", 3), ]:
    cursor.execute("""INSERT INTO pictures
                        (upload_date, filename, name, description, category_id)
                        VALUES (?, ?, ?, ?, ?)""", data)

# comments ------------------------------------------------------------------ #
for data in [
        ("2022-08-12 10:12:21", "foreign dog", "you rock", 1),
        ("2022-08-10 10:12:21", "false cat", "you cat sucks", 1), ]:
    cursor.execute("""INSERT INTO comments
                        (upload_date, author, content, picture_id)
                        VALUES (?, ?, ?, ?)""", data)

# We save our changes into the database file
db.commit()

# We close the connection to the database
db.close()
