import sqlite3
import random
import string

DATABASE = 'app.db'
db = sqlite3.connect(DATABASE)

cursor = db.cursor()

# Creation of table "categories".
# If it existed already, we delete the table and create a new one
cursor.execute('DROP TABLE IF EXISTS category')
cursor.execute("""CREATE TABLE category (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(200) NOT NULL)""")


cursor.execute('DROP TABLE IF EXISTS picture')
cursor.execute("""CREATE TABLE picture (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            upload_date TEXT NOT NULL,
                            filename VARCHAR(200) NOT NULL,
                            name VARCHAR(20) NOT NULL,
                            description VARCHAR(200) NOT NULL,
                            user_id INTEGER NOT NULL,
                            category_id INTEGER NOT NULL,
                            CONSTRAINT fk_user
                                FOREIGN KEY (user_id)
                                REFERENCES user(id)
                            CONSTRAINT fk_categories
                                FOREIGN KEY (category_id)
                                REFERENCES category(id))""")

cursor.execute('DROP TABLE IF EXISTS comment')
cursor.execute("""CREATE TABLE comment (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            upload_date TEXT NOT NULL,
                            content VARCHAR(100) NOT NULL,
                            user_id INTEGER NOT NULL,
                            picture_id INTEGER NOT NULL,
                            CONSTRAINT fk_user
                                FOREIGN KEY (user_id)
                                REFERENCES user(id)
                            CONSTRAINT fk_picture
                                FOREIGN KEY (picture_id)
                                REFERENCES picture(id))""")


cursor.execute('DROP TABLE IF EXISTS tag')
cursor.execute("""CREATE TABLE tag (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(200) NOT NULL)""")


cursor.execute('DROP TABLE IF EXISTS tagtopicture')
cursor.execute("""CREATE TABLE tagtopicture(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            tag_id INTEGER NOT NULL,
                            picture_id INTEGER NOT NULL,
                            CONSTRAINT fk_tag
                                FOREIGN KEY (tag_id)
                                REFERENCES tag(id),
                            CONSTRAINT fk_picture
                                FOREIGN KEY (picture_id)
                                REFERENCES picture(id))""")


cursor.execute('DROP TABLE IF EXISTS user')
cursor.execute("""CREATE TABLE user (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(20) NOT NULL)""")


# --------------------------------------------------------------------------- #
# dummy data creation                                                         #
# --------------------------------------------------------------------------- #


def randomString():
    letters = string.ascii_letters
    rv = ''.join(random.choice(letters) for i in range(8))
    return rv


# users --------------------------------------------------------------------- #
for name in ['Jean', 'Michou', 'Renaud', 'Marie']:
    cursor.execute("INSERT INTO user (name) VALUES (?)", (name,))


# categories ---------------------------------------------------------------- #
for name in ["Cats", "Dogs", "People", "Backgrounds"]:
    cursor.execute("INSERT INTO category (name) VALUES (?)", (name,))

# picture ------------------------------------------------------------------ #
for data in [
        ("2022-08-12 10:12:21", "cat-1.jpg",  "Cat", "Lorem ipsum dolor sit\
         amet, consectetur adipiscing elit. Nulla sapien felis, ornare vitae\
         urna quis, volutpat vestibulum sapien. Curabitur turpis lorem, \
         viverra hendrerit dapibus nec, aliquet nec orci. Phasellus\
         scelerisque risus sapien, non iaculis dolor condimentum ac.\
         Nulla a enim elit efficitur.", 1, 1),
        ("2022-08-10 10:12:21", "dog-1.jpg", "Dog", "Hello", 2,  2),
        ("2022-07-12 10:12:21", "guy-1.jpg", "Guy", "Hello", 3, 3),
        ("2021-08-12 10:12:21", "woman-1.jpg", "Woman", "Hello", 4, 3), ]:
    cursor.execute("""INSERT INTO picture
                        (upload_date, filename,
                        name, description, user_id, category_id)
                        VALUES (?, ?, ?, ?, ?, ?)""", data)

# comment ------------------------------------------------------------------ #
comments = []
for i in range(20):
    comments.append(
        (f'2021-01-01 {random.randint(10, 23)}:{random.randint(10,46)}:00',
         f'commentaire-\u2060{randomString()*2}', random.randint(1, 4),
         random.randint(1, 4),))

for data in comments:
    cursor.execute("""INSERT INTO comment
                        (upload_date, content, user_id, picture_id)
                        VALUES (?, ?, ?, ?)""", data)


# tag ---------------------------------------------------------------------- #
tags = ["photographie", "cinématographique", "poster", "web",
        "cinema", "random", "else"]

for i in range(10):
    tags += [f'photographer-\u2060{randomString()}']

for tag in tags:
    cursor.execute("INSERT INTO tag (name) VALUES (?)", (tag,))


# maintag ------------------------------------------------------------------- #
for i in range(20):
    cursor.execute(
        "INSERT INTO tagtopicture (tag_id, picture_id) VALUES (?, ?)",
        (random.randint(1, 10), random.randint(1, 4),))


# We save our changes into the database file
db.commit()

# We close the connection to the database
db.close()
