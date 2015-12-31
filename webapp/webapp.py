from flask import Flask
from flask import render_template, request, jsonify, send_file
import werkzeug.utils
import os
import engine.search as srch
import librosa
import util
import engine.engine as engine
import db.database as db

app = Flask(__name__)

ALLOWED_UPLOAD_EXTENSIONS = {'mp3', 'wav', 'au'}
DEFAULT_DATASET = "genres"
DEFAULT_ENGINE = "BeatEngine"
UPLOAD_FOLDER = "uploaded"


@app.route('/')
def homepage():
    datasets = db.Dataset.query.all()
    engines = db.EngineModel.query.all()
    return render_template('index.html', datasets=datasets, engines=engines)


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            sec_filename = werkzeug.utils.secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, sec_filename)
            util.mkdir_p(UPLOAD_FOLDER)
            file.save(path)
            search_result_list = search_results(path, engine=request.form['engine'],
                                                      dataset=request.form['dataset'])
            return jsonify(process_search_results(search_result_list, sec_filename))
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

    h, ret = [], {}
    for result in results:
        h.append({
            "signature_file": result["signature"].path,
            "name": result["signature"].audio_track.name,
            "similarity": "{0:.4f}".format(result["absolute_similarity"]),
            "standardized_similarity": result["standardized_similarity"],
            "audio_url": audio_url_for_file(result["signature"].audio_track)
        })

    ret['original_file'] = uploaded_file
    ret['original_audio_url'] = audio_url_for_file(uploaded_file, uploaded=True)
    ret['results'] = h
    return ret


def search_results(path, dataset=DEFAULT_DATASET, engine=DEFAULT_ENGINE):
    (data, rate) = librosa.load(path)
    return srch.search_greatest_similarity(data, rate, engine, dataset)


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

