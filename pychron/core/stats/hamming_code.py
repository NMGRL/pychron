import numpy as np

G = np.array([[1, 0, 0, 0, 1, 1, 1], [0, 1, 0, 0, 0, 1, 1], [0, 0, 1, 0, 1, 0, 1], [0, 0, 0, 1, 1, 1, 0]])
H = np.array([[1, 0, 1, 1, 1, 0, 0], [1, 1, 0, 1, 0, 1, 0], [1, 1, 1, 0, 0, 0, 1], ])

def encode(m):
    m = np.frombuffer(m.encode(), dtype=np.uint8)-ord('0')
    en = np.dot(m, G) % 2
    return en


def decode(m):
    dec = np.dot(H, m) % 2
    return dec


# def flipbit(enc, bitpos):
#     if (enc[bitpos] == 1):
#         enc[bitpos] = 0
#     else:
#         enc[bitpos] = 1
#     return enc



