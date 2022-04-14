import os
from flask import (Flask, g, request, render_template, abort,
                   redirect, send_from_directory, url_for)
from methods import *

# --------------------------------------------------------------------------- #
# global setup                                                                #
# --------------------------------------------------------------------------- #

DATABASE = 'app.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.add_url_rule('/uploads/<path:filename>',
                 endpoint='uploads', view_func=app.send_static_file)


# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #

# life cycle ---------------------------------------------------------------- #


@ app.before_request
def check_if_image_missing():
    """Checks if the image is missing. If it is missing,
       deletes the picture in the database."""
    rv = get_data('picture')
    sql_request = 'DELETE FROM picture WHERE filename = ?'
    for i in rv:
        if not os.path.exists(app.config["UPLOAD_FOLDER"]+f'/{i["filename"]}'):
            print(f'{i["filename"]} is missing')
            get_db().execute(sql_request, (i["filename"],))
            get_db().commit()


@ app.context_processor
def menu_creator():
    """Creates the menu."""
    rv = get_data('category')
    menu = list(map(lambda x: x['name'], rv))
    return dict(menu=menu)


@ app.errorhandler(404)
def page_not_found(error):
    """Handles the 404 error."""
    return render_template('404.html'), 404


@ app.route('/uploads/<name>')
def secure_file(name):
    """This is a route that is used to serve the uploaded files."""

    return send_from_directory(app.config['UPLOAD_FOLDER'], name)


# index --------------------------------------------------------------------- #

@ app.route('/')
def index():
    """Renders the index page."""
    # fetch data ------------------------------------------------------------ #
    pictures = get_data('picture')
    pictures_sorted = sorted(pictures, key=lambda x: x['upload_date'],
                             reverse=True)
    pictures = convert_data(pictures_sorted)
    # fetch tags ------------------------------------------------------------ #
    tags = convert_data(get_data('tagtopicture'))
    tags_by_picture = {
        i['id']: list(filter(lambda x: x['picture_id'] == i['id'],
                             tags)) for i in pictures
    }
    # render ---------------------------------------------------------------- #
    JINJA_DATA = {
        'pictures': pictures,
        'tags': tags_by_picture
    }

    return render_template('index.html', **JINJA_DATA)


# categories ---------------------------------------------------------------- #

@ app.route('/categories/<name>')
def categories(name):
    """Renders the categories page."""
    # first case: tag ------------------------------------------------------- #
    if request.args.get('tag'):
        all_tags = convert_data(get_data('tagtopicture'))
        tag = list(filter(lambda x: (x['tag_id'] == name), all_tags))
        tag_list = list(map(lambda x: x['picture_id'], tag))

        rv = get_data('picture')
        pictures = list(filter(lambda x: (x['id'] in tag_list), rv))
        pictures_sorted = sorted(pictures, key=lambda x: x['upload_date'],
                                 reverse=True)
        pictures = convert_data(pictures_sorted)

    # second case: category ------------------------------------------------- #
    else:
        rv = get_data('picture')
        pictures_sorted = sorted(rv, key=lambda x: x['upload_date'],
                                 reverse=True)
        pictures_tmp = convert_data(pictures_sorted)
        pictures = list(
            filter(lambda x: (x['category_id'] == name), pictures_tmp))

    if pictures == []:
        abort(404)

    tags = convert_data(get_data('tagtopicture'))
    tags_by_picture = {
        i['id']: list(filter(lambda x: x['picture_id'] == i['id'],
                             tags)) for i in pictures
    }

    # render ---------------------------------------------------------------- #
    JINJA_DATA = {
        'pictures': pictures,
        'tags': tags_by_picture
    }

    return render_template('index.html', **JINJA_DATA)


# show ---------------------------------------------------------------------- #

@ app.route("/gallery/<name>", methods=["GET", "POST"])
def show_picture(name):
    """Renders the show page."""
    rv = convert_data(get_data('picture', id=(f'{name}%', 'filename')))
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
        if error := validator(request, ['content', 'nickname']):
            JINJA_DATA['error'] = error
            return render_template('show.html', **JINJA_DATA,
                                   scroll="show--form")

        rv = [tuple(request.form.values()) + (id,)]
        res = convert_data(clean_data('comment', 'POST', rv))
        args = tuple(res[0].values())
        update_db('comment', args)
        if tags := extract_tags(res[0]['content']):
            inject_tags(tags, id)

        return redirect(url_for('show_picture', _anchor="show--form",
                                name=name))

    return render_template('show.html', **JINJA_DATA)


# image upload -------------------------------------------------------------- #
@ app.route('/upload', methods=['GET', 'POST'])
def upload_picture():
    """Renders the upload page."""
    JINJA_DATA = {
        'error': '',
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'categories': convert_data(get_data('category')),
    }

    # display without POST -------------------------------------------------- #
    if 'picture' not in request.files:
        return render_template('upload.html', **JINJA_DATA)

    # POST ------------------------------------------------------------------ #
    JINJA_DATA['error'] = validator(
        request, ['picture', 'name', 'nickname', 'description'])
    print(JINJA_DATA['error'])
    if JINJA_DATA['error']:
        return render_template('upload.html', **JINJA_DATA,
                               scroll="upload--form")

    # request.form to dict with image data
    rv = [tuple(request.form.values()) + (rename_picture(request),)]
    res = convert_data(clean_data('picture', 'POST', rv))
    JINJA_DATA['picture'] = res[0]

    # insert picture into database & on the server
    request.files['picture'].save(
        os.path.join(UPLOAD_FOLDER, res[0]['filename']))

    args = tuple(res[0].values())
    picture_id = update_db('picture', args)

    # tags ------------------------------------------------------------------ #
    if tags := extract_tags(res[0]['description']):
        inject_tags(tags, picture_id)

    return redirect(url_for('index'))


# test ---------------------------------------------------------------------- #
if __name__ == '__main__':
    app.run(debug=True)
