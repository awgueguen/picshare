import os
from flask import (Flask, g, request, render_template, abort,
                   redirect, send_from_directory, url_for)

# methods ------------------------------------------------------------------- #
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
from unidecode import unidecode

# --------------------------------------------------------------------------- #
# global setup                                                                #
# --------------------------------------------------------------------------- #

DATABASE = 'app.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.jpg', '.png', '.gif', '.jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.add_url_rule('/uploads/<path:filename>',
                 endpoint='uploads', view_func=app.send_static_file)

# ressources ---------------------------------------------------------------- #
tabs_titles = {
    'category': ['id', 'name'],
    'picture': ['id', 'upload_date', 'filename', 'name',
                'description', 'user_id', 'category_id'],
    'comment': ['id', 'upload_date', 'content', 'user_id', 'picture_id'],
    'tag': ['id', 'name'],
    'tagtopicture': ['id', 'tag_id', 'picture_id']
}

pairs = {'category_id': 'category',
         "picture_id": 'picture',
         'tag_id': 'tag',
         'user_id': 'user'}


# methods ------------------------------------------------------------------- #


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query: str, args=(), one: bool = False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return ([rv[0]] if rv else None) if one else rv


def update_db(query: str, args=()):
    cur = get_db().execute(query, args)
    get_db().commit()
    return cur.lastrowid


def get_data(table: str, id=()):
    tabs = tabs_titles[table]
    if id:
        if isinstance(id, tuple):
            sql_request = f'SELECT * FROM {table} WHERE {id[1]} LIKE ?'
            rv = query_db(sql_request, (id[0],), one=True)
        else:
            sql_request = f'SELECT * FROM {table} WHERE id = ?'
            rv = query_db(sql_request, (id,), one=True)
    else:
        sql_request = f'SELECT * FROM {table}'
        rv = query_db(sql_request)

    clean_data = [{tabs[i]: j[i]
                   for i in range(len(tabs))} for j in rv]
    return clean_data


def convert_data(rv: list):
    for i in rv:
        for j in i:
            if ('_id' in j) and (j != "picture_id"):
                if str(i[j]).isalpha():
                    query = f'''SELECT id FROM {pairs[j]}
                            WHERE name = ?'''
                    i[j] = query_db(query, (i[j],), one=True)[0][0]
                elif str(i[j]).isnumeric():
                    query = f'''SELECT name FROM {pairs[j]}
                            WHERE id = ?'''
                    i[j] = query_db(query, (i[j],), one=True)[0][0]
    return rv


# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #

# life cycle ---------------------------------------------------------------- #


@app.before_request
def check_if_image_missing():
    rv = get_data('picture')
    sql_request = 'DELETE FROM pictures WHERE filename = ?'
    for i in rv:
        if not os.path.exists(app.config["UPLOAD_FOLDER"]+f'/{i["filename"]}'):
            update_db(sql_request, (i["filename"],))


@app.context_processor
def menu_creator():
    rv = get_data('category')
    menu = list(map(lambda x: x['name'], rv))
    return dict(menu=menu)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.route('/uploads/<name>')
def secure_file(name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], name)


# index --------------------------------------------------------------------- #

@app.route('/')
def index():
    pictures = convert_data(get_data('picture'))
    tags = convert_data(get_data('tagtopicture'))
    tags_by_picture = {
        i['id']: list(filter(lambda x: x['picture_id'] == i['id'],
                             tags)) for i in pictures
    }

    JINJA_DATA = {
        'pictures': sorted(pictures, key=lambda x: x['upload_date'],
                           reverse=True),
        'tags': tags_by_picture
    }

    return render_template('index.html', **JINJA_DATA)


# categories ---------------------------------------------------------------- #

@app.route('/categories/<name>')
def categories(name):
    rv = convert_data(get_data('picture'))
    pictures = list(filter(lambda x: (x['category_id'] == name), rv))
    if pictures == []:
        abort(404)

    tags = convert_data(get_data('tagtopicture'))

    tags_by_picture = {
        i['id']: list(filter(lambda x: x['picture_id'] == i['id'],
                             tags)) for i in pictures
    }

    JINJA_DATA = {
        'pictures': sorted(pictures, key=lambda x: x['upload_date'],
                           reverse=True),
        'tags': tags_by_picture
    }

    return render_template('index.html', **JINJA_DATA)


# show ---------------------------------------------------------------------- #

@ app.route("/gallery/<name>", methods=["GET", "POST"])
def show_picture(name):
    rv = convert_data(get_data('picture', id=(name+'%', 'filename',)))
    if rv is None:
        abort(404)

    id = rv[0]['id']
    comments = convert_data(get_data('comment'))
    tags = convert_data(get_data('tagtopicture'))

    JINJA_DATA = {
        'picture': rv[0],
        'comments': list(filter(lambda x: (x['picture_id'] == id), comments)),
        'tags': list(filter(lambda x: (x['picture_id'] == id), tags)),

    }

    return render_template('show.html', **JINJA_DATA)
