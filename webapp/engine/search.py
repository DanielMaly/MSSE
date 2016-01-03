__author__ = 'dm'

import os
import heapq
import numpy
import scipy.stats as stats
import db.database as db
import engine.engine as engine

SIGNATURE_PARENT_DIR = os.path.join("data", "signatures")


class Similarity:
    def __init__(self, signature, similarity_measure):
        self.signature = signature
        self.similarity_measure = similarity_measure

    def __lt__(self, other):
        return self.similarity_measure < other.similarity_measure


def search_greatest_similarity(data, rate, engine_classname, dataset_id, signature_dir=SIGNATURE_PARENT_DIR, n_tracks=10):
    engine_class = getattr(engine, engine_classname)
    sig_track = engine_class.extract_signature(data, rate)
    signatures = db.TrackSignature.query.filter(db.TrackSignature.audio_track.has(dataset_name=dataset_id))\
        .filter_by(engine_class=engine_classname)

    h = []
    similarities = []
    for signature_record in signatures:
        sig_file = signature_record.path + ".npz"
        signature = numpy.load(sig_file)

        print("measuring similarity with track " + signature_record.audio_track.name)
        similarity_measure = engine_class.measure_similarity(sig_track, signature)
        print("similarity is " + str(similarity_measure))

        sim_object = Similarity(signature_record, similarity_measure)
        similarities.append(sim_object)

    similarities = normalize_similarities(similarities, engine_class)

    for sim_object in similarities:
        if len(h) < n_tracks:
            heapq.heappush(h, sim_object)

        elif sim_object > h[0]:
            heapq.heappushpop(h, sim_object)

    h.sort()
    h = h[::-1]

    ret = []
    for s in h:
        ret.append({
            "absolute_similarity": s.similarity_measure,
            "signature": s.signature
        })

    return ret


def normalize_similarities(similarities, engine_class):
    if isinstance(similarities[0].similarity_measure, dict):
        # For every key in the dictionary, make minimum, maximum and range
        weights = engine_class.get_partial_weights()
        weight_sum = numpy.sum([weights[k] for k in weights])
        for key in weights:
            print("Normalizing " + key)
            all_meaures = [s.similarity_measure[key] for s in similarities]
            am_max = numpy.amax(all_meaures)
            am_min = numpy.amin(all_meaures)
            print("am_max: " + str(am_max) + "\t am_min: " + str(am_min))
            sorted_measures = sorted(all_meaures)
            for s in similarities:
                # s.similarity_measure[key] = ((s.similarity_measure[key] - am_min) / (am_max - am_min))\
                s.similarity_measure[key] = (sorted_measures.index(s.similarity_measure[key]) / len(sorted_measures))\
                                            * weights[key] / weight_sum
                if s.similarity_measure[key] == numpy.nan:
                    s.similarity_measure[key] = 0

        numpy.savez("similarities", similarities)
        for s in similarities:
            s.similarity_measure = numpy.sum([s.similarity_measure[key] for key in s.similarity_measure])

    return similarities
