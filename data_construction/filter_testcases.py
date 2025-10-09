import os
import json
from datetime import datetime
from load_data_filter import get_data
from excute_tool_filter import run_cpp_code_linux
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import logging

import re

def is_decimal(s):
    try:
        a = float(s)
    except:
        return False
        
    return bool(re.match(r"^-?\d+\.\d+$", s))

def get_testcases(testcase_path):
    data = []
    if not os.path.exists(testcase_path):
        return []
    with open(testcase_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def check_difference(arr):
    if len(arr) <= 0 or not is_decimal(arr[0]):
        return False
    # 
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            # 
            if abs(float(arr[i]) - float(arr[j])) > 1e-6:
                return False  # 
    return True  # 

def append_dict_to_jsonl(file_path, data_dict):
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data_dict, ensure_ascii=False) + '\n')

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def process_code_with_logging(data_item):
    """包装函数，用于添加日志"""
    problem_id = data_item["problem_id"]
    try:
        result = run_cpp_code_linux(data_item)
        status = result.get("error", "Unknown")
        logger.info(f"执行完成 - 问题ID: {problem_id}, 状态: {status}")
        return result
    except Exception as e:
        logger.error(f"执行异常 - 问题ID: {problem_id}, 错误: {str(e)}")
        data_item["error"] = ["EXE"]
        data_item["details"] = str(e)
        return data_item


def save_results(results, correct_code_output_file, output_file):
    
    problem_results = {}
    status_counts = {"AC": 0, "CE": 0, "TLE": 0, "MLE": 0, "RE": 0, "WA": 0, "EXE": 0}
    
    for result in results:
        problem_id = result["problem_id"]
        code_id = result["code_id"]
        status = result.get("error", "Unknown")

        for status_name in status_counts.keys():
            if status_name == "AC" and not all(sta == "AC" for sta in status):
                continue
            if status_name in status:
                status_counts[status_name] += 1
        
        if problem_id not in problem_results:
            problem_results[problem_id] = {
                "problem_id": problem_id,
                "codes": [],
                "time_limit": result["time_limit"],
                "memory_limit": result["memory_limit"],
                "test_cases": result["test_cases"]
            }
        
        problem_results[problem_id]["codes"].append({
            "code_id": code_id,
            "code": result["code"],
            "status": status,
            "details": result.get("details", "")
        })
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(problem_results, f, indent=3)
    
    correct_codes = {}
    for problem_id, problem_data in problem_results.items():
        correct_problem_codes = []
        for code_info in problem_data["codes"]:
            if all(status == "AC" for status in code_info["status"]):
                correct_problem_codes.append({
                    "code_id": code_info["code_id"],
                    "code": code_info["code"]
                })
        
        if correct_problem_codes:
            correct_codes[problem_id] = {
                "problem_id": problem_id,
                "codes": correct_problem_codes,
                "time_limit": problem_data["time_limit"],
                "memory_limit": problem_data["memory_limit"],
                "test_cases": problem_data["test_cases"]
            }
    
    with open(correct_code_output_file, "w", encoding="utf-8") as f:
        json.dump(correct_codes, f, indent=3)
    
    return status_counts, problem_results
import os
if __name__ == "__main__":
    datasets_name = "tcb"
    import argparse
    parser = argparse.ArgumentParser(description="Process testcase algorithm and model name.")
    
    parser.add_argument('--testcase_alg', type=str, default="lcb", help="Algorithm for testcase.")
    parser.add_argument('--model_name', type=str, default="claude-sonnet-4-20250514-thinking", help="Model name.")
    parser.add_argument('--base_dir', type=str, default="", help="base_dir")
    parser.add_argument('--cpu', type=int, default=50, help="cpu_count")
    parser.add_argument('--data_path', type=str, default='TestcaseBench-v29.json', help="TC-Bench data path")

    args = parser.parse_args()

    testcase_alg = args.testcase_alg
    model_name = args.model_name
    base_dir = args.base_dir
    cpu = args.cpu
    data_path = args.data_path

    save_dir = f"{base_dir}/save_tests_{model_name}-fliter/{testcase_alg}/" + "tests-{}.jsonl"

    os.makedirs(f"{base_dir}/save_tests_{model_name}", exist_ok=True)
    os.makedirs(f"{base_dir}/save_tests_{model_name}-fliter/{testcase_alg}", exist_ok=True)

    test_dir = f"{base_dir}/save_tests_{model_name}/{testcase_alg}/" + "tests-{}.jsonl"
    pass_rate_save_file = f"{base_dir}/save_tests_{model_name}-fliter/{testcase_alg}/test_pass_rate.jsonl"

    logger = setup_logging()
    logger.info("开始执行代码评估...")

    data = get_data(name=datasets_name, data_path=data_path, prefix_dir=test_dir, save_dir=save_dir, testcase_alg=testcase_alg, pass_rate_save_file=pass_rate_save_file)
    logger.info(f"加载了 {len(data)} 个代码项目")

    logger.info(f"使用 {cpu} 个CPU核心进行并行处理")

    with Pool(cpu) as pool:
        results = list(tqdm(
            pool.imap_unordered(process_code_with_logging, data),
            total=len(data),
            desc="执行进度"
        ))
    logger.info("所有代码执行完成 - 开始保存筛选后的测试样例")

    result_dict = {}
    for item in results:
        if item['problem_id'] not in result_dict.keys():
            result_dict[item['problem_id']] = [item, ]
        else:
            result_dict[item['problem_id']].append(item)

    for k, v in result_dict.items():
        testcases = get_testcases(test_dir.format(k))
        save_path = save_dir.format(k)
        status_array_length = len(v[0]["error"])
        remove_index = []
        status_wrong = ["TLE", "RE", "MLE", "WA", "EXE"]
        for idx, item in enumerate(v):
            if all(e in status_wrong for e in item["error"]):
                remove_index.append(idx)
        remove_index.sort(reverse=True)
        for idx in remove_index:
            del v[idx]
        
        saved_nums = 0
        for i in range(status_array_length):
            all_AC = True 
            all_WA = True
            output_list = []
            status_list = []

            for item in v:
                if i >= len(item["error"]):
                    logger.info(f"{k} error list not the same")
                    continue
                status_list.append(item['error'][i])
                output_list.append(item['details'][i])
                if not item["error"][i] == "AC":
                    all_AC = False
                
                if not item["error"][i] == "WA":
                    all_WA = False
            
            if all_AC:
                append_dict_to_jsonl(save_path, testcases[i])
                saved_nums += 1
                
            if all_WA and (len(list(set(output_list))) == 1 or check_difference(output_list)):
                testcases[i]['output'] = output_list[0]
                append_dict_to_jsonl(save_path, testcases[i])
                saved_nums += 1

        append_dict_to_jsonl(pass_rate_save_file, {
            "tcb_id": k,
            "gen_nums": len(testcases),
            "right_nums": saved_nums
        })

