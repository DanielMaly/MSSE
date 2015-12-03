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
            return jsonify(result=process_search_results(search_results(path), sec_filename))

        else:
            return jsonify(result="You nit.")


@app.route('/play/data/wav/<path:path>')
def get_audio(path):
    return send_file(os.path.join('data', 'wav', path))


@app.route('/play/uploaded/<path:path>')
def get_uploaded_audio(path):
    return send_file(os.path.join('uploaded', path))


def process_search_results(results, uploaded_file):
    for result in results:
        print(result)

    ret = []
    for result in results:
        ret.append({
            "signature_file": result["signature"].path,
            "name": result["signature"].audio_track.name,
            "similarity": result["absolute_similarity"],
            "standardized_similarity": result["standardized_similarity"],
            "audio_url": audio_url_for_file(result["signature"].audio_track),
            "original_file": uploaded_file,
            "original_audio_url": audio_url_for_file(uploaded_file, uploaded=True)
        })
    return ret


def search_results(path):
    (data, rate) = librosa.load(path)
    return srch.search_greatest_similarity(data, rate, DEFAULT_ENGINE, DEFAULT_DATASET)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_UPLOAD_EXTENSIONS


def audio_url_for_file(audio_track, uploaded=False):

    if uploaded:
        wav_path = os.path.join(UPLOAD_FOLDER, audio_track)
    else:
        util.mkdir_p(os.path.join('data', 'wav'))
        wav_path = os.path.join('data', 'wav', str(audio_track.id) + ".wav")

    if not os.path.isfile(wav_path):
        data, rate = librosa.load(audio_track.path)
        librosa.output.write_wav(wav_path, data, rate)

    return os.path.join('play', wav_path)



if __name__ == '__main__':
    app.run(port=8000, debug=True)

