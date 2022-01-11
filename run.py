import os
import sqlite3
from flask import (Flask, g, render_template, request,
                   redirect, send_from_directory)
from werkzeug.utils import secure_filename

app = Flask(__name__)
DATABASE = 'app.db'
UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/')
def index():
    db = get_db()
    pictures = db.execute("SELECT filename FROM pictures")
    return render_template('index.html', all_pictures=pictures)


@app.route('/', methods=['POST'])
def create():
    # permet de vérifier que le fichier n'est pas vide
    if 'file' not in request.files:
        return redirect('/')
    file = request.files['file']
    # permet de vérifier que le nom n'est pas vulnérable
    filename = secure_filename(file.filename)
    # permet de vérifier que le nom n'est pas vide
    if filename != '':
        # permet de récupérer l'image du form // request.form
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        # os.path.join permet de récupérer le nom du ficher et de la position
        db = get_db()
        db.execute("INSERT INTO pictures (filename) VALUES (?)",
                   (filename, ))
        db.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
