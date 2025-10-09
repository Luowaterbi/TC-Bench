import numpy as np
from scipy.linalg import lu,qr # Can be used for rank, or numpy.linalg.matrix_rank
from itertools import combinations
from collections import Counter
import json
from utils import *
from multiprocessing import Pool, cpu_count
import os
from tqdm import tqdm
import random
import logging
from datetime import datetime

def init():
    ds = json.load(open("data/filter_info.json"))
    new_ds = {}
    for pro, infos in ds.items():
        rank = infos["rank"]
        wc = infos["wc"]
        matrix = transform2matrix(wc)
        basis_indices = get_basis(matrix, rank)
        infos["rank"] = rank
        infos["basis_indices"] = basis_indices
        temp_matrix = matrix[basis_indices, :]
        infos["jaccard_row_sum"], infos["jaccard"] = cal_jaccard_similarity(temp_matrix)
        new_infos = {
            "rank": rank,
            "basis_indices": basis_indices,
            "jaccard_row_sum": infos["jaccard_row_sum"].tolist(),
            "jaccard": infos["jaccard"].item(),
            "wc": infos["wc"],
            "name": pro
        }
        new_ds[pro] = new_infos
    json.dump(new_ds, open("data/0903/init.json", "w"), indent=4)

def setup_logger(log_file=None):
    if log_file is None:
        log_file = f"logs/solve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def find_balance(info):
    name, matrix, rank, basis, balance_metric = info
    basis = np.array(basis)
    R = matrix[basis, :]
    all_indices = np.arange(matrix.shape[0])
    X = np.setdiff1d(all_indices, basis)  

    if balance_metric == "jaccard":
        balance_states, balance_value = cal_jaccard_similarity(R)
    else:
        raise ValueError(f"Unknown balance_metric: {balance_metric}")
    
    max_iter = 1000
    iter_count = 0
    # logger.info(f"[{name}] Starting optimization with initial {balance_metric}={balance_value}")
    while iter_count < max_iter:
        iter_count += 1
        change = [balance_states, balance_value, None, None, None]
        balance_min = balance_value
        
        for i_idx, i in enumerate(basis):
            i_row = matrix[i]
            for j in X:
                j_row = matrix[j]
                temp_basis = basis.copy()
                temp_basis[i_idx] = j
                R_temp = matrix[temp_basis, :]

                if get_rank(R_temp) < rank:
                    continue

                if balance_metric == "jaccard":
                    temp_balance_states, temp_balance_value = cal_jaccard_similarity(R_temp)
                else:
                    raise ValueError(f"Unknown balance_metric: {balance_metric}")
                
                if temp_balance_value < balance_min:
                    balance_min = temp_balance_value
                    change = [temp_balance_states, temp_balance_value, i, i_idx, j]

        if change[2] is not None:
            # logger.info(f"[{name}] Iter {iter_count}: {balance_metric} improved from {balance_value} to {change[1]} (swap index {i} -> {j})")
            balance_states, balance_value, i, i_idx, j = change
            basis[i_idx] = j
            X = np.setdiff1d(all_indices, basis)
        else:
            break
    return name, basis.tolist(), balance_value, balance_states.tolist(), matrix


