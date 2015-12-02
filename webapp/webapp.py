from flask import Flask
from flask import render_template, request, jsonify, send_file
import werkzeug.utils
import psycopg2
import os
import engine.search as srch
import librosa
import util
import engine.engine as engine

app = Flask(__name__)

#conn = psycopg2.connect(database="asse", user="asse", password="zabalenymotylek2015")
#cur = conn.cursor()

ALLOWED_UPLOAD_EXTENSIONS = {'mp3', 'wav', 'au'}
DEFAULT_DATASET = "genres"
DEFAULT_ENGINE = engine.MandelEllisEngine
UPLOAD_FOLDER = "uploaded"


@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            sec_filename = werkzeug.utils.secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, sec_filename)
            util.mkdir_p(UPLOAD_FOLDER)
            file.save(path)
            return jsonify(result=process_search_results(search_results(path)))

        else:
            return jsonify(result="You nit.")


@app.route('/play/data/audio/<path:path>')
def get_audio(path):
    return send_file(os.path.join('data', 'audio', path))


def process_search_results(results):
    for result in results:
        print(result)

    ret = []
    for result in results:
        ret.append({
            "signature_file": result["signature"].path,
            "name": result["signature"].audio_track.name,
            "similarity": result["absolute_similarity"],
            "standardized_similarity": result["standardized_similarity"],
            "audio_url": os.path.join('play', result["signature"].audio_track.path)
        })
    return ret


def search_results(path):
    (data, rate) = librosa.load(path)
    return srch.search_greatest_similarity(data, rate, DEFAULT_ENGINE, DEFAULT_DATASET)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_UPLOAD_EXTENSIONS


if __name__ == '__main__':
    app.run(port=8000, debug=True)

