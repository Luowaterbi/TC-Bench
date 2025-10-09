import os
import json
from datetime import datetime
from load_data import get_data, save_back_results
from excute_tool_linux import run_cpp_code_linux
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import logging

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

import time
def process_code_with_logging(data_item):
    """包装函数，用于添加日志"""
    problem_id = data_item["problem_id"]
    code_id = data_item["code_id"]

    try:
        result = run_cpp_code_linux(data_item, test_mode)
        status = result.get("error", "Unknown")
        logger.info(f"执行完成 - 问题ID: {problem_id}, 代码ID: {code_id}, 状态: {status}")
        return result
    except Exception as e:
        logger.error(f"执行异常 - 问题ID: {problem_id}, 代码ID: {code_id}, 错误: {str(e)}")
        data_item["error"] = ["EXE"]
        data_item["details"] = str(e)
        return data_item


def save_results(results, correct_code_output_file, output_file):
    """保存结果到文件"""

    # 初始化结果字典
    problem_results = {}
    status_counts = {"AC": 0, "CE": 0, "TLE": 0, "MLE": 0, "RE": 0, "WA": 0, "EXE": 0}

    # 分类归整结果
    for result in results:
        problem_id = result["problem_id"]
        code_id = result["code_id"]
        status = result.get("error", [])

        if len(status) == [] or all(sta == "AC" for sta in status):
            status_counts['AC'] += 1
        else:
            sta = [x for x in status if x != "AC"][0]
            status_counts[sta] += 1

        # 加入问题结果集
        if problem_id not in problem_results:
            problem_results[problem_id] = {
                "problem_id": problem_id,
                "codes": [],
                "time_limit": result["time_limit"],
                "memory_limit": result["memory_limit"],
                "test_cases": result["test_cases"]
            }

        # 添加代码执行结果
        problem_results[problem_id]["codes"].append({
            "code_id": code_id,
            "code": result["code"],
            "status": status,
            "details": result.get("details", ""),
        })
        # 保存完整结果
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(problem_results, f, indent=3)

    # 保存正确的代码（AC状态）
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

    # 保存正确代码结果
    with open(correct_code_output_file, "w", encoding="utf-8") as f:
        json.dump(correct_codes, f, indent=3)

    # 返回状态统计
    return status_counts, problem_results


rank_p = 5
if __name__ == "__main__":
    import argparse

    # 创建一个解析器
    parser = argparse.ArgumentParser(description="Process testcase algorithm and model name.")
    test_mode = False
    # 添加命令行参数
    parser.add_argument('--testcase_alg', type=str, default="crux", help="Algorithm for testcase.")
    parser.add_argument('--model_name', type=str, default="claude-sonnet-4-20250514-thinking", help="Model name.")
    parser.add_argument('--cpu', type=int, default=50, help="cpu count")
    parser.add_argument('--prefix_url', type=str, default='./', help="testcase path")
    parser.add_argument('--data_path', type=str, default='TestcaseBench-v29.json', help="TC-Bench data path")

    # 解析命令行参数
    args = parser.parse_args()

    # 将命令行参数赋值给变量
    testcase_alg = args.testcase_alg
    model_name = args.model_name
    cpu = args.cpu
    prefix_url = args.prefix_url
    data_path = args.data_path

    datasets_name = f"tcb-{model_name}-{testcase_alg}"

    logger = setup_logging()
    logger.info("开始执行代码评估...")
    logger.info(datasets_name)

    data = get_data(name=datasets_name, data_path=data_path, prefix_dir=f"{prefix_url}/save_tests_{model_name}-fliter/{testcase_alg}/", testcase_alg=testcase_alg)
    logger.info(f"加载了 {len(data)} 个代码项目")

    logger.info(f"使用 {cpu} 个CPU核心进行并行处理")
    import time

    # 记录开始时间
    start_time = time.time()

    with Pool(cpu) as pool:
        results = list(tqdm(
            pool.imap_unordered(process_code_with_logging, data),
            total=len(data),
            desc="执行进度"
        ))
    end_time = time.time()

    # 计算并打印执行时间
    execution_time = end_time - start_time
    results = sorted(results, key=lambda x: (x["problem_id"], x["code_id"]))
    logger.info("所有代码执行完成，开始保存结果...")
    save_dir = "ALLmode_results" if not test_mode else "rank_result"
    os.makedirs("ALLmode_results", exist_ok=True)

    json.dump(results, open(f"{save_dir}/{datasets_name}-{testcase_alg}.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    logger.info(f"结果已保存到 {save_dir}/{datasets_name}-{testcase_alg}.json")
    status_counts, problem_results = save_results(results,correct_code_output_file=f"{save_dir}/{datasets_name}-{testcase_alg}-correct.json", output_file=f"{save_dir}/{datasets_name}-{testcase_alg}-all.json")
    for status, count in status_counts.items():
        percentage = (count / len(results)) * 100
        logger.info(f"{status}: {count} ({percentage:.2f}%)")
    logger.info("结果还原到原始格式并保存...")
    save_back_results(problem_results, data_path=data_path, name=f"{datasets_name}-{testcase_alg}", save_dir=save_dir)
    logger.info("结果还原完成，保存到原始文件")
    logger.info(f"执行时间：{execution_time} ")
