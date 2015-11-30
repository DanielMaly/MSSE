__author__ = 'dm'

import glob
import sys

import engine.engine as engine
import librosa
import numpy
import os
import util
import db.database as database


def save_signature(signature, path):
    """
    Saves a signature of a multivariate Gaussian to a file
    :param signature: Tuple (means, covariance matrix)
    :param path: Path to save to
    :return:
    """
    numpy.savez(path, **signature)


def get_all_files_in_tree(dir_path):
    return glob.glob(os.path.join(dir_path, "**/*.*"))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 preprocess.py source_audioset engine_class")
        exit()

    dir_name = os.path.join("data", "audio", sys.argv[1])

    engine_class = getattr(engine, sys.argv[2])

    # Save the engine
    engine_model = database.EngineModel.query.filter_by(clazz=engine_class.get_engine_identifier()).first()
    if engine_model is None:
        engine_model = database.EngineModel(engine_class.get_engine_identifier())
        database.db.session.add(engine_model)

    signatureset_identifier = engine_class.get_engine_identifier()
    dest_dir = os.path.join("data", "signatures", sys.argv[1], signatureset_identifier)

    # Save the dataset
    dataset = database.Dataset.query.filter_by(name=sys.argv[1]).first()
    if dataset is None:
        dataset = database.Dataset(sys.argv[1])
        database.db.session.add(dataset)

    # Find audio files in tree
    util.mkdir_p(dest_dir)
    print("Looking for audio files in " + dir_name)
    filenames = get_all_files_in_tree(dir_name)
    print("Found " + str(len(filenames)) + " audio files.")
    i = 0

    for filename in filenames:
        # Save the track
        track = database.AudioTrack.query.filter_by(path=filename).first()
        if track is None:
            track = database.AudioTrack(os.path.splitext(os.path.basename(filename))[0], filename, dataset)
            database.db.session.add(track)

        data, rate = librosa.load(filename)
        sig = engine_class.extract_signature(data, rate)

        rel_path = os.path.relpath(filename, dir_name)
        dest_path = os.path.join(dest_dir, rel_path)
        dest_parent = os.path.dirname(dest_path)
        util.mkdir_p(dest_parent)

        print("Processing file " + filename + ", will save to " + dest_path)
        save_signature(sig, dest_path)

        # Save the signature
        track_signature = database.TrackSignature.query.filter_by(engine_model=engine_model, audio_track=track).first()
        if track_signature is None:
            track_signature = database.TrackSignature(dest_path, engine_model, track)
            database.db.session.add(track_signature)

        i += 1
        print("Progress: " + str(i*100/len(filenames)) + "%")

    database.db.session.commit()
