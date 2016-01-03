__author__ = 'dm'

import numpy
import numpy.linalg as linalg
import pulp
import math


def kl_divergence(means1, covariance1, means2, covariance2):
    d = len(means1)

    e1_inv = linalg.inv(covariance1)
    e2_inv = linalg.inv(covariance2)

    inv_trace = (numpy.dot(e2_inv, covariance1) + numpy.dot(e1_inv, covariance2)).trace()
    mean_product = numpy.dot(numpy.dot((means1 - means2).T, (e2_inv + e1_inv)), (means1 - means2))
    result = inv_trace - 2*d + mean_product

    return result / 2


def earth_movers_distance(hist1, hist2, distance_matrix):  # Histogram 1 must always be the larger one
    sum_weights_1 = numpy.sum(hist1)
    sum_weights_2 = numpy.sum(hist2)
    flow_sum = min(sum_weights_1, sum_weights_2)

    n_bins = len(hist1)
    n_cols = len(hist1)

    if sum_weights_1 != sum_weights_2:
            # Add an entry to the end of hist2 with the difference
            hist2 = numpy.append(hist2, abs(sum_weights_2 - sum_weights_1))

            # Add a column to the dist_matrix filled with zeroes
            z = numpy.zeros((n_cols, 1))
            distance_matrix = numpy.append(distance_matrix, z, axis=1)
            n_cols += 1

    # Solve the optimization
    problem = pulp.LpProblem("Transportation problem", sense=pulp.LpMinimize)
    routes = [(i, j) for i in range(n_bins) for j in range(n_cols)]
    route_vars = pulp.LpVariable.dicts("Route", (range(n_bins), range(n_cols)), 0, None, pulp.LpInteger)
    problem += pulp.lpSum([route_vars[i][j]*distance_matrix[i][j] for (i, j) in routes])

    # The supply maximum constraints are added to prob for each supply node
    for i in range(n_bins):
        problem += pulp.lpSum([route_vars[i][j] for j in range(n_cols)]) <= hist1[i]

    # The demand minimum constraints are added to prob for each demand node
    for j in range(n_cols):
        problem += pulp.lpSum([route_vars[i][j] for i in range(n_bins)]) >= hist2[j]

    problem.solve()
    flow_cost = pulp.value(problem.objective)


    return flow_cost / flow_sum


def quadratic_chi_distance(hist1, hist2, distance_matrix):
    norm_factor = 0.5

    # Convert distance matrix into similarity matrix
    m = numpy.amax(distance_matrix)
    dim = distance_matrix.shape[0]

    for i in range(dim):
        for j in range(dim):
            distance_matrix[i][j] = 1 - distance_matrix[i][j] / m

    result = 0
    for i in range(dim):
        for j in range(dim):
            qcdq1 = qcd_quotient(hist1, hist2, distance_matrix, i, norm_factor)
            qcdq2 = qcd_quotient(hist1, hist2, distance_matrix, j, norm_factor)
            result += qcdq1 * qcdq2 * distance_matrix[i][j]

    if result < 0:
        return 0
    return math.sqrt(result)


def qcd_quotient(hist1, hist2, distance_matrix, i, m):
    numerator = hist1[i] - hist2[i]
    denominator = 0

    for c in range(distance_matrix.shape[0]):
        denominator += (hist1[c] + hist2[c]) * distance_matrix[c][i]

    denominator = denominator ** m

    if numerator == 0 and denominator == 0:
        return 0

    return numerator / denominator