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
                            upload_date DATE DEFAULT (datetime
                            ('now','localtime')),
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
                            timestamp DATE DEFAULT (datetime
                            ('now','localtime')),
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
    return ''.join(random.choice(letters) for _ in range(8))


# users --------------------------------------------------------------------- #
for name in ['Jean', 'Michou', 'Renaud', 'Marie', 'Louise']:
    cursor.execute("INSERT INTO user (name) VALUES (?)", (name,))


# categories ---------------------------------------------------------------- #
for name in ["Graphisme", "Photographie", "Cinéma"]:
    cursor.execute("INSERT INTO category (name) VALUES (?)", (name,))


# picture ------------------------------------------------------------------ #
for data in [
        ("carte-archi-1.jpg",
         "Carte Archi", """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 1),
        ("deakins-1.jpg", "Deakins", """Lorem
        ipsum dolor sit amet, consectetur adipiscing elit. Nulla posuere
        sapien vel purus pretium, vitae lobortis turpis consequat.
        In id auctor lectus.""", 2, 3),
        ("deakins-2.jpg", "Deakins", """Lorem
        ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 3),
        ("deakins-3.jpg", "Deakins", """Lorem
        ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 3, 3),
        ("forme-graphique-1.jpg",
         "Forme Graphique", """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 4, 1),
        ("illustration-livre-1.jpg",
         "Illustration Livre", """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 1),
        ("japanese-poster-1.jpg",
         "Japanese Poster", """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 2, 1),
        ("japanese-poster-2.jpg",
         "Japanese Poster", """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 1),
        ("leiter-1.jpg", "Leiter",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 3, 2),
        ("lubezki-1.png", "Lubezki",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 3, 2),
        ("lubezki-2.jpg", "Lubezki",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 2),
        ("photo-metro-1.jpg", "Photo Metro",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 2, 2),
        ("photo-metro-2.jpg", "Photo Metro",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 2),
        ("poster-ntl-1.jpg",  "Poster NTL",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 3, 1),
        ("poster-pyrexal-1.jpg",
         "Poster Pyrexal", """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 1, 1),
        ("webdesign-1.jpg",  "Webdesign",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 3, 1),
        ("webdesign-2.jpg",  "Webdesign",
         """Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. Nulla posuere sapien vel purus pretium,
        vitae lobortis turpis consequat. In id auctor lectus.""", 2, 1), ]:
    cursor.execute("""INSERT INTO picture
                        (filename,
                        name, description, user_id, category_id)
                        VALUES (?, ?, ?, ?, ?)""", data)

# comment ------------------------------------------------------------------ #
comments = [(f"""202{random.randint(1, 2)}-0{random.randint(1, 3)}-01
            {random.randint(10, 23)}:{random.randint(10, 46)}:00""",
            f'commentaire-\u2060{randomString()*2}', random.randint(1, 4),
             random.randint(1, 17),) for _ in range(40)]

for data in comments:
    cursor.execute("""INSERT INTO comment
                        (timestamp, content, user_id, picture_id)
                        VALUES (?, ?, ?, ?)""", data)


# tag ---------------------------------------------------------------------- #
tags = ["photographie", "cinématographique", "poster", "web",
        "cinema", "random", "else"]

for _ in range(5):
    tags += [f'photographer-\u2060{randomString()}']

for tag in tags:
    cursor.execute("INSERT INTO tag (name) VALUES (?)", (tag,))


# maintag ------------------------------------------------------------------- #
for _ in range(40):
    cursor.execute(
        "INSERT INTO tagtopicture (tag_id, picture_id) VALUES (?, ?)",
        (random.randint(1, 12), random.randint(1, 17),))


# We save our changes into the database file
db.commit()

# We close the connection to the database
db.close()