PATH = "/data/TestcaseBenchmark/final/data/0903/"
def better_problem(var_threshold=0, source_file="init.json", output_file="balance_v1.0.json", balance_metric="jaccard"):
    ds = json.load(open(PATH + source_file))
    turn = 0
    writer = open((PATH + output_file).replace("json", "jsonl"), "w")
    if balance_metric == "jaccard":
        balance_states_name = "balance_jaccard_row_sum"
        balance_value_name = "balance_jaccard"
        balance_basis_name = "balance_jaccard_basis"
        balance_wc_name = "final_jaccard_wc"
    else:
        raise ValueError(f"Unknown balance_metric: {balance_metric}")
    logger = setup_logger()
    logger.info(f"Starting better_problem with balance_metric={balance_metric}, var_threshold={var_threshold}")
    
    while turn < 10000:
        turn += 1
        logger.info(f"Turn {turn}...")
        infos = []
        for k, p in ds.items():
            if balance_value_name not in p:
                value_name = balance_metric
            else:
                value_name = balance_value_name
            
            if p[value_name] <= var_threshold or p["rank"] == len(p["wc"]):
                continue
            final_wc = p["wc"].copy()
            random.shuffle(final_wc)
            matrix = transform2matrix(final_wc)
            basis_indices = get_basis(matrix, p["rank"])
            infos.append([p["name"], matrix, p["rank"], basis_indices, balance_metric])
        logger.info(f"Processing {len(infos)} problems with {balance_value_name} > {var_threshold}...")
        if not infos:
            logger.info("No more problems to process.")
            break
        pool = Pool(cpu_count()-4)
        processed_count = 0
        for name, basis, var, matrix_column_sum, matrix in tqdm(pool.imap_unordered(find_balance, infos), total=len(infos)):
        # for name, basis, var, matrix_column_sum in tqdm(find_balance(info) for info in infos):
            if balance_value_name not in ds[name]:
                value_name = balance_metric
            else:
                value_name = balance_value_name
            if var < ds[name][value_name]:
                # print(f"{name}: {ds[name][balance_value_name] if balance_value_name in ds[name] else None} -> {var}", flush=True)
                logger.info(f"{name}: {ds[name][value_name]} -> {var}")
                final_wc = transform2aw(matrix)
                ds[name][balance_wc_name] = final_wc
                ds[name][balance_basis_name] = basis
                ds[name][balance_value_name] = var
                ds[name][balance_states_name] = matrix_column_sum
                writer.write(json.dumps(ds[name]) + "\n")
                processed_count += 1
        logger.info(f"Turn {turn} completed. Updated {processed_count} problems.")
    
    json.dump(ds, open(PATH + output_file, "w"), indent=4)


def merge(input_file="data/0903/init.json", jsonl_file="data/0903/balance_v1.0.jsonl", output_file="data/0903/balance_v1.0.dev.json"):
    ds = json.load(open(input_file))
    with open(jsonl_file, "r") as f:
        for line in f:
            data = json.loads(line.strip())
            name = data["name"]
            # print(f"{name}: {ds[name]['balance_jaccard']} -> {data['balance_var']}")
            ds[name]["balance_jaccard_row_sum"] = data["balance_jaccard_row_sum"]
            ds[name]["balance_jaccard"] = data["balance_jaccard"]
            ds[name]["balance_jaccard_basis"] = data["balance_jaccard_basis"]
            ds[name]["final_jaccard_wc"] = data["final_jaccard_wc"]
    
    json.dump(ds, open(output_file, "w"), indent=4)

# merge()
def add_code(input_file, output_file):
    ds = json.load(open(input_file))
    sources = json.load(open("data/pro2sub_with_info.json"))
    correct = json.load(open("./data/select_correct_code.json"))
    final_ds = {}
    for k, v in ds.items():
        rank = v["rank"]
        if "balance_jaccard" not in v:
            final_jaccard_wc = v["wc"]
            basis = v["basis_indices"]
            tmp_wc = [final_jaccard_wc[i] for i in basis]
        else:
            final_jaccard_wc = v["final_jaccard_wc"]
            basis = v["balance_jaccard_basis"]
            tmp_wc = [final_jaccard_wc[i] for i in basis]

        source = sources[k]
        mapping = {c["output_str"]:c for c in source["codes"]}
        wrong_code = [mapping[wc] for wc in tmp_wc]
        source["cowrong_codes"] = wrong_code
        source["rank"] = rank
        source["correct_codes"] = correct[k]
        del source["codes"]

        final_ds[k] = source
    json.dump(final_ds, open(output_file, "w"), indent=4)

if __name__ == "__main__":
    add_code(input_file="data/0903/balance_v1.0.dev.json", output_file="data/0903/balance_v1.0.dev_with_code.json")
    # better_problem(var_threshold=0, source_file="init.json", output_file="balance_v1.0.json", balance_metric="jaccard")
    # init()
    # merge()