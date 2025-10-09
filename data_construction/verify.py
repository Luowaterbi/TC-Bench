import json
from utils import *


def verify_balance(input_file = ""):
    ds = json.load(open(input_file))
    for k, v in ds.items():
        if "balance_jaccard" not in v:
            balance_value = v["jaccard"]
            final_jaccard_wc = v["wc"]
            basis = v["basis_indices"]
            tmp_wc = [final_jaccard_wc[i] for i in basis]
            tmp_matrix = transform2matrix(tmp_wc)
            balance_jaccard_row_sum = v["jaccard_row_sum"]
        else:
            balance_value = v["balance_jaccard"]
            final_jaccard_wc = v["final_jaccard_wc"]
            basis = v["balance_jaccard_basis"]
            tmp_wc = [final_jaccard_wc[i] for i in basis]
            tmp_matrix = transform2matrix(tmp_wc)
            balance_jaccard_row_sum = v["balance_jaccard_row_sum"]

        balance_states, calculated_balance_value = cal_jaccard_similarity(tmp_matrix)
        
        if abs(balance_value - calculated_balance_value) > 1e-6:
            print(f"Problem {k} has inconsistent balance values: "
                  f"stored={balance_value}, calculated={calculated_balance_value}")
        # else:
        #     print(f"Problem {k} balance value is consistent: {balance_value}")
        if not np.allclose(balance_states, balance_jaccard_row_sum):
            print(f"Problem {k} has inconsistent balance states: "
                  f"stored={balance_jaccard_row_sum}, calculated={balance_states}")


verify_balance("data/0903/balance_v1.0.dev.json")