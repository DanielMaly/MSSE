from flask.json import load
from numpy.lib.scimath import log

__author__ = 'dm'

import abc
import librosa
import numpy
import numpy.linalg as linalg
import sklearn.cluster as cluster
from math import sqrt
import pulp


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


class MandelEllisEngine(Engine):
    gamma = 0.068

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        mfccs = librosa.feature.mfcc(track_data, track_rate, n_mfcc=20)[1:]
        means = numpy.mean(mfccs, axis=1)
        covariance = numpy.cov(mfccs)
        return {'means': means, 'covariance': covariance}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        """
        Computes the symmetrized KL_divergence on two multivariate Gaussians.
        :param sig1: A tuple containing the signature of a multivariate Gaussian (means, covariance matrix).
        :param sig2: A tuple containing the signature of a multivariate Gaussian (means, covariance matrix).
        :return: The measure of KL divergence between the two Gaussians
        """
        e1 = sig1['covariance']  # Covariance matrix of distribution 1
        e2 = sig2['covariance']  # Covariance matrix of distribution 2
        m1 = sig1['means']
        m2 = sig2['means']
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
    @classmethod
    def get_engine_identifier(cls):
        return "Logan_Engine_v01"

    @classmethod
    def extract_signature(cls, track_data, track_rate):
        n_clusters = 12
        n_mfccs = 20
        mfccs = librosa.feature.mfcc(track_data, track_rate, n_mfcc=n_mfccs, hop_length=256)[1:]
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
            all_means[i:] = cluster_mean
            all_covs[i:] = cluster_covariance
            all_weights[i] = sample_indices.size

        return {'means': all_means, 'covariances': all_covs, 'weights': all_weights}

    @classmethod
    def measure_similarity(cls, sig1, sig2):
        n_clusters = 12
        n_cols = n_clusters
        dist_matrix = numpy.ndarray((n_clusters, n_cols))

        sum_weights_1 = numpy.sum(sig1['weights'])
        sum_weights_2 = numpy.sum(sig2['weights'])

        if sum_weights_1 < sum_weights_2:  # Make sure sig1 is always the larger one (supply > demand)
            sig1, sig2 = sig2, sig1

        for i in range(n_clusters):
            for j in range(n_clusters):
                dist_matrix[i][j] = cls.kl_divergence(sig1['means'][i],
                                                      sig2['means'][j],
                                                      sig1['covariances'][i],
                                                      sig2['covariances'][j])

        flow_sum = min(sum_weights_1, sum_weights_2)
        weights1 = numpy.copy(sig1['weights'])
        weights2 = numpy.copy(sig2['weights'])

        if sum_weights_1 != sum_weights_2:
            # Add an entry to the end of weights2 with the difference
            weights2 = numpy.append(weights2, abs(sum_weights_2 - sum_weights_1))

            # Add a column to the dist_matrix filled with zeroes
            z = numpy.zeros((n_clusters, 1))
            dist_matrix = numpy.append(dist_matrix, z, axis=1)
            n_cols += 1

        # Solve the optimization
        problem = pulp.LpProblem("Transportation problem", sense=pulp.LpMinimize)
        routes = [(i, j) for i in range(n_clusters) for j in range(n_cols)]
        route_vars = pulp.LpVariable.dicts("Route", (range(n_clusters), range(n_cols)), 0, None, pulp.LpInteger)
        problem += pulp.lpSum([route_vars[i][j]*dist_matrix[i][j] for (i, j) in routes])

        # The supply maximum constraints are added to prob for each supply node
        for i in range(n_clusters):
            problem += pulp.lpSum([route_vars[i][j] for j in range(n_cols)]) <= weights1[i]

        # The demand minimum constraints are added to prob for each demand node (bar)
        for j in range(n_cols):
            problem += pulp.lpSum([route_vars[i][j] for i in range(n_clusters)]) >= weights2[j]

        problem.solve()
        flow_cost = pulp.value(problem.objective)
        return 1 / (1 + (flow_cost / flow_sum))

    @classmethod
    def kl_divergence(cls, m1, m2, e1, e2):
        d = len(m1)

        e1_inv = linalg.inv(e1)
        e2_inv = linalg.inv(e2)

        inv_trace = (numpy.dot(e2_inv, e1) + numpy.dot(e1_inv, e2)).trace()
        mean_product = numpy.dot(numpy.dot((m1 - m2).T, (e2_inv + e1_inv)), (m1 - m2))
        result = inv_trace - d + mean_product

        if result < 0:
            print("KL divergence is negative!!!")

        return result / 2


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