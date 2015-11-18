__author__ = 'dm'

import os
import glob
import heapq
import numpy

SIGNATURE_PARENT_DIR = os.path.join("data", "similarity")


def search_greatest_similarity(data, rate, engine_class, dataset_id, signature_dir=SIGNATURE_PARENT_DIR, n_tracks=10):
    sig_track = engine_class.extract_signature(data, rate)
    signature_path = os.path.join(SIGNATURE_PARENT_DIR, dataset_id, engine_class.get_engine_identifier())
    signature_files = glob.iglob(os.path.join(signature_path, "**/*.*"))

    h = []
    for sig_file in signature_files:
        signature = numpy.load(sig_file)
        similarity = engine_class.measure_similarity(sig_track, signature)
        print("Computed similarity for file " + sig_file + ", it is " + str(similarity))

        if len(h) < n_tracks:
            heapq.heappush(h, (similarity, sig_file))

        elif similarity > h[0][0]:
            heapq.heappushpop(h, (similarity, sig_file))

    h.sort()
    return h