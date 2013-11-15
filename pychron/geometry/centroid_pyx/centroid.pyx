'''
see http://paulbourke.net/geometry/polyarea/


'''
# @PydevCodeAnalysisIgnore
import numpy as np
cimport numpy as np
def _area(np.ndarray[np.float64_t, ndim=2] data):
	cdef int n = data.shape[0]
	cdef int j = n - 1
	cdef float x = 0
	cdef float y = 0
	cdef float a = 0
	for i in range(n):
		p1 = data[i]
		p2 = data[j]
		a += (p1[0] * p2[1])
		a -= (p1[1] * p2[0])
		j = i
	return a / 2

def calculate_centroid(np.ndarray[np.float64_t, ndim=2] data):
	cdef int n = data.shape[0]
	cdef int j = n - 1
	cdef float x = 0
	cdef float y = 0
	for i in range(n):
		p1 = data[i]
		p2 = data[j]
		f = p1[0] * p2[1] - p2[0] * p1[1]
		x += (p1[0] + p2[0]) * f
		y += (p1[1] + p2[1]) * f
		j = i

	cdef float a = _area(data)
	return x / (6 * a), y / (6 * a)

# def circle_approx(np.ndarray[np.float64_t, ndim=2] data, float tol):
# 	cdef int n = data.shape[0]
#
# 	cdef float x=0
# 	cdef float y=0
#
# 	x,y=calculate_centroid(data)
#
# 	cdef np.ndarray[np.float64_t, ndim=2] ndata
# 	for i in range(n):
# 		#calc dist from centroid
# 		d=((cx-data[i,0])**2+(cy-data[i,1])**2)**0.5
#
# 		#include this point
# 		if d<tol:
# 			np.hstack((ndata,data[i])
