__author__ = 'dm'

import abc
import librosa
import numpy
import numpy.linalg as linalg


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
        mfccs = librosa.feature.mfcc(track_data, track_rate, n_mfcc=20)
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
        result = inv_trace - 2*d + mean_product

        div = result / 2
        return numpy.exp(-cls.gamma * div)

    @classmethod
    def get_engine_identifier(cls):
        return "Mandel_Ellis_v01"
