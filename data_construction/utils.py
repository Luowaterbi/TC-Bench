import numpy as np
from typing import List
import numpy as np
from scipy.linalg import qr

def transform2matrix(s:List[str]) -> np.ndarray:
    matrix = []
    for wc in s:
        row = [1 if c == 'W' else 0 for c in wc]
        matrix.append(row)
    matrix_np = np.array(matrix)
    return matrix_np

def transform2aw(matrix:np.ndarray) -> List[str]:
    aw_list = []
    for row in matrix:
        aw_str = ''.join(['W' if c == 1 else 'A' for c in row])
        aw_list.append(aw_str)
    return aw_list


def print_aw(s:List[str]) -> List[str]:
    for wc in s:
        wc = " ".join(wc.replace('A', '0').replace('W', '1'))
        print(wc)


def get_rank(matrix):
    rank = np.linalg.matrix_rank(matrix)
    return rank.item()


def get_basis(matrix, rank=None):
    if rank is None:
        rank = get_rank(matrix)
    q, r, p = qr(matrix.T, pivoting=True)
    basis_indices = p[:rank]
    return basis_indices.tolist()

def cal_jaccard_similarity(temp_matrix):
    intersection_matrix = temp_matrix @ temp_matrix.T
    row_sums = np.sum(temp_matrix, axis=1, keepdims=True)
    union_matrix = row_sums + row_sums.T - intersection_matrix
    jaccard_matrix = np.where(union_matrix == 0, 1.0, intersection_matrix / union_matrix)
    np.fill_diagonal(jaccard_matrix, 0)
    return np.sum(jaccard_matrix, axis=1), np.sum(jaccard_matrix)

