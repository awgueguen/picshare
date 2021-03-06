import os
from flask import g

# methods ------------------------------------------------------------------- #
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
from unidecode import unidecode

DATABASE = 'app.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']

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
    'picture': ['category_id', 'user_id', 'name', 'description',  'filename'],
    'tag': ['name'],
    'tagtopicture': ['tag_id', 'picture_id'],
    'user': ['name']
}

pairs = {'category_id': 'category',
         "picture_id": 'picture',
         'tag_id': 'tag',
         'user_id': 'user'}


# --------------------------------------------------------------------------- #
# db functions                                                                #
# --------------------------------------------------------------------------- #

def get_db():
    """Opens a new database connection if there is none yet.

    Returns:
        (db): database
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query: str, args=(), one: bool = False):
    """Queries the database and returns a list of dictionaries.

    Args:
        query (str): SQL query
        args (tuple, optional): arguments to be passed to the query
        one (bool, optional): whether to return one result or all

    Returns:
        (list): list of dictionaries
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return ([rv[0]] if rv else None) if one else rv


def update_db(table: str, args=()):
    """Updates the database.

    Args:
        table (str): table to be updated
        args (tuple, optional): arguments to be passed to the query

    Returns:
        (int): id of the updated row
    """
    tabs = post_tabs[table]
    sql_inject = ', '.join(list('?' * len(tabs)))
    sql_query = f'INSERT INTO {table}({", ".join(tabs)}) VALUES ({sql_inject})'
    cur = get_db().execute(sql_query, args)
    get_db().commit()
    return cur.lastrowid


# --------------------------------------------------------------------------- #
# fetch data functions                                                        #
# --------------------------------------------------------------------------- #

def get_data(table: str, id=()):
    """Gets data from the database.

    Args:
        table (str): table to be queried
        id (tuple, optional): id of the row to be queried

    Returns:
        (list): list of dictionaries
    """
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
    return [{tabs[i]: j[i] for i in range(len(tabs))} for j in rv]


# --------------------------------------------------------------------------- #
# modify data functions                                                       #
# --------------------------------------------------------------------------- #

def clean_data(table: str, method='', args=()):
    """Cleans the data from the database.

    Args:
        table (str): table to be queried
        method (str, optional): method of the request
        args (tuple, optional): arguments to be passed to the query

    Returns:
        (list): list of dictionaries
    """
    tabs = tabs_titles[table] if method == 'GET' else post_tabs[table]
    return [{tabs[i]: j[i]
             for i in range(len(tabs))} for j in args]


def convert_data(rv: list, method='GET'):
    """Converts the data from the database.

    Args:
        rv (list): list of dictionaries
        method (str, optional): method of the request

    Returns:
        (list): list of dictionaries
    """
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
    """Calculates the difference between the current date and the given date.

    Returns:
        (str): difference between the current date and the given date
    """
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


def rename_picture(request):
    """Renames the picture.

    Args:
        request (dict): request

    Returns:
        (str): new name of the picture
    """
    tmp_filename = request.form['name'].replace(' ', '-')
    filename = (
        ''.join((i for i in tmp_filename if
                 (i.isalnum() or i == '-')))).lower()
    query = 'SELECT filename FROM picture WHERE filename LIKE ?'
    number = str(len(query_db(query, (f'{filename}-%', ))) + 1)
    true_name, file_extension = os.path.splitext(
        secure_filename(request.files['picture'].filename))
    return f'{filename}-{number}{file_extension}'


# --------------------------------------------------------------------------- #
# misc functions                                                              #
# --------------------------------------------------------------------------- #

def validator(request, conditions: list):
    """Validates the request.

    Args:
        request (dict): request
        conditions (list): conditions to be checked

    Returns:
        (dict): contains the errors
    """
    error = {}
    values = request.form.to_dict()
    for i in values:
        if i in conditions:
            if values[i] == '':
                error[i] = ('This field is required')
            elif i == 'content':
                if len(values[i]) > 300:
                    error[i] = (
                        'This field must be less than 300 characters')
            elif i == 'description':
                if len(values[i]) > 300:
                    error[i] = (
                        'This field must be less than 300 characters')
            elif i == 'nickname':
                tmp_nickname = values[i].replace(" ", '')
                if len(tmp_nickname) > 20:
                    error[i] = ('Must be less than 20 characters')
                elif not tmp_nickname.isalpha():
                    error[i] = ('No special characters allowed')
            elif i == 'name':
                if len(values[i]) > 20:
                    error[i] = ('Must be less than 20 characters')
                elif not values[i].replace(' ', '').isalpha():
                    error[i] = ('No special characters allowed')

    if 'picture' in conditions:
        filename, file_extension = os.path.splitext(
            secure_filename(request.files['picture'].filename))
        if filename == '':
            error['picture'] = ('Missing picture')
        elif file_extension not in ALLOWED_EXTENSIONS:
            error['picture'] = ('Invalid file type')
    return error


def extract_tags(string: str, recurse=False):
    """Extracts the tags from the string.

    Args:
        string (str): string to be parsed
        recurse (bool, optional): whether in a recurse loop or not

    Returns:
        (list): list of tags
    """
    if recurse is False:
        allowed = [' ', '#']
        string = unidecode(string)
        string = ''.join([i for i in string if (i.isalnum() or i in allowed)])
        while '# ' in string:
            string = string.replace('# ', ' ')
        if len(string) == 1:
            string = ''
        else:
            while string[-1] == '#':
                string = string[:-1]

    if not string or '#' not in string:
        return []
    hash_pos = string.index('#')
    if ' ' in string[hash_pos:]:
        tag = string[hash_pos:string.index(' ', hash_pos)]
    else:
        tag = string[hash_pos:]
    tag_length = len(tag)
    return [tag.replace('#', '')] + extract_tags(
        string[tag_length:], recurse=True)


def inject_tags(tags: list, picture_id: int):
    """Injects the tags into the database.

    Args:
        tags (list): list of tags
        picture_id (int): id of the picture
    """
    sql_existing = query_db('SELECT id, name FROM tag')
    res = {i[1]: i[0] for i in sql_existing}
    for i in tags:
        pictures_tags = query_db(
            """SELECT tag_id, picture_id
               FROM tagtopicture WHERE picture_id = ?""", (picture_id,))
        if i not in res:
            tag_id = update_db('tag', (i,))
            res[i] = tag_id
        combinaison = (res[i], picture_id)
        if combinaison not in pictures_tags:
            update_db('tagtopicture', (res[i], picture_id, ))
