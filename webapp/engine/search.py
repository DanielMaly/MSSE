__author__ = 'dm'

import os
import heapq
import numpy
import scipy.stats as stats
import db.database as db

SIGNATURE_PARENT_DIR = os.path.join("data", "signatures")


class Similarity:
    def __init__(self, signature, similarity_measure):
        self.signature = signature
        self.similarity_measure = similarity_measure

    def __lt__(self, other):
        return self.similarity_measure < other.similarity_measure


def search_greatest_similarity(data, rate, engine_class, dataset_id, signature_dir=SIGNATURE_PARENT_DIR, n_tracks=10):
    sig_track = engine_class.extract_signature(data, rate)
    signatures = db.TrackSignature.query.filter(db.TrackSignature.audio_track.has(dataset_name=dataset_id))\
        .filter_by(engine_class=engine_class.get_engine_identifier())

    h = []
    sim_vector = []
    for signature_record in signatures:
        sig_file = signature_record.path + ".npz"
        signature = numpy.load(sig_file)
        similarity_measure = engine_class.measure_similarity(sig_track, signature)
        sim_vector.append(similarity_measure)
        sim_object = Similarity(signature_record, similarity_measure)

        if len(h) < n_tracks:
            heapq.heappush(h, sim_object)

        elif sim_object > h[0]:
            heapq.heappushpop(h, sim_object)

    h.sort()
    h = h[::-1]
    sim_vector_np = numpy.array(sim_vector)
    mn = numpy.mean(sim_vector_np)
    sd = numpy.std(sim_vector_np)

    ret = []
    for s in h:
        ret.append({
            "absolute_similarity": s.similarity_measure,
            "standardized_similarity": stats.chi2.cdf(s.similarity_measure, 5, mn, sd),
            "signature": s.signature
        })

    return ret