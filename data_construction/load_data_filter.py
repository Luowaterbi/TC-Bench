import json
import os
import random

def read_jsonl_to_dict(file_path):
    result = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            # 跳过 gen_nums 和 right_nums 都为 0 的条目
            if data.get("gen_nums", 0) == 0 and data.get("right_nums", 0) == 0:
                continue
            # 使用 tcb_id 作为 key，重复的直接覆盖
            result[data["tcb_id"]] = {
                "gen_nums": data["gen_nums"],
                "right_nums": data["right_nums"]
            }
    print(f"has flited {len(result)}")
    return result

def get_data(name="tcb", data_path=None,prefix_dir=None, save_dir=None, testcase_alg="", pass_rate_save_file=""):
    

    if name == "tcb":
        ds = json.load(open(data_path, "r", encoding="utf-8"))
        res = []
        ds = ds[0:1]
        for item in ds:
            if not os.path.exists(prefix_dir.format(item['tcb_id'])):
                continue
            solutions = []
            if len(item['solutions']) < 8:
                solutions = item['solutions']
            else:
                solutions = random.sample(item['solutions'], 8)
            for c in (solutions):
                res.append({
                    "code": c['code'],
                    "time_limit": item["runtime_limit"],
                    "memory_limit": item["memory_limit"],
                    "compileAndRunOptions": c["compileAndRunOptions"],
                    "test_cases": prefix_dir.format(item['tcb_id']),
                    "save_path": save_dir.format(item['tcb_id']),
                    "problem_id": item['tcb_id'],
                    "testcase_alg": testcase_alg
                })
    return res


if __name__ == "__main__":
    model_name = "deepseek-v3"
    testcase_alg = "crux"
    base_dir = ""
    pass_rate_save_file = f"{base_dir}/save_tests_{model_name}-fliter/{testcase_alg}/test_pass_rate.jsonl"

    data = get_data(name="tcb", prefix_dir=f"{base_dir}/save_tests_{model_name}/{testcase_alg}/" + "tests-{}.jsonl", save_dir=f"{base_dir}/save_tests_{model_name}-fliter/{testcase_alg}/" + "tests-{}.jsonl", testcase_alg=testcase_alg, pass_rate_save_file=pass_rate_save_file)
    print(len(data))