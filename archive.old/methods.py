import sqlite3
from flask import (Flask, g)
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

# --------------------------------------------------------------------------- #
# tabs var                                                                    #
# --------------------------------------------------------------------------- #

templates = {
    'pictures': ['author', 'name', 'description', 'category_id'],
    'comments': ['author', 'content'],
    'tags': ['name']
}
tab_titles = {
    'pictures': ['id', 'upload_date', 'filename', 'author', 'name',
                 'description', 'category_id'],
    'comments': ['id', 'upload_date', 'author', 'content', 'picture_id'],
    'tags': ['id', 'name'],
    'maintag': ['id', 'tag_id', 'picture_id']
}
pairs = {'category_id': 'categories',
         "picture_id": 'pictures',
         'tag_id': 'tags'}

# --------------------------------------------------------------------------- #
# methods                                                                     #
# --------------------------------------------------------------------------- #


def get_db():
    """get the db or even a cursor using `cur = get_db.execute(query)`

    Returns:
        (db): database
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query: str, args=(), one=False):
    """execute a query in order to request some data.

    Args:
        query (str): need to be a complete `SELECT` query
        args (tuple, optional): values if the query has `?`. Defaults to ().
        one (bool, optional): `True` if only one value requested.
        Defaults to False.

    Returns:
        (tuple): all the values fetched using the query
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query: str, args=()):
    """exectute the db in case of a `POST` or a `PUT`.

    Args:
        query (str): `INSERT` type of query for e.g.
        args (tuple, optional): args if the query has `?`. Defaults to ().

    Returns:
        (int): return `cur.lastrowid`
    """
    cur = get_db().execute(query, args)
    get_db().commit()
    return cur.lastrowid


def get_data(
        tab: str, request=None, id: list = [],
        args=(),
        rules: list = []):
    """use this function if you need to get more complexe set of data from a
    request or by using fraction of informations
     except `rules` and `tab`, only use one of the other parameters.
    for now `rules` only works with `request`.

    Args:
        tab (str): primary table from where you get the data
        request (any, optional): send the request if you need to get
        informations from the form
        id (list, optional): use if you need to get all the informations from
        the db regarding specific id(s)
        args (tuple, optional): use if you need specific tabs, not the whole
        set of informations
        rules (list, optional): use a set of rules like `filename` in order
        to get information not given by a form

    Returns:
        (list, dict): return the set of data requested
    """
    # multiple elements ----------------------------------------------------- #
    # ? what use
    if args:
        query_values = ', '.join(list(args))
        sql_request = f'SELECT {query_values} FROM {tab}'
        rv = query_db(sql_request)
        clean_data = [{args[j]: i[j] for j in range(len(args))} for i in rv]

    # * ok
    elif id:
        tabs = templates[tab]
        query_values = ', '.join(list(tabs))
        sql_request = f'SELECT {query_values} FROM {tab} WHERE id = ?'
        # clean_data = [{tabs[i]:
        #                query_db(sql_request, (j,), one=True)
        #                for i in range(len(tabs))} for j in id]
        clean_data = query_db(sql_request, (id,), one=True)

    # one element ----------------------------------------------------------- #
    elif request:
        tabs = templates[tab]
        rv = list(request.form.values())
        clean_data = {tabs[i]: rv[i]
                      for i in range(len(rv))}

    # all data from a tab --------------------------------------------------- #
    else:
        tabs = tab_titles[tab]
        sql_request = f'SELECT * FROM {tab}'
        rv = query_db(sql_request)
        clean_data = [{tabs[i]: rv[j][i] for i in range(
            len(tabs))} for j in range(len(rv))]

    # specificities --------------------------------------------------------- #
    if 'upload_date' in rules:
        # add the timestamp to the dataset
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        clean_data['upload_date'] = timestamp
    if 'filename' in rules:
        # add the the new filename to the dataset
        clean_data['filename'] = renamePicture(request, tab)
    return clean_data


