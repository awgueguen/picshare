import os
import sqlite3
from flask import (Flask, g, render_template, request, flash,
                   redirect, send_from_directory)
from werkzeug.utils import secure_filename
from datetime import datetime

# --------------------------------------------------------------------------- #
# global setup                                                                #
# --------------------------------------------------------------------------- #

DATABASE = 'app.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.jpg', '.png', '.gif', '.jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.add_url_rule('/uploads/<path:filename>', endpoint='uploads',
                 view_func=app.send_static_file)

# app.secret_key = '123123'

templates = {
    'pictures': ['upload_date', 'filename', 'name', 'description',
                 'category_id']
}
pairs = {'category_id': 'categories'}

# --------------------------------------------------------------------------- #
# methods                                                                     #
# --------------------------------------------------------------------------- #


def get_db():
    """get the db or even a cursor using `cur = get_db.execute(query)`

    Returns:
        db: database
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=(), one=False):
    """fetch data from a query and some args if needed

    Args:
        query (str): a complete SQLite query
        args (tuple, optional): args if the query has `?`. Defaults to ().
        one (bool, optional): `True` if only one value requested.
        Defaults to False.

    Returns:
        tuple: all the values fetched using the query
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    """exectute the db in case of a POST or a PUT

    Args:
        query (str): `INSERT` type of query for e.g.
        args (tuple, optional): args if the query has `?`. Defaults to ().

    Returns:
        int: return `cur.lastrowid`
    """
    cur = get_db().execute(query, args)
    get_db().commit()
    return cur.lastrowid


def get_data(request, route=None, tab=None):
    if tab is not None:
        template = templates[tab]
        data = {i: j for i, j in request.form.items()}
        clean_data = {template[i]: convert_data(data, template[i], tab)
                      for i in range(len(template))}
    if route == 'post_picture':
        clean_data['filename'] = rename_picture(request, tab)
        return clean_data
    elif route == 'valid_picture':
        return secure_filename(request.files['picture'].filename)
    elif route == 'valid_name':
        return request.form.get('name')


def convert_data(data, dependency, table):
    if dependency == 'upload_date':
        return str(datetime.now())
    elif '_id' in dependency:
        query = f'''SELECT id FROM {pairs[dependency]}
                    WHERE name = ?'''
        rv = query_db(query, (data[dependency.replace("_id", "")],), one=True)
        return rv[0]
    else:
        return data.get(dependency)


def uber_validator(request, conditions):
    if 'picture' in conditions:
        filename = get_data(request, 'valid_picture')
        if filename == '':
            return 'missing picture'
        elif filename[filename.index('.'):] not in ALLOWED_EXTENSIONS:
            return 'format not allowed'
    if 'name' in conditions:
        if get_data(request, 'valid_name') == '':
            return 'title missing'


def rename_picture(data, table):
    """function used to return a new file name for any given picture
    according to it's table.

    Args:
        data (req): request from POST
        table (str): name of the table where the path is registered

    Returns:
        str: new name for the picture `'cat-1.jpg'`
    """
    filename = (
        ''.join((i for i in data.form['name'] if i.isalnum()))).lower()
    query = f'SELECT filename FROM {table} WHERE filename LIKE ?'
    number = str(len(query_db(query, (filename+'-%',))) + 1)
    actual_filename = secure_filename(data.files['picture'].filename)
    extension = actual_filename[actual_filename.index('.'):]
    return filename+'-'+number+extension


# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #

# jinja routes -------------------------------------------------------------- #


@ app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


# index --------------------------------------------------------------------- #


@ app.route('/')
def index():
    return


# show ---------------------------------------------------------------------- #


@ app.route('/')
def show_picture():
    return


# image upload -------------------------------------------------------------- #

@ app.route('/upload', methods=['GET', 'POST'])
def upload_picture():
    # envoi à Jinja de la data sous forme d'un dictionnaire
    jinja_data = {}
    jinja_data['ok_ext'] = ALLOWED_EXTENSIONS
    # récupération des catégories pour les envoyer à Jinja
    sql_request = 'SELECT name FROM categories'
    jinja_data['categories'] = [i[0] for i in query_db(sql_request)]

    # cas 1: accès simple à la page
    if 'picture' not in request.files:
        return render_template('upload.html', data=jinja_data)

    # cas 2: un fichier est envoyé via le formulaire
    else:
        # vérification des paramètres
        # si il y a bien une 'picture' & qu'un 'name' est donné
        jinja_data['error'] = uber_validator(request, ['picture', 'name'])
        if jinja_data['error']:
            return render_template('upload.html', data=jinja_data)

        # récupération propres des données enregistrés dans le request.form
        # sous la forme d'un dictionnaire
        data = get_data(request, 'post_picture', 'pictures')

        # enregistrement sur le serveur de l'image '.save'
        # enregistrement dans la bdd des valeurs du form 'execute_db'
        request.files['picture'].save(
            os.path.join(UPLOAD_FOLDER, data['filename']))
        sql_inject = ', '.join(list('?'*len(data.keys())))
        sql_request = f"""INSERT INTO pictures ({', '.join(data.keys())})
                    VALUES ({sql_inject})"""
        execute_db(sql_request, tuple(data.values()))

        # rajout aux données les informations de l'image
        jinja_data['picture_data'] = data

    # après upload retourne la page avec un message de validation
    return render_template('upload.html', data=jinja_data)


# test ---------------------------------------------------------------------- #
if __name__ == '__main__':
    app.run(debug=True)

# If you don't want save the file to disk first,
# use the following code, this work on in-memory stream

# import os

# file = request.files['file']
# file.seek(0, os.SEEK_END)
# file_length = file.tell()

# or

# request.files['file'].save('/tmp/file')
# file_length = os.stat('/tmp/file').st_size
