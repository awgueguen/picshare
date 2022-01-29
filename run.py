import os
from flask import (Flask, g, render_template, request, flash, abort,
                   redirect, send_from_directory, url_for)
from methods import *

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
# routes                                                                      #
# --------------------------------------------------------------------------- #

# jinja routes -------------------------------------------------------------- #


@ app.before_request
def checkIfDeleted():
    # check if a picture have been deleted manualy. If so, delete the
    # corresponding entry in the database.
    rv = get_data('pictures', args=('filename',))
    sql_request = 'DELETE FROM pictures WHERE filename = ?'
    for i in rv:
        if not os.path.exists(app.config["UPLOAD_FOLDER"]+f'/{i["filename"]}'):
            execute_db(sql_request, (i["filename"],))


@ app.context_processor
def inject_menu():
    # create a menu variable accessible in order to get the list of categories
    # from anywhere
    rv = get_data('categories', args=('name',))
    return dict(menu=rv)


@ app.errorhandler(404)
def page_not_found(e):
    # route to give an explicit action to the 404 error
    return render_template('404.html'), 404


@ app.route('/uploads/<name>')
def download_file(name):
    # check if the image shown when accessing a route is not malicsious
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


# index --------------------------------------------------------------------- #

@ app.route('/')
def index():
    # CODE LUDOVIC ---------------------------------------------------------- #
    # accéder à la db
    db = get_db()
    # selectionner les images de la table pictures et les
    # trier selon date de téléchargement
    display_pictures = db.execute(
        """SELECT filename, name, author
           FROM pictures
           ORDER BY upload_date DESC""")
    # retourne des éléments de type sqlite => extraire avec fetchall
    results = display_pictures.fetchall()

    # perso ----------------------------------------------------------------- #
    rv = convertData(get_data('pictures'))
    jinja_data = {
        'pictures': sorted(rv, key=lambda rv: rv['upload_date'], reverse=True),
        'tags': getMostPopular('tags', 'maintag', 'tag_id', 5)
    }
    # - --------------------------------------------------------------------- #

    # TODO: perfect sizing images in gallery

    return render_template('index.html', all_pictures=results)


# search -------------------------------------------------------------------- #


@ app.route('/categories/<category_name>')
def categories(category_name):
    db = get_db()
    # CODE LUDOVIC ---------------------------------------------------------- #
    # l'utilisateur pourrait chercher une catégorie qui n'existe pas
    # empécher l'ppli de bugger avec un try/except
    sql = """SELECT filename, pictures.name, author FROM pictures
                INNER JOIN categories
                ON pictures.category_id = categories.id
                WHERE categories.name = ?
                ORDER BY upload_date DESC"""
    display_category = db.execute(sql, [category_name])
    # exécute la requête sql selon la variable catégorie_name
    # entrée par l'utilisateur
    results = display_category.fetchall()
    # si la catégorie n'existe pas il affiche indexerror
    # afficher une page non trouvée = erreur 404
    if results == []:
        abort(404)
    # comme c'est un élément sql on fetch tous les résultats
    # resultat sous forme de liste d'un tuple

    # PERSO ----------------------------------------------------------------- #
    rv = convertData(get_data('pictures'))
    if rv == []:
        abort(404)
    rv_f = list(filter(lambda x: (x['category_id'] == category_name), rv))
    jinja_data = {
        'pictures': sorted(rv_f, key=lambda x: x['upload_date'], reverse=True)
    }

    # - --------------------------------------------------------------------- #
    return render_template('index.html', all_pictures=results)


# show ---------------------------------------------------------------------- #


@ app.route("/gallery/<name>", methods=["GET", 'POST'])
def show_pictures(name):
    # CODE MIX -------------------------------------------------------------- #
    db = get_db()
    cursor = db.execute(
        """SELECT upload_date, filename, author,
           name, description, category_id, id
           FROM pictures
           WHERE filename LIKE  ?""", ((name+'%'),))
    picture = cursor.fetchone()
    if picture is None:
        abort(404)
    cursor = db.execute(
        """SELECT comments.upload_date, content, comments.author
           FROM comments INNER JOIN pictures
           ON comments.picture_id = pictures.id
           WHERE pictures.id = ?
           ORDER BY comments.upload_date DESC""", (picture[-1],))
    comments = cursor.fetchall()

    # POST ------------------------------------------------------------------ #
    maintags = query_db("""SELECT tags.name FROM tags
                           INNER JOIN maintag ON maintag.tag_id = tags.id
                           WHERE maintag.picture_id = ? """, (picture[-1],))
    if request.method == 'POST':
        error = uberValidator(request, ['author', 'content', 'limit'])
        if error:
            return render_template('show.html',
                                   image=picture,
                                   comments=comments,
                                   alert=error,
                                   picture_tags=maintags)
        comment = get_data('comments', request, rules=['upload_date'])
        comment['picture_id'] = picture[-1]
        postData(comment, 'comments')
    # TAGS ------------------------------------------------------------------ #
        tags = extractTags(comment['content'])
        if tags:
            injectTags(tags, comment['picture_id'])

        return redirect(url_for('show_pictures', name=name))

    # PERSO ----------------------------------------------------------------- #
    rv = convertData(get_data('pictures'))
    comments = get_data('comments')
    jinja_data = {
        'show': next(filter(lambda x: name in x['filename'], rv), None),
        'comments':  list(
            filter(lambda x:
                   (x['picture_id'] == jinja_data['show']['id']), comments))
    }
    if jinja_data['show'] is None:
        abort(404)

    # - --------------------------------------------------------------------- #
    return render_template("show.html",
                           image=picture,
                           comments=comments,
                           picture_tags=maintags)


# image upload -------------------------------------------------------------- #

@ app.route('/upload', methods=['GET', 'POST'])
def upload_picture():
    # jinja ----------------------------------------------------------------- #
    jinja_data = {
        'ok_ext': ALLOWED_EXTENSIONS,
        'categories': get_data('categories', args=('name',))
    }

    # cas 1: accès simple à la page ----------------------------------------- #
    if 'picture' not in request.files:
        return render_template('upload.html', data=jinja_data)

    # cas 2: un fichier est envoyé via le formulaire ------------------------ #
    # vérification selon paramètre(s)
    jinja_data['error'] = uberValidator(
        request, ['picture', 'name', 'author', 'limit'])
    if jinja_data['error']:
        return render_template('upload.html', data=jinja_data)

    # transforme request.form > dict avec les données de l'image
    data = get_data('pictures', request, rules=['upload_date', 'filename'])
    jinja_data['picture_data'] = convertData(data)

    # sauvegarde image dans la bdd & sur le serveur
    request.files['picture'].save(
        os.path.join(UPLOAD_FOLDER, data['filename']))
    picture_id = postData(data, 'pictures')

    # récupère & sauvegarde les tags de la description
    jinja_data['tags'] = extractTags(data['description'])
    if jinja_data['tags']:
        injectTags(jinja_data['tags'], picture_id)

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
