import json
import os

def get_testcases(testcase_path):
    data = []
    if not os.path.exists(testcase_path):
        return []
    with open(testcase_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

import random
def get_data(name="tcb", data_path='', prefix_dir="",testcase_alg = ""):

    ds = json.load(open(data_path, "r", encoding="utf-8"))
    res = []
    for item in ds:
        testcases = os.path.join(prefix_dir, f"tests-{item['tcb_id']}.jsonl")
        for idx, c in enumerate(item["wrong_code"]):
            res.append({
                "code": c['code'],
                "compileAndRunOptions": c["compileAndRunOptions"],
                "time_limit": item["runtime_limit"],
                "memory_limit": item["memory_limit"],
                "test_cases": testcases,
                "problem_id": item['tcb_id'],
                "code_id": idx,
                "rank": len(item["wrong_code"]),
            })
    return res

def save_back_results(problem_results, data_path = "",name="tcb", save_dir="results"):
    ds = json.load(open(data_path, "r", encoding="utf-8"))
    ds_dict = {}
    for item in ds:
        ds_dict[item['tcb_id']] = item
    for problem_id, v in problem_results.items():
        ds_dict[problem_id]["res"] = [{"status": code_info["status"], "details": code_info["details"]} for code_info in v["codes"]]
    json.dump(ds, open(f"{save_dir}/{name}-extracted_executed.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)


if __name__ == "__main__":
    ds = json.load(open("/home/luoxianzhen/yang/eval_wrong_code/results/all_results.json"))
    save_back_results(ds, name="codeforces")
    print("Data loaded and saved back successfully.")
