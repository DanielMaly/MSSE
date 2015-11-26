__author__ = 'dm'

import os
import glob
import heapq
import numpy
import scipy.stats as stats

SIGNATURE_PARENT_DIR = os.path.join("data", "signatures")


def search_greatest_similarity(data, rate, engine_class, dataset_id, signature_dir=SIGNATURE_PARENT_DIR, n_tracks=10):
    sig_track = engine_class.extract_signature(data, rate)
    signature_path = os.path.join(SIGNATURE_PARENT_DIR, dataset_id, engine_class.get_engine_identifier())
    signature_files = glob.iglob(os.path.join(signature_path, "**/*.*"))

    h = []
    sim_vector = []
    for sig_file in signature_files:
        signature = numpy.load(sig_file)
        similarity = engine_class.measure_similarity(sig_track, signature)
        sim_vector.append(similarity)

        if len(h) < n_tracks:
            heapq.heappush(h, (similarity, sig_file))

        elif similarity > h[0][0]:
            heapq.heappushpop(h, (similarity, sig_file))

    h.sort()
    h = h[::-1]
    sim_vector_np = numpy.array(sim_vector)
    mn = numpy.mean(sim_vector_np)
    sd = numpy.std(sim_vector_np)

    ret = []
    for s in h:
        ret.append({
            "absolute_similarity": s[0],
            "standardized_similarity": stats.chi2.cdf(s[0], 5, mn, sd),
            "signature_file": s[1]
        })

    return ret