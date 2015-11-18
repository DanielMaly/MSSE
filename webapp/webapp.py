from flask import Flask
from flask import render_template, request, jsonify
import werkzeug
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(database="asse", user="asse", password="zabalenymotylek2015")
cur = conn.cursor()

ALLOWED_UPLOAD_EXTENSIONS = {'mp3', 'wav'}
DEFAULT_DATASET = "genres"


@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            sec_filename = sec
            return jsonify(result="Got your file okay")
        else:
            return jsonify(result="You nit.")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_UPLOAD_EXTENSIONS


if __name__ == '__main__':
    app.run(port=8000, debug=True)
