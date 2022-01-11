from flask import Flask, render_template

app = Flask(__name__)

# route --------------------------------------------------------------------- #


@app.route("/")
def index():
    todo_list = ['Create HTML file',
                 'Add route for pictures', 'Upload pictures']
    return render_template("index.html", subtitle='helllo friennnnds',
                           title="you suck", list_items=todo_list)


if __name__ == '__main__':
    app.run(debug=True)
