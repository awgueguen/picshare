import os
from flask import (Flask, g, request, render_template, abort,
                   redirect, send_from_directory, url_for, flash)

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
    'comment': ['id', 'timestamp', 'content', 'user_id', 'picture_id'],
    'tag': ['id', 'name'],
    'tagtopicture': ['id', 'tag_id', 'picture_id'],
    'user': ['id', 'name']
}

post_tabs = {
    'comment': ['content', 'user_id', 'picture_id'],
    'picture': ['filename', 'description', 'user_id', 'category_id'],
    'tag': ['name'],
    'tagtopicture': ['tag_id', 'picture_id'],
    'user': ['name']
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


def update_db(table: str, args=()):
    tabs = post_tabs[table]
    sql_inject = ', '.join(list('?' * len(tabs)))
    sql_query = f'INSERT INTO {table}({", ".join(tabs)}) VALUES ({sql_inject})'
    cur = get_db().execute(sql_query, args)
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


def clean_data(table, method='', args=()):
    tabs = tabs_titles[table] if method == 'GET' else post_tabs[table]
    return [{tabs[i]: j[i]
             for i in range(len(tabs))} for j in args]


def convert_data(rv: list, method='GET'):
    for i in rv:
        for j in i:
            if ('_id' in j) and (j != "picture_id"):
                if str(i[j]).isalpha():
                    query = f'''SELECT id FROM {pairs[j]}
                            WHERE name = ?'''
                    if query_db(query, (i[j],), one=True):
                        i[j] = query_db(query, (i[j],), one=True)[0][0]
                    elif j == 'user_id':
                        i[j] = update_db('user', (i[j],))
                elif str(i[j]).isnumeric() and method == 'GET':
                    query = f'''SELECT name FROM {pairs[j]}
                            WHERE id = ?'''
                    i[j] = query_db(query, (i[j],), one=True)[0][0]
        if "upload_date" in i:
            i['upload_date'] = datetime.strptime(
                i['upload_date'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
        elif "timestamp" in i:
            i['date_difference'] = date_difference(i['timestamp'])
    return rv


def date_difference(date):
    date_now = datetime.now()
    delta = date_now - datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    if delta.days < 1:
        value = delta.seconds//60
        return f'{value} minute{"s" if value > 1 else ""} ago'
    elif delta.days < 7:
        value = delta.days
        return f'{value} day{"s" if value > 1 else ""} ago'
    elif delta.days < 30:
        value = delta.days//7
        return f'{value} week{"s" if value > 1 else ""} ago'
    elif delta.days < 365:
        value = delta.days//30
        return f'{value} month{"s" if value > 1 else ""} ago'
    else:
        value = delta.days//365
        return f'{value} year{"s" if value > 1 else ""} ago'


def validator(request, conditions: list):
    error = {}
    values = request.form.to_dict()
    for i in values:
        if i in conditions:
            if values[i] == '':
                error[i] = ('This field is required')
            elif i == 'picture':
                filename = secure_filename(request.files['picture'].filename)
                if filename == '':
                    error[i] = ('Missing picture')
                elif filename[filename.index('.'):] not in ALLOWED_EXTENSIONS:
                    error[i] = ('Invalid file type')
            elif i == 'content':
                if len(values[i]) > 300:
                    error[i] = (
                        'This field must be less than 300 characters')
            elif i == 'description':
                if len(values[i]) > 300:
                    error[i] = (
                        'This field must be less than 300 characters')
            elif i == 'nickname':
                if len(values[i]) > 20:
                    error[i] = (
                        'Must be less than 20 characters')
            elif i == 'name':
                if len(values[i]) > 20:
                    error[i] = (
                        'Must be less than 20 characters')
    return error


def extract_tags(string: str, recurse=False):
    if recurse is False:
        allowed = [' ', '#']
        string = unidecode(string)
        string = ''.join([i for i in string if (i.isalnum() or i in allowed)])
        while '# ' in string:
            string = string.replace('# ', ' ')
        while string[-1] == '#':
            string = string[:-1]

    if not string or '#' not in string:
        return []
    hash_pos = string.index('#')
    if ' ' in string[hash_pos:]:
        tag = string[hash_pos:string.index(' ', hash_pos)]
    else:
        tag = string[hash_pos:]
    return [tag[1:]] + extract_tags(string[hash_pos+1:], recurse=True)


def inject_tags(tags: list, picture_id: int):
    sql_existing = query_db('SELECT id, name FROM tag')
    clean_data = {i[1]: i[0] for i in sql_existing}
    sql_join = 'INSERT INTO tagtopicture (tag_id, picture_id) VALUES (?, ?)'
    for i in tags:
        if i not in clean_data:
            tag_id = update_db('tag', (i,))
            clean_data[i] = tag_id
        update_db('tagtopicture', (clean_data[i], picture_id, ))

# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #

# life cycle ---------------------------------------------------------------- #


@ app.before_request
def check_if_image_missing():
    rv = get_data('picture')
    sql_request = 'DELETE FROM picture WHERE filename = ?'
    for i in rv:
        if not os.path.exists(app.config["UPLOAD_FOLDER"]+f'/{i["filename"]}'):
            update_db(sql_request, (i["filename"],))


@ app.context_processor
def menu_creator():
    rv = get_data('category')
    menu = list(map(lambda x: x['name'], rv))
    return dict(menu=menu)


@ app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@ app.route('/uploads/<name>')
def secure_file(name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], name)


# index --------------------------------------------------------------------- #

@ app.route('/')
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

@ app.route('/categories/<name>')
def categories(name):
    if request.args.get('tag'):
        all_tags = convert_data(get_data('tagtopicture'))
        tag = list(filter(lambda x: (x['tag_id'] == name), all_tags))
        tag_list = list(map(lambda x: x['picture_id'], tag))
        print(tag_list)
        rv = convert_data(get_data('picture'))
        pictures = list(filter(lambda x: (x['id'] in tag_list), rv))
    else:
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
        'error': '',
        'picture': rv[0],
        'comments': sorted(list(
            filter(lambda x: (x['picture_id'] == id), comments)),
            key=lambda x: x['timestamp'], reverse=True),
        'tags': list(filter(lambda x: (x['picture_id'] == id), tags)),
    }

    # POST ------------------------------------------------------------------ #
    if request.method == 'POST':
        error = validator(request, ['content', 'nickname'])
        if error:
            JINJA_DATA['error'] = error
            return render_template('show.html', **JINJA_DATA,
                                   scroll="show--form")

        rv = [tuple(request.form.values()) + (id,)]
        res = convert_data(clean_data('comment', 'POST', rv))
        args = tuple(res[0].values())
        update_db('comment', args)

    # TAGS ------------------------------------------------------------------ #
        tags = extract_tags(res[0]['content'])
        print(tags)
        if tags:
            inject_tags(tags, id)

        return redirect(url_for('show_picture', _anchor="show--form",
                                name=name))

    return render_template('show.html', **JINJA_DATA)
