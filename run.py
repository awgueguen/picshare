import os
import sqlite3
from flask import (Flask, g, render_template, request, flash, abort,
                   redirect, send_from_directory)
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
app.add_url_rule('/uploads/<path:filename>', endpoint='uploads',
                 view_func=app.send_static_file)

templates = {
    'pictures': ['upload_date', 'filename', 'name', 'description',
                 'category_id'],
    'categories': ['name']
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


def query_db(query: str, args=(), one=False):
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


def execute_db(query: str, args=()):
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


def get_data(request=None, route=None, tab=None, args=()):
    if tab:
        if args:
            description = ', '.join([i for i in args])
            values = query_db(f'SELECT {description} FROM {tab}')
            clean_data = [{args[j]: i[j]
                           for j in range(len(args))} for i in values]
        else:
            template = templates[tab]
            values = {i: j for i, j in request.form.items()}
            clean_data = {template[i]: convert_data(values, template[i])
                          for i in range(len(template))}

    if route == 'post_picture':
        clean_data['filename'] = rename_picture(request, tab)
    elif route == 'valid_picture':
        return secure_filename(request.files['picture'].filename)
    elif route == 'valid_name':
        return request.form.get('name')
    return clean_data


def convert_data(data: dict, dependency: str):
    if dependency == 'upload_date':
        return str(datetime.now())
    elif '_id' in dependency:
        query = f'''SELECT id FROM {pairs[dependency]}
                    WHERE name = ?'''
        rv = query_db(query, (data[dependency.replace("_id", "")],), one=True)
        return rv[0]
    else:
        return data.get(dependency)


def uber_validator(request, conditions: list):
    if 'picture' in conditions:
        filename = get_data(request, 'valid_picture')
        if filename == '':
            return 'missing picture'
        elif filename[filename.index('.'):] not in ALLOWED_EXTENSIONS:
            return 'format not allowed'
    if 'name' in conditions:
        if get_data(request, 'valid_name') == '':
            return 'title missing'


def rename_picture(data: dict, table: str):
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


def extract_tags(string: str, recurse=False):
    """function use to extract all the # from a comment or description

    Args:
        string (str): a comment or description that might contain tags
        recurse (bool, optional): state define in the function,
        lighten the load of the function. Do not change to True.

    Returns:
        list: list containing all the extracted tags or an empty list
    """
    # clean
    if recurse is False:
        allowed = [' ', '#']
        string = string
        string = ''.join([i for i in string if (i.isalnum() or i in allowed)])
        while '# ' in string:
            string = string.replace('# ', ' ')
        while string[-1] == '#':
            string = string[:-1]

    # recursion
    # base case
    if not string or '#' not in string:
        return []
    # recursive case
    else:
        hash_pos = string.index('#')
        if ' ' in string[hash_pos:]:
            tag = string[hash_pos:string.index(' ', hash_pos)]
        else:
            tag = string[hash_pos:]
        return [tag[1:]] + extract_tags(string[hash_pos+1:], recurse=True)


def inject_tags(tags: list, picture_id: int):
    """function used to inject in the two tables of the db the differents tags
    and their dependencies

    Args:
        tags (list): list of tags
        picture_id (int): picture_id for the join table
    """
    sql_existing = query_db('SELECT id, name FROM tags')
    clean_data = {i[1]: i[0] for i in sql_existing}
    sql_tags = 'INSERT INTO tags (name) VALUES (?)'
    sql_jointable = 'INSERT INTO maintag (tag_id, picture_id) VALUES (?, ?)'
    for i in tags:
        if i not in clean_data:
            tag_id = execute_db(sql_tags, (i,))
            clean_data[i] = tag_id
        execute_db(sql_jointable, (clean_data[i], picture_id, ))

# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #

# jinja routes -------------------------------------------------------------- #


@ app.before_request
def checkIfDeleted():
    # va vérifier que tous les fichiers enregistrés dans la bdd sont bien
    # existant dans le dossier upload. Si non, delete la ligne de la bdd.

    # mise en place --------------------------------------------------------- #
    rv = get_data(tab='pictures', args=('filename',))
    sql_request = 'DELETE FROM pictures WHERE filename = ?'
    # vérification ---------------------------------------------------------- #
    for i in rv:
        if not os.path.exists(app.config["UPLOAD_FOLDER"]+f'/{i["filename"]}'):
            execute_db(sql_request, (i["filename"],))


@ app.context_processor
def inject_menu():
    # rv = get_data(tab='categories', args=('id', 'name'))
    rv = get_data(tab='categories', args=('name',))

    return dict(menu=rv)


@ app.errorhandler(404)
def page_not_found(e):
    # gestion d'une page html personnalisée
    return render_template('404.html'), 404


@ app.route('/uploads/<name>')
def download_file(name):
    # vérifie l'intégrité des fichiers affichés
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

# index --------------------------------------------------------------------- #

# TODO:


@ app.route('/')
def index():
    # accéder à la db
    db = get_db()
    # selectionner les images de la table pictures
    display_pictures = db.execute("SELECT filename FROM pictures")
    # retourne des éléments de type sqlite => extraire avec fetchall
    results = display_pictures.fetchall()
    return render_template('index.html', all_pictures=results)

# search -------------------------------------------------------------------- #

# TODO:


@ app.route('/search')
def search_engine():
    data = request.args.to_dict()
    return render_template('index.html')

# show ---------------------------------------------------------------------- #

# TODO:


@ app.route("/gallery/<name>", methods=["GET", "POST"])
def show_pictures(name):
    db = get_db()
    cursor = db.execute(
        """SELECT upload_date, filename, name, description, category_id, id
           FROM pictures
           WHERE filename LIKE  ?""", ((name+'%'),))
    picture = cursor.fetchone()
    if picture is None:
        abort(404)
    cursor = db.execute(
        """SELECT comments.upload_date, content, author
           FROM comments
           INNER JOIN pictures
           ON comments.picture_id = pictures.id
           WHERE pictures.id = ?""", (picture[-1],))
    comment = cursor.fetchall()

    return render_template("show.html", image=picture, comments=comment)


# image upload -------------------------------------------------------------- #

@ app.route('/upload', methods=['GET', 'POST'])
def upload_picture():
    # jinja ----------------------------------------------------------------- #
    jinja_data = {}
    jinja_data['ok_ext'] = ALLOWED_EXTENSIONS
    jinja_data['categories'] = get_data(tab='categories', args=('name',))

    # cas 1: accès simple à la page ----------------------------------------- #
    if 'picture' not in request.files:
        return render_template('upload.html', data=jinja_data)

    # cas 2: un fichier est envoyé via le formulaire ------------------------ #
    else:
        # vérification selon paramètre(s)
        jinja_data['error'] = uber_validator(request, ['picture', 'name'])
        if jinja_data['error']:
            return render_template('upload.html', data=jinja_data)

        # transforme request.form > dict
        data = get_data(request, 'post_picture', 'pictures')

        # sauvegarde image dans la bdd & sur le serveur
        request.files['picture'].save(
            os.path.join(UPLOAD_FOLDER, data['filename']))
        sql_inject = ', '.join(list('?'*len(data.keys())))
        sql_request = f"""INSERT INTO pictures ({', '.join(data.keys())})
                          VALUES ({sql_inject})"""
        picture_id = execute_db(sql_request, tuple(data.values()))

        # infos image upload pour jinja
        jinja_data['picture_data'] = data

        # récupère & sauvegarde les tags de la description
        jinja_data['tags'] = extract_tags(data['description'])
        if jinja_data['tags']:
            inject_tags(jinja_data['tags'], picture_id)

    # affichage après upload ------------------------------------------------ #
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

# extract tags