def convertData(data):
    """use this to convert some data, for the moment convert id to their
    equivalent if called.

    Args:
        data (any): the original data before conversion
    """
    liste = data if isinstance(data, list) else [data]
    for i in liste:
        for j in i:
            if '_id' in j:
                if str(i[j]).isalpha():
                    query = f'''SELECT id FROM {pairs[j]}
                            WHERE name = ?'''
                    i[j] = query_db(query, (i[j],), one=True)[0]
                elif str(i[j]).isnumeric():
                    query = f'''SELECT name FROM {pairs[j]}
                            WHERE id = ?'''
                    i[j] = query_db(query, (i[j],), one=True)[0]

    return data if isinstance(data, dict) else liste


def postData(data: dict, tab: str):
    """use this function in order to `POST` data in the database

    Args:
        data (dict): the set of data to inject
        tab (str): the destination tab for the `POST`

    Returns:
        (int): return the last injected item id
    """
    sql_inject = ', '.join(list('?'*len(data.keys())))
    sql_request = f"""INSERT INTO {tab}({', '.join(data.keys())})
                        VALUES({sql_inject})"""
    return execute_db(sql_request, tuple(data.values()))


def uberValidator(request, conditions: list):
    """verify the request with each conditions specified in the list.

    Args:
        request (request): the route request
        conditions (list): set of conditions, rules, to check

    Returns:
        (str): if there is an error, return a message
    """
    for i in conditions:
        if i == 'picture':
            filename = secure_filename(request.files['picture'].filename)
            if filename == '':
                return 'missing picture'
            elif filename[filename.index('.'):] not in ALLOWED_EXTENSIONS:
                return 'format not allowed'
        elif i == 'limit':
            lenght = len(request.form.get('content')) if request.form.get(
                'content') else len(request.form.get('description'))
            if lenght > 200:
                return 'content too long'
        elif not request.form[i]:
            return f'missing {i}'


def renamePicture(data: dict, table: str):
    """function used to return a new file name for any given picture
    according to it's table.

    Args:
        data (req): request from POST containing the picture
        table (str): name of the table use to check if already existing
        pictures have the same name.

    Returns:
        str: new name for the picture `'cat-1.jpg'` adding a number
    """
    filename = (
        ''.join((i for i in data.form['name'] if i.isalnum()))).lower()
    query = f'SELECT filename FROM {table} WHERE filename LIKE ?'
    number = str(len(query_db(query, (filename+'-%',))) + 1)
    actual_filename = secure_filename(data.files['picture'].filename)
    extension = actual_filename[actual_filename.index('.'):]
    return filename+'-'+number+extension


def extractTags(string: str, recurse=False):
    """recursive function use to extract all the  # from a
    comment or description

    Args:
        string(str): a string that might contain tags
        recurse(bool, optional): state define in the function,
        lighten the load of the function. Do not set to True beforehand.

    Returns:
        list: list containing all the extracted tags or an empty list
    """
    # clean ----------------------------------------------------------------- #
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
    return [tag[1:]] + extractTags(string[hash_pos+1:], recurse=True)


def injectTags(tags: list, picture_id: int):
    """inject in the join table and the tag categories the data

    Args:
        tags(list): list of tags
        picture_id(int): picture_id for the join table
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


def getMostPopular(tab: str, ft: str, fk: str, limit: int = None):
    """get elements ordered by some criterias, you can also set a limit to
    how many you need in the return
        e.g. pictures by number of comments, most popular tags

    Args:
        tab (str): the name of the primary tab
        ft (str): the name of the second table used
        fk (str): the foreign key linking the two tabs
        limit (int, optional): use if you need a limit in the output
        Defaults to None.

    Returns:
        (list): list of the items ordered
    """
    rv = get_data(tab, args=('id',))
    sql_request = f'SELECT COUNT(*) FROM {ft} WHERE {fk} = ?'
    occurences = {i['id']: query_db(
        sql_request, (i['id'],), one=True)[0] for i in rv}

    order = sorted(occurences, key=occurences.get, reverse=True)[:limit]
    return get_data(tab, id=order)
