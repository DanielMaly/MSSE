__author__ = 'dm'

import numpy
import glob
import os
import sys
import librosa
import util
import engine.engine as engine

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
    if len(sys.argv) != 4:
        print("Usage: python3 preprocess.py src_dir dest_dir engine_class")
        exit()

    dir_name = os.path.join("data", "audio", sys.argv[1])

    engine_class = getattr(engine, sys.argv[3])

    signatureset_identifier = engine_class.get_engine_identifier()
    dest_dir = os.path.join(sys.argv[2], signatureset_identifier)

    util.mkdir_p(dest_dir)

    filenames = get_all_files_in_tree(dir_name)
    i = 0
    for filename in filenames:
        data, rate = librosa.load(filename)
        sig = engine_class.extract_signature(data, rate)

        rel_path = os.path.relpath(filename, dir_name)
        dest_path = os.path.join(dest_dir, rel_path)
        dest_parent = os.path.dirname(dest_path)
        util.mkdir_p(dest_parent)

        print("Processing file " + filename + ", will save to " + dest_path)
        save_signature(sig, dest_path)

        i += 1
        print("Progress: " + str(i*100/len(filenames)) + "%")
