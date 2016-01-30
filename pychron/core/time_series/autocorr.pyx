'''
see http://paulbourke.net/geometry/polyarea/


'''
cimport numpy as np


cdef autocorr(np.ndarray[np.float64_t] data, int nlags=100):

    cdef int n = len(data)
    cdef float m = np.mean(data)
    cdef float sum = 0
    cdef list rh = []
    cdef float Co = np.var(data)
    for h in range(0, nlags):
        sum = 0
        for i in range(0, n - h):
            sum += ((data[i] - m) * (data[i + h] - m))
        rh.append((sum / n) / Co)

    return rh
