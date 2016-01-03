import math

import abc
import librosa
import numpy
import numpy.linalg as linalg
import sklearn.cluster as cluster
from math import sqrt
import engine.distance as distance


__author__ = 'dm'


class Engine(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractclassmethod
    def extract_signature(cls, track_data, track_rate):
        pass

    @classmethod
    @abc.abstractclassmethod
    def measure_similarity(cls, sig1, sig2):
        pass

    @classmethod
    @abc.abstractclassmethod
    def get_engine_identifier(cls):
        pass

    @classmethod
    def allows_metric_indexing(cls):
        return False

    @classmethod
    def get_partial_weights(cls):
        return {}


class CompoundEngine(Engine):
    @classmethod
    def get_engine_identifier(cls):
        pass

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        signature = {}
        for key in cls.get_components():
            engine_class, weight = cls.get_components()[key]
            signature.update(engine_class.extract_signature(track_data, track_rate))

        return signature


    @classmethod
    def measure_similarity(cls, sig1, sig2):
        similarity = {}
        for key in cls.get_components():
            engine_class, weight = cls.get_components()[key]
            sim = engine_class.measure_similarity(sig1, sig2)
            similarity[key] = sim

        return similarity

    @classmethod
    @abc.abstractmethod
    def get_components(cls):
        # Will return a dictionary of {'key': (EngineClass, weight)}
        pass

    @classmethod
    def get_partial_weights(cls):
        cps = cls.get_components()
        return {key: cps[key][1] for key in cps}


class UltimateEngine(CompoundEngine):
    @classmethod
    def get_components(cls):
        return {
            'mfcc' : (MandelEllisEngine, 160), # 160
            'zero_crossing' : (ZeroCrossingEngine, 2), # 2
            'spectral_contrast': (SpectralContrastEngine, 2), # 2
            'tempo': (TempogramEngine, 8) # 8
        }

    @classmethod
    def get_engine_identifier(cls):
        return "MalyValasek_Engine_v01"


class SpectralContrastEngine(Engine):
    @classmethod
    def extract_signature(cls, track_data, track_rate):
        sc = librosa.feature.spectral_contrast(track_data, track_rate)
        means = numpy.mean(sc, axis=1)
        covariance = numpy.cov(sc, rowvar=1)
        return {'sct_means': means, 'sct_covariance' : covariance}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        e1 = sig1['sct_covariance']  # Covariance matrix of distribution 1
        e2 = sig2['sct_covariance']  # Covariance matrix of distribution 2
        m1 = sig1['sct_means']
        m2 = sig2['sct_means']

        dist = distance.kl_divergence(m1, e1, m2, e2)
        '''dist = 0
        for i in range(len(m1)):
            dist += math.sqrt((m1[i] - m2[i])**2)'''

        return 1 / (1 + dist)

    @classmethod
    def get_engine_identifier(cls):
        return "SpectralContrast_Engine_v01"


class ZeroCrossingEngine(Engine):

    n_clusters = 16

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        zcr = librosa.feature.zero_crossing_rate(track_data)
        kmeans = cluster.KMeans(n_clusters=cls.n_clusters, precompute_distances=True, n_jobs=-1)
        labels = kmeans.fit_predict(zcr.T)

        all_means = numpy.zeros(cls.n_clusters)
        all_weights = numpy.zeros(cls.n_clusters)

        for i in range(cls.n_clusters):
            sample_indices = numpy.where(labels == i)[0]  # Indices of frames belonging to cluster i
            samples = zcr.T[sample_indices]  # The frames themselves
            all_means[i] = numpy.mean(samples)
            all_weights[i] = sample_indices.size

        return {'zcr_means' : all_means, 'zcr_weights' : all_weights}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        n_cols = cls.n_clusters
        dist_matrix = numpy.ndarray((cls.n_clusters, n_cols))

        sum_weights_1 = numpy.sum(sig1['zcr_weights'])
        sum_weights_2 = numpy.sum(sig2['zcr_weights'])

        if sum_weights_1 < sum_weights_2:  # Make sure sig1 is always the larger one (supply > demand)
            sig1, sig2 =  sig2, sig1

        for i in range(cls.n_clusters):
            for j in range(n_cols):
                dist_matrix[i][j] = sqrt((sig1['zcr_means'][i] - sig2['zcr_means'][j])**2)

        weights1 = numpy.copy(sig1['zcr_weights'])
        weights2 = numpy.copy(sig2['zcr_weights'])

        dist = distance.quadratic_chi_distance(weights1, weights2, dist_matrix)
        return 1 / (1 + dist)


    @classmethod
    def get_engine_identifier(cls):
        return "ZCR_engine_v01"


class SpectralCentroidEngine(Engine):

    n_clusters = 8

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        sc = librosa.feature.spectral_centroid(track_data, track_rate)
        kmeans = cluster.KMeans(n_clusters=cls.n_clusters, precompute_distances=True, n_jobs=-1)
        labels = kmeans.fit_predict(sc.T)

        all_means = numpy.zeros(cls.n_clusters)
        all_variances = numpy.zeros(cls.n_clusters)
        all_weights = numpy.zeros(cls.n_clusters)

        for i in range(cls.n_clusters):
            sample_indices = numpy.where(labels == i)[0]  # Indices of frames belonging to cluster i
            samples = sc.T[sample_indices]  # The frames themselves
            all_means[i] = numpy.mean(samples)
            all_variances[i] = numpy.var(samples)
            all_weights[i] = sample_indices.size

        return {'sc_means' : all_means, 'sc_weights' : all_weights, 'sc_variances': all_variances}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        n_cols = cls.n_clusters
        dist_matrix = numpy.ndarray((cls.n_clusters, n_cols))

        sum_weights_1 = numpy.sum(sig1['sc_weights'])
        sum_weights_2 = numpy.sum(sig2['sc_weights'])

        if sum_weights_1 < sum_weights_2:  # Make sure sig1 is always the larger one (supply > demand)
            sig1, sig2 =  sig2, sig1

        for i in range(cls.n_clusters):
            for j in range(n_cols):
                dist_matrix[i][j] = sqrt((numpy.log(sig1['sc_means'][i]) - numpy.log(sig2['sc_means'][j]))**2)

        weights1 = numpy.copy(sig1['sc_weights'])
        weights2 = numpy.copy(sig2['sc_weights'])

        dist = distance.quadratic_chi_distance(weights1, weights2, dist_matrix)

        sim = 1 / (1 + dist)
        if sim == numpy.nan or math.isnan(sim):
            return 0
        return sim



    @classmethod
    def get_engine_identifier(cls):
        return "SC_engine_v01"



class MandelEllisEngine(Engine):

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        harmonic_data = librosa.effects.harmonic(track_data)
        mfccs = librosa.feature.mfcc(harmonic_data, track_rate, n_mfcc=20)[1:]  # TODO: Back to no harmonic
        means = numpy.mean(mfccs, axis=1)
        covariance = numpy.cov(mfccs)
        return {'me_means': means, 'me_covariance': covariance}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        """
        Computes the symmetrized KL_divergence on two multivariate Gaussians.
        :param sig1: A tuple containing the signature of a multivariate Gaussian (means, covariance matrix).
        :param sig2: A tuple containing the signature of a multivariate Gaussian (means, covariance matrix).
        :return: The measure of KL divergence between the two Gaussians
        """
        e1 = sig1['me_covariance']  # Covariance matrix of distribution 1
        e2 = sig2['me_covariance']  # Covariance matrix of distribution 2
        m1 = sig1['me_means']
        m2 = sig2['me_means']
        d = len(m1)

        e1_inv = linalg.inv(e1)
        e2_inv = linalg.inv(e2)

        inv_trace = (numpy.dot(e2_inv, e1) + numpy.dot(e1_inv, e2)).trace()
        mean_product = numpy.dot(numpy.dot((m1 - m2).T, (e2_inv + e1_inv)), (m1 - m2))
        result = inv_trace - 2 * d + mean_product

        if result < 0:
            print("KL divergence is negative!!!")

        div = result / 2
        # return numpy.exp(-cls.gamma * div)
        return 1 / (1 + div)

    @classmethod
    def get_engine_identifier(cls):
        return "Mandel_Ellis_v01"


class LoganEngine(Engine):

    n_clusters = 8

    @classmethod
    def get_engine_identifier(cls):
        return "Logan_Engine_v01"

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        n_clusters = cls.n_clusters
        n_mfccs = 20
        mfccs = librosa.feature.mfcc(track_data, track_rate, n_mfcc=n_mfccs, hop_length=512)[1:]
        kmeans = cluster.KMeans(n_clusters=n_clusters, precompute_distances=True, n_jobs=-1)
        labels = kmeans.fit_predict(mfccs.T)

        all_means = numpy.ndarray((n_clusters, n_mfccs - 1))
        all_covs = numpy.ndarray((n_clusters, n_mfccs - 1, n_mfccs - 1))
        all_weights = numpy.ndarray(n_clusters)

        for i in range(n_clusters):
            sample_indices = numpy.where(labels == i)[0]  # Indices of frames belonging to cluster i
            samples = mfccs.T[sample_indices]  # The frames themselves

            cluster_mean = numpy.mean(samples, axis=0)  # 1D array
            cluster_covariance = numpy.cov(samples, rowvar=0)  # 2D array (should be 19 by 19)

            if linalg.matrix_rank(mfccs.T) < n_mfccs - 1:
                print("ERROR: cluster " + str(i) + " has rank only " + str(linalg.matrix_rank(mfccs.T)) + "!")

            if (linalg.eig(cluster_covariance)[0] < 0).any():
                print("ERROR: cluster " + str(i) + " has an indefinite covariance matrix!")

            all_means[i:] = cluster_mean
            all_covs[i:] = cluster_covariance
            all_weights[i] = sample_indices.size

        return {'means': all_means, 'covariances': all_covs, 'weights': all_weights}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        n_clusters = cls.n_clusters
        n_cols = n_clusters
        dist_matrix = numpy.ndarray((n_clusters, n_cols))

        sum_weights_1 = numpy.sum(sig1['weights'])
        sum_weights_2 = numpy.sum(sig2['weights'])

        if sum_weights_1 < sum_weights_2:  # Make sure sig1 is always the larger one (supply > demand)
            sig1, sig2 = sig2, sig1

        for i in range(n_clusters):
            for j in range(n_clusters):
                dist_matrix[i][j] = distance.kl_divergence(sig1['means'][i],
                                                           sig1['covariances'][i],
                                                           sig2['means'][j],
                                                           sig2['covariances'][j])

        weights1 = numpy.copy(sig1['weights'])
        weights2 = numpy.copy(sig2['weights'])

        emd = distance.earth_movers_distance(weights1, weights2, dist_matrix)
        return 1 / (1 + emd)


class TempogramEngine(Engine):

    win_length = 30

    @classmethod
    def get_engine_identifier(cls):
        return "Tempogram_Engine_v01"

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        win_length = cls.win_length
        onset_env = librosa.onset.onset_strength(track_data, track_rate)
        tempogram = librosa.feature.tempogram(sr=track_rate, onset_envelope=onset_env, win_length=win_length,
                                              hop_length=2048)

        means = numpy.mean(tempogram, axis=1)

        return {'tempogram_means': means}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        win_length = cls.win_length
        n_cols = win_length
        dist_matrix = numpy.ndarray((win_length, n_cols))
        means_1 = numpy.round(sig1['tempogram_means'] * 1000)
        means_2 = numpy.round(sig2['tempogram_means'] * 1000)

        sum_weights_1 = numpy.sum(means_1)
        sum_weights_2 = numpy.sum(means_2)

        if sum_weights_1 < sum_weights_2:  # Make sure sig1 is always the larger one (supply > demand)
            means_1, means_2 =  means_2, means_1

        for i in range(win_length):
            for j in range(n_cols):
                dist_matrix[i][j] = sqrt((i - j)**2)

        weights1 = numpy.copy(means_1)
        weights2 = numpy.copy(means_2)

        dist = distance.quadratic_chi_distance(weights1, weights2, dist_matrix)
        return 1 / (1 + dist)


class BeatEngine(Engine):
    @classmethod
    def euclidean_distance(cls, x, y):
        # obe rady se zarovnaji na stejnou delku, uz maji orezane tiche konce
        length = min(x.size, y.size)
        x_sliced = x[:length]
        y_sliced = y[:length]

        # vrati se euklid. vzdalenost mezi polema
        # return sqrt(sum(pow(a-b,2) for a, b in zip(x_sliced, y_sliced))) #nenormalizovana verze
        return sqrt(sum(pow(a - b, 2) for a, b in zip(x_sliced, y_sliced)) / pow(length, 2))

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        tempo, beats = librosa.beat.beat_track(y=track_data, sr=track_rate)

        return {'tempo': tempo, 'beats': beats}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        dist = cls.euclidean_distance(sig1['beats'] / sig1['tempo'], sig2['beats'] / sig2[
            'tempo'])  # puvodne se pronasobovalo tempem, ale vraci pak horsi vysledky
        similarity = 1 / (dist + 1)  # aby se pri stejnych songach nedelilo nulou, tak se pricita ta jednicka
        return similarity

    @classmethod
    def get_engine_identifier(cls):
        return "beatovaciEngine"